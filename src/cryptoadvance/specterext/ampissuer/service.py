import logging

from cryptoadvance.specter.services.service import Service, devstatus_alpha, devstatus_prod
# A SpecterError can be raised and will be shown to the user as a red banner
from cryptoadvance.specter.specter_error import SpecterError
from flask import current_app as app
from cryptoadvance.specter.wallet import Wallet
from cryptoadvance.specter.services.callbacks import after_serverpy_init_app
from .amp import Amp

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

    # TODO: As more Services are integrated, we'll want more robust categorization and sorting logic
    sort_priority = 2

    # ServiceEncryptedStorage field names for this service
    # Those will end up as keys in a json-file
    SPECTER_WALLET_ALIAS = "wallet"

    def callback(self, callback_id):
        if callback_id == after_serverpy_init_app:
            try:
                self.amp = Amp(app.config["API_URL"],app.config["AUTH"])
                self.amp.sync()
                # wallet = self.get_associated_wallet()
            except Exception as e:
                logger.exception(e)

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