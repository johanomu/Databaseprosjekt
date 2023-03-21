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
    emailCheck = cursorObj.execute("SELECT email FROM Customer")
    for i in emailCheck.fetchall():
        if i[0] == name:
            print("Epost eksisterer allerede")
            return False
    cursorObj.execute("INSERT INTO Customer (name, phoneNr, email, password) VALUES ('{}', '{}', '{}', '{}')".format(name, tlf, epost, password))
    database.commit()

def getRoutesStartEnd(start, end, dateTime):
    sqlQuery = """
        SELECT stationsOnRoute.routeID, stationsOnRoute.name, stationsOnRoute.arrivalTime, stationsOnRoute.departureTime
        FROM stationsOnRoute
        JOIN TrainRoute ON stationsOnRoute.routeID = TrainRoute.routeID
        WHERE stationsOnRoute.name = %s AND TrainRoute.DateAndTime BETWEEN %s AND %s
        """
    cursorObj.execute(sqlQuery(start, dateTime.strftime("%m/%d/%Y, %H:%M:%S"), (dateTime.date() + datetime.timedelta(days=1)).strftime("%m/%d/%Y")))
    routesFromStart = cursorObj.fetchall()
    cursorObj.execute(sqlQuery(end, dateTime.strftime("%m/%d/%Y, %H:%M:%S"), (dateTime.date() + datetime.timedelta(days=1)).strftime("%m/%d/%Y")))
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
    out.sort(key=lambda x: x["dateAndTime"])
    return out


def main():
    print("Velkommen til togbaneDB")
    logIn = input("Log in eller registrer")
    if logIn == "l":
        signin()
    elif logIn == "r":
        signup()

    action = input("Hvilken brukerhistorie vil du gjennomføre a-h")
    if (action == "d"):
        print("Gjennomfører brukerhistorie " + action)
        start = input("Fra stasjon: ")
        end = input("Til stasjon: ")
        dateAndTime = input("Dato og tid (YYYY-MM-DD HH:MM:SS): ")
        dateTime = datetime.datetime.strptime(dateAndTime, "%Y-%m-%d %H:%M:%S")
        routes = getRoutesStartEnd(start, end, dateTime)
        for route in routes:
            print(route)
main()
