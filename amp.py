import os
from typing import Tuple
import requests
import json
import logging
from rpc import find_rpc
import threading
import time
import shutil

logger = logging.getLogger(__name__)

def list2dict(arr:list, idkey:str='id', cls=None, args=[]) -> dict:
    """Converts a list to dict using `idkey` field as key in the dict"""
    return { a[idkey]: cls(*args, **a) if cls else a for a in arr }

class APIException(Exception):
    def __init__(self, msg, code):
        self.msg = msg
        self.code = code
    
    def __str__(self):
        return f"Error {self.code}: {self.msg}"

class Asset(dict):
    def __init__(self, amp, **kwargs):
        self.amp = amp
        self._summary = {}
        self._assignments = None
        self._distributions = None
        self._lost_outputs = None
        super().__init__(**kwargs)

    def clear_cache(self):
        self._summary = {}
        self._assignments = None
        self._distributions = None
        self._lost_outputs = None

    def create_assignment(self, assignments):
        for ass in assignments:
            self.amp.fetch_json(f"/assets/{self.asset_uuid}/assignments/create", method="POST", data=json.dumps({"assignments": [ass]}))
        self.amp.clear_cache(f"/assets/{self.asset_uuid}/assignments")
        self._assignments = None

    def change_assignment(self, assid, action="lock"):
        if action == "delete":
            self.amp.fetch_json(f"/assets/{self.asset_uuid}/assignments/{assid}/delete", method="DELETE")
        elif action == "lock":
            self.amp.fetch_json(f"/assets/{self.asset_uuid}/assignments/{assid}/lock", method="PUT")
        elif action == "unlock":
            self.amp.fetch_json(f"/assets/{self.asset_uuid}/assignments/{assid}/unlock", method="PUT")
        else:
            raise RuntimeError("Unknown action")
        self.amp.clear_cache(f"/assets/{self.asset_uuid}/assignments")
        self._assignments = None

    def create_distribution(self):
        # sanity check that node is running and we have balance
        balance = self.balance()
        if balance['trusted'] == 0:
            raise RuntimeError("Not enough funds in the treasury wallet")
        res = self.amp.fetch_json(f"/assets/{self.asset_uuid}/distributions/create/")
        if 'distribution_uuid' not in res:
            raise APIException(str(res), 500)
        duuid = res['distribution_uuid']
        # write data to temp file
        fpath = f"data/assets/{self.asset_uuid}/distributions/{duuid}.json"
        try:
            os.makedirs(os.path.dirname(fpath))
        except:
            pass
        with open(fpath, "w") as f:
            f.write(json.dumps(res))
        # no need to check assignments - we just created the distribution
        # create transaction
        map_address_amount = res.get('map_address_amount')
        map_address_asset = res.get('map_address_asset')
        txid = self.treasury.sendmany('', map_address_amount, 0, duuid, [], False, 1, 'UNSET', map_address_asset)
        # spawn checking thread
        self.start_confirm_distribution_thread(txid, duuid)
        # clear cache
        self.amp.clear_cache(f"/assets/{self.asset_uuid}/distributions")
        self.amp.clear_cache(f"/assets/{self.asset_uuid}/assignments")
        self._distributions = None
        self._assignments = None
        return res

    def confirm_distribution_thread(self, txid, duuid, wallet):
        t0 = time.time()
        confs = wallet.gettransaction(txid).get('confirmations', 0)
        # 15 minutes max, continue as soon as we have 2 confirmations
        while time.time()-t0 < 60*15 and confs < 2:
            logger.warn(f"Waiting for {txid} to confirm. Currently {confs} confirmations")
            time.sleep(15)
            confs = wallet.gettransaction(txid).get('confirmations', 0)
        if confs == 0:
            logger.error("Transaction did not confirm. Abort.")
            return # timeout
        details = wallet.gettransaction(txid).get('details')
        tx_data = {'details': details, 'txid': txid}
        listunspent = wallet.listunspent()
        change_data = [u for u in listunspent if u['asset'] == self.asset_id and u['txid'] == txid]
        confirm_payload = {'tx_data': tx_data, 'change_data': change_data}
        res = self.amp.fetch_json(f"/assets/{self.asset_uuid}/distributions/{duuid}/confirm", method="POST", data=json.dumps(confirm_payload))
        logger.debug(res)
        # clear cache
        self.amp.clear_cache(f"/assets/{self.asset_uuid}/distributions")
        self.amp.clear_cache(f"/assets/{self.asset_uuid}/assignments")
        self._distributions = None
        self._assignments = None

    def start_confirm_distribution_thread(self, txid, duuid):
        t = threading.Thread(target=self.confirm_distribution_thread, args=(txid, duuid, self.treasury))
        t.start()

    def change_distribution(self, distribution_uuid, action):
        self.amp.clear_cache(f"/assets/{self.asset_uuid}/assignments")
        self._assignments = None
        if action == "cancel":
            raise NotImplementedError("Blockstream API can't cancel distribution even though it should.")
            self.amp.fetch_json(f"/assets/{self.asset_uuid}/distributions/{distribution_uuid}/cancel", method="DELETE")
        else:
            raise RuntimeError("Unknown action")

    @property
    def treasury(self):
        return self.amp.rpc.wallet("")

    def balance(self):
        b = self.treasury.getbalances()
        return { k: int(1e8*b.get("mine", {}).get(k, {}).get(self.asset_id, 0)) for k in ["trusted", "untrusted_pending"] }

    @property
    def users(self):
        return {
            uid: user
            for uid,user in self.amp.users.items()
            if all([cid in user.categories for cid in self['requirements']])
        }

    @property
    def summary(self):
        if not self._summary:
            self._summary = self.amp.fetch_json(f"/assets/{self.asset_uuid}/summary")
        return self._summary

    @property
    def assignments(self):
        if self._assignments is None:
            self._assignments = self.amp.fetch_json(f"/assets/{self.asset_uuid}/assignments")
        return self._assignments or []

    @property
    def pending_assignments(self):
        return sorted([ass for ass in self.assignments if not ass['is_distributed']], key=lambda ass: -ass['id'])

    @property
    def distributions(self):
        if self._distributions is None:
            self._distributions = self.amp.fetch_json(f"/assets/{self.asset_uuid}/distributions")
        return self._distributions or []

    @property
    def unconfirmed_distributions(self):
        pending_ass = self.pending_assignments
        untracked_uuids = {ass['distribution_uuid'] for ass in pending_ass if ass['distribution_uuid']}
        pending = [{
            "distribution_uuid": uuid,
            "distribution_status": "DRAFT",
            "transactions": [{
                "txid": None,
                "transaction_status": "DRAFT",
                "assignments": [
                    {
                        "registered_user": ass["registered_user"],
                        "amount": ass["amount"],
                    }
                    for ass in pending_ass
                    if ass['distribution_uuid'] == uuid
                ]
            }]
        } for uuid in untracked_uuids]
        unconfirmed = list(sorted([dist for dist in self.distributions if dist['distribution_status'] == 'UNCONFIRMED'], key=lambda dist: dist['id']))
        return pending + unconfirmed

    @property
    def lost_outputs(self):
        if self._lost_outputs is None:
            self._lost_outputs = self.amp.fetch_json(f"/assets/{self.asset_uuid}/lost-outputs")
        return self._lost_outputs

    @property
    def asset_uuid(self):
        return self['asset_uuid']

    @property
    def id(self):
        return self.asset_uuid

    @property
    def name(self):
        return self['name']

    @property
    def ticker(self):
        return self['ticker']

    @property
    def asset_id(self):
        return self['asset_id']

    @property
    def transfer_restricted(self):
        return self['transfer_restricted']
    
    @property
    def asset_type(self):
        return 'transfer restricted' if self.transfer_restricted else 'trackable'

    @property
    def status(self):
        s = []
        for k in ["is_registered", "is_authorized", "is_locked"]:
            s.append(k.replace("is_", "" if self[k] else "not "))
        return ", ".join(s)

    @property
    def categories(self):
        return {cat: self.amp.categories[cat] for cat in self['requirements']}

