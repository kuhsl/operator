from flask import Flask, request, redirect, jsonify

app = Flask(__name__)

operator_id = 'operator_id_001'
operator_pw = 'pw_operator'
callback_url = "http://operator.example.com/cb"

@app.get('/')
def home():
    return "Hello World!"

@app.get('/register')
def register():

    redirect_url  = "http://data-source.example.com/authorize"
    redirect_url += "?response_type=code"
    redirect_url += "&scope=" + request.args.get('scope')
    redirect_url += "&operator_id=" + operator_id
    redirect_url += "&redirect_uri=" + callback_url

    return redirect(redirect_url, code=302)

@app.get('/cb')
def callback():

    

    return

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=80, debug=True)