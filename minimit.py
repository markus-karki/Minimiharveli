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
        
        self.wxDestOps = 1
        self.wxDestPlan = 1
        self.wxAlt1Plan = 1
        self.wxAlt1Ops = 1
        self.wxAlt2Plan = 1
        self.wxAlt2Ops = 1

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
        self.A_ub  = zeros((26,0))
        self.b_ub = zeros((26,0))
        self.A_eq = zeros((5,0))
        self.b_eq = zeros((5,0))
        self.bounds = (0, 1)
        
        self.b_ub[1:5] = -1

        # Add feasible approaches 
        for airport in airports.airport:
            for approach in airport.approach:
                self.A_ub  = zeros((26,0))
                self.b_ub = zeros((26,0))
                self.A_eq = zeros((5,0))
                self.b_eq = zeros((5,0))
                
                self.addDestOps(airport, approach, flight)
                self.addDestPlan(airport, approach, flight)
                self.addAlt1Ops(airport, approach, flight)
                self.addAlt1Plan(airport, approach, flight)
                self.addAlt2Ops(airport, approach, flight)
                self.addAlt2Plan(airport, approach, flight)

    def solve(self):
        pass
        #self.solution = linprog(self.c, self.A_ub, self.b_ub, self.A_eq, self.b_eq, self.bounds)

    def addDestOps(self, airport, approach, flight):
        # Append list of added approaches and their types
        self.approach.append(approach)
        self.type.append("DestOps")

        # Append objective
        append(self.c, (approach.RVR + approach.visibility + approach.cloudbase) / 500)
        
        # Constraint 0 
        self.A_ub[0,-1] = airport.distanceFromDest

        # Constraint 4
        self.A_ub[4,-1] = - approach.wxDestOps
        
    def addDestPlan(self, airport, approach, flight):
        # Append list of added approaches and their types
        self.approach.append(approach)
        self.type.append("DestPlan")

        # Append objective
        append(self.c, (approach.RVR + approach.visibility + approach.cloudbase) / 500)
        
        # Constraint 2 
        self.A_ub[2,-1] = - approach.wxDestPlan

        # Constraint 3
        self.A_ub[3,-1] = - approach.wxDestPlan


    def addAlt1Ops(self, airport, approach, flight):
        # Append list of added approaches and their types
        self.approach.append(approach)
        self.type.append("Alt1Ops")

        # Append objective
        append(self.c, (approach.RVR + approach.visibility + approach.cloudbase) / 500 + airport.distanceFromDest)
        
        # Constraint 1
        self.A_ub[1,-1] = - airport.distanceFromDest

        # Constraint 5
        self.A_ub[5,-1] = 1

        # Constraint 6
        self.A_ub[6,-1] = 1 - approach.wxAlt1Ops


    def addAlt1Plan(self, airport, approach, flight):
        # Append list of added approaches and their types
        self.approach.append(approach)
        self.type.append("Alt1Plan")

        # Append objective
        append(self.c, (approach.RVR + approach.visibility + approach.cloudbase) / 500)
    
        # Constraint 5
        self.A_ub[5,-1] = - approach.wxAlt1Plan

    def addAlt2Ops(self, airport, approach, flight):
        # Append list of added approaches and their types
        self.approach.append(approach)
        self.type.append("Alt2Ops")

        # Append objective
        append(self.c, (approach.RVR + approach.visibility + approach.cloudbase) / 500 + airport.distanceFromDest)
        
        # Constraint 2
        self.A_ub[1,-1] = - airport.distanceFromDest

        # Constraint 3
        self.A_ub[3,-1] = - 1

        # Constraint 4
        self.A_ub[4,-1] = - 1

        # Constraint 7
        self.A_ub[7,-1] = 1

        # Constraint 8
        self.A_ub[8,-1] = 1 - approach.wxAlt2Ops

    def addAlt2Plan(self, airport, approach, flight):
        # Append list of added approaches and their types
        self.approach.append(approach)
        self.type.append("Alt2Plan")

        # Append objective
        append(self.c, (approach.RVR + approach.visibility + approach.cloudbase) / 500)

        # Constraint 7
        self.A_ub[7,-1] = - approach.wxAlt2Plan

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