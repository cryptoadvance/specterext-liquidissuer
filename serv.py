from flask import Flask, render_template, request
from amp import Amp

app = Flask(__name__)

API_URL = "https://amp-test.blockstream.com/api/"
AUTH = "token 66b946392661e192718a8822046a1e9a9dc7af51"

amp = Amp(API_URL, AUTH)

@app.route("/")
def index():
    return render_template('dashboard.jinja', amp=amp)




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
    return render_template('base.jinja', amp=amp, asset=asset)

@app.route("/assets/<asset_uuid>/distributions/")
def asset_distributions(asset_uuid):
    asset = amp.assets[asset_uuid]
    return render_template('base.jinja', amp=amp, asset=asset)

@app.route("/assets/<asset_uuid>/activities/")
def asset_activities(asset_uuid):
    asset = amp.assets[asset_uuid]
    return render_template('base.jinja', amp=amp, asset=asset)

@app.route("/assets/<asset_uuid>/utxos/")
def asset_utxos(asset_uuid):
    asset = amp.assets[asset_uuid]
    return render_template('base.jinja', amp=amp, asset=asset)

@app.route("/assets/<asset_uuid>/users/")
def asset_users(asset_uuid):
    asset = amp.assets[asset_uuid]
    return render_template('base.jinja', amp=amp, asset=asset)

@app.route("/assets/<asset_uuid>/new_assignment/")
def new_assignment(asset_uuid):
    asset = amp.assets[asset_uuid]
    return render_template('base.jinja', amp=amp, asset=asset)

@app.route("/assets/<asset_uuid>/new_distribution/")
def new_distribution(asset_uuid):
    asset = amp.assets[asset_uuid]
    return render_template('base.jinja', amp=amp, asset=asset)





@app.route("/categories/")
def categories():
    return render_template('categories.jinja', amp=amp)

@app.route("/new_category/")
def new_category():
    return render_template('base.jinja', amp=amp)

@app.route("/categories/<cid>/")
def category(cid):
    return render_template('base.jinja', amp=amp)




@app.route("/users/")
def users():
    return render_template('users.jinja', amp=amp)

@app.route("/new_user/")
def new_user():
    return render_template('base.jinja', amp=amp)

@app.route("/users/<uid>/")
def user(uid):
    uid = int(uid)
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
    return amp.fetch(path, request.method, request.data)

if __name__ == "__main__":
    amp.sync()
    app.run(debug=True, port=8081)