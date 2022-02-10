import os
from typing import Tuple
import requests
import json

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
        return [ass for ass in self.assignments if not ass['is_distributed']]

    @property
    def distributions(self):
        if self._distributions is None:
            self._distributions = self.amp.fetch_json(f"/assets/{self.asset_uuid}/distributions")
        return self._distributions or []

    @property
    def unconfirmed_distributions(self):
        return [dist for dist in self.distributions if dist['distribution_status'] == 'UNCONFIRMED']

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

    @property
    def headers(self) -> dict:
        return {'content-type': 'application/json', 'Authorization': self.auth}

    def fetch(self, path:str, method="GET", data=None) -> Tuple[str, int]:
        path = path.lstrip("/")
        fpath = f"public/api/{path}.json"
        # return cached version
        if method == "GET":
            if os.path.isfile(fpath):
                print(f"cached {path}")
                with open(fpath, "r") as f:
                    return f.read(), 200

        api_url = f"{self.api}{path}"
        params = dict(headers=self.headers)
        if data:
            params["data"] = data
        print(f"fetch {path}")
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

    def fetch_json(self, path:str, method="GET", data=None):
        txt, code = self.fetch(path, method, data)
        if code < 200 or code > 299:
            raise APIException(txt, code)
        return json.loads(txt)

    def sync(self):
        self.users = list2dict(self.fetch_json("/registered_users"), cls=User, args=[self])
        self.assets = list2dict(self.fetch_json("/assets"), 'asset_uuid', cls=Asset, args=[self])
        self.categories = list2dict(self.fetch_json("/categories"))
        self.managers = list2dict(self.fetch_json("/managers"))
