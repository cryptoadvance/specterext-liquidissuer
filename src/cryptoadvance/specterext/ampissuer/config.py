"""
Here Configuration of your Extension (and maybe your Application) takes place
"""
import os

class BaseConfig:
    ''' This is a extension-based Config which is used as Base '''
    AMPISSUER_SOMEKEY = "some value"
    API_TESTNET_URL = "https://amp-test.blockstream.com/api/"
    API_MAINNET_URL = "https://amp.blockstream.com/api/"
    AUTH = "token 66b946392661e192718a8822046a1e9a9dc7af51"

class ProductionConfig(BaseConfig):
    ''' This is a extension-based Config for Production '''
    pass


