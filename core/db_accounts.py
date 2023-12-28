import hashlib
from random import randint, choice
from datetime import datetime
from datetime import timedelta
import sqlite3
from dotenv import dotenv_values
import uuid
from .my_response import ResponseState, SimpleResponse

# Store data in hex_bytes or bytes
HEX_BYTES = False

ACCOUNT_TEMPLATE_PATH = "sql_scripts/create_accounts_tables.sql"
USER_TEMPLATE_PATH = "sql_scripts/create_user_tables.sql"

def create_database(filename:str) -> SimpleResponse:

    con = sqlite3.connect(filename)
    cur = con.cursor()

    try:
        with open(ACCOUNT_TEMPLATE_PATH,"r") as script:
            cur.executescript(script.read())

        with open(USER_TEMPLATE_PATH,"r") as script:
            cur.executescript(script.read())

        return SimpleResponse(ResponseState.SUCCESS)
    
    except Exception as ex:

        return SimpleResponse(ResponseState.FAILURE, None, ex)


def generate_random_alphanum(length:int) -> str:

    alphanum = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return ''.join(choice(alphanum) for i in range(length))



def generate_email_code(con:sqlite3.Connection, email:str) -> SimpleResponse:
    code = randint(100000, 999999)
    data = (email, code, datetime.now())
    con.cursor().execute("INSERT OR REPLACE INTO EmailVerify VALUES(?, ?, ?)", data)
    con.commit()
    return SimpleResponse(ResponseState.SUCCESS, None, code)

def validate_email(con:sqlite3.Connection, email:str, code:str) -> SimpleResponse:
    cur = con.cursor()
    code_query = cur.execute("SELECT * FROM EmailVerify WHERE email = ? AND code = ?",(email, code))

    result = code_query.fetchone()

    if result is None:
        print("Error: Email is not verified")
        return SimpleResponse(ResponseState.FAILURE, "EMAIL_NOT_VERIFIED")
    
    cur.execute("DELETE FROM EmailVerify WHERE email = ?", (email,))
    con.commit()

    expiry_duration = int(dotenv_values(".env")["EMAIL_VERIFY_EXPIRY_DURATION"])
    creation_datetime = datetime.fromisoformat(result[2])
    seconds_from_expiry = (datetime.now() - creation_datetime).total_seconds()

    if seconds_from_expiry > expiry_duration:
        print("Error: Code expired")
        return SimpleResponse(ResponseState.FAILURE, "CODE_EXPIRED")
    
    return SimpleResponse(ResponseState.SUCCESS)

def validate_session(con:sqlite3.Connection, session_id:str) -> SimpleResponse:

    cur = con.cursor()
    session_query_result = cur.execute("SELECT * FROM Sessions WHERE session_id = ?", (session_id,)).fetchone()

    if session_query_result is None:
        print("Error: Session ID is invalid")
        return SimpleResponse(ResponseState.FAILURE, "SESSION_ID_INVALID")

    expiry_duration = int(dotenv_values(".env")["SESSION_EXPIRY_DURATION"])
    creation_datetime = datetime.fromisoformat(session_query_result[2])
    seconds_from_expiry = (datetime.now() - creation_datetime).total_seconds()

    if seconds_from_expiry > expiry_duration:
        print("Error: Session expired")
        return SimpleResponse(ResponseState.FAILURE, "SESSION_EXPIRED")
    
    return SimpleResponse(ResponseState.SUCCESS)

