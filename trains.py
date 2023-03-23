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
    print("Login")
    name = input("Skriv inn navn: ")
    password = input("Skriv inn passord: ")
    customer = cursorObj.execute("SELECT passord FROM Customer WHERE name = '{}'".format(name))
    for i in customer.fetchall():
        if i[0] == password:
            print("Du er logget inn")
            return True
    print("Feil navn eller passord")

def signup():
    print("Lag bruker")
    name = input("Skriv inn navn: ")
    epost = input("Skriv inn epost: ")
    tlf = input("Skriv inn tlf: ")
    password = input("Skriv inn passord: ")
    emailCheck = cursorObj.execute("SELECT email FROM Customer")
    for i in emailCheck.fetchall():
        if i[0] == epost:
            print("Epost eksisterer allerede")
            return False
    cursorObj.execute("INSERT INTO Customer (name, phoneNr, email, password) VALUES ('{}', '{}', '{}', '{}')".format(name, tlf, epost, password))
    database.commit()
    print("Bruker oprettet")

def getRoutesStartEnd():
    start = input("Fra stasjon: ")
    end = input("Til stasjon: ")
    dateAndTime = input("Dato og tid (YYYY-MM-DD HH:MM): ")
    dateTime = datetime.datetime.strptime(dateAndTime, '%Y-%m-%d %H:%M')

    sqlQuery = """
        SELECT DISTINCT TrainRoute.routeID, TrainRoute.trackID, TrainRoute.dateAndTime, TrainRoute.weekday
        FROM Visits
        JOIN Tracks ON Visits.trackID = Tracks.trackID
        JOIN TrainRoute ON Tracks.trackID = TrainRoute.trackID
        WHERE (Visits.name = ? OR Visits.name = ?) AND TrainRoute.dateAndTime BETWEEN ? AND ?
        ORDER BY TrainRoute.dateAndTime ASC
        """
    cursorObj.execute(sqlQuery, (start, end, dateTime.strftime('%Y-%m-%d %H:%M'), (dateTime + datetime.timedelta(days=2)).strftime('%Y-%m-%d %H:%M')))
    routes = cursorObj.fetchall()

    if len(routes) == 0:
        print("Ingen ruter funnet.")
    else:
        print("Ruter funnet:")
        for route in routes:
            print(f"Rute ID: {route[0]}, Kjører på bane: {route[1]} Tidspunkt: {route[2]}, Dag: {route[3]}, Fra {start}, Til {end}")

def getFutureOrders():
    epost = input("Skriv inn mailen din: ")
    query = """SELECT Orders.orderID, Orders.numberOfTickets, Orders.orderDateAndTime, TrainRoute.dateAndTime, TrainRoute.startOfRoute, TrainRoute.endOfRoute, Operator.name, Carts.type, ReservedSeat.sectionID, ReservedSeat.ticketID
            FROM Orders
            INNER JOIN Ticket ON Orders.orderID = Ticket.orderID
            INNER JOIN TrainRoute ON Ticket.routeID = TrainRoute.routeID
            INNER JOIN Operator ON TrainRoute.routeID = Operator.routeID
            INNER JOIN Carts ON Operator.operatorID = Carts.operatorID
            INNER JOIN ReservedSeat ON Ticket.ticketID = ReservedSeat.ticketID
            INNER JOIN SectionStation ON ReservedSeat.sectionID = SectionStation.sectionID
            INNER JOIN Station ON SectionStation.name = Station.name
            WHERE Orders.customerID = (SELECT customerID FROM Customer WHERE email = ?)
            AND TrainRoute.dateAndTime > ?
            ORDER BY TrainRoute.dateAndTime ASC"""

    today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results = cursorObj.execute(query, (epost, today)).fetchall()

    for row in results:
        print("Order ID:", row[0])
        print("Number of Tickets:", row[1])
        print("Order Date and Time:", row[2])
        print("Trip Date and Time:", row[3])
        print("Start Station:", row[4])
        print("End Station:", row[5])
        print("Operator Name:", row[6])
        print("Cart Type:", row[7])
        print("Section ID:", row[8])
        print("Ticket ID:", row[9])
        print("--------------------------")


def main():
    print("Velkommen til togbaneDB")
    logIn = input("Log in eller registrer: ")
    if logIn == "l":
        signin()
    elif logIn == "r":
        signup()

    action = input("Hvilken brukerhistorie vil du gjennomføre a-h: ")
    print("Gjennomfører brukerhistorie " + action)
    print("----------------------------------------")
    if (action == "d"):
        getRoutesStartEnd()
    elif (action == "h"):
        getFutureOrders()
main()
