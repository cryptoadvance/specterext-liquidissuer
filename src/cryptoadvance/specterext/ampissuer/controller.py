import logging
import json

from cryptoadvance.specter.services.controller import \
    user_secret_decrypted_required
from cryptoadvance.specter.user import User
from cryptoadvance.specter.wallet import Wallet
from cryptoadvance.specterext.ampissuer.amp import APIException
from cryptoadvance.specterext.ampissuer.rpc import SpecterError
from flask import current_app as app
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .service import AmpissuerService

logger = logging.getLogger(__name__)

ampissuer_endpoint = AmpissuerService.blueprint

def ext():
    ''' convenience for getting the extension-object'''
    return app.specter.service_manager.services["ampissuer"]

# Those commented endpoints might make sense for deeper integration

# @ampissuer_endpoint.route("/")
# @login_required
# @user_secret_decrypted_required
# def index():
#     return render_template(
#         "ampissuer/index.jinja",
#     )


# @ampissuer_endpoint.route("/transactions")
# @login_required
# @user_secret_decrypted_required
# def transactions():
#     # The wallet currently configured for ongoing autowithdrawals
#     wallet: Wallet = AmpissuerService.get_associated_wallet()

#     return render_template(
#         "ampissuer/transactions.jinja",
#         wallet=wallet,
#         services=app.specter.service_manager.services,
#     )


# @ampissuer_endpoint.route("/settings", methods=["GET"])
# @login_required
# def settings_get():
#     associated_wallet: Wallet = AmpissuerService.get_associated_wallet()

#     # Get the user's Wallet objs, sorted by Wallet.name
#     wallet_names = sorted(current_user.wallet_manager.wallets.keys())
#     wallets = [current_user.wallet_manager.wallets[name] for name in wallet_names]

#     return render_template(
#         "ampissuer/settings.jinja",
#         associated_wallet=associated_wallet,
#         wallets=wallets,
#         cookies=request.cookies,
#     )

# @ampissuer_endpoint.route("/settings", methods=["POST"])
# @login_required
# def settings_post():
#     show_menu = request.form["show_menu"]
#     user = app.specter.user_manager.get_user()
#     if show_menu == "yes":
#         user.add_service(AmpissuerService.id)
#     else:
#         user.remove_service(AmpissuerService.id)
#     used_wallet_alias = request.form.get("used_wallet")
#     if used_wallet_alias != None:
#         wallet = current_user.wallet_manager.get_by_alias(used_wallet_alias)
#         AmpissuerService.set_associated_wallet(wallet)
#     return redirect(url_for(f"{ AmpissuerService.get_blueprint_name()}.settings_get"))


@ampissuer_endpoint.route("/")
def index():
    return redirect(url_for('ampissuer_endpoint.assets'))




@ampissuer_endpoint.route("/assets/")
def assets():
    try:
        return render_template('ampissuer/assets.jinja', amp=ext().amp)
    except APIException as apie:
        logger.error(apie)
        flash(str(apie))
        # ToDo: setting up API-Credentials in the settings endpoint
        return redirect(url_for('ampissuer_endpoint.settings'))
    except Exception as e:
        logger.exception(e)
        raise e

@ampissuer_endpoint.route("/new_asset/", methods=["GET", "POST"])
def new_asset():
    obj = {}
    if request.method == "POST":
        w = ext().amp.rpc.wallet()
        addr = w.getnewaddress()
        obj = {
            "asset_name": request.form.get("asset_name"),
            "amount": int(request.form.get("amount") or 0),
            "domain": request.form.get("domain"),
            "ticker": request.form.get("ticker"),
            "precision": int(request.form.get("precision", 0)),
            "pubkey": request.form.get("pubkey"),
            "is_confidential": bool(request.form.get("is_confidential")),
            "reissue": int(request.form.get("reissue", 0) or 0),
            "transfer_restricted": bool(request.form.get("transfer_restricted")),
        }
        try:
            asset = ext().amp.new_asset(obj)
            return redirect(url_for('ampissuer_endpoint.asset_settings', asset_uuid=asset.asset_uuid))
        except Exception as e:
            flash(f"{e}", "error")
    return render_template('ampissuer/new_asset.jinja', amp=ext().amp, obj=obj)

