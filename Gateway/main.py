from flask import Flask, request
import requests

app = Flask(__name__)

def make_request(path, port):
    headers = {key: value for key, value in request.headers}
    if request.method == 'GET':
        resp = requests.get(f'http://localhost:{port}/{path}', headers=headers)
    elif request.method == 'POST':
        resp = requests.post(f'http://localhost:{port}/{path}', json=request.get_json(), headers=headers)
    elif request.method == 'PUT':
        resp = requests.put(f'http://localhost:{port}/{path}', json=request.get_json(), headers=headers)
    else:
        resp = requests.delete(f'http://localhost:{port}/{path}', json=request.get_json(), headers=headers)
    return resp.content, resp.status_code, resp.headers.items()


@app.route('/auth/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def auth_service(path):
    return make_request(path, 6800)

@app.route('/restaurant/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def restaurant_service(path):
    return make_request(path, 6900)

if __name__ == '__main__':
    app.run(port=6700)
