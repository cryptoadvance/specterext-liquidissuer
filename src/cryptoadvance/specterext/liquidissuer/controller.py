import json
import logging
import os

from cryptoadvance.specter.services.controller import \
    user_secret_decrypted_required
from cryptoadvance.specter.services.service_encrypted_storage import \
    ServiceEncryptedStorageError
from cryptoadvance.specter.user import User
from cryptoadvance.specter.wallet import Wallet
from cryptoadvance.specterext.liquidissuer.amp import Amp, APIException
from cryptoadvance.specterext.liquidissuer.rpc import SpecterError
from flask import current_app as app
from flask import flash, redirect, render_template, request, url_for
from flask_babel import lazy_gettext as _
from flask_login import current_user, login_required

from .service import AmpissuerService

logger = logging.getLogger(__name__)

ampissuer_endpoint = AmpissuerService.blueprint

def ext() -> AmpissuerService:
    ''' convenience for getting the extension-object'''
    return app.specter.service_manager.services["ampissuer"]

@ampissuer_endpoint.before_request
def selfcheck():
    """check status before every request"""
    if '/static/' in request.path:
        return
    # This is some horrible awesome workaround which makes development easier 
    # Instead of loading the Amp-credentials from the SecureStorage, it loads them from the 
    # Environment variable but only in DevelopmentConfig and only if AMP_AUTH exists
    if app.config["SPECTER_CONFIGURATION_CLASS_FULLNAME"].endswith("DevelopmentConfig") and os.environ.get("AMP_AUTH"):
        if not ext()._amp.get("liquidtestnet"):
            ext()._amp["liquidtestnet"] = Amp(app.config["API_TESTNET_URL"], os.environ["AMP_AUTH"], app.specter.rpc.clone())
            ext().amp.sync()
        if not ext().amp.healthy:
            ext().amp.auth = app.config("AMP_AUTH")
        return
    if app.config["LOGIN_DISABLED"]:
        # No logins means no password so no user_secret is possible
        flash(
            _(
                "Service integration requires an authentication method that includes a password"
            )
        )
        return redirect(url_for(f"settings_endpoint.auth"))
    elif not current_user.is_authenticated:
        return app.login_manager.unauthorized()
    elif not current_user.is_user_secret_decrypted:
        flash(_("Must login again to access encrypted Amp credentials"))
        # Force re-login; automatically redirects back to calling page
        return app.login_manager.unauthorized()

@ampissuer_endpoint.route("/")
@login_required
def index():
    if ext().amp.healthy:
        return redirect(url_for('ampissuer_endpoint.assets'))
    else:
        return redirect(url_for('ampissuer_endpoint.settings_get'))

@ampissuer_endpoint.route("/rawassets/")
def rawassets():
    return render_template('ampissuer/rawassets.jinja', amp=ext().amp)

@ampissuer_endpoint.route("/new_rawasset/", methods=["GET", "POST"])
def new_rawasset():
    obj = {"raw": True}
    if request.method == "POST":
        obj = {
            "raw": True,
            "asset_name": request.form.get("asset_name"),
            "amount": int(request.form.get("amount") or 0),
            "domain": request.form.get("domain"),
            "ticker": request.form.get("ticker"),
            "precision": int(request.form.get("precision", 0)),
            "pubkey": request.form.get("pubkey"),
            "is_confidential": bool(request.form.get("is_confidential")),
            "reissue": int(request.form.get("reissue", 0) or 0),
            "issue_address": request.form.get("issue_address", ""),
            "reissue_address": request.form.get("reissue_address", ""),
        }
        try:
            asset = ext().amp.new_rawasset(obj)
            flash(f"Asset {asset.ticker} was issued")
            return redirect(url_for('ampissuer_endpoint.rawassets'))
        except Exception as e:
            flash(f"{e}", "error")
    return render_template('ampissuer/new_asset.jinja', amp=ext().amp, rawasset=True, obj=obj)

@ampissuer_endpoint.route("/rawasset/<asset_id>/", methods=["GET", "POST"])
def rawasset(asset_id):
    asset = ext().amp.rawassets[asset_id]
    if request.method == "POST":
        action = request.form.get("action")
        try:
            if action == "register":
                asset.register()
                flash('Asset registered')
            elif action == "reissue":
                amount = int(request.form.get('reissue_amount', 0) or 0)
                txid = asset.reissue(amount)
                flash(f"Reissued {amount} sats in transaction {txid}")
            else:
                raise NotImplementedError(f"Unknown action {action}")
        except Exception as e:
            flash(f"{e}", "error")
    return render_template('ampissuer/rawasset.jinja', amp=ext().amp, asset=asset)

