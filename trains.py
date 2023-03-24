import sqlite3
import datetime
from datetime import datetime, timedelta


database = sqlite3.connect("Hotfix.db")
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


def get_available_seats(start_station, end_station, departure_time):
    query = """
    SELECT tr.routeID, c.cartsID, c.type, ch.numberOfSeats - COUNT(rs.ticketID) AS available_seats, v_start.departureTime AS start_departure_time, v_end.arrivalTime
    FROM TrainRoute tr
    JOIN CartsOnRoute cor ON tr.routeID = cor.routeID
    JOIN Carts c ON cor.cartsID = c.cartsID
    JOIN Chair ch ON c.cartsID = ch.chairCartsID
    LEFT JOIN ReservedSeat rs ON c.cartsID = rs.cartsID
    JOIN Visits v_start ON tr.trackID = v_start.trackID AND v_start.name = ?
    JOIN Visits v_end ON tr.trackID = v_end.trackID AND v_end.name = ?
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
    UNION ALL
    SELECT tr.routeID, c.cartsID, c.type, sl.numberOfCompartments - COUNT(rs.ticketID) AS available_seats, v_start.departureTime AS start_departure_time, v_end.arrivalTime
    FROM TrainRoute tr
    JOIN CartsOnRoute cor ON tr.routeID = cor.routeID
    JOIN Carts c ON cor.cartsID = c.cartsID
    JOIN Sleeping sl ON c.cartsID = sl.sleepCartsID
    LEFT JOIN ReservedSeat rs ON c.cartsID = rs.cartsID
    JOIN Visits v_start ON tr.trackID = v_start.trackID AND v_start.name = ?
    JOIN Visits v_end ON tr.trackID = v_end.trackID AND v_end.name = ?
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
    """

    cursorObj.execute(query, (start_station, end_station, start_station, end_station, departure_time, departure_time, start_station, end_station, start_station, end_station, departure_time, departure_time))
    results = cursorObj.fetchall()
    return results

def get_section_ids(start_station, end_station):
    

    query = """
    WITH RECURSIVE route_sections (section_id, start_station, end_station) AS (
        SELECT sectionID, startStation, endStation
        FROM TrackSection
        WHERE startStation = ?
        UNION ALL
        SELECT ts.sectionID, ts.startStation, ts.endStation
        FROM TrackSection ts
        JOIN route_sections rs ON ts.startStation = rs.end_station
    )
    SELECT section_id
    FROM route_sections
    WHERE end_station = ?
    """

    cursorObj.execute(query, (start_station, end_station))
    section_ids = [row[0] for row in cursorObj.fetchall()]

    return section_ids

def purchase_ticket(route_id, cart_id, seat_nr, user_id, section_ids):
    
    # Insert a new ticket into the Ticket table
    insert_ticket_query = "INSERT INTO Tickets (customerID) VALUES (?)"
    cursorObj.execute(insert_ticket_query, (user_id,))

    # Get the ID of the inserted ticket
    ticket_id = cursorObj.lastrowid

    # Insert a new reserved seat into the ReservedSeat table for each section
    for section_id in section_ids:
        insert_reserved_seat_query = "INSERT INTO ReservedSeat (ticketID, cartsID, sectionID) VALUES (?, ?, ?)"
        cursorObj.execute(insert_reserved_seat_query, (ticket_id, cart_id, section_id))

    # Commit the changes
    database.commit()

    
    print(f"Successfully purchased ticket with Ticket ID: {ticket_id}, Route ID: {route_id}, Cart ID: {cart_id}, Seat Number: {seat_nr}, Section IDs: {section_ids}")

def create_order(customerID, numberOfTickets, orderDateAndTime):
    query = """
    INSERT INTO Orders (customerID, numberOfTickets, orderDateAndTime)
    VALUES (?, ?, ?)
    """
    cursorObj.execute(query, (customerID, numberOfTickets, orderDateAndTime))
    orderID = cursorObj.lastrowid

    database.commit()
   

    return orderID


