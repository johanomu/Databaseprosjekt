import sqlite3
import datetime
from datetime import date

database = sqlite3.connect("lastTestDb.db")
cursorObj = database.cursor()
epost = ""

def fetch(database):
    cursorObj.execute('SELECT name FROM sqlite_master WHERE type= "table"')
fetch(database)

def signin():
    print("---------------Login-----------------")
    name = input("Skriv inn navn: ")
    password = input("Skriv inn passord: ")
    print("---------------------------------")
    customer = cursorObj.execute("SELECT password FROM Customer WHERE name = '{}'".format(name))
    for i in customer.fetchall():
        if i[0] == password:
            print("Du er logget inn")
            return True
    print("Feil navn eller passord")

def signup():
    print("------------Lag ny bruker-----------------")
    name = input("Skriv inn navn: ")
    epost = input("Skriv inn epost: ")
    tlf = input("Skriv inn tlf: ")
    password = input("Skriv inn passord: ")
    print("----------------------------------")
    emailCheck = cursorObj.execute("SELECT email FROM Customer")
    for i in emailCheck.fetchall():
        if i[0] == epost:
            print("Epost eksisterer allerede")
            return False
    cursorObj.execute("INSERT INTO Customer (name, phoneNr, email, password) VALUES ('{}', '{}', '{}', '{}')".format(name, tlf, epost, password))
    database.commit()
    print("Bruker har blit oprettet")

def getRoutesStartEnd():
    start = input("Fra stasjon: ")
    end = input("Til stasjon: ")
    dateAndTime = input("Dato og tid (YYYY-MM-DD HH:MM): ")
    dateTime = datetime.datetime.strptime(dateAndTime, '%Y-%m-%d %H:%M:%S')

    sqlQuery = """
        SELECT DISTINCT TrainRoute.routeID, TrainRoute.trackID, TrainRoute.dateAndTime, TrainRoute.weekday
        FROM Visits
        JOIN Tracks ON Visits.trackID = Tracks.trackID
        JOIN TrainRoute ON Tracks.trackID = TrainRoute.trackID
        WHERE (Visits.name = ? OR Visits.name = ?) AND TrainRoute.dateAndTime BETWEEN ? AND ?
        ORDER BY TrainRoute.dateAndTime ASC
        """
    cursorObj.execute(sqlQuery, (start, end, dateTime.strftime('%Y-%m-%d %H:%M:%S'), (dateTime + datetime.timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')))
    routes = cursorObj.fetchall()
    print("------------------------------------")
    if len(routes) == 0:
        print("Ingen ruter funnet.")
    else:
        print("Ruter funnet:")
        for route in routes:
            print(f"Rute ID: {route[0]}, Kjører på bane: {route[1]} Tidspunkt: {route[2]}, Dag: {route[3]}, Fra {start}, Til {end}")

def getFutureOrders():
    email = input("Skriv inn mailen din: ")
    dateAndTime = input("Fra dato: ")
    dateTime = datetime.datetime.strptime(dateAndTime, '%Y-%m-%d %H:%M')
    
    sqlQuery = """
    SELECT * FROM Customer 
    JOIN Orders ON Customer.customerID = Orders.customerID
    WHERE Customer.email = ? AND Orders.orderDateAndTime > ?
    """

    cursorObj.execute(sqlQuery, (email, dateTime,))
    orders = cursorObj.fetchall()
    
    for order in orders:
        cursorObj.execute("SELECT Ticket.startLoc, Ticket.endLoc, Ticket.seatNr FROM Ticket WHERE Ticket.orderID = ?", (order[0],))
        tickets = cursorObj.fetchall()
        print(f"Ordre ID: {order[0]}")
        print(f"Dato: {order[1]}")
        print(f"Total pris: {order[2]}")
        print("Biletter:")
        for ticket in tickets:
            print(f"Fra: {ticket[0]}, Til: {ticket[1]}, Sete nummer: {ticket[2]}")
        print("------------------------------------------")

def main():
    print("Velkommen til togbaneDB")
    logIn = input("Logg inn eller registrer: ")
    if logIn == "logg inn":
        signin()
    elif logIn == "registrer":
        signup()

    action = input("Hvilken brukerhistorie vil du gjennomføre a-h: ")
    print("Gjennomfører brukerhistorie " + action)
    print("----------------------------------------")
    if (action == "d"):
        getRoutesStartEnd()
    elif (action == "h"):
        getFutureOrders()
main()
