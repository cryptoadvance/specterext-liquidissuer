# Liquid issuer

Make sure your liquid node is running on [`liquidtestnet`](https://liquidtestnet.com/) with rpc server enabled (`elementsd`, or `elements-qt` with `server=1` in `elements.conf`).
Also , you'll need an existing default wallet on that elements node, something like this:
```
elements-cli -rpcport=18891 -rpcuser=liquid -rpcpassword=liquid createwallet ""
```


```
cd src                # or wherever all your projects are
git clone git@github.com:cryptoadvance/liquidissuer.git

# we assume that you have cloned specter-desktop in parallel with amp-issuer
cd ../specter-desktop # your specter-desktop is here
git checkout master   # you need at least the master-branch
cd ../liquidissuer       # jump back to liquidissuer

# Use the environment from specter-desktop
. ../specter-desktop/.env/bin/activate
# Install additional requirements
pip3 install -r requirements.txt
# Start specter
python3 -m cryptoadvance.specter server --config DevelopmentConfig --debug
```

Configure your specter to have the liquid node ready.

# Releasing

```
# Build
python3 -m pip install --upgrade build
python3 -m build

# ... and upload
python3 -m pip install --upgrade twine
python3 -m twine upload --repository testpypi dist/*
```
