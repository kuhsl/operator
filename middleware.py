from interface import *

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