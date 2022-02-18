from flask import Flask, flash, redirect, render_template, request, url_for
from amp import Amp
import logging
import json

logger = logging.getLogger(__name__)

app = Flask(__name__)

API_URL = "https://amp-test.blockstream.com/api/"
AUTH = "token 66b946392661e192718a8822046a1e9a9dc7af51"

amp = Amp(API_URL, AUTH)

@app.route("/")
def index():
    return redirect(url_for('assets'))




@app.route("/assets/")
def assets():
    return render_template('assets.jinja', amp=amp)

@app.route("/new_asset/", methods=["GET", "POST"])
def new_asset():
    obj = {}
    if request.method == "POST":
        w = amp.rpc.wallet()
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
            asset = amp.new_asset(obj)
            return redirect(url_for('asset_settings', asset_uuid=asset.asset_uuid))
        except Exception as e:
            flash(f"{e}", "error")
    return render_template('new_asset.jinja', amp=amp, obj=obj)

@app.route("/assets/<asset_uuid>/")
def asset(asset_uuid):
    asset = amp.assets[asset_uuid]
    return render_template('asset/dashboard.jinja', amp=amp, asset=asset)

@app.route("/assets/<asset_uuid>/settings/", methods=["GET", "POST"])
def asset_settings(asset_uuid):
    asset = amp.assets[asset_uuid]
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
                return redirect(url_for('asset_reissuance', asset_uuid=asset.asset_uuid, txid=txid))
            elif action == "fix_reissuances":
                asset.fix_reissuances()
                flash("Reissuances are fixed")
            else:
                raise NotImplementedError(f"Unknown action {action}")
        except Exception as e:
            flash(f"{e}", "error")
    return render_template('asset/settings.jinja', amp=amp, asset=asset)

@app.route("/assets/<asset_uuid>/assignments/")
def asset_assignments(asset_uuid):
    asset = amp.assets[asset_uuid]
    return render_template('asset/assignments.jinja', amp=amp, asset=asset)

@app.route("/assets/<asset_uuid>/distributions/")
def asset_distributions(asset_uuid):
    asset = amp.assets[asset_uuid]
    return render_template('asset/distributions.jinja', amp=amp, asset=asset)

@app.route("/assets/<asset_uuid>/activities/")
def asset_activities(asset_uuid):
    asset = amp.assets[asset_uuid]
    return render_template('asset/base.jinja', amp=amp, asset=asset)

@app.route("/assets/<asset_uuid>/utxos/", methods=["GET", "POST"])
def asset_utxos(asset_uuid):
    asset = amp.assets[asset_uuid]
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
    return render_template('asset/utxos.jinja', amp=amp, asset=asset, utxos=utxos)

@app.route("/assets/<asset_uuid>/users/")
def asset_users(asset_uuid):
    asset = amp.assets[asset_uuid]
    return render_template('asset/users.jinja', amp=amp, asset=asset)

@app.route("/assets/<asset_uuid>/new_assignment/", methods=["GET", "POST"])
def new_assignment(asset_uuid):
    asset = amp.assets[asset_uuid]
    if request.method == "GET":
        return render_template('asset/new_assignment.jinja', amp=amp, asset=asset)
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
            return render_template('asset/new_assignment.jinja', amp=amp, asset=asset)
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
    return redirect(url_for('asset', asset_uuid=asset_uuid))

@app.route("/assets/<asset_uuid>/assignment/<int:assid>/", methods=["POST"])
def change_assignment(asset_uuid, assid):
    asset = amp.assets[asset_uuid]
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
    return redirect(url_for('asset', asset_uuid=asset_uuid))


@app.route("/assets/<asset_uuid>/new_distribution/")
def new_distribution(asset_uuid):
    asset = amp.assets[asset_uuid]
    try:
        duuid = asset.create_distribution()
        flash("Distribution created")
        return redirect(url_for('asset_distribution', asset_uuid=asset_uuid, duuid=duuid))
    except Exception as e:
        flash(f"{e}", "error")
    return redirect(url_for('asset', asset_uuid=asset_uuid))

