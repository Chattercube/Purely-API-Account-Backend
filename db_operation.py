import hashlib
from random import randint, choice
from datetime import datetime
from datetime import timedelta
import sqlite3
from os.path import exists
from dotenv import dotenv_values
import uuid
import db_accounts

import json

DATA_TEMPLATE = json.load(open("userdata_data_template.json","r"))
INVENTORY_TEMPLATE = json.load(open("userdata_inventory_template.json","r"))





def initialize_userdata(con:sqlite3.Connection):
    cur = con.cursor()

    user_id_result = cur.execute("SELECT user_id FROM Users").fetchall()
    data_zip = [(i[0], json.dumps(DATA_TEMPLATE), json.dumps(INVENTORY_TEMPLATE)) for i in user_id_result]

    cur.executemany("INSERT OR IGNORE INTO UserData VALUES(?, ?, ?)", data_zip)
    con.commit()

def get_inventory(con:sqlite3.Connection, user_id:str):
    cur = con.cursor()
    inventory_query_object = cur.execute("SELECT inventory FROM UserData WHERE user_id = ?", (user_id,)).fetchone()

    if inventory_query_object is None:
        return None

    return json.loads(inventory_query_object[0])

def get_quantity_of_inventory_item(con:sqlite3.Connection, user_id:str, id:str):

    body = get_inventory(con, user_id)['body']

    if id not in body:
        return 0
    else:
        return int(body[id]['quantity'])
    
def set_inventory(con:sqlite3.Connection, user_id:str, body:json, do_commit:bool = True):

    cur = con.cursor()
    cur.execute("UPDATE UserData SET inventory = json_set(inventory, '$.body', json(?)) WHERE user_id = ?" , (json.dumps(body), user_id))
    if do_commit:
        con.commit()

def set_quantity_of_inventory_item(con:sqlite3.Connection, user_id:str, id:str, quantity:int , do_commit:bool = True):

    body = get_inventory(con, user_id)['body']

    if quantity <= 0:
        if id in body:
            del body[id]
    else:
        body[id] = { "quantity": quantity }

    set_inventory(con, user_id, body, do_commit)

    



def user_operation(con:sqlite3.Connection, session_id:str, operation_code:str, data:json):
    cur = con.cursor()
    match(operation_code):

        case "change_status":
            if 'content' not in data:
                print("Error: Invalid data")
                return
            
            user = db_accounts.get_user_by_session_id(con, session_id)
            user_id = user[0]
            cur.execute("UPDATE OR IGNORE UserData SET data = json_set(data, '$.status', ?) WHERE user_id = ?", (data['content'], user[0]))
            con.commit()

        case "change_blurb":
            if 'content' not in data:
                print("Error: Invalid data")
                return
            
            user = db_accounts.get_user_by_session_id(con, session_id)
            user_id = user[0]
            cur.execute("UPDATE OR IGNORE UserData SET data = json_set(data, '$.blurb', ?) WHERE user_id = ?", (data['content'], user[0]))
            con.commit()

        case "login":
            if 'content' not in data:
                print("Error: Invalid data")
                return
            
            user = db_accounts.get_user_by_session_id(con, session_id)
            user_id = user[0]
            cur.execute("UPDATE OR IGNORE UserData SET data = json_set(data, '$.blurb', ?) WHERE user_id = ?", (data['content'], user[0]))
            con.commit()