def get_user_by_session_id(con:sqlite3.Connection, session_id:str, hex:bool = False) -> SimpleResponse:
    print(session_id)
    cur = con.cursor()

    if hex:
        session_id = bytes.fromhex(session_id)

    session_query_result = cur.execute("SELECT * FROM Sessions WHERE session_id = ?", (session_id,)).fetchone()

    if session_query_result is None:
        print("Error: Session ID is invalid")
        return SimpleResponse(ResponseState.FAILURE, "SESSION_ID_INVALID")

    expiry_duration = int(dotenv_values(".env")["SESSION_EXPIRY_DURATION"])
    creation_datetime = datetime.fromisoformat(session_query_result[2])
    seconds_from_expiry = (datetime.now() - creation_datetime).total_seconds()

    if seconds_from_expiry > expiry_duration:
        print("Error: Session expired")
        return SimpleResponse(ResponseState.FAILURE, "SESSION_EXPIRED")
    
    user_id = session_query_result[1]
    
    user_query_result = cur.execute("SELECT * FROM Users WHERE user_id = ?", (user_id,)).fetchone()

    if user_query_result is None:
        return SimpleResponse(ResponseState.FAILURE, "USER_DOES_NOT_EXIST")
    
    return SimpleResponse(ResponseState.SUCCESS, None, user_query_result)


def get_hashed_info(secret:str) -> str:
    t2 = hashlib.sha512()
    password_hashkey = dotenv_values(".env")["SECRET_KEY"]
    t2.update(bytes(password_hashkey, 'utf-8'))
    t2.update(bytes(secret , 'utf-8'))

    if HEX_BYTES:
        return t2.hexdigest()
    
    return t2.digest()


def create_account(con:sqlite3.Connection, email:str, username:str, password:str, code:str) -> SimpleResponse:

    cur = con.cursor()
    
    if not (sr := validate_email(con, email, code)):
        return sr
    
    username_query = cur.execute("SELECT * FROM Users WHERE username = ?",(username,))
    result = username_query.fetchone()

    if result is not None:
        print("Error: Username taken")
        return SimpleResponse(ResponseState.FAILURE, "USERNAME_TAKEN")
    
    email_query = cur.execute("SELECT * FROM Users WHERE email = ?",(email,))
    result = email_query.fetchone()

    if result is not None:
        print("Error: Email taken")
        return SimpleResponse(ResponseState.FAILURE, "EMAIL_TAKEN")

    hashed_password = get_hashed_info(password)

    cur.execute("INSERT OR IGNORE INTO Users VALUES(NULL, ?, ?, ?)", (username, hashed_password, email))
    con.commit()

    return SimpleResponse(ResponseState.SUCCESS)

def delete_expired_sessions(con:sqlite3.Connection):

    SESSION_CLEANUP_DURATION = int(dotenv_values(".env")["SESSION_CLEANUP_DURATION"])
    cur = con.cursor()
    cur.execute("DELETE FROM Sessions WHERE start_time <= ?", (datetime.now() - timedelta(seconds=SESSION_CLEANUP_DURATION),))
    con.commit()

def delete_expired_email_verify(con:sqlite3.Connection):

    EMAIL_VERIFY_CLEANUP_DURATION = int(dotenv_values(".env")["EMAIL_VERIFY_CLEANUP_DURATION"])
    cur = con.cursor()
    cur.execute("DELETE FROM EmailVerify WHERE creation_time <= ?", (datetime.now() - timedelta(seconds=EMAIL_VERIFY_CLEANUP_DURATION),))
    con.commit()

def login_by_username(con:sqlite3.Connection, username:str, password:str, hex:bool = False):
    
    cur = con.cursor()

    hashed_password = get_hashed_info(password)
    user_query_result = cur.execute("SELECT * FROM Users WHERE username = ? AND password = ?", (username, hashed_password)).fetchone()

    if user_query_result is None:
        print("Error: Username or Password is incorrect")
        return SimpleResponse(ResponseState.FAILURE, "INVALID_CREDENTIALS")
    
    
    max_sessions = int(dotenv_values(".env")["MAX_SESSIONS"])
    session_query_results = cur.execute("SELECT * FROM Sessions WHERE user_id = ? ORDER BY start_time ASC", (user_query_result[0],)).fetchmany(max_sessions)

    if session_query_results is None:
        print("Error: Cannot fetch")
        return SimpleResponse(ResponseState.FAILURE, "NO_CONCURRENT_SESSIONS")
    
    
    # Check if there are too many ongoing sessions
    if len(session_query_results) >= max_sessions:

        print("Warning: Too many ongoing sessions, deleting the oldest as of now")
        oldest_session = session_query_results[0]
        cur.execute("DELETE FROM Sessions WHERE session_id = ?", (oldest_session[0],))
        con.commit()

    # Create session_id with user's email address
    if HEX_BYTES:
        session_id = uuid.uuid4().bytes.hex()
    else:
        session_id = uuid.uuid4().bytes
    
    cur.execute("INSERT INTO Sessions VALUES(?, ?, ?)", (session_id, int(user_query_result[0]), datetime.now()))
    con.commit()

    if hex:
        return SimpleResponse(ResponseState.SUCCESS, None, session_id.hex())
    else:
        return SimpleResponse(ResponseState.SUCCESS, None, session_id)