@app.route("/assets/<asset_uuid>/distribution/<distribution_uuid>/", methods=["POST"])
def change_distribution(asset_uuid, distribution_uuid):
    asset = amp.assets[asset_uuid]
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
    return redirect(url_for('asset', asset_uuid=asset_uuid))

@app.route("/assets/<asset_uuid>/distributions/<duuid>/")
def asset_distribution(asset_uuid, duuid):
    asset = amp.assets[asset_uuid]
    distr = asset.get_distribution(duuid)
    if not distr:
        redirect(url_for('asset', asset_uuid=asset_uuid))
    return render_template('asset/distribution.jinja', amp=amp, asset=asset, distr=distr)

@app.route("/assets/<asset_uuid>/distributions/<duuid>/status/")
def asset_distribution_status(asset_uuid, duuid):
    asset = amp.assets[asset_uuid]
    distr = asset.get_distribution(duuid)
    if not distr:
        return json.dumps({"error": "Distribution is not found"}), 404
    return json.dumps(distr)

@app.route("/assets/<asset_uuid>/reissuance/<txid>/")
def asset_reissuance(asset_uuid, txid):
    asset = amp.assets[asset_uuid]
    reissuance = asset.get_reissuance(txid)
    if not reissuance:
        redirect(url_for('asset', asset_uuid=asset_uuid))
    return render_template('asset/reissuance.jinja', amp=amp, asset=asset, reissuance=reissuance)

@app.route("/assets/<asset_uuid>/reissuance/<txid>/status/")
def asset_reissuance_status(asset_uuid, txid):
    asset = amp.assets[asset_uuid]
    reissuance = asset.get_reissuance(txid)
    if not reissuance:
        return json.dumps({"error": "Distribution is not found"}), 404
    return json.dumps(reissuance)


@app.route("/categories/")
def categories():
    return render_template('categories.jinja', amp=amp)

@app.route("/new_category/", methods=["GET", "POST"])
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
            amp.new_category(name, description)
            flash("New category created")
            return redirect(url_for("categories"))
        except Exception as e:
            flash(f"{e}", "error")
    return render_template('new_category.jinja', amp=amp, obj=obj)

@app.route("/categories/<int:cid>/")
def category(cid):
    return render_template('base.jinja', amp=amp)




@app.route("/users/")
def users():
    return render_template('users.jinja', amp=amp)

@app.route("/new_user/", methods=["GET", "POST"])
@app.route("/new_user/for/<asset_uuid>/", methods=["GET", "POST"])
def new_user(asset_uuid=None):
    obj = {'categories': [] if asset_uuid is None else amp.assets[asset_uuid]['requirements']}
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
            uid = amp.new_user(obj["user_name"], obj["user_GAID"], obj["is_company"], categories=categories)
            flash("User created")
            if asset_uuid:
                return redirect(url_for('asset_users', asset_uuid=asset_uuid))
            return redirect(url_for('user', uid=uid))
        except Exception as e:
            flash(f"{e}", "error")
    return render_template('new_user.jinja', amp=amp, obj=obj)

@app.route("/users/<int:uid>/", methods=["GET", "POST"])
def user(uid):
    user = amp.users[uid]
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
                amp.delete_user(uid)
                flash("User deleted")
                return redirect(url_for('users'))
            else:
                raise NotImplementedError(f"Unknown action {action}")
        except Exception as e:
            flash(f"{e}", "error")
    return render_template('user.jinja', amp=amp, user=user)




@app.route("/managers/")
def managers():
    return render_template('base.jinja', amp=amp)




@app.route("/treasury/")
def treasury():
    return render_template('base.jinja', amp=amp)




@app.route("/settings/", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "clear_cachex":
            try:
                amp.clear_cache()
                flash("Cache cleared")
            except Exception as e:
                flash(f"{e}", "error")
        else:
            import time
            time.sleep(10)
            flash("Unknown action", "error")
    return render_template('settings.jinja', amp=amp)




@app.route("/api/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def api(path):
    return amp.fetch(path, request.method, request.data, cache=False)

if __name__ == "__main__":
    import os
    amp.sync()
    app.secret_key = 'shitcoin factory'
    app.run(debug=True, port=8081)