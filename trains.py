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
    customer = cursorObj.execute("SELECT password FROM Customer WHERE name = '{}'".format(name))
    for i in customer.fetchall():
        if i[0] == password:
            print("Du er logget inn")
            return True
    print("Feil navn eller passord")

customerID = signin()

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


def get_available_seats(start_station, end_station, date_time):
    query = '''
    SELECT tr.routeID, c.cartsID, c.type, ch.numberOfSeats - COUNT(rs.ticketID) AS available_seats
    FROM TrainRoute tr
    JOIN CartsOnRoute cor ON tr.routeID = cor.routeID
    JOIN Carts c ON cor.cartsID = c.cartsID
    JOIN Chair ch ON c.cartsID = ch.chairCartsID
    LEFT JOIN ReservedSeat rs ON c.cartsID = rs.cartsID
    WHERE tr.routeID IN (
        SELECT DISTINCT tr.routeID
        FROM TrainRoute tr
        JOIN Visits v_start ON tr.trackID = v_start.trackID
        JOIN Visits v_end ON tr.trackID = v_end.trackID
        WHERE v_start.name = ? AND v_end.name = ? AND v_start.departureTime < v_end.arrivalTime
    )
    AND tr.dateAndTime >= ? AND tr.dateAndTime < date(?, '+1 day')
    GROUP BY tr.routeID, c.cartsID
    HAVING available_seats > 0
    '''
    cursorObj.execute(query, (start_station, end_station, date_time, date_time))
    available_seats = cursorObj.fetchall()
    
    return available_seats

def purchase_ticket(customer_id, route_id, start_station, end_station, carts_id, seat_nr):
    query = '''
    INSERT INTO Ticket (customerID, routeID, startLoc, endLoc, seatNr)
    VALUES (?, ?, ?, ?, ?)
    '''
    cursorObj.execute(query, (customer_id, route_id, start_station, end_station, seat_nr))
    database.commit()
    ticket_id = cursorObj.lastrowid
    
    return ticket_id

def brukerhistorie_G():
    start_station = input("Enter the start station: ")
    end_station = input("Enter the end station: ")
    date_time = input("Enter the date and time (YYYY-MM-DD HH:MI:SS): ")
    customer_id = customerID

    available_seats = get_available_seats(start_station, end_station, date_time)
    if not available_seats:
        print("No available seats found.")
    else:
        for route_id, carts_id, cart_type, available_seat in available_seats:
            print(f"Route ID: {route_id}, Cart ID: {carts_id}, Cart Type: {cart_type}, Available Seats: {available_seat}")
        
        selected_route_id = int(input("Enter the Route ID you want to book: "))
        selected_carts_id = int(input("Enter the Cart ID you want to book: "))
        selected_seat_nr = int(input("Enter the seat number you want to book: "))
        
        ticket_id = purchase_ticket(customer_id, selected_route_id, start_station, end_station, selected_carts_id, selected_seat_nr)
        print(f"Ticket successfully booked. Your ticket ID is: {ticket_id}")



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

    elif (action == "d"):
        routes = getRoutesStartEnd()
        for route in routes:
            print(route)

    elif (action == "g"):
        brukerhistorie_G()
    elif (action == "h"):
        getFutureOrders()
main()
