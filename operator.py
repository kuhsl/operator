from flask import Flask, request, redirect, jsonify
import requests
from base64 import b64encode

app = Flask(__name__)

operator_id = 'operator_id_001'
operator_pw = 'pw_operator'
callback_url = "http://operator.example.com/cb"

access_token = None
access_token_expires_in = None

@app.get('/')
def home():
    return "Hello World!"

@app.get('/register')
def register():

    redirect_url  = "http://data-source.example.com/authorize"
    redirect_url += "?response_type=code"
    redirect_url += "&scope=" + request.args.get('scope')
    redirect_url += "&operator_id=" + operator_id
    redirect_url += "&redirect_uri=" + callback_url

    return redirect(redirect_url, code=302)

@app.get('/cb')
def callback():

    grant_code = request.args.get('code')
    url = 'http://data-source.example.com/token'
    params = {'grant_type':'authorization_code',
                'code':grant_code,
                'redirect_uri':callback_url}
    headers = {'Authorization':'Basic ' + b64encode((operator_id+':'+operator_pw).encode()).decode(), 
                'Content-Type':'application/x-www-form-urlencoded'}
    requests.post(url, data = params, headers=headers)

    # HTTP_response = receive_HTTP_response()	
	# access_token = get_HTTP_body(HTTP_response)

    return 'success'

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=80, debug=True)