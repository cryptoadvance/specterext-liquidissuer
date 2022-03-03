# Amp issuer

## Run

Make sure your liquid node is running on [`liquidtestnet`](https://liquidtestnet.com/) with rpc server enabled (`elementsd`, or `elements-qt` with `server=1` in `elements.conf`).
Also , you'll need am existing default-wallet on that elements-node, then:

```
# have the specter-desktop source checked out in parallel
# and make sure you're on the right branch:
cd ../specter-desktop
git remote add k9ert https://github.com/k9ert/specter-desktop.git
git fetch k9ert
git checkout service_class_refactoring
cd ../ampissuer

# Use the environment from specter-desktop
. ../specter-desktop/.env/bin/activate
# Install additional requirements
pip3 install -r requirements.txt
# Start specter
python3 -m cryptoadvance.specter server --config DevelopmentConfig --debug
```
