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

def brukerhistorie_C(station, weekday):
    query = '''
    SELECT tr.routeID, tr.dateAndTime, tr.weekday, v_start.name AS start_station, v_end.name AS end_station
    FROM TrainRoute tr
    JOIN Visits v ON tr.trackID = v.trackID
    JOIN Visits v_start ON tr.trackID = v_start.trackID AND v_start.departureTime IS NULL
    JOIN Visits v_end ON tr.trackID = v_end.trackID AND v_end.arrivalTime IS NULL
    WHERE v.name = ? AND tr.weekday = ?
    '''

    cursorObj.execute(query, (station, weekday))
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
    logIn = input("Login eller registrer: : r")
    if logIn == "l":
        signin()
    elif logIn == "r":
        signup()

    action = input("Hvilken brukerhistorie vil du gjennomføre a-h: ")
    print("Gjennomfører brukerhistorie " + action)
    print("----------------------------------------")

    if (action == "c"):
        station = input("Oppgi navnet på stasjonen du vil reise fra: ")
        weekday1 = input("Oppgi ukedag du har lyst til å reise på, f.eks (Mandag, Tirsdag, osv.): ")
        weekday = weekday1.lower()

        train_routes = brukerhistorie_C(station, weekday)

        if train_routes:
            print(f"Togruter for {station} på {weekday}:")
            for route in train_routes:
                print(f"Rutenummer: {route[0]}, Dato og tidspunkt: {route[1]}, Startstasjon: {route[3]}, Endestasjon: {route[4]}")
        else:
            print("No train routes found for the given station and weekday.")

    if (action == "d"):
        routes = getRoutesStartEnd()
        for route in routes:
            print(route)
    elif (action == "h"):
        getFutureOrders()
main()
