import re
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey.RSA import construct

from interface import *

def request_data(id, scope):
    ### request data to data source
    data_source_url = url_list_back[scope]
    token = db.get_token(id, scope)
    params = {'token':token, 'data':scope}
    data = requests.get(data_source_url + '/resource', params = params).json()

    ### update engine db

    ### encrypt data
    

    ### store data in db
    db.add_data(id, scope, data[scope])

    return "success\n"

def encrypt_data(data, key):
    # RSA 2048 encryption
    # key : "OpenSSLRSAPublicKey{modulus=be90...a8209,publicExponent=10001}"
    # [output] enc_data : raw ciphertext (not base64 encoded)

    ### parsing 'key' -> modular, exp
    key_string = re.compile('=[0-9|a-f]')
    _modular, _exp = key_string.findall(key)
    modular = int(_modular[1:], 16)
    exp = int(_exp[1:], 16)

    ### RSA encryption 
    pubkey = construct((modular, exp))
    cipher = PKCS1_OAEP.new(pubkey)
    enc_data = cipher.encrypt(data.encode())

    return enc_data

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
        _scope = request_queue.get(_id)

    ### make request for data source
    data_source_url = url_list_back[_scope]
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
    result = request_data(_id, _scope)

    request_queue.pop(_id)      # prevent race condition

    return result