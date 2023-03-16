import sqlite3
import datetime

database = sqlite3.connect("Kaffe.db")
cursorObj = database.cursor()
epost = ""

def fetch(database):
    cursorObj.execute('SELECT name FROM sqlite_master WHERE type= "table"')
    
## Henter innholdet i databasen
fetch(database)

## Funksjon for å registrere ny bruker
def signup():
    fornavn = input("Skriv inn fornavn: ")
    etternavn = input("Skriv inn etternavn: ")
    global epost
    epost = input("Skriv inn epost: ")
    passord = input("Lag passord: ")

    epost_db = cursorObj.execute('SELECT epostadresse FROM bruker')
    for i in epost_db.fetchall():
        if i[0] == epost:
            print("E-postadressen er allerede i bruk")
            return False
    
    cursorObj.execute("INSERT INTO bruker VALUES ('{}', '{}', '{}', '{}')".format(epost, passord, fornavn, etternavn))
    database.commit()

    
    return True, epost

## Funksjon for å logge inn med eksisterende bruker   
def login():
    global epost
    epost = input("Skriv inn epost: ")
    passord = input("Skriv inn passord: ")

    bruker = cursorObj.execute("SELECT passord FROM bruker WHERE epostadresse = '{}'".format(epost))
    for i in bruker.fetchall():
        if i[0] == passord:
            return True, epost
    print("Feil e-postadresse eller passord")
    return False

## Funksjon for å legge til en ny kaffesmaking, som beskrevet i brukerhistorie 1
def brukerhistorie_1():
    while True:
        login_eller_signup = input("\nVelg 1 for å logge inn.\nVelg 2 for å opprette ny bruker.\nValg: ")
        print("")
        if login_eller_signup == '1':
            if login():
                break
        elif login_eller_signup == '2':
            if signup():
                break

    ## Henter ut kaffe fra databasen 
    print("\nHvilken kaffe? ")
    kaffer = cursorObj.execute('SELECT navn FROM kaffe')
    liste_med_kaffe = []
    for i in kaffer.fetchall():
        print("- " + i[0])
        liste_med_kaffe.append(i[0])
    kaffenavn = input("\nKaffenavn: ")
    while kaffenavn not in liste_med_kaffe:
        print("Vennligst velg en kaffe fra lista.\n")
        kaffenavn = input("Kaffenavn: ")

    ##Henter ut brennerier som har brent en kaffe med navnet som brukeren valgte   
    print("\nHvilket brenneri?")  
    brennerier = cursorObj.execute("SELECT DISTINCT brenneriNavn FROM kaffe WHERE navn='{}'".format(kaffenavn))
    liste_med_brennerier = []
    for i in brennerier.fetchall():
        print("- " + i[0])
        liste_med_brennerier.append(i[0])
    brenneri = input("\nBrenneri: ")
    while brenneri not in liste_med_brennerier:
        print("Vennligst velg et brenneri fra listen. ")
        brenneri = input("Brenneri: ")

    ##Bruker brennerinavn og kaffenavn for å hente ut id-en til kaffen som brukeren har valgt
    kaffe_id_bruk = 0
    kaffe_id = cursorObj.execute("SELECT kaffeID FROM kaffe WHERE navn = '{}' AND brenneriNavn = '{}'".format(kaffenavn, brenneri))
    for i in kaffe_id.fetchall():
        kaffe_id_bruk = i[0]
    
    kaffe_id_epost = cursorObj.execute("SELECT kaffeID, epostadresse FROM kaffesmaking WHERE epostadresse = '{}' AND kaffeID = {}".format(epost, kaffe_id_bruk))
    count = 0
    for i in kaffe_id_epost.fetchall():
        count += 1
    
    if(count > 0):
        print("Du har allerede lagt inn kaffesmaking for denne kaffen.\n")
    else:
        smaksnotater = input("\nSkriv inn ditt smaksnotat: ")

        ##Sjekker at poeng er et tall fra 1 til 10
        poeng = input("\nPoeng (1 - 10): ")
        while int(poeng) > 10 or int (poeng) < 1:
            print("Må være poeng mellom 1 og 10.")
            poeng = input("Poeng (1 - 10): ")

        smaksdato = datetime.datetime.now()
        
        ## Genererer en ny kaffesmakingID
        kaffesmaking_id = cursorObj.execute("SELECT kaffesmakingID FROM kaffesmaking")
        output = []
        for i in kaffesmaking_id.fetchall():
            output.append(i[0])
        counter = int(output[-1])
        counter += 1
        
        cursorObj.execute("INSERT INTO kaffesmaking VALUES ({}, '{}', {}, '{}', '{}', {})".format(int(counter), smaksnotater, int (poeng), smaksdato, epost, kaffe_id_bruk))
        database.commit()

        print("Kaffesmakingen ble lagret!\n")
      