@ampissuer_endpoint.route("/assets/")
@login_required
def assets():
    try:
        return render_template('ampissuer/assets.jinja', amp=ext().amp)
    except APIException as apie:
        logger.error(apie)
        flash_apiexc(apie)
        # ToDo: setting up API-Credentials in the settings endpoint
        return redirect(url_for('ampissuer_endpoint.settings_get'))
    except Exception as e:
        logger.exception(e)
        raise e

@ampissuer_endpoint.route("/new_asset/", methods=["GET", "POST"])
@login_required
def new_asset():
    obj = {}
    if request.method == "POST":
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
            "issue_address": request.form.get("issue_address", ""),
            "reissue_address": request.form.get("reissue_address", ""),
        }
        try:
            asset = ext().amp.new_asset(obj)
            return redirect(url_for('ampissuer_endpoint.asset_settings', asset_uuid=asset.asset_uuid))
        except Exception as e:
            flash(f"{e}", "error")
    return render_template('ampissuer/new_asset.jinja', amp=ext().amp, obj=obj)

@ampissuer_endpoint.route("/assets/<asset_uuid>/")
@login_required
def asset(asset_uuid):
    asset = ext().amp.assets[asset_uuid]
    return render_template('ampissuer/asset/dashboard.jinja', amp=ext().amp, asset=asset)

@ampissuer_endpoint.route("/assets/<asset_uuid>/settings/", methods=["GET", "POST"])
@login_required
def asset_settings(asset_uuid):
    asset = ext().amp.assets[asset_uuid]
    if request.method == "POST":
        action = request.form.get("action")
        try:
            if action == "register":
                asset.register()
                flash('Asset registered')
            elif action == "authorize":
                # asset.authorize()
                # flash('Asset authorized')
                flash("Asset authorization is temporarily disabled", "error")
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
@login_required
def asset_assignments(asset_uuid):
    asset = ext().amp.assets[asset_uuid]
    return render_template('ampissuer/asset/assignments.jinja', amp=ext().amp, asset=asset)

@ampissuer_endpoint.route("/assets/<asset_uuid>/distributions/")
@login_required
def asset_distributions(asset_uuid):
    asset = ext().amp.assets[asset_uuid]
    return render_template('ampissuer/asset/distributions.jinja', amp=ext().amp, asset=asset)

@ampissuer_endpoint.route("/assets/<asset_uuid>/activities/")
@login_required
def asset_activities(asset_uuid):
    asset = ext().amp.assets[asset_uuid]
    return render_template('ampissuer/asset/base.jinja', amp=ext().amp, asset=asset)

@ampissuer_endpoint.route("/assets/<asset_uuid>/utxos/", methods=["GET", "POST"])
@login_required
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
@login_required
def asset_users(asset_uuid):
    asset = ext().amp.assets[asset_uuid]
    return render_template('ampissuer/asset/users.jinja', amp=ext().amp, asset=asset)

@ampissuer_endpoint.route("/assets/<asset_uuid>/new_assignment/", methods=["GET", "POST"])
@login_required
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
@login_required
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
@login_required
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
@login_required
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
@login_required
def asset_distribution(asset_uuid, duuid):
    asset = ext().amp.assets[asset_uuid]
    distr = asset.get_distribution(duuid)
    if not distr:
        redirect(url_for('ampissuer_endpoint.asset', asset_uuid=asset_uuid))
    return render_template('ampissuer/asset/distribution.jinja', amp=ext().amp, asset=asset, distr=distr)

@ampissuer_endpoint.route("/assets/<asset_uuid>/distributions/<duuid>/status/")
@login_required
def asset_distribution_status(asset_uuid, duuid):
    asset = ext().amp.assets[asset_uuid]
    distr = asset.get_distribution(duuid)
    if not distr:
        return json.dumps({"error": "Distribution is not found"}), 404
    return json.dumps(distr)

@ampissuer_endpoint.route("/assets/<asset_uuid>/reissuance/<txid>/")
@login_required
def asset_reissuance(asset_uuid, txid):
    asset = ext().amp.assets[asset_uuid]
    reissuance = asset.get_reissuance(txid)
    if not reissuance:
        redirect(url_for('ampissuer_endpoint.asset', asset_uuid=asset_uuid))
    return render_template('ampissuer/asset/reissuance.jinja', amp=ext().amp, asset=asset, reissuance=reissuance)

