from flask import Flask, request, redirect, jsonify
import pymysql
import requests
from base64 import b64encode

app = Flask(__name__)
db = None
cur = None

operator_id = 'operator_id_001'
operator_pw = 'pw_operator'
callback_url = "http://operator.example.com/cb"

scope_list = ['banking', 'public', 'medical']

access_token = None
access_token_expires_in = None

err_msg = lambda x : '[ERROR] ' + x + '\n'

def check_args(args, li):
    for i in li:
        if args.get(i) == None:
            return False
    return True

@app.get('/')
def home():
    return "mydata_cloud: Operator System\n"

@app.post('/signup')
def sign_up():
    if not check_args(request.form, ['id', 'password']):
        return err_msg('id, password required')

    new_id = request.form['id']
    new_pw = request.form['password']
    
    sql  = "INSERT INTO user (id, pw) "
    sql += "VALUES ('%s', '%s');"%(new_id, new_pw)

    cur.execute(sql)
    db.commit()

    return 'sign up success\n'

@app.post('/register')
def register():
    if not check_args(request.form, ['id', 'password']):
        return err_msg('id, password required')

    sql  = "SELECT id FROM user WHERE "
    sql += "id='%s' AND pw='%s';"%(request.form['id'], request.form['password'])
    cur.execute(sql)
    if len(cur.fetchall()) != 1:
        return 'wrong id or password\n'

    if not check_args(request.args, ['scope']):
        return err_msg('scope required')
    if request.args['scope'] not in scope_list:
        return err_msg('wrong scope')

    redirect_url  = "http://data-source.example.com/authorize"
    redirect_url += "?response_type=code"
    redirect_url += "&scope=" + request.args['scope']
    redirect_url += "&operator_id=" + operator_id
    redirect_url += "&redirect_uri=" + callback_url

    return redirect(redirect_url, code=302)

@app.get('/cb')
def callback():
    if not check_args(request.args, ['code']):
        return err_msg('code required')

    grant_code = request.args['code']
    url = 'http://data-source.example.com/token'
    params = {'grant_type':'authorization_code',
                'code':grant_code,
                'redirect_uri':callback_url}
    headers = {'Authorization':'Basic ' + b64encode((operator_id+':'+operator_pw).encode()).decode(), 
                'Content-Type':'application/x-www-form-urlencoded'}
    requests.post(url, data = params, headers=headers)

    # HTTP_response = receive_HTTP_response()
	# access_token = get_HTTP_body(HTTP_response)

    return 'success\n'

def init_db():
    global db, cur
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
