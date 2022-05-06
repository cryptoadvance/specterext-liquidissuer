import logging

from cryptoadvance.specter.rpc import BitcoinRPC
from cryptoadvance.specter.services.callbacks import after_serverpy_init_app
from cryptoadvance.specter.services.service import (Service, devstatus_alpha,
                                                    devstatus_beta)
# A SpecterError can be raised and will be shown to the user as a red banner
from cryptoadvance.specter.specter_error import SpecterError
from cryptoadvance.specter.wallet import Wallet
from flask import current_app as app

from cryptoadvance.specter.rpc import RpcError

from .amp import Amp, APIException
import os

logger = logging.getLogger(__name__)

class LiquidissuerService(Service):
    id = "liquidissuer"
    name = "Liquidissuer Service"
    icon = "liquidissuer/img/diamond-multiple.svg"
    logo = "liquidissuer/img/diamond-multiple.svg"
    desc = "Issuing Amp Assets."
    has_blueprint = True
    blueprint_module = "cryptoadvance.specterext.liquidissuer.controller"
    devstatus = devstatus_beta
    isolated_client = False

    AMP_TESTNET_CREDS = "amp_testnet_creds"
    AMP_MAINNET_CREDS = "amp_mainnet_creds"

    # TODO: As more Services are integrated, we'll want more robust categorization and sorting logic
    sort_priority = 2

    # ServiceEncryptedStorage field names for this service
    # Those will end up as keys in a json-file
    SPECTER_WALLET_ALIAS = "wallet"

    def callback(self, callback_id, *args, **kwargs):
        if callback_id == after_serverpy_init_app:
            # We could do it in a constructor, maybe we should?
            self._amp = {} # self.amp will lazily fill the dictionary
            

    @property
    def amp(self):
        ''' Depending on the current node chosen in specter, this is returning a fitting
            Amp instance. It might be healthy or not. check with amp.healthy
        '''
        network, api_url, registry_url, esplora_url = self.detect_liquid()
        if not self._amp.get(network):
            # We need a "pure" BitcoinRPC-class, NOT a liquidRPC-class here
            # specter.rpc would return a LiquidRPC class.
            # This exploits a bug a in the BitcoinRPC-class: clone is not overridden in 
            # the LiquidRPC and does not use type(self) in the clone-method
            bitcoin_rpc = self.specter.rpc.clone()
            if not isinstance(bitcoin_rpc, BitcoinRPC):
                raise Exception("clone is no longer returning a BitcoinRPC-instance")
            self.load_or_create_default_wallet(bitcoin_rpc)
            amp_creds = self.get_amp_token()
            data_folder = os.path.join(self.specter.data_folder, "liquidissuer", network)
            self._amp[network] = Amp(api_url, amp_creds, bitcoin_rpc, data_folder=data_folder, registry_url=registry_url, esplora_url=esplora_url)
            self._amp[network].sync()
        # it might be healthy or not, we're returning it nevertheless
        return self._amp[network]

    def detect_liquid(self):
        ''' returns either liquidtestnet or liquidv1 depending on the specter.rpc 
            and the corresponding correct API-Endpoint from the config
        '''
        if not self.specter.is_liquid:
            logger.error("Running on non Liquid-Server")
            raise SpecterError("Liquid node is not detected. Please configure and select Liquid node in Specter settings.")
        if self.specter.is_testnet:
            return "liquidtestnet", app.config["API_TESTNET_URL"], app.config["ASSET_REGISTRY_TESTNET_URL"], app.config["API_ESPLORA_TESTNET_URL"]
        else:
            return "liquidv1", app.config["API_MAINNET_URL"], app.config["ASSET_REGISTRY_MAINNET_URL"], app.config["API_ESPLORA_MAINNET_URL"]

    def load_or_create_default_wallet(self,rpc):
        if '' not in rpc.listwallets():
            try:
                rpc.createwallet("")
            except RpcError as rpce:
                rpc.loadwallet("")

    def get_amp_token(self) -> str:
        ''' gets the token specific to the current liquid-network (liquidtestnet / liquidv1)'''
        service_data = self.get_current_user_service_data()
        network, *_ = self.detect_liquid()
        return service_data.get(network, "")

    def set_amp_token(self, token):
        ''' sets the token specific to the current liquid-network (liquidtestnet / liquidv1)'''
        network, *_ = self.detect_liquid()
        self.update_current_user_service_data({network: token})
        if self._amp.get(network):
            self._amp[network].auth = token

    @classmethod
    def get_associated_wallet(cls) -> Wallet:
        """Get the Specter `Wallet` that is currently associated with this service"""
        service_data = cls.get_current_user_service_data()
        if not service_data or cls.SPECTER_WALLET_ALIAS not in service_data:
            # Service is not initialized; nothing to do
            return
        try:
            return app.specter.wallet_manager.get_by_alias(
                service_data[cls.SPECTER_WALLET_ALIAS]
            )
        except SpecterError as e:
            logger.debug(e)
            # Referenced an unknown wallet
            # TODO: keep ignoring or remove the unknown wallet from service_data?
            return

    @classmethod
    def set_associated_wallet(cls, wallet: Wallet):
        """Set the Specter `Wallet` that is currently associated with this Service"""
        cls.update_current_user_service_data({cls.SPECTER_WALLET_ALIAS: wallet.alias})