@ampissuer_endpoint.route("/assets/<asset_uuid>/")
def asset(asset_uuid):
    asset = ext().amp.assets[asset_uuid]
    return render_template('ampissuer/asset/dashboard.jinja', amp=ext().amp, asset=asset)

@ampissuer_endpoint.route("/assets/<asset_uuid>/settings/", methods=["GET", "POST"])
def asset_settings(asset_uuid):
    asset = ext().amp.assets[asset_uuid]
    if request.method == "POST":
        action = request.form.get("action")
        try:
            if action == "register":
                asset.register()
                flash('Asset registered')
            elif action == "authorize":
                asset.authorize()
                flash('Asset authorized')
            elif action == "change_requirements":
                requirements = []
                for k, v in request.form.items():
                    if k.startswith("cid_"):
                        requirements.append(int(k[4:]))
                asset.change_requirements(requirements)
                flash('Requirements updated')
            elif action == "reissue":
                txid = asset.reissue(int(request.form.get('reissue_amount', 0) or 0))
                return redirect(url_for('ampissuer_endpoint.asset_reissuance', asset_uuid=asset.asset_uuid, txid=txid))
            elif action == "fix_reissuances":
                asset.fix_reissuances()
                flash("Reissuances are fixed")
            else:
                raise NotImplementedError(f"Unknown action {action}")
        except Exception as e:
            flash(f"{e}", "error")
    return render_template('ampissuer/asset/settings.jinja', amp=ext().amp, asset=asset)

@ampissuer_endpoint.route("/assets/<asset_uuid>/assignments/")
def asset_assignments(asset_uuid):
    asset = ext().amp.assets[asset_uuid]
    return render_template('ampissuer/asset/assignments.jinja', amp=ext().amp, asset=asset)

@ampissuer_endpoint.route("/assets/<asset_uuid>/distributions/")
def asset_distributions(asset_uuid):
    asset = ext().amp.assets[asset_uuid]
    return render_template('ampissuer/asset/distributions.jinja', amp=ext().amp, asset=asset)

@ampissuer_endpoint.route("/assets/<asset_uuid>/activities/")
def asset_activities(asset_uuid):
    asset = ext().amp.assets[asset_uuid]
    return render_template('ampissuer/asset/base.jinja', amp=ext().amp, asset=asset)

@ampissuer_endpoint.route("/assets/<asset_uuid>/utxos/", methods=["GET", "POST"])
def asset_utxos(asset_uuid):
    asset = ext().amp.assets[asset_uuid]
    if request.method == "POST":
        action = request.form.get("action")
        txid = request.form.get("txid")
        vout = int(request.form.get("vout"))
        try:
            asset.change_utxo(action, txid, vout)
            flash(f"UTXO is {action}ed")
        except Exception as e:
            flash(f"{e}", "error")
    utxos = asset.get_utxos()
    return render_template('ampissuer/asset/utxos.jinja', amp=ext().amp, asset=asset, utxos=utxos)

@ampissuer_endpoint.route("/assets/<asset_uuid>/users/")
def asset_users(asset_uuid):
    asset = ext().amp.assets[asset_uuid]
    return render_template('ampissuer/asset/users.jinja', amp=ext().amp, asset=asset)

