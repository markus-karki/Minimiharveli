import csv
from scipy.optimize import linprog
from datetime import date
from math import cos, sin, acos, pi
# Step 1: Closest approach, with lowest minimums. a) dest+alt b) to
# import approach data, build optimization problem, print solution, 
# Step 2: Filter by TAF
# Step 3: Filter by opening hours
# Step 4: Filter by night
# Step 5: Filter by metar

# Check minimum contigency

class Conditions():
    def __init__(self):
        self.RVR = 0
        self.visibility = 0
        self.cloubase = 0
        self.TS = 0
        self.FZ = 0
        self.windDirection = 0
        self.windSpeed = 0

class Flight():
    def __init__(self, parameters, arg0, arg1, arg2):
        self.date = date.today()
        self.origin = arg0[0:4]
        self.destination = arg1[0:4]
        self.endurance = int(arg2[0:2]) + int(arg2[2:4])/60
        self.departureTime = int(arg0[4:6]) + (int(arg0[6:8])) / 60
        self.flightTime = int(arg1[4:6]) + (int(arg1[6:8]) + 10) / 60
        self.arrivalTime = self.departureTime + self.flightTime
        self.enduranceLeft = self.endurance - self.flightTime - max(self.flightTime * 0.05, 0.1)
        self.maxTailwind = parameters['maxTailwind']
        self.maxCrosswind = parameters['maxCrosswind']
        self.minRVR = parameters['minRVR']
        self.TOALTminRVR = parameters['TOALTminRVR']
        self.OEIXCSpeed = parameters['OEIXCSpeed']
        self.XCSpeed = parameters['XCSpeed']

class Airports():
    def __init__(self, AirportDataFile):
        self.airport = list()
        ifile  = open(AirportDataFile)
        read = csv.reader(ifile)
        for row in read :  
            if len(row[0])==4:
                self.airport.append(Airport(row[0], row[1], row[2]))
        
    def calculateDistanceAndTime(self, flight):
        for airport in self.airport:
            if airport.name == flight.destination:
                destination = airport
                break
        
        for airport in self.airport:
            airport.calculateDistanceAndTime(flight, destination)
            
    def readNOTAM(self, NOTAM_url):
        pass

    def readTAF(self, TAF_url):
        pass
    
class Airport():
    def __init__(self, name, latitude, longitude):
        self.name = name
        self.latitude = float(latitude) / 360 * 2 * pi
        self.longitude = float(longitude) / 360 * 2 * pi
        self.TAF = 'NIL'
        #self.METAR = 0
        self.openingHours = 0
        self.approach = list() 
        self.distanceFromDest = 0.0
        self.timeFromDest = 0.0 
        self.arrivalTime = 0.0
        self.extraFuel = 0.0 
        self.oneHourExtra = 0
    
    def calculateDistanceAndTime(self, flight, origin):
        if self.name == origin.name:
            self.distanceFromDest = 0
        else:
            self.distanceFromDest = 3440 * acos(sin(self.latitude)*sin(origin.latitude)+cos(self.latitude)*cos(origin.latitude)*cos(self.longitude-origin.longitude))
        self.timeFromDest = self.distanceFromDest / flight.XCSpeed + 12/60
        self.arrivalTime = flight.arrivalTime + self.timeFromDest
        self.extraFuel = flight.enduranceLeft - self.timeFromDest - 0.5
        self.oneHourExtra = (self.extraFuel > 1)

    def addOpeninghours(self):
        pass

    def addTAF(self):
        pass

class Approach():
    def __init__(self):
        self.ID = "ILS RWY30"
        self.CAT1 = 1
        self.NPA = 0
        self.circle = 0
        self.groudEquipment = 0
        self.rwyheading = 298 

class TAFparser():
    def __init__(self):
        pass

class METARparser():
    def __init__(self):
        pass

