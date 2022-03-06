from flask import Flask, request, redirect, jsonify
import pymysql
import requests
from base64 import b64encode

app = Flask(__name__)
cur = None

operator_id = 'operator_id_001'
operator_pw = 'pw_operator'
callback_url = "http://operator.example.com/cb"

access_token = None
access_token_expires_in = None

@app.get('/')
def home():
    return "mydata_cloud: Operator System"

@app.get('/signup')
def sign_up():
    return 'SIGN UP'


@app.get('/register')
def register():
    if request.args.get('scope') == None:
        return '[ERROR] parameter "scope" required'

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

def init_db():
    # create database operator;
    # create user operator@localhost identified by 'mysql_pw';
    # grant all on operator.* to operator@localhost;
    db = pymysql.connect(host='localhost', user='operator', passwd='mysql_pw', db='operator', charset='utf8')
    cur = db.cursor()
    sql  = "CREATE TABLE IF NOT EXISTS user ("
    sql += "id varchar(20) UNIQUE NOT NULL, "
    sql += "pw varchar(20) NOT NULL, "
    sql += "token char(22))"
    cur.execute(sql)

if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=80, debug=True)
