import json
import logging
import os
import shutil
import threading
import time
from typing import Tuple

import requests
from cryptoadvance.specter.rpc import BitcoinRPC

from .rpc import find_rpc

logger = logging.getLogger(__name__)

USE_CACHE = False

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
        self._unconfirmed_distributions = {}
        self._reissuances = {}
        super().__init__(**kwargs)
        self.sync()

    def sync_summary(self):
        # fetch will happen on property access
        return self.summary

    def sync_assignments(self):
        # fetch will happen on property access
        return self.assignments

    def sync_distributions(self):
        # fetch will happen on property access
        return self.distributions

    def sync_lost_outputs(self):
        # fetch will happen on property access
        return self.lost_outputs

    def sync(self):
        # run every request in a thread to speed up initial fetch
        sync_fns = [
            self.sync_summary,
            self.sync_assignments,
            self.sync_distributions,
            self.sync_lost_outputs,
        ]
        threads = [threading.Thread(target=sync_fn) for sync_fn in sync_fns]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    def clear_cache(self):
        self._summary = {}
        self._assignments = None
        self._distributions = None
        self._lost_outputs = None

    def register(self):
        res = self.amp.fetch_json(f"/assets/{self.asset_uuid}/register")
        self.clear_cache()
        self.update(res)

    def get_utxos(self):
        return self.amp.fetch_json(f"/assets/{self.asset_uuid}/utxos")

    def change_utxo(self, action, txid, vout):
        if action not in ["lock", "unlock"]:
            raise ValueError(f"Invalid action {action}")
        endpoint = "blacklist" if action == "lock" else "whitelist"
        data = [{
            "txid": txid,
            "vout": vout,
        }]
        return self.amp.fetch_json(f"/assets/{self.asset_uuid}/utxos/{endpoint}", method="POST", data=json.dumps(data))

    def authorize(self):
        res = self.amp.fetch_json(f"/assets/{self.asset_uuid}/register-authorized")
        self.clear_cache()
        self.update(res)

    def change_requirements(self, cids):
        new_reqs = [cid for cid in cids if cid not in self['requirements']]
        removed_reqs = [cid for cid in self['requirements'] if cid not in cids]
        for cid in removed_reqs:
            self.amp.fetch_json(f"/categories/{cid}/assets/{self.asset_uuid}/remove", method="PUT")
            if cid in self.amp.categories:
                if self.asset_uuid in self.amp.categories[cid]["assets"]:
                    self.amp.categories[cid]["assets"].remove(self.asset_uuid)
        for cid in new_reqs:
            self.amp.fetch_json(f"/categories/{cid}/assets/{self.asset_uuid}/add", method="PUT")
            if cid in self.amp.categories:
                if self.asset_uuid not in self.amp.categories[cid]["assets"]:
                    self.amp.categories[cid]["assets"].append(self.asset_uuid)
        self['requirements'] = cids

    def create_assignment(self, assignments):
        for ass in assignments:
            self.amp.fetch_json(f"/assets/{self.asset_uuid}/assignments/create", method="POST", data=json.dumps({"assignments": [ass]}))
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
        self._assignments = None

    def create_distribution(self):
        # sanity check that node is running and we have balance
        balance = self.balance()
        # TODO: check that LBTC balance is enough
        if balance['trusted'] == 0:
            raise RuntimeError("Not enough funds in the treasury wallet")
        res = self.amp.fetch_json(f"/assets/{self.asset_uuid}/distributions/create/")
        if 'distribution_uuid' not in res:
            raise APIException(str(res), 500)
        duuid = res['distribution_uuid']
        # no need to check assignments - we just created the distribution
        # create transaction
        map_address_amount = res.get('map_address_amount')
        map_address_asset = res.get('map_address_asset')
        txid = self.treasury.sendmany('', map_address_amount, 0, duuid, [], False, 1, 'UNSET', map_address_asset)
        # spawn checking thread
        self.start_confirm_distribution_thread(txid, duuid)
        # clear cache
        self._distributions = None
        self._assignments = None
        return duuid

    def confirm_distribution_thread(self, txid, duuid, wallet):
        t0 = time.time()
        confs = wallet.gettransaction(txid).get('confirmations', 0)
        # 15 minutes max, continue as soon as we have 2 confirmations
        while time.time()-t0 < 60*15 and confs < 2:
            self._unconfirmed_distributions[duuid] = {"txid": txid, "confirmations": confs, "confirmed": False}
            logger.warn(f"Waiting for {txid} to confirm. Currently {confs} confirmations")
            time.sleep(15)
            confs = wallet.gettransaction(txid).get('confirmations', 0)
        self._unconfirmed_distributions[duuid] = {"txid": txid, "confirmations": confs, "confirmed": False}
        if confs == 0:
            logger.error("Transaction did not confirm. Abort.")
            return # timeout
        details = wallet.gettransaction(txid).get('details')
        tx_data = {'details': details, 'txid': txid}
        listunspent = wallet.listunspent()
        change_data = [u for u in listunspent if u['asset'] == self.asset_id and u['txid'] == txid]
        confirm_payload = {'tx_data': tx_data, 'change_data': change_data}
        for _ in range(3):
            try:
                res = self.amp.fetch_json(f"/assets/{self.asset_uuid}/distributions/{duuid}/confirm", method="POST", data=json.dumps(confirm_payload))
                break
            except:
                time.sleep(10)
        self._unconfirmed_distributions[duuid] = {"txid": txid, "confirmations": confs, "confirmed": True}
        logger.debug(res)
        # clear cache
        self._distributions = None
        self._assignments = None

    def start_confirm_distribution_thread(self, txid, duuid):
        self._unconfirmed_distributions[duuid] = {
            "txid": txid,
            "confirmations": 0,
            "confirmed": False,
        }
        t = threading.Thread(target=self.confirm_distribution_thread, args=(txid, duuid, self.treasury))
        t.start()

    def confirm_distribution(self, duuid):
        txid = self.get_distribution_tx(duuid)
        self.confirm_distribution_thread(txid, duuid, self.treasury)

    def change_distribution(self, distribution_uuid, action):
        self._assignments = None
        if action == "cancel":
            raise NotImplementedError("Blockstream API can't cancel distribution even though it should.")
            self.amp.fetch_json(f"/assets/{self.asset_uuid}/distributions/{distribution_uuid}/cancel", method="DELETE")
        elif action == "confirm":
            self.confirm_distribution(distribution_uuid)
        else:
            raise RuntimeError("Unknown action")

    def reissue(self, amount):
        # sanity check that node is running and we have balance
        balance = self.balance()
        if balance['trusted'] == 0:
            raise RuntimeError("Not enough funds in the treasury wallet")
        # TODO: check that LBTC balance is enough
        res = self.amp.fetch_json(f"/assets/{self.asset_uuid}/reissue-request", method="POST", data=json.dumps({"amount_to_reissue": amount}))
        reissue_amount = res['amount']
        # create transaction
        reissuedetails = self.treasury.reissueasset(self.asset_id, reissue_amount)
        # spawn checking thread
        self.start_confirm_reissue_thread(reissuedetails["txid"], reissuedetails["vin"], amount)
        return reissuedetails["txid"]

    def start_confirm_reissue_thread(self, txid, vin, amount):
        self._reissuances[txid] = {
            "vin": vin,
            "amount": amount,
            "confirmed": False,
            "confirmations": 0,
        }
        t = threading.Thread(target=self.confirm_reissuance_thread, args=(txid, vin, amount, self.treasury))
        t.start()

    def confirm_reissuance_thread(self, txid, vin, amount, wallet):
        t0 = time.time()
        confs = wallet.gettransaction(txid).get('confirmations', 0)
        # 15 minutes max, continue as soon as we have 2 confirmations
        while time.time()-t0 < 60*15 and confs < 2:
            self._reissuances[txid] = {"vin": vin, "confirmations": confs, "amount": amount, "confirmed": False}
            logger.warn(f"Waiting for {txid} to confirm. Currently {confs} confirmations")
            time.sleep(15)
            confs = wallet.gettransaction(txid).get('confirmations', 0)
        self._reissuances[txid] = {"vin": vin, "confirmations": confs, "amount": amount, "confirmed": False}
        if confs == 0:
            logger.error("Transaction did not confirm. Abort.")
            return # timeout
        details = wallet.gettransaction(txid).get('details')
        issuances = wallet.listissuances()
        listissuances = [issuance for issuance in issuances if issuance['txid'] == txid]

        confirm_payload = {'details': details, 'reissuance_output': {"txid": txid, "vin": vin}, 'listissuances': listissuances}
        for _ in range(3):
            try:
                res = self.amp.fetch_json(f"/assets/{self.asset_uuid}/reissue-confirm", method="POST", data=json.dumps(confirm_payload))
                break
            except:
                time.sleep(10)
        self._reissuances[txid] = {"txid": txid, "confirmations": confs, "confirmed": True}
        logger.debug(res)
        self._summary = {}

    def get_reissuance(self, txid):
        if txid not in self._reissuances:
            return None
        obj = {"txid": txid}
        obj.update(self._reissuances.get(txid, {}))
        return obj

    def fix_reissuances(self):
        issuances = self.treasury.listissuances(self.asset_id)
        listissuances = [issuance for issuance in issuances if issuance['asset'] == self.asset_id and issuance['isreissuance']]
        known = self.amp.fetch_json(f"/assets/{self.asset_uuid}/reissuances")
        known_txids = [tx["txid"] for tx in known]
        unknown = [issuance for issuance in listissuances if issuance["txid"] not in known_txids]
        for tx in unknown:
            txid = tx["txid"]
            vin = tx["vin"]
            details = self.treasury.gettransaction(txid).get('details')
            listissuances = [issuance for issuance in issuances if issuance['txid'] == txid]
            confirm_payload = {'details': details, 'reissuance_output': {"txid": txid, "vin": vin}, 'listissuances': listissuances}
            res = self.amp.fetch_json(f"/assets/{self.asset_uuid}/reissue-confirm", method="POST", data=json.dumps(confirm_payload))

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
    def is_reissuable(self):
        return self.summary.get('reissuance_tokens', 0) > 0

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

    def get_distribution(self, duuid):
        distr_arr = [d for d in self.unconfirmed_distributions if d['distribution_uuid'] == duuid]
        distr = None
        if distr_arr:
            distr = distr_arr[0]
            distr['confirmed'] = False
            distr['confirmations'] = self._unconfirmed_distributions.get(duuid, {}).get("confirmations")
        else:
            distr_arr = [d for d in self.distributions if d['distribution_uuid'] == duuid]
            if distr_arr:
                distr = distr_arr[0]
                distr['confirmed'] = True
        return distr

    def get_distribution_tx(self, duuid):
        txid = self._unconfirmed_distributions.get(duuid, {}).get("txid")
        if txid is not None:
            return txid
        txlist = self.treasury.listtransactions()
        for tx in txlist:
            if tx.get('comment') == duuid:
                txid = tx.get('txid')
                self._unconfirmed_distributions[duuid] = {"txid": txid, "confirmations": tx.get('confirmations', 0), "confirmed": False}
                self.start_confirm_distribution_thread(txid, duuid)
                return txid
        return txid

    @property
    def unconfirmed_distributions(self):
        pending_ass = self.pending_assignments
        untracked_uuids = {ass['distribution_uuid'] for ass in pending_ass if ass['distribution_uuid']}
        pending = [{
            "distribution_uuid": uuid,
            "distribution_status": "UNCONFIRMED",
            "transactions": [{
                "txid": self.get_distribution_tx(uuid),
                "transaction_status": "UNCONFIRMED",
                "assignments": [
                    ass
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

    def update_categories(self, cids):
        new_categories = [cid for cid in cids if cid not in self['categories']]
        removed_categories = [cid for cid in self['categories'] if cid not in cids]
        for cid in new_categories:
            self.amp.fetch_json(f"/categories/{cid}/registered_users/{self['id']}/add", method="PUT")
        for cid in removed_categories:
            self.amp.fetch_json(f"/categories/{cid}/registered_users/{self['id']}/remove", method="PUT")
        self['categories'] = cids

    @property
    def categories(self):
        return {cat: self.amp.categories[cat] for cat in self['categories']}


class Amp:
    def __init__(self, api, auth, rpc) -> None:
        self.api = api
        self.auth = auth
        self.assets = {}
        self.categories = {}
        self.users = {}
        self.managers = {}
        self.healthy = False
        self._rpc = rpc
        self._session = None

    @property
    def session(self):
        if self._session is None:
            self._session = requests.Session()
        return self._session

    def new_asset(self, obj):
        w = self.rpc.wallet()
        addr = w.getnewaddress()
        data = {
            "name": obj.get("asset_name"),
            "amount": int(obj.get("amount") or 0),
            "destination_address": addr,
            "domain": obj.get("domain"),
            "ticker": obj.get("ticker"),
            "precision": int(obj.get("precision", 0)),
            "pubkey": obj.get("pubkey") or w.getaddressinfo(addr).get('pubkey'),
            "is_confidential": bool(obj.get("is_confidential")),
            "is_reissuable": (int(obj.get("reissue", 0) or 0) > 0),
            "reissuance_amount": int(obj.get("reissue", 0) or 0),
            "reissuance_address": w.getnewaddress(),
            "transfer_restricted": bool(obj.get("transfer_restricted")),
        }
        res = self.fetch_json("/assets/issue", method="POST", data=json.dumps(data))
        aid = res['asset_uuid']
        self.sync()
        return self.assets[aid]

    def new_category(self, name, description=""):
        data = {
            "name": name,
            "description": description,
        }
        res = self.fetch_json("/categories/add", method="POST", data=json.dumps(data))
        self.sync()
        return res['id']

    def new_user(self, name, gaid, is_company=False, categories=[]):
        data = {
            "name": name,
            "GAID": gaid,
            "is_company": is_company,
        }
        res = self.fetch_json("/registered_users/add", method="POST", data=json.dumps(data))
        uid = res['id']
        for cid in categories:
            self.fetch_json(f"/categories/{cid}/registered_users/{uid}/add", method="PUT")
        self.users = list2dict(self.fetch_json("/registered_users"), cls=User, args=[self])
        return res['id']

    def delete_user(self, uid):
        raise NotImplementedError('Deleting users is a bit buggy, will be implemented shortly')
        user = self.users[uid]
        user.update_categories([])
        self.fetch_json(f"/registered_users/{uid}/delete", method="DELETE")
        if uid in self.users:
            self.users.pop(uid)

    @property
    def rpc(self) -> BitcoinRPC:
        if self._rpc is None:
            self._rpc = find_rpc("liquidtestnet", liquid=True)
        return self._rpc

    @property
    def headers(self) -> dict:
        return {'content-type': 'application/json', 'Authorization': self.auth}

    def fetch(self, path:str, method="GET", data=None) -> Tuple[str, int]:
        path = path.lstrip("/")
        api_url = f"{self.api}{path}"
        params = dict(headers=self.headers)
        if data:
            params["data"] = data
        logger.debug(f"fetch {path}")
        res = self.session.request( method, api_url, **params)
        return res.text, res.status_code

    def fetch_json(self, path:str, method="GET", data=None):
        txt, code = self.fetch(path, method, data)
        if code < 200 or code > 299:
            self.healthy = False
            raise APIException(txt, code)
        return json.loads(txt) if txt else {}

    def sync_assets(self):
        self.assets = list2dict(self.fetch_json("/assets"), 'asset_uuid', cls=Asset, args=[self])

    def sync_users(self):
        self.users  = list2dict(self.fetch_json("/registered_users"), cls=User, args=[self])

    def sync_categories(self):
        self.categories = list2dict(self.fetch_json("/categories"))

    def sync_managers(self):
        self.managers = list2dict(self.fetch_json("/managers"))

    def sync(self):
        # run every request in a thread to speed up initial fetch
        sync_fns = [
            self.sync_assets,
            self.sync_users,
            self.sync_categories,
            self.sync_managers,
        ]
        threads = [threading.Thread(target=sync_fn) for sync_fn in sync_fns]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.healthy = True
