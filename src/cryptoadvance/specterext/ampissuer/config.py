"""
Here Configuration of your Extension (and maybe your Application) takes place
"""
import os

class BaseConfig:
    ''' This is a extension-based Config which is used as Base '''
    API_TESTNET_URL = "https://amp-test.blockstream.com/api/"
    API_MAINNET_URL = "https://amp.blockstream.com/api/"

class DevelopmentConfig(BaseConfig):
    pass

class ProductionConfig(BaseConfig):
    ''' This is a extension-based Config for Production '''
    pass


