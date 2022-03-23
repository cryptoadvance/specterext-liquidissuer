import logging

from cryptoadvance.specter.rpc import BitcoinRPC
from cryptoadvance.specter.services.callbacks import after_serverpy_init_app
from cryptoadvance.specter.services.service import (Service, devstatus_alpha,
                                                    devstatus_prod)
# A SpecterError can be raised and will be shown to the user as a red banner
from cryptoadvance.specter.specter_error import SpecterError
from cryptoadvance.specter.wallet import Wallet
from flask import current_app as app

from .amp import Amp, APIException

logger = logging.getLogger(__name__)

class AmpissuerService(Service):
    id = "ampissuer"
    name = "Ampissuer Service"
    icon = "ampissuer/img/diamond-multiple.svg"
    logo = "ampissuer/img/diamond-multiple.svg"
    desc = "Issuing Amp Assets."
    has_blueprint = True
    blueprint_module = "cryptoadvance.specterext.ampissuer.controller"
    devstatus = devstatus_alpha
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
            self._amp = {} # self.amp will lazily fill the dictionary
            

    @property
    def amp(self):
        ''' Depending on the current node chosen in specter, this is returning a fitting
            Amp instance. It might be healthy or not. check with amp.healthy
        '''
        network, api_url = self.detect_liquid()
        if not self._amp.get(network):
            # We need a "pure" BitcoinRPC-class, NOT a liquidRPC-class here
            # specter.rpc would return a LiquidRPC class.
            # This exploits a bug a in the BitcoinRPC-class: clone is not overridden in 
            # the LiquidRPC and does not use type(self) in the clone-method
            bitcoin_rpc = self.specter.rpc.clone()
            if network == "liquidtestnet":
                amp_creds = self.get_amp_testnet_creds()
            elif network == "liquidv1":
                amp_creds = self.get_amp_mainnet_creds()
            if amp_creds == None:
                raise APIException("Amp credentials not configured")
            if not isinstance(bitcoin_rpc, BitcoinRPC):
                raise Exception("clone is no longer returning a BitcoinRPC-instance")
            self._amp[network] = Amp(api_url, amp_creds, bitcoin_rpc)
            self._amp[network].sync()
        # it might be healthy or not, we're returning it nevertheless
        return self._amp[network]

    def detect_liquid(self):
        ''' returns either liquidtestnet or liquidv1 depending on the specter.rpc 
            and the corresponding correct API-Endpoint from the config
        '''
        if not self.specter.is_liquid:
            logger.error("Running on non Liquid-Server")
            raise SpecterError("Liquid not detected")
        if self.specter.is_testnet:
            return "liquidtestnet", app.config["API_TESTNET_URL"]
        else:
            return "liquidv1", app.config["API_MAINNET_URL"]

    def get_amp_testnet_creds(self) -> str:
        service_data = self.get_current_user_service_data()
        return service_data.get(self.AMP_TESTNET_CREDS)

    def set_amp_testnet_creds(self, creds):
        self.update_current_user_service_data({self.AMP_TESTNET_CREDS: creds})
        if self._amp.get("liquidtestnet"):
            self._amp["liquidtestnet"].auth = creds

    def get_amp_mainnet_creds(self) -> str:
        service_data = self.get_current_user_service_data()
        return service_data.get(self.AMP_MAINNET_CREDS)

    def set_amp_mainnet_creds(self, creds):
        self.update_current_user_service_data({self.AMP_MAINNET_CREDS: creds})
        if self._amp.get("liquidv1"):
            self._amp["liquidv1"].auth = creds

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
