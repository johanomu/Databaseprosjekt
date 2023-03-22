import sqlite3
from datetime import datetime

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

def brukerhistorie_C(station_name, weekday):
    query = '''
    SELECT DISTINCT tr.routeID, tr.dateAndTime, tr.startOfRoute, tr.endOfRoute
    FROM TrainRoute tr
    JOIN StationsOnRoute sor ON tr.routeID = sor.routeID
    WHERE sor.name = ? AND sor.weekday = ?
    '''

    cursorObj.execute(query, (station_name, weekday))
    routes = cursorObj.fetchall()

    database.close()

    return routes


def get_available_seats(route_id, date_time):

    query = '''
    SELECT c.cartsID, c.type, ts.sectionID, 
    (CASE WHEN c.type = 'Chair' THEN ch.numberOfSeats ELSE s.numberOfBeds END) - COUNT(rs.ticketID) AS available_seats
    FROM Carts c
    JOIN Operator o ON c.operatorID = o.operatorID
    JOIN TrainRoute tr ON o.routeID = tr.routeID
    JOIN TrackSection ts ON tr.trackID = ts.trackID
    LEFT JOIN ReservedSeat rs ON c.cartsID = rs.cartsID AND ts.sectionID = rs.sectionID
    WHERE tr.routeID = ? AND tr.dateAndTime = ?
    GROUP BY c.cartsID, c.type, ts.sectionID
    HAVING available_seats > 0
    ORDER BY c.cartsID, ts.sectionID;
    '''

    cursorObj.execute(query, (route_id, date_time))
    seats = cursorObj.fetchall()

    database.close()

    return seats

def purchase_tickets(customer_id, order_id, tickets):

    cursorObj.execute("INSERT INTO Orders (orderID, numberOfTickets, orderDateAndTime, customerID) VALUES (?, ?, ?, ?)", (order_id, len(tickets), datetime.now(), customer_id))

    for ticket in tickets:
        cursorObj.execute("INSERT INTO Ticket (ticketID, startLoc, endLoc, seatNr, orderID, routeID) VALUES (?, ?, ?, ?, ?, ?)", ticket)
        cursorObj.execute("INSERT INTO ReservedSeat (ticketID, cartsID, sectionID) VALUES (?, ?, ?)", (ticket[0], ticket[4], ticket[5]))

    database.commit()
    database.close()

def get_route_ids(start_station, end_station):
    query = '''
    SELECT tr.routeID
    FROM TrainRoute tr
    JOIN StationsOnRoute sor_start ON tr.routeID = sor_start.routeID
    JOIN StationsOnRoute sor_end ON tr.routeID = sor_end.routeID
    WHERE sor_start.name = ? AND sor_end.name = ?
    '''

    cursorObj.execute(query, (start_station, end_station))
    route_ids = [row[0] for row in cursorObj.fetchall()]

    database.close()

    return route_ids

def brukerhistorie_G():
    start_station = input("Oppgi startstasjon: ")
    end_station = input("Oppgi endestasjon: ")
    date_time = input("Oppgi dato og tidspunkt for reisen (YYYY-MM-DD HH:MI:SS): ")

    route_ids = get_route_ids(start_station, end_station)

    if not route_ids:
        print("Finner ingen rute for denne start- og endestasjonen")
    else:
        for route_id in route_ids:
            available_seats = get_available_seats(route_id, date_time)

            if available_seats:
                print(f"Ledige seter for Route ID {route_id}:")
                print("CartsID | CartType | SectionID | AvailableSeats")
                for seat in available_seats:
                    print(f"{seat[0]} | {seat[1]} | {seat[2]} | {seat[3]}")
            else:
                print(f"Ingen ledige seter funnet for Route ID {route_id} og den oppgitte dato.")


    # User selects seats and provides customer_id and order_id
    customer_id = 1  # Replace with the actual customer_id
    order_id = 1  # Replace with the actual order_id
    selected_tickets = [
        (1, "StartLoc1", "EndLoc1", 1, 1, 1),  # Replace with actual ticket data (ticketID, startLoc, endLoc, seatNr, cartsID, sectionID)
        (2, "StartLoc2", "EndLoc2", 2, 2, 1)  # Replace with actual ticket data (ticketID, startLoc, endLoc, seatNr, cartsID, sectionID)
    ]

    purchase_tickets(customer_id, order_id, selected_tickets)
    print("Tickets purchased successfully.")




def main():
    print("Velkommen til togbaneDB")
    print("Trykk 'l' for login, eller 'r' for registrer: ")
    logIn = input("Login eller registrer: r")
    if logIn == "l":
        signin()
    elif logIn == "r":
        signup()

    action = input("Hvilken brukerhistorie vil du gjennomføre a-h")

    if (action == "c"):
        station_name = input("Oppgi navnet på stasjonen du vil reise fra: ")
        weekday = input("Oppgi ukedag du har lyst til å reise på, f.eks (Mandag, Tirsdag, osv.): ")

        train_routes = brukerhistorie_C(station_name, weekday)

        if train_routes:
            print("Train routes passing through the station on the given weekday:")
            print("RouteID | DateAndTime | StartOfRoute | EndOfRoute")
            for route in train_routes:
                print(f"{route[0]} | {route[1]} | {route[2]} | {route[3]}")
        else:
            print("No train routes found for the given station and weekday.")

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
