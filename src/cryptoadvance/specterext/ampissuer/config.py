"""
Here Configuration of your Extension (and maybe your Application) takes place
"""
import os
from cryptoadvance.specter.config import ProductionConfig as SpecterProductionConfig


class BaseConfig:
    ''' This is a extension-based Config which is used as Base '''
    AMPISSUER_SOMEKEY = "some value"
    API_URL = "https://amp-test.blockstream.com/api/"
    AUTH = "token 66b946392661e192718a8822046a1e9a9dc7af51"

class ProductionConfig(BaseConfig):
    ''' This is a extension-based Config for Production '''
    pass


class AppProductionConfig(SpecterProductionConfig):
    ''' The AppProductionConfig class can be used to user this extension as application
    '''
    # Where should the User endup if he hits the root of that domain?
    ROOT_URL_REDIRECT = "/spc/ext/ampissuer"
    # I guess this is the only extension which should be available?
    EXTENSION_LIST = [
        "cryptoadvance.specterext.ampissuer.service"
    ]
    # You probably also want a different folder here
    SPECTER_DATA_FOLDER=os.path.expanduser("~/.ampissuer")