def logout_session(con:sqlite3.Connection, session_id:str):
    cur = con.cursor()
    cur.execute("DELETE FROM Sessions WHERE session_id = ?", (session_id,))
    con.commit()
    return SimpleResponse(ResponseState.SUCCESS)

def logout_all_sessions_by_userid(con:sqlite3.Connection, user_id:str):
    cur = con.cursor()
    cur.execute("DELETE FROM Sessions WHERE user_id = ?", (user_id,))
    con.commit()
    return SimpleResponse(ResponseState.SUCCESS)

def logout_all_sessions(con:sqlite3.Connection, session_id:str):
    cur = con.cursor()
    user_id = get_user_by_session_id(con, session_id)[0]
    logout_all_sessions_by_userid(con, user_id)
    return SimpleResponse(ResponseState.SUCCESS)

def reset_password(con:sqlite3.Connection, email:str, code:str):
    
    cur = con.cursor()

    if not (sr := validate_email(con, email, code)):
        return sr
    
    email_query_result = cur.execute("SELECT * FROM Users WHERE email = ?", (email,)).fetchone()

    if email_query_result is None:
        print("Error: Email has not been registered")
        return SimpleResponse(ResponseState.FAILURE, "EMAIL_NOT_FOUND")
    
    new_password = generate_random_alphanum(6)
    hashed_new_password = get_hashed_info(new_password)
    
    cur.execute("UPDATE OR IGNORE Users SET password = ? WHERE email = ?", (hashed_new_password, email))
    con.commit()

    return SimpleResponse(ResponseState.SUCCESS, None, new_password)

def change_password(con:sqlite3.Connection, session_id:str, old_password:str, new_password:str):

    cur = con.cursor()
    
    if not (get_user := get_user_by_session_id(con, session_id)):
        return get_user
    
    user = get_user.data
    user_id = user[0]
    
    hashed_password = get_hashed_info(old_password)
    user_query_result = cur.execute("SELECT * FROM Users WHERE user_id = ? AND password = ?", (user_id, hashed_password)).fetchone()

    if user_query_result is None:
        print("Error: Old Password does not match")
        return SimpleResponse(ResponseState.FAILURE, "WRONG_OLD_PASSWORD")
    
    hashed_new_password = get_hashed_info(new_password)

    cur.execute("UPDATE OR IGNORE Users SET password = ? WHERE user_id = ?", (hashed_new_password, user_id))
    con.commit()

    return SimpleResponse(ResponseState.SUCCESS)

def renew_session(con:sqlite3.Connection, session_id:str):

    cur = con.cursor()

    if not (sr := validate_session(con, session_id)):
        return sr

    cur.execute("UPDATE OR IGNORE Sessions SET start_time = ? WHERE session_id = ?", (datetime.now(), session_id))
    con.commit()

    return SimpleResponse(ResponseState.SUCCESS)

def log_session_data(con:sqlite3.Connection, session_id:str, ip_addr:str, user_agent:str):
    cur = con.cursor()
    cur.execute("INSERT OR REPLACE INTO SessionData VALUES(?, ?, ?)", (session_id, ip_addr, user_agent))
    con.commit()
    

    
        





