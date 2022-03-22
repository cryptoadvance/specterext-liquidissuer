# COPY-PASTE with slight modifications from Specter-Desktop
import datetime
import json
import logging
import os
import sys
from cryptoadvance.specter.rpc import BitcoinRPC
import requests
import urllib3

# from .helpers import is_ip_private
def is_ip_private(*args, **kwargs):
    return False

# from .specter_error import SpecterError
class SpecterError(Exception):
    pass

logger = logging.getLogger(__name__)

# TODO: redefine __dir__ and help

RPC_PORTS = {
    "testnet": 18332,
    "test": 18332,
    "regtest": 18443,
    "main": 8332,
    "mainnet": 8332,
    "signet": 38332,
}

ELEMENTS_PORTS = {
    "liquidtestnet": 7040,
    "liquidv1": 7041,
}


def get_default_datadir(node_type="ELM"):
    """Get default Bitcoin directory depending on the system"""
    datadir = None
    if node_type == "BTC":
        last_part = "Bitcoin"
    elif node_type == "ELM":
        last_part = "Elements"
    else:
        raise SpecterError(f"Unknown node_type {node_type}")

    if sys.platform == "darwin":
        # Not tested yet!
        datadir = os.path.join(
            os.environ["HOME"], f"Library/Application Support/{last_part}/"
        )
    elif sys.platform == "win32":
        # Not tested yet!
        datadir = os.path.join(os.environ["APPDATA"], last_part)
    else:
        datadir = os.path.join(os.environ["HOME"], f".{last_part.lower()}")
    return datadir


def _get_rpcconfig(datadir=get_default_datadir()):
    """returns the bitcoin.conf configurations (multiple) in a datastructure
    for all networks of a specific datadir.
    """
    config = {
        "elements.conf": {"default": {}, "liquidv1": {}, "liquidtestnet": {}},
        "bitcoin.conf": {"default": {}, "main": {}, "test": {}, "regtest": {}},
        "cookies": [],
    }
    folders = {
        "bitcoin.conf": {"main": "", "test": "testnet3", "regtest": "regtest", "signet": "signet"},
        "elements.conf": {"liquidv1": "liquidv1", "liquidtestnet": "liquidtestnet"},
    }

    if not os.path.isdir(datadir):  # we don't know where to search for files
        logger.warning(f"{datadir} not found")
        return config
    # load content from bitcoin.conf
    for config_filename in ["bitcoin.conf", "elements.conf"]:
        bitcoin_conf_file = os.path.join(datadir, config_filename)
        if os.path.exists(bitcoin_conf_file):
            try:
                with open(bitcoin_conf_file, "r") as f:
                    current = config[config_filename]["default"]
                    for line in f.readlines():
                        line = line.split("#")[0]

                        for net in config[config_filename]:
                            if f"[{net}]" in line:
                                current = config[config_filename][net]

                        if "=" not in line:
                            continue
                        k, v = line.split("=", 1)
                        # lines like main.rpcuser and so on
                        if "." in k:
                            net, k = k.split(".", 1)
                            config[config_filename][net.strip()][k.strip()] = v.strip()
                        else:
                            current[k.strip()] = v.strip()
            except Exception:
                print("Can't open %s file" % bitcoin_conf_file)

        chain_folders = folders.get(config_filename, [])
        for chain in chain_folders:
            fname = os.path.join(datadir, chain_folders[chain], ".cookie")
            if os.path.exists(fname):
                try:
                    with open(fname, "r") as f:
                        content = f.read()
                        user, password = content.split(":")
                        obj = {"user": user, "password": password, "port": RPC_PORTS[chain], "chain": chain}
                        config["cookies"].append(obj)
                except:
                    print("Can't open %s file" % fname)
    return config


def _detect_rpc_confs_via_datadir(config=None, datadir=get_default_datadir()):
    if config is None:
        config = _get_rpcconfig(datadir=datadir)
    confs = []
    default = {}
    for network in config["bitcoin.conf"]:
        if "rpcuser" in config["bitcoin.conf"][network]:
            default["user"] = config["bitcoin.conf"][network]["rpcuser"]
        if "rpcpassword" in config["bitcoin.conf"][network]:
            default["password"] = config["bitcoin.conf"][network]["rpcpassword"]
        if "rpcconnect" in config["bitcoin.conf"][network]:
            default["host"] = config["bitcoin.conf"][network]["rpcconnect"]
        if "rpcport" in config["bitcoin.conf"][network]:
            default["port"] = int(config["bitcoin.conf"][network]["rpcport"])
        if "user" in default and "password" in default:
            if (
                "port" not in config["bitcoin.conf"]["default"]
            ):  # only one rpc makes sense in this case
                if network == "default":
                    continue
                default["port"] = RPC_PORTS[network]
            confs.append(default.copy())
    # try cookies now
    for cookie in config["cookies"]:
        o = {}
        o.update(default)
        o.update(cookie)
        confs.append(o)
    return confs


