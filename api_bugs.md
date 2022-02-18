# Issues

- distribution:
    - if no assignments are valid for distribution -> doesn't return error code
    - after cancel distributions can't create a new one, ever again - I had to create a new asset
    - distribution that is not confirmed yet doesn't appear in the list of distributions

- users
    - If the user was added to categories, then removed and deleted it can't be created again

# TODO before release

- pending distributions (total doesn't match)
- better updates (no need to clear all, sync in thread etc)
- force update everything btn (in settings probably)
- login page - user pass or token
- rpc manual connection
- check btc balance
- check default wallet
- number of blocks
- custom 500 error page?
- specter extension (binary)
- links to distributions, assignments?, users, categories
# Q

# TODO next

High priority
- multisig, watch-only and HW support
- Elements Core wallets separation
- Treasury management - minimal impl. addresses, recv addresses for btc, send from treasury

Mid priority
- icons
? elects for backend

- managers support (incl. without Elements Core)
- filters, search in tables
- activities (full tx history)
- ownerships at time
- users: multiple GAIDs
- burn asset
- time lock on assignments

Multisig
- ledger - need to whitelist the asset
- jade - no multisig
- specter-diy - works but large
- airgapped Elements Core

# Test GAIDs

GAZfXqe2Zi4vfJUKXuvKaXqTKkCkb
GA3FvdbVoibfvkqUE3ivpD1aHPmfxP