##Henter ut data som beskrevet i brukerhistorie 2
def brukerhistorie_2():
    string = cursorObj.execute("""SELECT bruker.fornavn AS fornavn, bruker.etternavn AS etternavn, antallKaffe 
    FROM bruker, (SELECT kaffesmaking.epostadresse AS antallKaffeID, strftime('%Y', smaksdato) AS aar,
    COUNT(kaffesmaking.epostadresse) AS antallKaffe 
    FROM kaffesmaking 
    GROUP BY kaffesmaking.epostadresse) WHERE bruker.epostadresse = antallKaffeID AND aar = '2022'
    ORDER BY antallKaffe DESC""")
    
    for i in string.fetchall():
        output = i
        string = ""
        for j in range(len(output)):
            string += str(output[j])
            string += "  "
        print(string)

##Henter ut data som beskrevet i brukerhistorie 3
def brukerhistorie_3():
    string = cursorObj.execute("""SELECT brenneri.brenneriNavn AS brenneriNavn, kaffe.navn AS kaffeNavn, kaffe.kilopris AS pris, 
    AVG(kaffesmaking.poeng) AS snittscore 
    FROM (brenneri INNER JOIN kaffe ON brenneri.brenneriNavn = kaffe.brenneriNavn) 
    INNER JOIN kaffesmaking ON kaffe.kaffeID = kaffesmaking.kaffeID 
    GROUP BY kaffe.kaffeID 
    ORDER BY (snittscore/pris) DESC""")

    for i in string.fetchall():
        output = i
        string = ""
        for j in range (len(output)):
            string += str(output[j])
            string += "  "
        print(string)

##Henter ut data som beskrevet i brukerhistorie 4  
def brukerhistorie_4():
    ## Her skriver bruker inn beskrivelsen som ønskes
    beskrivelse = input("Søk: ")
    string = cursorObj.execute("""SELECT DISTINCT kaffe.navn AS kaffeNavn, brenneri.brenneriNavn AS brenneriNavn 
    FROM (kaffesmaking INNER JOIN kaffe ON kaffesmaking.kaffeID = kaffe.kaffeID) 
    INNER JOIN brenneri ON kaffe.brenneriNavn = brenneri.brenneriNavn 
    WHERE kaffe.beskrivelse LIKE '%{}%' OR kaffesmaking.smaksnotater LIKE '%{}%'""".format(str(beskrivelse), str(beskrivelse)))
    
    antall_print = 0
    for i in string.fetchall():
        output = i
        string = ""
        for j in range(len(output)):
            string += str(output[j])
            string += "  "
        print(string)
        antall_print += 1
    if(antall_print == 0):
        print("Fant ingen resultater\n")

##Henter ut data som beskrevet i brukerhistorie 5
def brukerhistorie_5():
    land_1 = input("Velg land nummer 1: ")
    land_2 = input("Velg land nummer 2: ")
    metode = input("Velg en metode du ikke vil at kaffen skal være foredlet med: ")
    string = cursorObj.execute("""SELECT kaffe.navn AS kaffeNavn, brenneri.brenneriNavn AS brenneriNavn 
    FROM (((kaffe INNER JOIN brenneri ON kaffe.brenneriNavn = brenneri.brenneriNavn) 
    INNER JOIN parti ON kaffe.partiID = parti.partiID) 
    INNER JOIN gaard ON parti.gaardID = gaard.gaardID) 
    INNER JOIN foredlingsmetode ON parti.foredlingsmetodeID = foredlingsmetode.foredlingsmetodeID 
    WHERE (gaard.land = '{}' OR gaard.land = '{}') AND foredlingsmetode.navn != '{}' AND foredlingsmetode.navn != 'vasket'""".format(land_1, land_2, metode))
    
    count = 0
    for i in string.fetchall():
        output = i
        string = ""
        for j in range(len(output)):
            string += str(output[j])
            string += "  "
        print(string)
        count +=1
    if(count == 0):
        print("Fant ingen resultater\n")

## Her kjøres programmet. Funksjonene over kalles her.
def main():
    print("\nVelkommen til KaffeDB!\n")
   
    while True:
        brukerhistorie = input("\nVelg handling: 1 for å legge til kaffesmaking, eller 2 til 5 for brukerhistorier 2-5.\nVelg 0 for å avslutte programmet.\n\nValg: ")
        if brukerhistorie == '0':
            print("\nTakk for nå!")
            break
        
        elif brukerhistorie == '1':
            brukerhistorie_1()
        
        elif brukerhistorie == '2':
            brukerhistorie_2()
            
        elif brukerhistorie == '3':
            brukerhistorie_3()
            
        elif brukerhistorie == '4':
            brukerhistorie_4()
            
        elif brukerhistorie == '5':
            brukerhistorie_5()
        
        else:
            print("Ugyldig kommando, prøv igjen!")
            
main()
        