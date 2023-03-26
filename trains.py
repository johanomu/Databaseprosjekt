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
    dateAndTime = input("Dato og tid (YYYY-MM-DD HH:MM:SS): ")
    dateTime = datetime.datetime.strptime(dateAndTime, '%Y-%m-%d %H:%M:%S')

    sqlQuery = """
        SELECT DISTINCT TrainRoute.routeID, TrainRoute.trackID, TrainRoute.dateAndTime, TrainRoute.weekday
        FROM Visits AS v1
        JOIN Tracks AS t1 ON v1.trackID = t1.trackID
        JOIN Visits AS v2 ON v1.trackID = v2.trackID
        JOIN Tracks AS t2 ON v2.trackID = t2.trackID
        JOIN TrainRoute ON t1.trackID = TrainRoute.trackID
        WHERE v1.name = ? AND v2.name = ? AND TrainRoute.dateAndTime BETWEEN ? AND ?
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
    dateTime = datetime.datetime.strptime(dateAndTime, '%Y-%m-%d %H:%M:%S')
    
    sqlQuery = """
    SELECT * FROM Customer 
    JOIN Orders ON Customer.customerID = Orders.customerID
    WHERE Customer.email = ? AND Orders.orderDateAndTime > ?
    """

    cursorObj.execute(sqlQuery, (email, dateTime,))
    orders = cursorObj.fetchall()

    print("-----------Dine fremtidige ordre-------------")
    for order in orders:
        cursorObj.execute("SELECT Ticket.startLoc, Ticket.endLoc, Ticket.seatNr FROM Ticket WHERE Ticket.orderID = ?", (order[5],))
        tickets = cursorObj.fetchall()
        print(f"Ordre ID: {order[5]}")
        print(f"Dato: {order[7]}")
        print(f"Antall biletter: {order[6]}")
        print("Biletter:")
        for ticket in tickets:
            print(f"    Fra: {ticket[0]}, Til: {ticket[1]}, Sete nummer: {ticket[2]}")
        print("------------------------------------------")

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



def create_ticket(customerID, startLoc, endLoc, seats, routeID, cartsID, section_ids):
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
        ticketID = cursorObj.fetchone()[0]
        ticketIDs.append(ticketID)

    #section_ids=get_section_ids(startLoc, endLoc)
    # Insert a new reserved seat into the ReservedSeat table for each section
    for ticketID in ticketIDs:
        for section_id in section_ids:
            if is_seat_reserved(seat, cartsID, section_id):
                print(f"Seat {seat} is already reserved for Cart ID {cartsID} and Section ID {section_id}. Please choose a different seat.")
                return None
            else:
                insert_reserved_seat_query = "INSERT INTO ReservedSeat (ticketID, cartsID, sectionID) VALUES (?, ?, ?)"
                cursorObj.execute(insert_reserved_seat_query, (ticketID, cartsID, section_id))
                database.commit()


    return ticketIDs


def is_seat_reserved(seat, cartsID, section_id):
    query = """
    SELECT COUNT(*) 
    FROM Ticket t
    JOIN ReservedSeat rs ON t.ticketID = rs.ticketID
    WHERE t.seatNr = ? AND rs.cartsID = ? AND rs.sectionID = ?
    """
    
    cursorObj.execute(query, (seat, cartsID, section_id))
    result = cursorObj.fetchone()[0]
    
    return result > 0




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

        
        routeID = int(input("Enter the route ID: "))
        cartsID = int(input("Enter the carts ID: "))
        # Get the number of seats to book and the seat numbers
        num_seats = int(input("Enter the number of seats you want to book: "))
        seats = []
        for i in range(num_seats):
            while True:
                seatNr = int(input(f"Enter seat number for seat {i + 1}: "))
                if not is_seat_reserved(seatNr, cartsID, section_ids[0]): # Check reservation for the first section
                    seats.append(seatNr)
                    break
                else:
                    print(f"Seat {seatNr} is already reserved. Please choose a different seat.")
        
        # Create the tickets
        ticketIDs = create_ticket(customer_id, start_station, end_station, seats, routeID, cartsID, section_ids)
        if ticketIDs:
            print(f"Created tickets with ticketIDs: {ticketIDs}")



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

    elif (action == "g"):
        brukerhistorie_G()
    elif (action == "h"):
        getFutureOrders()
main()