class User(dict):
    def __init__(self, amp, **kwargs):
        self.amp = amp
        super().__init__(**kwargs)

    @property
    def categories(self):
        return {cat: self.amp.categories[cat] for cat in self['categories']}


class Amp:
    def __init__(self, api, auth) -> None:
        self.api = api
        self.auth = auth
        self.assets = {}
        self.categories = {}
        self.users = {}
        self.managers = {}
        self._rpc = None

    @property
    def rpc(self):
        if self._rpc is None:
            self._rpc = find_rpc("liquidtestnet", liquid=True)
        return self._rpc

    @property
    def headers(self) -> dict:
        return {'content-type': 'application/json', 'Authorization': self.auth}

    def fetch(self, path:str, method="GET", data=None, cache=True) -> Tuple[str, int]:
        path = path.lstrip("/")
        fpath = f"public/api/{path}.json"
        # return cached version
        if method == "GET" and cache:
            if os.path.isfile(fpath):
                logger.debug(f"cached {path}")
                with open(fpath, "r") as f:
                    return f.read(), 200

        api_url = f"{self.api}{path}"
        params = dict(headers=self.headers)
        if data:
            params["data"] = data
        logger.debug(f"fetch {path}")
        res = requests.request( method, api_url, **params)
        try:
            os.makedirs(os.path.dirname(fpath))
        except:
            pass
        try:
            with open(fpath, "w") as f:
                f.write(res.text)
        except:
            pass
        return res.text, res.status_code

    def clear_cache(self, path=None):
        if path is not None:
            path = path.lstrip("/")
            fpath = f"public/api/{path}.json"
            if os.path.isfile(fpath):
                logger.debug(f"removed cached {path}")
                os.remove(fpath)
        else:
            try:
                shutil.rmtree("public/api")
            except:
                pass
            for ass in self.assets.values():
                ass.clear_cache()

    def fetch_json(self, path:str, method="GET", data=None):
        txt, code = self.fetch(path, method, data)
        if code < 200 or code > 299:
            raise APIException(txt, code)
        return json.loads(txt) if txt else {}

    def sync(self):
        self.users = list2dict(self.fetch_json("/registered_users"), cls=User, args=[self])
        self.assets = list2dict(self.fetch_json("/assets"), 'asset_uuid', cls=Asset, args=[self])
        self.categories = list2dict(self.fetch_json("/categories"))
        self.managers = list2dict(self.fetch_json("/managers"))
