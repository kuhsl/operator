from flask import Flask, request, redirect, jsonify, make_response

from database import init_db, scope_list

# ERROR message
err_msg = lambda x : '[ERROR] ' + x + '\n'

app = Flask(__name__)
app_db, mid_db = init_db()
scope_list = list(scope_list.keys())

operator_id = 'operator_id_001'
operator_pw = 'pw_operator'
callback_url = "http://163.152.71.223/cb"

request_queue = {}
cookie_secret_key = ''

def check_args(args, li):
    ### check if necessary parameter included
    for i in li:
        if args.get(i) == None:
            return False
    return True