def _detect_rpc_confs_via_env(prefix):
    """returns an array which might contain one configmap derived from Env-Vars
    Env-Vars for prefix=BTC: BTC_RPC_USER, BTC_RPC_PASSWORD, BTC_RPC_HOST, BTC_RPC_PORT
    configmap: {"user":"user","password":"password","host":"host","port":"port","protocol":"https"}
    """
    rpc_arr = []
    if (
        os.getenv(f"{prefix}_RPC_USER")
        and os.getenv(f"{prefix}_RPC_PASSWORD")
        and os.getenv(f"{prefix}_RPC_HOST")
        and os.getenv(f"{prefix}_RPC_PORT")
        and os.getenv(f"{prefix}_RPC_PROTOCOL")
    ):
        logger.info(f"Detected RPC-Config on Environment-Variables for prefix {prefix}")
        env_conf = {
            "user": os.getenv(f"{prefix}_RPC_USER"),
            "password": os.getenv(f"{prefix}_RPC_PASSWORD"),
            "host": os.getenv(f"{prefix}_RPC_HOST"),
            "port": os.getenv(f"{prefix}_RPC_PORT"),
            "protocol": os.getenv(f"{prefix}_RPC_PROTOCOL"),
        }
        rpc_arr.append(env_conf)
    return rpc_arr


def autodetect_rpc_confs(
    node_type,
    datadir=get_default_datadir(),
    port=None,
    proxy_url="socks5h://localhost:9050",
    only_tor=False,
):
    """Returns an array of valid and working configurations which
    got autodetected.
    autodetection checks env-vars and bitcoin-data-dirs
    """
    if port == "":
        port = None
    if port is not None:
        port = int(port)
    conf_arr = []
    conf_arr.extend(_detect_rpc_confs_via_env(node_type))
    conf_arr.extend(_detect_rpc_confs_via_datadir(datadir=datadir))
    available_conf_arr = []
    if len(conf_arr) > 0:
        for conf in conf_arr:
            rpc = BitcoinRPC(
                **conf, proxy_url="socks5h://localhost:9050", only_tor=False
            )
            if port is not None:
                if int(rpc.port) != port:
                    continue
            try:
                rpc.getmininginfo()
                available_conf_arr.append(conf)
            except requests.exceptions.RequestException as e:
                pass
                # no point in reporting that here
            except RpcError:
                pass
                # have to make a list of acceptable exception unfortunately
                # please enlarge if you find new ones
    return available_conf_arr


class RpcError(Exception):
    """Specifically created for error-handling of the BitcoinCore-API
    if thrown, check for errors like this:
    try:
        rpc.does_not_exist()
    except RpcError as rpce:
        assert rpce.status_code == 401 # A https-status-code
        assert rpce.error_code == -32601
        assert rpce.error_msg == "Method not found"
    See for error_codes https://github.com/bitcoin/bitcoin/blob/v0.15.0.1/src/rpc/protocol.h#L32L87
    """

    def __init__(self, message, response):
        super(Exception, self).__init__(message)
        self.status_code = 500  # default
        try:
            self.status_code = response.status_code
            error = response.json()
        except Exception as e:
            # it's a dict already
            error = response
        try:
            self.error_code = error["error"]["code"]
            self.error_msg = error["error"]["message"]
        except Exception as e:
            self.error_code = -99
            self.error = "UNKNOWN API-ERROR:%s" % response.text


def find_rpc(net="liquidtestnet", liquid=True):
    config = _get_rpcconfig(get_default_datadir("ELM" if liquid else "BTC"))
    lqtconf = config["elements.conf" if liquid else "bitcoin.conf"].get(net, {})
    if not lqtconf.get("rpcuser"):
        cookies = [cookie for cookie in config["cookies"] if cookie["chain"] == net]
        if len(cookies) > 0:
            lqtconf = cookies[0]
    if not (lqtconf.get("rpcuser") and lqtconf.get("rpcpassword")):
        raise RuntimeError("Can't find node credentials")
    creds = {
        "user": lqtconf["rpcuser"],
        "password": lqtconf["rpcpassword"],
        "port": int(lqtconf.get("rpcport", ELEMENTS_PORTS[net])),
    }
    return BitcoinRPC(**creds)

if __name__ == "__main__":
    # detect liquidtestnet user and password
    rpc = find_rpc("liquidtestnet", liquid=True)
    print(rpc.getmininginfo())

    # default wallet
    w = rpc.wallet("")
    print(w.getbalances())

    # rpc = BitcoinRPC(
    #     "bitcoinrpc", "foi3uf092ury97iufhjf30982hf928uew9jd209j", port=18443
    # )

    # print(rpc.url)

    # print(rpc.getmininginfo())

    # print(rpc.listwallets())

    # ##### WORKING WITH WALLETS #########

    # # print(rpc.getbalance(wallet=""))

    # # or

    # w = rpc.wallet("")  # will load default wallet.dat

    # print(w.url)

    # print(w.getbalance())  # now you can run -rpcwallet commands
