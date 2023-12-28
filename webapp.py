from flask import Flask, request
import json
import sqlite3
import core.db_accounts as db_accounts
import core.db_operation as db_operation
import core.db_transaction as db_transaction
from core.db_transaction import DonationTransaction, ItemQuant, ExchangeTransaction
from core.my_response import ResponseState, SimpleResponse

DB_PATH = "main.sqlite"
CON:sqlite3.Connection

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
        return "Invalid data", 400
    
    sr = db_accounts.create_account(CON, data['email'], data['username'], data['password'], data['code'])

    if sr.state != ResponseState.SUCCESS:
        return sr.content, 400
    
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
        return "Invalid data", 400
    
    sr = db_accounts.login_by_username(CON, data['username'], data['password'], True)

    if sr.state != ResponseState.SUCCESS:
        return sr.content, 400

    db_accounts.log_session_data(CON, sr.data, request.remote_addr, request.user_agent.string)
    
    return sr.data, 200

@app.route('/profile', methods=['POST'])
def profile():
    """
    data = {
        session_id
        }
    """
    data = request.get_json()
    print(data)

    if not all( field in data for field in ('session_id',)):
        return "Invalid data", 400
    
    if not (sr := db_accounts.get_user_by_session_id(CON, data['session_id'], True)):
        return sr.content, 400
    
    print(sr.data)
    user = sr.data

    return "Welcome, " + user[1] + "!", 200

@app.route('/email_code', methods=['POST'])
def email_code():
    """
    data = {
        email
    }
    """

    data = request.get_json(force=True)
    print(data['email'])

    if not all( field in data for field in ('email',)):
        return "Invalid data", 400
    
    if not (sr := db_accounts.generate_email_code(CON, data['email'])):
        return sr.content, 400
    
    return "Verification Code Sent", 200



if __name__ == "__main__":
    DB_PATH = "main.sqlite"
    CON = sqlite3.connect(DB_PATH, check_same_thread=False)
    app.run(debug=True)