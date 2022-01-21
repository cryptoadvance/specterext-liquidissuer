from flask import Flask, send_from_directory, request
from flask_cors import CORS
import os
import requests

app = Flask(__name__)
CORS(app)

API_URL = "https://amp-test.blockstream.com/api/"
AUTH = "token 66b946392661e192718a8822046a1e9a9dc7af51"

@app.route('/api/<path:path>', methods=["GET", "POST", "PUT", "DELETE"])
def api(path):
    path = path.lstrip("/")
    fpath = f"public/api/{path}.json"
    # return cached version
    if request.method == "GET":
        if os.path.isfile(fpath):
            print(f"cached {path}")
            with open(fpath, "r") as f:
                return f.read()

    api_url = f"{API_URL}{path}"
    headers = {'content-type': 'application/json', 'Authorization': AUTH}
    data = request.data
    params = dict(headers=headers)
    if data:
        params["data"] = data
    print(f"fetch {path}")
    res = requests.request( request.method, api_url, **params)
    try:
        os.makedirs(os.path.dirname(fpath))
    except:
        pass
    try:
        with open(fpath, "w") as f:
            f.write(res.text)
    except:
        pass
    return res.text, res.status_code

if __name__ == "__main__":
    app.run(debug=True, port=8081)