@ampissuer_endpoint.route("/assets/<asset_uuid>/reissuance/<txid>/status/")
@login_required
def asset_reissuance_status(asset_uuid, txid):
    asset = ext().amp.assets[asset_uuid]
    reissuance = asset.get_reissuance(txid)
    if not reissuance:
        return json.dumps({"error": "Distribution is not found"}), 404
    return json.dumps(reissuance)


@ampissuer_endpoint.route("/categories/")
@login_required
def categories():
    return render_template('ampissuer/categories.jinja', amp=ext().amp)

@ampissuer_endpoint.route("/new_category/", methods=["GET", "POST"])
@login_required
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
@login_required
def category(cid):
    return render_template('ampissuer/base.jinja', amp=ext().amp)


@ampissuer_endpoint.route("/users/")
@login_required
def users():
    return render_template('ampissuer/users.jinja', amp=ext().amp)


@ampissuer_endpoint.route("/new_user/", methods=["GET", "POST"])
@ampissuer_endpoint.route("/new_user/for/<asset_uuid>/", methods=["GET", "POST"])
@login_required
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
@login_required
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
            logger.exception(e)
            flash(f"{e}", "error")
    return render_template('ampissuer/user.jinja', amp=ext().amp, user=user)




@ampissuer_endpoint.route("/managers/")
@login_required
def managers():
    return render_template('ampissuer/base.jinja', amp=ext().amp)


@ampissuer_endpoint.route("/treasury/", methods=["GET", "POST"])
@login_required
def treasury():
    if request.method == "POST":
        action = request.form.get("action")
        try:
            if action == "getnewaddress":
                address = ext().amp.getnewaddress()
                flash(f"New address: {address}")
            elif action == "send":
                address = request.form.get("sendaddress")
                asset = request.form.get("asset")
                if asset == "bitcoin":
                    asset = None
                amount = int(request.form.get("sendamount"))
                txid = ext().amp.send(address=address, sats=amount, asset=asset)
                flash(f"Transaction sent: {txid}")
            else:
                raise NotImplementedError(f"Unknown action {action}")
        except Exception as e:
            logger.exception(e)
            flash(f"{e}", "error")
    return render_template('ampissuer/treasury.jinja', amp=ext().amp)


@ampissuer_endpoint.route("/settings/", methods=["GET"])
@login_required
def settings_get():
    amp_token = ext().get_amp_token()
    return render_template('ampissuer/settings.jinja', 
        amp=ext().amp, 
        amp_token=amp_token,
        show_menu=AmpissuerService.id in app.specter.user_manager.get_user().services
    )

@ampissuer_endpoint.route("/settings/", methods=["POST"])
@login_required
def settings_post():
    action = request.form.get("action")
    if action == "obtain_token":
        logger.info("Obtaining an Amp token")
        try:
            token = ext().amp.obtain_token(request.form["amp_username"], request.form["amp_password"])
            ext().set_amp_token("token " + token)
            user = app.specter.user_manager.get_user()
            user.add_service(AmpissuerService.id)
        except APIException as apie:
            flash_apiexc(apie)
        
    elif action == "delete_token":
        logger.info("Deleting the Amp token")
        ext().set_amp_token("")
    elif action == "save":
        logger.info("Saving")
        user = app.specter.user_manager.get_user()
        if request.form["show_menu"] == "yes":
            user.add_service(AmpissuerService.id)
        else:
            user.remove_service(AmpissuerService.id)
    else:
        import time
        time.sleep(10)
        flash("Unknown action", "error")
    return redirect(url_for('ampissuer_endpoint.settings_get'))


@ampissuer_endpoint.route("/api/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
@login_required
def api(path):
    return ext().amp.fetch(path, request.method, request.data, cache=False)

def flash_apiexc(e: APIException):
    try:
        if e == None:
            flash("Sorry, an Error occured and i can't be more specific", "error")
        print(f"msg: {e.msg}")
        msg = json.loads(e.msg)
        if msg.get("detail"):
            flash(msg.get("detail"), "error")
        for error in msg.get("non_field_errors",[]):
            flash(error, "error")
        for field in msg.keys():
            if field != "detail" and field != "non_field_errors":
                flash(f"{field}: {', '.join(msg[field])}", "error")
    except Exception as le:
        logger.exception(le)
        flash(str(e), "error")


