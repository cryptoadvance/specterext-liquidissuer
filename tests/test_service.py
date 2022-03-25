
from unittest.mock import MagicMock, patch

import pytest
from cryptoadvance.specter.services.callbacks import after_serverpy_init_app
from cryptoadvance.specterext.ampissuer.rpc import find_rpc
from cryptoadvance.specterext.ampissuer.service import AmpissuerService
from cryptoadvance.specter.process_controller.bitcoind_controller import BitcoindPlainController
from flask import Flask

@patch("cryptoadvance.specter.services.service.ServiceEncryptedStorageManager")
def test_AmpissuerService(svc_ESM_mock, mock_specter,mock_flaskapp):
    mock_flaskapp.config["API_TESTNET_URL"] = "https://amp-test.blockstream.com/api/"
    mock_specter.is_liquid.return_value = True
    mock_specter.is_testnet.return_value = True
    if '' in mock_specter.rpc.listwallets():
        mock_specter.rpc.unloadwallet("")
        
    assert '' not in mock_specter.rpc.listwallets()
    amp_svc = AmpissuerService(True, mock_specter)
    amp_svc.callback(after_serverpy_init_app)
    amp = amp_svc.amp
    assert '' in mock_specter.rpc.listwallets()
    assert amp_svc.detect_liquid() == ('liquidtestnet', 'https://amp-test.blockstream.com/api/')



@pytest.fixture
def mock_specter(elements_elreg: BitcoindPlainController):
    specter_mock = MagicMock()
    # This assumes a running liquid-testnode at the default ~/.elements
    specter_mock.rpc = elements_elreg.get_rpc()
    specter_mock.config = {"services": {}}
    return specter_mock

@pytest.fixture
def mock_flaskapp(mock_specter):

    flaskapp_mock = Flask(__name__)
    flaskapp_mock.config["EXTENSION_LIST"] = [
        "cryptoadvance.specterext.ampissuer.service"
    ]
    flaskapp_mock.config["ISOLATED_CLIENT_EXT_URL_PREFIX"] = "/spc/ext"
    flaskapp_mock.config["EXT_URL_PREFIX"] = "/ext"
    # The ServiceManager is a flask-aware component. It will load all the services
    # however, in order to configure them, he needs to know about the configuration
    # of the specterApp.
    flaskapp_mock.config[
        "SPECTER_CONFIGURATION_CLASS_FULLNAME"
    ] = "cryptoadvance.specter.config.TestConfig"

    ctx = flaskapp_mock.app_context()
    ctx.push()
    return flaskapp_mock