@ampissuer_endpoint.route("/assets/<asset_uuid>/new_assignment/", methods=["GET", "POST"])
def new_assignment(asset_uuid):
    asset = ext().amp.assets[asset_uuid]
    if request.method == "GET":
        return render_template('ampissuer/asset/new_assignment.jinja', amp=ext().amp, asset=asset)
    # if POST request
    ass = []
    for uid in asset.users:
        amount = request.form.get(f"amount_{uid}", "")
        if not amount:
            continue
        try:
            amount = int(amount)
            if amount < 0:
                raise ValueError()
        except:
            flash(f"Invalid amount: {amount}", "error")
            return render_template('ampissuer/asset/new_assignment.jinja', amp=ext().amp, asset=asset)
        if amount == 0:
            continue
        ass.append({
            "registered_user": uid,
            "ready_for_distribution": bool(request.form.get(f"ready_for_distribution_{uid}", "")),
            "amount": amount,
            "vesting_timestamp": None,
        })
    try:
        asset.create_assignment(ass)
        flash("Assignment created sucessfully")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for('ampissuer_endpoint.asset', asset_uuid=asset_uuid))

@ampissuer_endpoint.route("/assets/<asset_uuid>/assignment/<int:assid>/", methods=["POST"])
def change_assignment(asset_uuid, assid):
    asset = ext().amp.assets[asset_uuid]
    try:
        action = request.form.get("action", "lock")
        asset.change_assignment(assid, action)
        if action == "delete":
            flash("Assignment deleted")
        elif action == "unlock":
            flash("Assignment unlocked")
        else:
            flash("Assignment locked")
    except Exception as e:
        flash(f"{e}", "error")
    return redirect(url_for('ampissuer_endpoint.asset', asset_uuid=asset_uuid))


@ampissuer_endpoint.route("/assets/<asset_uuid>/new_distribution/")
def new_distribution(asset_uuid):
    asset = ext().amp.assets[asset_uuid]
    try:
        duuid = asset.create_distribution()
        flash("Distribution created")
        return redirect(url_for('ampissuer_endpoint.asset_distribution', asset_uuid=asset_uuid, duuid=duuid))
    except Exception as e:
        flash(f"{e}", "error")
    return redirect(url_for('ampissuer_endpoint.asset', asset_uuid=asset_uuid))

@ampissuer_endpoint.route("/assets/<asset_uuid>/distribution/<distribution_uuid>/", methods=["POST"])
def change_distribution(asset_uuid, distribution_uuid):
    asset = ext().amp.assets[asset_uuid]
    try:
        action = request.form.get("action", "")
        asset.change_distribution(distribution_uuid, action)
        if action == "cancel":
            flash("Distribution canceled")
        elif action == "confirm":
            flash("Distribution confirmed")
        else:
            raise RuntimeError("Not implemented")
    except Exception as e:
        flash(f"{e}", "error")
    return redirect(url_for('ampissuer_endpoint.asset', asset_uuid=asset_uuid))

@ampissuer_endpoint.route("/assets/<asset_uuid>/distributions/<duuid>/")
def asset_distribution(asset_uuid, duuid):
    asset = ext().amp.assets[asset_uuid]
    distr = asset.get_distribution(duuid)
    if not distr:
        redirect(url_for('ampissuer_endpoint.asset', asset_uuid=asset_uuid))
    return render_template('ampissuer/asset/distribution.jinja', amp=ext().amp, asset=asset, distr=distr)

@ampissuer_endpoint.route("/assets/<asset_uuid>/distributions/<duuid>/status/")
def asset_distribution_status(asset_uuid, duuid):
    asset = ext().amp.assets[asset_uuid]
    distr = asset.get_distribution(duuid)
    if not distr:
        return json.dumps({"error": "Distribution is not found"}), 404
    return json.dumps(distr)

@ampissuer_endpoint.route("/assets/<asset_uuid>/reissuance/<txid>/")
def asset_reissuance(asset_uuid, txid):
    asset = ext().amp.assets[asset_uuid]
    reissuance = asset.get_reissuance(txid)
    if not reissuance:
        redirect(url_for('ampissuer_endpoint.asset', asset_uuid=asset_uuid))
    return render_template('ampissuer/asset/reissuance.jinja', amp=ext().amp, asset=asset, reissuance=reissuance)

