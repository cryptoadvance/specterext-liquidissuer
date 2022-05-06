from .config import ProductionConfig

class AppProductionConfig(ProductionConfig):
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