from flask import Flask, flash, redirect, render_template, request, url_for
from amp import Amp
import logging

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

@app.route("/new_asset/")
def new_asset():
    return render_template('base.jinja', amp=amp)

@app.route("/assets/<asset_uuid>/")
def asset(asset_uuid):
    asset = amp.assets[asset_uuid]
    return render_template('asset/dashboard.jinja', amp=amp, asset=asset)

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

@app.route("/assets/<asset_uuid>/utxos/")
def asset_utxos(asset_uuid):
    asset = amp.assets[asset_uuid]
    return render_template('asset/base.jinja', amp=amp, asset=asset)

@app.route("/assets/<asset_uuid>/users/")
def asset_users(asset_uuid):
    asset = amp.assets[asset_uuid]
    return render_template('asset/base.jinja', amp=amp, asset=asset)

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
        res = asset.create_distribution()
        logger.debug(res)
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
        else:
            raise RuntimeError("Not implemented")
    except Exception as e:
        flash(f"{e}", "error")
    return redirect(url_for('asset', asset_uuid=asset_uuid))




@app.route("/categories/")
def categories():
    return render_template('categories.jinja', amp=amp)

@app.route("/new_category/")
def new_category():
    return render_template('base.jinja', amp=amp)

@app.route("/categories/<int:cid>/")
def category(cid):
    return render_template('base.jinja', amp=amp)




@app.route("/users/")
def users():
    return render_template('users.jinja', amp=amp)

@app.route("/new_user/")
def new_user():
    return render_template('base.jinja', amp=amp)

@app.route("/users/<int:uid>/")
def user(uid):
    user = amp.users[uid]
    return render_template('base.jinja', amp=amp, user=user)




@app.route("/managers/")
def managers():
    return render_template('base.jinja', amp=amp)




@app.route("/treasury/")
def treasury():
    return render_template('base.jinja', amp=amp)




@app.route("/settings/")
def settings():
    return render_template('base.jinja', amp=amp)




@app.route("/api/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def api(path):
    return amp.fetch(path, request.method, request.data, cache=False)

if __name__ == "__main__":
    import os
    amp.sync()
    app.secret_key = 'shitcoin factory'
    app.run(debug=True, port=8081)