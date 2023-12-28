from flask import Flask, request, render_template
import json
import sqlite3
import core.db_accounts as db_accounts
import core.db_operation as db_operation
import core.db_transaction as db_transaction
from core.db_transaction import DonationTransaction, ItemQuant, ExchangeTransaction
from core.my_response import ResponseState, SimpleResponse
import time, threading
import os



DB_PATH = "main.sqlite"

def cleanup():
    # db_accounts.delete_expired_email_verify(CON)
    # db_accounts.delete_expired_sessions(CON)
    # threading.Timer(60, cleanup).start()
    pass


app = Flask(__name__)

@app.route('/')
def index():
    return "Welcome",200

@app.route('/register', methods=['POST'])
def register():

    """
    data = {
        email
        username
        password
        code
        }
    """

    data = request.get_json()

    if not all( field in data for field in ('email', 'username', 'password', 'code')):
        return json.dumps(SimpleResponse(ResponseState.FAILURE, "INVALID_DATA").__dict__), 400
    
    sr = db_accounts.create_account(CON, data['email'], data['username'], data['password'], data['code'])

    if sr.state != ResponseState.SUCCESS:
        return json.dumps(sr.__dict__), 400
    
    return "Account created", 201

@app.route('/login', methods=['POST'])
def login():

    """
    data = {
        username
        password
        }
    """

    data = request.get_json()

    if not all( field in data for field in ('username', 'password')):
        return json.dumps(SimpleResponse(ResponseState.FAILURE, "INVALID_DATA").__dict__), 400
    
    sr = db_accounts.login_by_username(CON, data['username'], data['password'], True)

    if sr.state != ResponseState.SUCCESS:
        return json.dumps(sr.__dict__), 400

    db_accounts.log_session_data(CON, sr.data, request.remote_addr, request.user_agent.string)
    
    return json.dumps(sr.__dict__), 200

@app.route('/login', methods=['GET'])
def login_page():
    return open("webpage/login_page.html").read(), 200

@app.route('/profile', methods=['POST'])
def profile():
    """
    data = {
        session_id
        }
    """
    data = request.get_json()

    if not all( field in data for field in ('session_id',)):
        return json.dumps(SimpleResponse(ResponseState.FAILURE, "INVALID_DATA").__dict__), 400
    
    if not (sr := db_accounts.get_user_by_session_id(CON, data['session_id'], True)):
        return json.dumps(sr.__dict__), 400
    
    user = sr.data

    return json.dumps(sr.__dict__), 200

@app.route('/email_code', methods=['POST'])
def email_code():
    """
    data = {
        email
    }
    """

    data = request.get_json(force=True)

    if not all( field in data for field in ('email',)):
        return json.dumps(SimpleResponse(ResponseState.FAILURE, "INVALID_DATA").__dict__), 400
    
    if not (sr := db_accounts.generate_email_code(CON, data['email'])):
        return json.dumps(sr.__dict__), 400
    
    return json.dumps(sr.__dict__), 200



if __name__ == "__main__":
    CON = sqlite3.connect(DB_PATH, check_same_thread=False)
    cleanup()
    app.run(debug=True)


    