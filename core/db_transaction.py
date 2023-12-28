import sqlite3
from . import db_operation

class ItemQuant:
    def __init__(self, id:str, quantity:int) -> None:
        self.id, self.quantity = id, quantity

class DonationTransaction:
    def __init__(self, sender:str, recipient:str, sender_offer:list[ItemQuant]) -> None:
        self.sender, self.recipient, self.sender_offer = sender, recipient, sender_offer

class ExchangeTransaction:
    def __init__(self, sender:str, recipient:str, sender_offer:list[ItemQuant] , recipient_offer:list[ItemQuant]) -> None:
        self.sender, self.recipient, self.sender_offer, self.recipient_offer = sender, recipient, sender_offer,recipient_offer 

def do_donation_transaction(con:sqlite3.Connection, transaction: DonationTransaction, do_commit:bool = True):
    cur = con.cursor()

    if do_commit:
        cur.execute("BEGIN TRANSACTION")

    try:
        sender_body = db_operation.get_inventory(con, transaction.sender)["body"]
        recipient_body = db_operation.get_inventory(con, transaction.recipient)["body"]
    except:
        print("Error: sender or recipient has invalid inventory")
        return False
    
    try:
        for iq in transaction.sender_offer:
            exisiting_quantity = db_operation.get_quantity_of_inventory_item(con, transaction.sender, iq.id)
            
            if exisiting_quantity - iq.quantity < 0 or iq.quantity < 0:
                raise ValueError("Invalid Operation")
            db_operation.set_quantity_of_inventory_item(con, transaction.sender, iq.id, exisiting_quantity - iq.quantity, False)

        for iq in transaction.sender_offer:
            exisiting_quantity = db_operation.get_quantity_of_inventory_item(con, transaction.recipient, iq.id)
            if exisiting_quantity + iq.quantity < 0 or iq.quantity < 0:
                raise ValueError("Invalid Operation")
            db_operation.set_quantity_of_inventory_item(con, transaction.recipient, iq.id, exisiting_quantity + iq.quantity, False)
        if do_commit:
            con.commit()
        print("Transaction Proceeded")

    except:
        print("Error: Invalid Offer!")
        print("Error: Rollback")
        if do_commit:
            con.rollback()
        return False
    
    return True

def do_exchange_transaction(con:sqlite3.Connection, transaction:ExchangeTransaction):
    cur = con.cursor()
    cur.execute("BEGIN TRANSACTION")

    sender_trans = DonationTransaction(transaction.sender, transaction.recipient, transaction.sender_offer)
    recipient_trans = DonationTransaction(transaction.recipient, transaction.sender, transaction.recipient_offer)
    
    try:
        if not do_donation_transaction(con, sender_trans, False):
            raise ValueError()
        
        if not do_donation_transaction(con, recipient_trans, False):
            raise ValueError()
        
        con.commit()
    except:
        print("Error: Invalid Exchage!")
        print("Error: Rollback")
        con.rollback()

        

