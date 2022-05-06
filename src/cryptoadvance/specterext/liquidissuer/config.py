"""
Here Configuration of your Extension (and maybe your Application) takes place
"""
import os

class BaseConfig:
    ''' This is a extension-based Config which is used as Base '''
    API_TESTNET_URL = "https://amp-test.blockstream.com/api/"
    API_MAINNET_URL = "https://amp.blockstream.com/api/"
    # blockstream's asset registry api
    ASSET_REGISTRY_MAINNET_URL = "https://assets.blockstream.info/"
    ASSET_REGISTRY_TESTNET_URL = "https://assets-testnet.blockstream.info/"
    # blockstream's block esplorer for asset info
    API_ESPLORA_MAINNET_URL = "https://blockstream.info/liquid/api/"
    API_ESPLORA_TESTNET_URL = "https://blockstream.info/liquidtestnet/api/"

class DevelopmentConfig(BaseConfig):
    pass

class ProductionConfig(BaseConfig):
    ''' This is a extension-based Config for Production '''
    pass