class Solver():
    def __init__(self, airports, parameters, arg0, arg1, arg2):
        self.parameters = parameters
        self.c = 0
        self.approach = 0
        self.A_ub  = 0
        self.b_ub = 0
        self.A_eq = 0
        self.b_eq = 0
        self.bounds = 0
        self.TOAirport = arg0[0:4]
        self.LDGAirport = arg1[0:4]
        self.TOtime = arg0[4:8]
        self.LDGtime = arg1[4:8]
        self.holdOK = arg2


        #for airport in airports.airport:
            #for approach in airport.approach:
                #self.addApproach(airport, approach)


    def solve(self):
        pass
        #self.solution = linprog(c, A_ub, b_ub, A_eq, b_eq, bounds)

    def addApproach(self, airport, approach):
        pass
        # Objective
        
        #TO Alt Ops airport exists
        #Dest Ops airport exists
        #Alt I Ops airport exists
        #Alt II Ops airport exists

        #TO Alt Plan weather minima
        #TO Alt Ops weather minima
        #Dest Plan weather minima/Alt II
        #Dest Ops weather minima/ Alt II
        #Alt I Plan weather minima
        #Alt I Ops weather minima
        #Alt II Plan weather minima
        #Alt II Ops weather minima

        #TO Alt distance

        #CAT-NPA worsening I
        #NPA - NPA worsening I
        #Circle-Circle worsening I
        #CAT-NPA worsening Alt II
        #NPA - NPA worsening Alt II
        #Circle-Circle worsening Alt II

        #Ground system condition

        #ALT 1 further than ALT 2

        #Airport and approach in use

        #TO Alt Open
        #Dest Open
        #Alt I Open
        #Alt II Open

        #Alt I exists
        #TO Alt Plan airport
        #Dest Plan airport
        #Alt I Plan airport
        #Alt II Plan airport

        #Bounds
        
        #Approach

    def printSolution(self):
        print('\n')
        print('TO: EFPO')
        print('Plan:', 'ILS RWY 30 ', '800m / -ft')
        print('Ops: ', 'ILS RWY 30 ', '800m / -ft')
        print('\n')
        print('DEST: EFTU')
        print('Plan:', 'ILS RWY 30 ', '600m / -ft')
        print('Ops: ', 'ILS RWY 30 ', '600m / -ft')
        print('\n')
        print('ALT1: EFTP')
        print('Plan:', 'LNAV/VNAV RWY 06 ', '750m / 384ft')
        print('Ops: ', 'ILS RWY 24 ', '600m / - ft')
        print('\n')
        print('ALT2: EFPO')
        print('Plan:', 'VOR RWY 30 ', '11000m / 454ft')
        print('Ops: ', 'ILS RWY 30 ', '600m / - ft')
        
def main(ApproachDataFile, AirportDataFile, NOTAM_url, TAF_url, parameters, arg0, arg1, arg2):
    # Read parameters
    flight = Flight(parameters, arg0, arg1, arg2)

    # Read airport data 
    airports = Airports(AirportDataFile)
    airports.calculateDistanceAndTime(flight)
    # Read approach data 
    airports.addApproach(ApproachDataFile)

    # Read NOTAM opening hours for next 24h
    #airports.readNOTAM(NOTAM_url)

    # Read day and night data for next 24h
    
    # Read TAF data
    #airports.readTAF(TAF_url)

    # Read METAR data

    # Build input 
    solver = Solver(airports, parameters, arg0, arg1, arg2)

    # Optimize
    solver.solve()

    # Print solution
    solver.printSolution()


if __name__ == '__main__':
    TAF_url = 'https://api.met.no/weatherapi/tafmetar/1.0/taf.txt?icao='
    METAR_url = 'https://api.met.no/weatherapi/tafmetar/1.0/metar.txt?icao='
    NOTAM_url = 'https://www.ais.fi/ais/bulletins/efinen.htm'
    ApproachDataFile = 'ApproachData.csv'
    AirportDataFile = 'AirportData.csv'
    parameters = {'maxTailwind': 10, 'maxCrosswind': 20, 'minRVR': 600, 'TOALTminRVR': 800, 'OEIXCSpeed': 120, 'XCSpeed': 140}
    AirportsInUse = 0
    arg0 = "EFPO1230"
    arg1 = "EFTU0045"
    arg2 = "0245"

    main(ApproachDataFile, AirportDataFile, NOTAM_url, TAF_url, parameters, arg0, arg1, arg2)