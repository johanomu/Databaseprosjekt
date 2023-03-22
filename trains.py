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
    dateTime = input("Dato og tid (YYYY-MM-DD HH:MM:SS): ")
    dateTime = datetime.datetime.strptime(dateTime, "%Y-%m-%d %H:%M:%S")

    sqlQuery = """
        SELECT Visits.trackID, Visits.name, Visits.arrivalTime, Visits.departureTime
        FROM Visits
        JOIN Tracks ON Visits.trackID = Tracks.trackID
        JOIN TrainRoute ON TrainRoute.routeID = Tracks.routeID
        WHERE Visits.name = ? AND TrainRoute.dateAndTime BETWEEN ? AND ?
        """
    cursorObj.execute(sqlQuery, (start, dateTime.time(), (dateTime + datetime.timedelta(days=1))))
    routesFromStart = cursorObj.fetchall()
    cursorObj.execute(sqlQuery, (end, dateTime.time(), (dateTime + datetime.timedelta(days=1))))
    routesFromEnd = cursorObj.fetchall()

    validRoutes = []
    for startRoute in routesFromStart:
        for endRoute in routesFromEnd:
            if startRoute[0] == endRoute[0]:
                if startRoute[2] < dateTime.time() and endRoute[3] > dateTime.time():
                    validRoutes.append(startRoute[0])
    out = []
    for route in validRoutes:
        cursorObj.execute("SELECT * FROM TrainRoute WHERE TrainRoute.routeID = %s"(route))
        out.append(cursorObj.fetchall())
    out.sort(key=lambda x: x[0][3])
    return out

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
        routes = getRoutesStartEnd()
        for route in routes:
            print(route)
    elif (action == "h"):
        getFutureOrders()
main()
