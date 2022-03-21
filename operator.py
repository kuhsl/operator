from flask import Flask, request, redirect, jsonify
from database import init_db, scope_list
import requests
from base64 import b64encode

app = Flask(__name__)
db = init_db()
scope_list = list(scope_list.keys())

operator_id = 'operator_id_001'
operator_pw = 'pw_operator'
callback_url = "http://10.11.12.3/cb"
data_source_url = "http://163.152.30.239"

request_queue = {}

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
        return 'wrong id or password\n'

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

@app.post('/data')          # user get data from operator
def get_data():
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
    
    ### get data from operator's db
    return jsonify(db.get_data(_id, _scope))

@app.post('/refresh')       # get data from data-source again if token not expired
def refresh():
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
    
    ### get data from data source
    return db.request_data(_id, _scope)

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
    return db.request_data(_id, _scope) + '\n'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
