from flask import Flask, request, redirect, jsonify, make_response
from database import init_db, scope_list
import requests
from base64 import b64encode
from secrets import token_bytes

app = Flask(__name__)
db = init_db()
scope_list = list(scope_list.keys())

operator_id = 'operator_id_001'
operator_pw = 'pw_operator'
callback_url = "http://163.152.71.223/cb"
data_source_url = "http://163.152.30.239"

request_queue = {}
cookie_secret_key = ''

# ERROR message
err_msg = lambda x : '[ERROR] ' + x + '\n'

def check_args(args, li):
    ### check if necessary parameter included
    for i in li:
        if args.get(i) == None:
            return False
    return True

def request_data(id, scope):
    ### request data to data source
    token = db.get_token(id, scope)
    params = {'token':token, 'data':scope}
    data = requests.get(data_source_url + '/resource', params = params).json()

    ### store data in db
    db.add_data(id, scope, data[scope])

    return "success\n"

def make_cookie(seed):
    ### make secret cookie 

    return seed

def check_cookie(seed, cookie):
    ### verify cookie

    if seed == cookie:
        return True
    
    return False

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
    
    db.add_user(new_id, new_pw)

    return 'sign up success\n'

@app.post('/register')      # register data to mydata system
def register():
    ### check id, pw
    if not check_args(request.form, ['id', 'password']):
        return err_msg('id, password required')
    else:
        _id = request.form['id']
        _pw = request.form['password']

    if db.get_user(_id, _pw) == None:
        return err_msg('wrong id or password')

    ### check scope
    if not check_args(request.args, ['scope']):
        return err_msg('scope required')
    else:
        _scope = request.args['scope']

    if _scope not in scope_list:
        return err_msg('wrong scope')

    ### add info into request_queue
    request_queue[_id] = _scope

    ### make redirect response
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

    if db.get_user(_id, _pw) == None:
        return err_msg('wrong id or password')
    
    ### make response (with cookie)
    cookie_value = make_cookie(_id)
    response = make_response("login success\n")
    response.set_cookie("login", cookie_value)

    return response

@app.post('/data')          # user get data from operator
def get_data():
    ### check id, pw
    if not check_args(request.form, ['id', 'password']):
        return err_msg('id, password required')
    else:
        _id = request.form['id']
        _pw = request.form['password']

    if db.get_user(_id, _pw) == None:
        return err_msg('wrong id or password')

    ### check scope
    if not check_args(request.args, ['scope']):
        return err_msg('scope required')
    else:
        _scope = request.args['scope']

    if _scope not in scope_list:
        return err_msg('wrong scope')
    
    ### get data from operator's db
    data = db.get_data(_id, _scope)
    return jsonify({_scope:data})

@app.post('/refresh')       # get data from data-source again if token not expired
def refresh():
    ### check id, pw
    if not check_args(request.form, ['id', 'password']):
        return err_msg('id, password required')
    else:
        _id = request.form['id']
        _pw = request.form['password']

    if db.get_user(_id, _pw) == None:
        return err_msg('wrong id or password')

    ### check scope
    if not check_args(request.args, ['scope']):
        return err_msg('scope required')
    else:
        _scope = request.args['scope']

    if _scope not in scope_list:
        return err_msg('wrong scope')
    
    ### get data from data source
    return request_data(_id, _scope)

@app.post('/delete')        # delete data from operator db
def delete():
    ### check id, pw
    if not check_args(request.form, ['id', 'password']):
        return err_msg('id, password required')
    else:
        _id = request.form['id']
        _pw = request.form['password']

    if db.get_user(_id, _pw) == None:
        return 'wrong id or password\n'
    
    ### check scope
    if not check_args(request.args, ['scope']):
        return err_msg('scope required')
    else:
        _scope = request.args['scope']

    if _scope not in scope_list:
        return err_msg('wrong scope')
    
    ### delete data from operator db
    db.del_data(_id, _scope)
    db.del_token(_id, _scope)
    return "success\n"

@app.get('/cb') # get grant code (from user) -> get access token (from data source)
def callback():
    ### parse request and get grant code
    if not check_args(request.args, ['state', 'code']):
        return err_msg('state, code required')
    else:
        _id = request.args['state']
        grant_code = request.args['code']
    
    ### validate if the user once requested for register data
    if request_queue.get(_id) == None:
        return err_msg('Not Proper Access')
    else:
        _scope = request_queue.pop(_id)

    ### make request for data source
    url = data_source_url + "/token"
    params = {'grant_type':'authorization_code',
                'code':grant_code,
                'redirect_uri':callback_url}
    headers = {'Authorization':'Basic ' + b64encode((operator_id+':'+operator_pw).encode()).decode(), 
                'Content-Type':'application/x-www-form-urlencoded'}
    response = requests.post(url, data = params, headers=headers).json()
    # response : dict type

    ### parse response and get access token
    access_token = response['access_token']
    expires_in = response['expires_in']

    ### save token in db
    db.add_token(_id, _scope, access_token, expires_in)

    ### get data from data source
    return request_data(_id, _scope)

if __name__ == '__main__':
    cookie_secret_key = token_bytes(22)
    app.run(host='0.0.0.0', port=80, debug=True)
