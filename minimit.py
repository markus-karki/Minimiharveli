import csv
from scipy.optimize import linprog
from datetime import date
from math import cos, sin, acos, pi
from numpy import zeros, append

# Step 1: Closest approach, with lowest minimums. a) dest+alt b) to
# build optimization problem, print solution, 
# Step 2: Filter by TAF
# Step 3: Filter by opening hours
# Step 4: Filter by night
# Step 5: Filter by metar

# Check minimum contigency

class Conditions():
    def __init__(self):
        self.RVR = 0
        self.visibility = 0
        self.cloudbase = 0
        self.tempoVisibility = 0
        self.tempoRVR = 0
        self.tempoCloudbase = 0
        self.TS = 0
        self.FZ = 0
        self.windDirection = 0
        self.windSpeed = 0

class Flight():
    def __init__(self, parameters, arg0, arg1, arg2):
        taxiTime = 10
        approachtTime = 10
        contigengyPercent = 0.05
        contigengyTime = 12
        
        # Calculate and save parameters
        self.date = date.today()
        self.origin = arg0[0:4]
        self.destination = arg1[0:4]
        self.endurance = int(arg2[0:2]) + int(arg2[2:4])/60
        self.departureTime = int(arg0[4:6]) + (int(arg0[6:8]) + taxiTime) / 60
        self.flightTime = int(arg1[4:6]) + (int(arg1[6:8]) + approachtTime) / 60
        self.arrivalTime = self.departureTime + self.flightTime
        self.enduranceLeft = self.endurance - self.flightTime - max(self.flightTime * contigengyPercent, contigengyTime/60)
        self.maxTailwind = parameters['maxTailwind']
        self.maxCrosswind = parameters['maxCrosswind']
        self.minRVR = parameters['minRVR']
        self.TOALTminRVR = parameters['TOALTminRVR']
        self.OEIXCSpeed = parameters['OEIXCSpeed']
        self.XCSpeed = parameters['XCSpeed']

class Airports():
    def __init__(self, AirportDataFile):
        # Open csv
        ifile  = open(AirportDataFile)
        read = csv.reader(ifile)
        
        # Add airports
        self.airport = list()
        for row in read :  
            if len(row[0])==4:
                self.airport.append(Airport(row[0], row[1], row[2]))
        
    def calculateDistanceAndTime(self, flight):
        # Find destination airport
        destination = self.getAirport(flight.destination)
        
        # Calculate distance between each airport and destination
        for airport in self.airport:
            airport.calculateDistanceAndTime(flight, destination)
            
    def addApproach(self, ApproachDataFile):
        # Open csv
        ifile  = open(ApproachDataFile)
        read = csv.reader(ifile)
        
        # Add approaches
        current_airport = ""
        for row in read :  
            if len(row[0]) == 4:
                if row[0] != current_airport:
                    current_airport = self.getAirport(row[0])         
                current_airport.addApproach(row)
    
    def readNOTAM(self, NOTAM_url):
        pass

    def readTAF(self, TAF_url):
        pass

    def getAirport(self, name):
        for airport in self.airport:
            if airport.name == name:
                destination = airport
                break
        return destination
    
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
        self.conditionHours = [14, 15]
        self.conditions = [0, 0]
    
    def calculateDistanceAndTime(self, flight, origin):
        if self.name == origin.name:
            self.distanceFromDest = 0
        else:
            self.distanceFromDest = 3440 * acos(sin(self.latitude)*sin(origin.latitude)+cos(self.latitude)*cos(origin.latitude)*cos(self.longitude-origin.longitude))
        
        sidAndApproach = 12
        finalReserves = 30

        self.timeFromDest = self.distanceFromDest / flight.XCSpeed + sidAndApproach/60
        self.arrivalTime = flight.arrivalTime + self.timeFromDest
        self.extraFuel = flight.enduranceLeft - self.timeFromDest - finalReserves/60
        self.oneHourExtra = (self.extraFuel > 1)

    def addApproach(self, row):
        self.approach.append(Approach(row))

    def addOpeninghours(self):
        pass

    def addTAF(self):
        pass

class Approach():
    def __init__(self, row):
        self.ID = row[1]
        self.groudEquipment = int(row[2])
        self.CAT1 = int(row[3])
        self.NPA = int(row[4])
        self.circle = int(row[5])
        self.rwyheading = int(row[6]) 
        self.cloudbase = int(row[7]) 
        if int(row[9]) == 0:
            self.RVR = int(row[8]) 
            self.visibility = int(9999) 
        else:
            self.visibility = int(row[8])
            self.RVR = int(9999)

class TAFparser():
    def __init__(self):
        pass

class METARparser():
    def __init__(self):
        pass

class Solver():
    def __init__(self, airports, flight):
        # Initialize variables
        self.c = zeros((1,0))
        self.approach = list()
        self.type = list()
        self.A_ub  = zeros((1,0))
        self.b_ub = zeros((1,0))
        self.A_eq = zeros((1,0))
        self.b_eq = zeros((1,0))
        self.bounds = zeros((1,0))
        
        # Add feasible approaches 
        for airport in airports.airport:
            for approach in airport.approach:
                self.addDestOps(airport, approach, flight)
                self.addDestPlan(airport, approach, flight)
                self.addAlt1Ops(airport, approach, flight)
                self.addAlt1Plan(airport, approach, flight)
                self.addAlt2Ops(airport, approach, flight)
                self.addAlt2Plan(airport, approach, flight)

    def solve(self):
        pass
        #self.solution = linprog(c, A_ub, b_ub, A_eq, b_eq, bounds)

    def addDestOps(self, airport, approach, flight):
        
        self.approach.append(approach)
        self.type.append("DestOps")

        # Objective
        append(self.c, (approach.RVR + approach.visibility + approach.cloudbase))

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
        
    def addDestPlan(self, airport, approach, flight):
        pass
        
    def addAlt1Ops(self, airport, approach, flight):
        pass
    def addAlt1Plan(self, airport, approach, flight):
        pass
    def addAlt2Ops(self, airport, approach, flight):
        pass
    def addAlt2Plan(self, airport, approach, flight):
        pass
    def printSolution(self):
        print('\n')
        print('TO: EFPO')
        #print('Plan:', 'ILS RWY 30 ', '800m / -ft')
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
    solver = Solver(airports, flight)

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