@ampissuer_endpoint.route("/assets/<asset_uuid>/reissuance/<txid>/status/")
def asset_reissuance_status(asset_uuid, txid):
    asset = ext().amp.assets[asset_uuid]
    reissuance = asset.get_reissuance(txid)
    if not reissuance:
        return json.dumps({"error": "Distribution is not found"}), 404
    return json.dumps(reissuance)


@ampissuer_endpoint.route("/categories/")
def categories():
    return render_template('ampissuer/categories.jinja', amp=ext().amp)

@ampissuer_endpoint.route("/new_category/", methods=["GET", "POST"])
def new_category():
    obj = {}
    if request.method == "POST":
        name = request.form.get("category_name", "")
        description = request.form.get("category_description", "")
        obj = {
            "category_name": name,
            "category_description": description,
        }
        try:
            ext().amp.new_category(name, description)
            flash("New category created")
            return redirect(url_for("categories"))
        except Exception as e:
            flash(f"{e}", "error")
    return render_template('ampissuer/new_category.jinja', amp=ext().amp, obj=obj)

@ampissuer_endpoint.route("/categories/<int:cid>/")
def category(cid):
    return render_template('ampissuer/base.jinja', amp=ext().amp)




@ampissuer_endpoint.route("/users/")
def users():
    return render_template('ampissuer/users.jinja', amp=ext().amp)

@ampissuer_endpoint.route("/new_user/", methods=["GET", "POST"])
@ampissuer_endpoint.route("/new_user/for/<asset_uuid>/", methods=["GET", "POST"])
def new_user(asset_uuid=None):
    obj = {'categories': [] if asset_uuid is None else ext().amp.assets[asset_uuid]['requirements']}
    if request.method == "POST":
        obj = {
            "user_name": request.form.get("user_name"),
            "user_GAID": request.form.get("user_GAID"),
            "is_company": bool(request.form.get("is_company")),
        }
        categories = []
        for k, v in request.form.items():
            if k.startswith("cid_"):
                categories.append(int(k[4:]))
        obj['categories'] = categories
        try:
            uid = ext().amp.new_user(obj["user_name"], obj["user_GAID"], obj["is_company"], categories=categories)
            flash("User created")
            if asset_uuid:
                return redirect(url_for('ampissuer_endpoint.asset_users', asset_uuid=asset_uuid))
            return redirect(url_for('ampissuer_endpoint.user', uid=uid))
        except Exception as e:
            flash(f"{e}", "error")
    return render_template('ampissuer/new_user.jinja', amp=ext().amp, obj=obj)

@ampissuer_endpoint.route("/users/<int:uid>/", methods=["GET", "POST"])
def user(uid):
    user = ext().amp.users[uid]
    if request.method == "POST":
        action = request.form.get("action")
        try:
            if action == "update_categories":
                categories = []
                for k, v in request.form.items():
                    if k.startswith("cid_"):
                        categories.append(int(k[4:]))
                user.update_categories(categories)
                flash("Categories updated")
            elif action == "delete":
                ext().amp.delete_user(uid)
                flash("User deleted")
                return redirect(url_for('ampissuer_endpoint.users'))
            else:
                raise NotImplementedError(f"Unknown action {action}")
        except Exception as e:
            flash(f"{e}", "error")
    return render_template('ampissuer/user.jinja', amp=ext().amp, user=user)




@ampissuer_endpoint.route("/managers/")
def managers():
    return render_template('ampissuer/base.jinja', amp=ext().amp)




@ampissuer_endpoint.route("/treasury/")
def treasury():
    return render_template('ampissuer/base.jinja', amp=ext().amp)




@ampissuer_endpoint.route("/settings/", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "clear_cache":
            try:
                ext().amp.sync()
                flash("Cache cleared")
            except Exception as e:
                flash(f"{e}", "error")
        else:
            import time
            time.sleep(10)
            flash("Unknown action", "error")
    return render_template('ampissuer/settings.jinja', amp=ext().amp)




@ampissuer_endpoint.route("/api/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def api(path):
    return ext().amp.fetch(path, request.method, request.data, cache=False)


