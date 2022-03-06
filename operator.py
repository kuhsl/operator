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
data_source_url = "http://data-source.example.com:8080"

scope_list = ['banking', 'public', 'medical']

# ERROR message
err_msg = lambda x : '[ERROR] ' + x + '\n'

def check_args(args, li):
    ### check if necessary parameter included
    for i in li:
        if args.get(i) == None:
            return False
    return True

@app.get('/')
def home():
    return "mydata_cloud: Operator System\n"

@app.post('/signup')        # sign up to mydata system
def sign_up():
    if not check_args(request.form, ['id', 'password']):
        return err_msg('id, password required')
    else:
        new_id = request.form['id']
        new_pw = request.form['password']
    
    sql  = "INSERT INTO user (id, pw) "
    sql += "VALUES ('%s', '%s')"%(new_id, new_pw)
    cur.execute(sql)

    sql  = "INSERT INTO token (id) "
    sql += "VALUES ('%s')"%(new_id)
    cur.execute(sql)

    db.commit()

    return 'sign up success\n'

@app.post('/register')      # register data to mydata system
def register():
    ### check id, pw
    if not check_args(request.form, ['id', 'password']):
        return err_msg('id, password required')
    else:
        _id = request.form['id']
        _pw = request.form['password']

    sql  = "SELECT id FROM user WHERE "
    sql += "id='%s' AND pw='%s'"%(_id, _pw)
    cur.execute(sql)
    if len(cur.fetchall()) != 1:
        return 'wrong id or password\n'

    ### check scope
    if not check_args(request.args, ['scope']):
        return err_msg('scope required')
    else:
        _scope = request.args['scope']

    if _scope not in scope_list:
        return err_msg('wrong scope')

    ### make redirect response
    redirect_url  = data_source_url + "/authorize"
    redirect_url += "?response_type=code"
    redirect_url += "&scope=" + request.args['scope']
    redirect_url += "&operator_id=" + operator_id
    redirect_url += "&redirect_uri=" + callback_url
    redirect_url += "&state=" + _id

    return redirect(redirect_url, code=302)

@app.get('/cb') # get grant code (from user) -> get access token (from data source)
def callback():
    ### parse request and get grant code
    if not check_args(request.args, ['code']):
        return err_msg('code required')
    else:
        grant_code = request.args['code']

    ### make request for data source
    url = data_source_url + "/token"
    params = {'grant_type':'authorization_code',
                'code':grant_code,
                'redirect_uri':callback_url}
    headers = {'Authorization':'Basic ' + b64encode((operator_id+':'+operator_pw).encode()).decode(), 
                'Content-Type':'application/x-www-form-urlencoded'}
    response = requests.post(url, data = params, headers=headers)
    # response : dict type

    ### parse response and get access token
    access_token = response['access_token']
    expires_in = response['expires_in']

    ### save token in db
    sql  = "INSERT INTO user"
    ### NOT FINISHED
    ### 
    ###

    return 'success\n'

def init_db():
    global db, cur
    # create database operator;
    # create user operator@localhost identified by 'mysql_pw';
    # grant all on operator.* to operator@localhost;

    ### connect db
    db = pymysql.connect(host='localhost', user='operator', passwd='mysql_pw', db='operator', charset='utf8')
    cur = db.cursor()

    ### creat table "user"
    sql  = "CREATE TABLE IF NOT EXISTS user ("
    sql += "id varchar(20) UNIQUE NOT NULL, "
    sql += "pw varchar(20) NOT NULL)"
    cur.execute(sql)

    ### create table "token"
    sql  = "CREATE TABLE IF NOT EXISTS token ("
    sql += "id varchar(20) UNIQUE NOT NULL, "
    sql += "b_token char(22), b_expire int, "
    sql += "p_token char(22), p_expire int, "
    sql += "m_token char(22), m_expire int)"
    cur.execute(sql)

    db.commit()

if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=80, debug=True)
