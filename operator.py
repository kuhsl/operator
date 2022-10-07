import json
import requests
from base64 import b64encode, b64decode
from secrets import token_bytes
import hashlib
from Crypto.Cipher import AES
import time
import inspect

from database import url_list_front, url_list_back
from interface import *
import middleware

# related to cookie (encryption)
BLOCK_SIZE = 16
pad = lambda s: bytes(s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * chr(BLOCK_SIZE - len(s) % BLOCK_SIZE), 'utf-8')
unpad = lambda s: s[:-ord(s[len(s) - 1:])].decode('utf-8')

def make_cookie(seed):
    ### make secret cookie
    timestamp = bytes(str(int(time.time())).rjust(BLOCK_SIZE, '0'),'utf-8')
    aes = AES.new(cookie_secret_key, AES.MODE_CBC, timestamp)
    enc = aes.encrypt(pad(seed))
    cookie = seed + ':' + b64encode(enc).decode()

    return cookie

def check_cookie(cookie):
    ### verify cookie
    if cookie == None:  # no cookie set
        return None

    ### verifying logic comes here
    seed, enc = cookie.split(':')
    aes = AES.new(cookie_secret_key, AES.MODE_CBC, pad(seed)[:16])
    timestamp = int(aes.decrypt(b64decode(enc))[:16])
    diff = int(time.time()) - timestamp

    if diff >= 3600:
        return None
    else:
        return seed

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

    pw_hash = hashlib.sha256(new_pw.encode()).hexdigest()

    app_db.add_user(new_id, pw_hash)

    return 'sign up success\n'

@app.post('/register')      # register data to mydata system
def register():
    ### check id, pw
    cookie = request.cookies.get("login")
    _id = check_cookie(cookie)

    if _id == None:
        return err_msg('login first')

    ### check scope
    if not check_args(request.args, ['scope']):
        return err_msg('scope required')
    else:
        _scope = request.args['scope']

    if _scope not in scope_list:
        return err_msg('wrong scope')

    ### check pubkey
    if not check_args(request.form, ['pubkey']):
        return err_msg('public key required')
    else:
        _pubkey = request.form['pubkey']

    app_db.add_pubkey(_id, _pubkey)     ## add pubkey into db

    ### add info into request_queue
    request_queue[_id] = _scope

    ### make redirect response
    data_source_url = url_list_front[_scope]
    redirect_url  = data_source_url + "/authorize"
    redirect_url += "?response_type=authorization_code"
    redirect_url += "&scope=" + _scope
    redirect_url += "&operator_id=" + operator_id
    redirect_url += "&redirect_uri=" + callback_url
    redirect_url += "&state=" + _id

    return redirect(redirect_url, code=302)

@app.post('/login')
def login():
    ### check id, pw
    if not check_args(request.form, ['id', 'password']):
        return err_msg('id, password required')
    else:
        _id = request.form['id']
        _pw = request.form['password']

    pw_hash = hashlib.sha256(_pw.encode()).hexdigest()

    if app_db.get_user(_id, pw_hash) == None:
        return err_msg('wrong id or password')

    ### make response (with cookie)
    cookie_value = make_cookie(_id)
    response = make_response("login success\n")
    response.set_cookie("login", cookie_value)

    return response

#@app.post('/data')
@app.get('/data')          # user get data from operator
def get_data():
    ### check id, pw
    cookie = request.cookies.get("login")
    _id = check_cookie(cookie)

    if _id == None:
        return err_msg('login first')

    ### check scope
    if not check_args(request.args, ['scope']):
        return err_msg('scope required')
    else:
        _scope = request.args['scope']

    if _scope not in scope_list:
        return err_msg('wrong scope')

    ### get data from operator's db
    data = app_db.get_enc_data(_id, _scope)
    return jsonify({_scope:data})


#@app.post('/refresh')
@app.get('/refresh')       # get data from data-source again if token not expired
def refresh():
    ### check id, pw
    cookie = request.cookies.get("login")
    _id = check_cookie(cookie)

    if _id == None:
        return err_msg('login first')

    ### check scope
    if not check_args(request.args, ['scope']):
        return err_msg('scope required')
    else:
        _scope = request.args['scope']

    if _scope not in scope_list:
        return err_msg('wrong scope')

    ### get data from data source
    return request_data(_id, _scope)

#@app.post('/delete')
@app.get('/delete')        # delete data from operator db
def delete():
    ### check id, pw
    cookie = request.cookies.get("login")
    _id = check_cookie(cookie)

    if _id == None:
        return err_msg('login first')

    ### check scope
    if not check_args(request.args, ['scope']):
        return err_msg('scope required')
    else:
        _scope = request.args['scope']

    if _scope not in scope_list:
        return err_msg('wrong scope')

    ### delete data from operator db
    app_db.del_data(_id, _scope)
    app_db.del_token(_id, _scope)
    return "success\n"

if __name__ == '__main__':
    cookie_secret_key = token_bytes(BLOCK_SIZE)
    app.run(host='0.0.0.0', port=80, debug=True)
    app.config['JSON_AS_ASCII'] = False

