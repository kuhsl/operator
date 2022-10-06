import json
import requests
from base64 import b64encode, b64decode
import re
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey.RSA import construct

from database import url_list_front, url_list_back
from interface import *

def encrypt_internal(data, cipher_spec):
    max_len=190
    encrypted = b''
    data=data.encode()


    for i in range(0, len(data), max_len):
        end = min(i+max_len, len(data))
        encrypted += cipher_spec.encrypt(data[i:end])

    return encrypted

def encrypt_data(data, key):
    # RSA 2048 encryption
    # key : "OpenSSLRSAPublicKey{modulus=be90...a8209,publicExponent=10001}"
    # [output] enc_data : raw ciphertext ( not base64 encoded / length: 256, 512, 768, ... )

    ### parsing 'key' -> modular, exp
    key_string = re.compile('=[0-9|a-f]*')
    _modular, _exp = key_string.findall(key)
    modular = int(_modular[1:], 16)
    exp = int(_exp[1:], 16)

    ### RSA encryption
    pubkey = construct((modular, exp))
    cipher = PKCS1_OAEP.new(pubkey)
    enc_data = encrypt_internal(data, cipher)

    return enc_data

def request_data(id, scope):
    ### request data to data source
    data_source_url = url_list_back[scope]
    token = mid_db.get_token(id, scope)
    params = {'token':token, 'data':scope}
    data = requests.get(data_source_url + '/resource', params = params, verify=False).json()
    
    ### data format ###
    # {
    #     scope : {
    #         table_name : [

    #             {   column1 : data1_1,
    #                 column2 : data1_2 },

    #             {   column1 : data2_1,
    #                 column2 : data2_2 }
    #         ]
    #     }
    # }

    ### update engine db
    ###
    ###

    ### get key from db
    key = mid_db.get_pubkey(id)

    ### encrypt data
    enc_data = {}
    for table_name in list(data[scope].keys()):
        data_string = str(data[scope][table_name])
        print('data_string: ',data_string)
        encrypted = encrypt_data(data_string, key)
        enc_data[table_name] = [ { 'enc_data': b64encode(encrypted).decode() } ]

    ### store data in db
    mid_db.add_data(id, scope, enc_data)      ## enc_data : { table1 : [ { 'enc_data' : encrypted_data } ], ... }

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
        _scope = request_queue.get(_id)

    ### make request for data source
    data_source_url = url_list_back[_scope]
    url = data_source_url + "/token"
    params = {'grant_type':'authorization_code',
                'code':grant_code,
                'redirect_uri':callback_url}
    headers = {'Authorization':'Basic ' + b64encode((operator_id+':'+operator_pw).encode()).decode(),
                'Content-Type':'application/x-www-form-urlencoded'}
    response = requests.post(url, data = params, headers=headers, verify=False).json()
    # response : dict type

    ### parse response and get access token
    access_token = response['access_token']
    expires_in = response['expires_in']

    ### save token in db
    mid_db.add_token(_id, _scope, access_token, expires_in)

    ### get data from data source
    result = request_data(_id, _scope)

    request_queue.pop(_id)      # prevent race condition

    return result