def create_ticket(orderID, startLoc, endLoc, seatNr, routeID, section_ids, cart_id):
    
    query = """
    INSERT INTO Ticket (orderID, startLoc, endLoc, seatNr, routeID)
    VALUES (?, ?, ?, ?, ?)
    """
    cursorObj.execute(query, (orderID, startLoc, endLoc, seatNr, routeID))
    ticketID = cursorObj.lastrowid

     # Insert a new reserved seat into the ReservedSeat table for each section
    for section_id in section_ids:
        insert_reserved_seat_query = "INSERT INTO ReservedSeat (ticketID, cartsID, sectionID) VALUES (?, ?, ?)"
        cursorObj.execute(insert_reserved_seat_query, (ticketID, cart_id, section_id))
    

    database.commit()
    

    return ticketID

def create_ticket(customerID, startLoc, endLoc, seats, routeID, cartsID, sectionID):
    # Insert an order in the Orders table
    order_date_time = datetime.now()
    cursorObj.execute("INSERT INTO Orders (numberOfTickets, orderDateAndTime, customerID) VALUES (?, ?, ?)",
                (len(seats), order_date_time, customerID))
    database.commit()

    # Get the orderID of the newly inserted order
    cursorObj.execute("SELECT last_insert_rowid()")
    orderID = cursorObj.fetchone()[0]

    # Insert tickets in the Ticket table
    ticketIDs = []
    for seat in seats:
        cursorObj.execute(
            "INSERT INTO Ticket (startLoc, endLoc, seatNr, orderID, routeID) VALUES (?, ?, ?, ?, ?)",
            (startLoc, endLoc, seat, orderID, routeID))
        database.commit()

        # Get the ticketID of the newly inserted ticket
        cursorObj.execute("SELECT last_insert_rowid()")
        ticketID = cur.fetchone()[0]
        ticketIDs.append(ticketID)

        # Insert into ReservedSeat table
        cursorObj.execute(
            "INSERT INTO ReservedSeat (ticketID, cartsID, sectionID) VALUES (?, ?, ?)",
            (ticketID, cartsID, sectionID))
        database.commit()

    return ticketIDs

# Get input from the user
startLoc = input("Enter the start location: ")
endLoc = input("Enter the end location: ")
routeID = int(input("Enter the route ID: "))
cartsID = int(input("Enter the carts ID: "))
sectionID = int(input("Enter the section ID: "))
customerID = int(input("Enter your customer ID: "))

# Get the number of seats to book and the seat numbers
num_seats = int(input("Enter the number of seats you want to book: "))
seats = []
for i in range(num_seats):
    seatNr = int(input(f"Enter seat number for seat {i + 1}: "))
    seats.append(seatNr)

# Create the tickets
ticketIDs = create_ticket(customerID, startLoc, endLoc, seats, routeID, cartsID, sectionID)
print(f"Created tickets with ticketIDs: {ticketIDs}")



def brukerhistorie_G():
    start_station = input("Enter the start station: ")
    end_station = input("Enter the end station: ")
    date_time = input("Enter the date and time (YYYY-MM-DD HH:MI:SS): ")
    customer_id = customerID
    section_ids = get_section_ids(start_station, end_station)

    available_seats = get_available_seats(start_station, end_station, date_time)
    if not available_seats:
        print("No available seats found.")
    else:
        for route_id, cart_id, cart_type, available_seats, departure_time, arrival_time in available_seats:
            print(f"Route ID: {route_id}, Cart ID: {cart_id}, Cart Type: {cart_type}, Available Seats: {available_seats}, Departure Time: {departure_time}, Arrival Time: {arrival_time}")

        
        selected_route_id = int(input("Enter the Route ID you want to book: "))
        selected_carts_id = int(input("Enter the Cart ID you want to book: "))
        selected_seat_nr = int(input("Enter the seat number you want to book: "))

        
        create_ticket(selected_route_id, selected_carts_id, selected_seat_nr, customer_id, section_ids)
        



def main():
    print("Velkommen til togbaneDB")
    print("Trykk 'l' for login, eller 'r' for registrer: ")
    logIn = input("Login eller registrer: : r")
    if logIn == "l":
        #global customerID = 
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
