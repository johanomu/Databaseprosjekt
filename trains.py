import math
import random
import sqlite3
import datetime

database = sqlite3.connect("trains.db")
cursorObj = database.cursor()
epost = ""

def fetch(database):
    cursorObj.execute('SELECT name FROM sqlite_master WHERE type= "table"')
fetch(database)

def signin():
    print("Login")
    name = input("Skriv inn navn")
    password = input("Skriv inn passord")
    customer = cursorObj.execute("SELECT passord FROM Customer WHERE name = '{}'".format(name))
    for i in customer.fetchall():
        if i[0] == password:
            print("Du er logget inn")
            return True
    print("Feil navn eller passord")

def signup():
    print("Lag bruker")
    name = input("Skriv inn navn")
    epost = input("Skriv inn epost")
    tlf = input("Skriv inn tlf")
    password = input("Skriv inn passord")
    emailCheck = cursorObj.execute("SELECT epost FROM Customer")
    for i in emailCheck.fetchall():
        if i[0] == name:
            print("Epost eksisterer allerede")
            return False
    cursorObj.execute("INSERT INTO Customer (name, phoneNr, email, password) VALUES ('{}', '{}', '{}', '{}')".format(name, tlf, epost, password))
    database.commit()

def main():
    print("Velkommen til togbaneDB")
    logIn = input("Log in eller registrer")
    if logIn == "l":
        signin()
    elif logIn == "r":
        signup()

main()
