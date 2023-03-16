import sqlite3
import datetime

database = sqlite3.connect("trains.db")
cursorObj = database.cursor()
epost = ""

def fetch(database):
    cursorObj.execute('SELECT name FROM sqlite_master WHERE type= "table"')
    

