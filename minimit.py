import csv
from scipy.optimize import linprog
from datetime import date
from math import cos, sin, acos, pi
from numpy import zeros, append, where, nditer
from html.parser import HTMLParser
from urllib.request import urlopen

# Step 1: w44
#   .1 Closest approach, with lowest minimums.  dest+alt , done
#   .2 Include TOALT and TO, w45
# Step 2: Filter by TAF w45 
#   .1 Read TAF, done
#   .2 Filter by TAF   
# Step 3: Filter by opening hours w46
#   .1 Read NOTAM, done
#   .2 Filter by opening hours
# (Step 4: Filter by night w47
#   .1 Calculate night
#   .2 Filter by night)
# Step 5: Filter by metar w48
#   .1 Read METAR, done
#   .2 Filter by METAR
# Redesign optimization to loop-search 
# Step 7: Publish as web or commandline app w49

# Rewrite solution class

class Conditions():
    def __init__(self):
        self.lateralVisibility = 0
        self.cloudbase = 0
        self.tempoLateralVisibility = 0
        self.tempoCloudbase = 0
        self.TS = 0
        self.FZ = 0
        self.windDirection = 0
        self.windSpeed = 0
        self.ATCopen = 0
        self.isNight = 0

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
        #Import HTML from a URL
        url = urlopen(NOTAM_url)
        html = url.read().decode('latin1')
        url.close()

        p = NOTAMparser()
        p.feed(html)

        print_all = 0
        currentNOTAM = ''
        for row in p.dataList:    
            if (row[0:2] == 'EF') and len(row)>7:
                    if (row[5] == '-'):
                        current_airport = self.getAirport(row[0:4])
                        if current_airport != 'None':
                            current_airport.NOTAM = ''
            if 'OPR HR' in row:
                print_all = 1

            if 'FROM' in row:
                print_all = 0
                if current_airport != 'None':
                    current_airport.NOTAM = current_airport.NOTAM + currentNOTAM 
                currentNOTAM = ''
            if ('TWR CLSD' in row) or ('AFIS CLSD' in row):
                print_all = 1
            if print_all:
                currentNOTAM = currentNOTAM + row
        
        for airport in self.airport:
            airport.NOTAMtoConditions()

    def readAvinorData(self, baseUrl, data):
        # Get data from Avinor
        url = baseUrl
        for airport in self.airport:
            url = url + airport.name + ","
        
        file = urlopen(url)
        new_line = '\n'
        for line in file:
            old_line = new_line
            new_line = line.decode("utf-8")
            if (old_line[0:4] != new_line[0:4]) and (old_line != '\n'):
                airport = self.getAirport(old_line[0:4])
                setattr(airport,data,old_line)
        
        for airport in self.airport:
            airport.TAFtoConditions()

    def getAirport(self, name):
        destination = 'None'
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
        self.TAF = 'NA'
        self.METAR = 'NA'
        self.NOTAM = 'NA'

        self.approach = list() 
        
        self.isOpen = 0
        self.distanceFromDest = 0.0
        self.timeFromDest = 0.0 
        self.arrivalTime = 0.0
        self.extraFuel = 0.0 
        self.oneHourExtra = 0
        #self.conditionHours = [14, 15]
        self.conditions = 0 #[0, 0]
    
    def calculateDistanceAndTime(self, flight, origin):
        if self.name == origin.name:
            self.distanceFromDest = 0
        else:
            self.distanceFromDest = 3440 * acos(sin(self.latitude)*sin(origin.latitude)+cos(self.latitude)*cos(origin.latitude)*cos(self.longitude-origin.longitude))
        
        sidAndApproach = 12
        finalReserves = 45

        self.timeFromDest = self.distanceFromDest / flight.XCSpeed + sidAndApproach/60
        self.arrivalTime = flight.arrivalTime + self.timeFromDest
        self.extraFuel = flight.enduranceLeft - self.timeFromDest - finalReserves/60
        self.oneHourExtra = (self.extraFuel > 1)

    def addApproach(self, row):
        self.approach.append(Approach(row))

    def NOTAMtoConditions(self):
        months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
        weekdays = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        NOTAM = self.NOTAM.split()
        for group in NOTAM:
            if group[0:3] in months:
                pass
                #Format: MONTH DAY - MONTH DAY
                #Format: MONTH DAY - DAY
                #Format: MONTH DAY
            elif group[0:3] in weekdays:
                pass
                #Format: DAY - DAY
                #Format: DAY
            elif group[4] == '-':
                pass
                #Format: HHMM - HHMM

    def TAFtoConditions(self):
        TAF = self.TAF.split()
        for group in TAF:
            if group[0:2] == 'KT':
                pass
            elif (len(group) == 4) and group.isdigit():
                pass
            elif group[0:3] == 'OVC':
                pass
            elif group[0:3] == 'BKN':
                pass
            elif group[0:2] == 'VV':
                pass
            elif group == 'TEMPO':
                pass
            elif group[0:4] == 'PROB':
                pass
            elif group[0:5] == 'BECMG':
                pass
            elif group[0:2] == 'FM':
                pass
            elif group[0:2] == 'TL':
                pass
            elif group[0:2] == 'AT':
                pass
            elif group[0:5] == 'CAVOK':
                pass
            elif group[0:3] == 'SKC':
                pass
            elif group[0:3] == 'NSC':
                pass
            elif 'FZ' in group:
                pass
            elif group[4] == '/':
                pass

class Runway():
    def __init__(self, name, direction):
        pass

class Approach():
    def __init__(self, row):
        self.airportName = row[0]
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
        self.wxAlt1Worse = 1
        self.wxAlt2Worse = 1

class NOTAMparser(HTMLParser):
    def __init__(self):
    #Since Python 3, we need to call the __init__() function of the parent class
        super().__init__()
        self.reset()
        self.dataList = list()
    #Defining what the method should output when called by HTMLParser.
    def handle_data(self, data):
        # Only parse the 'anchor' tag.
        self.dataList.append(data)

class Solver():
    def __init__(self, airports, flight):
        # Initialize variables
        self.c = zeros(0)
        self.approach = list()
        self.type = list()
        self.A_ub  = zeros((17,0))
        self.b_ub = zeros((17,1))
        self.A_eq = zeros((5,0))
        self.b_eq = zeros((5,1))
        self.bounds = (0, 1)
        
        self.b_ub[1:5] = -1
        self.b_ub[16] = -1

        self.b_eq[0] = 1
        self.b_eq[4] = 1
        
        # Add feasible approaches 
        for airport in airports.airport:
            if airport.extraFuel > 0:
                for approach in airport.approach:
                    if airport.name == flight.destination:
                        self.addDestOps(airport, approach, flight)
                        self.addDestPlan(airport, approach, flight)
                    else:
                        self.addAlt1Ops(airport, approach, flight)
                        self.addAlt1Plan(airport, approach, flight)
                        self.addAlt2Ops(airport, approach, flight)
                        self.addAlt2Plan(airport, approach, flight)

    def solve(self):
        if len(self.c) == 0:
            print('No suitable alternates found')
        else:
            # Solve
            self.solution = linprog(self.c, self.A_ub, self.b_ub, self.A_eq, self.b_eq, self.bounds, options={'tol': 1e-6})
            if self.solution.status != 0:
                print('No suitable alternates found')
            else:
                # Print solution
                Solution(self)      

    def addDestOps(self, airport, approach, flight):
        # Append list of added approaches and their types
        self.approach.append(approach)
        self.type.append("DestOps")
        self.A_ub = append(self.A_ub, zeros((17,1)), axis=1)
        self.A_eq = append(self.A_eq, zeros((5,1)), axis=1)
        
        # Append objective
        self.c = append(self.c, (approach.RVR + approach.visibility + approach.cloudbase) / 500)
        
        # Constraint 0: DestOPS is at destination
        self.A_ub[0,-1] = airport.distanceFromDest

        # Constraint 4
        self.A_ub[4,-1] = - approach.wxDestOps

        # Constraint 15
        self.A_ub[15,-1] = - approach.groudEquipment

        # EQ Constraint 5
        self.A_eq[4,-1] = 1
        
    def addDestPlan(self, airport, approach, flight):
        # Append list of added approaches and their types
        self.approach.append(approach)
        self.type.append("DestPlan")
        self.A_ub = append(self.A_ub, zeros((17,1)), axis=1)
        self.A_eq = append(self.A_eq, zeros((5,1)), axis=1)

        # Append objective
        self.c = append(self.c, (approach.RVR + approach.visibility + approach.cloudbase) / 500)
        
        # Constraint 2 
        self.A_ub[2,-1] = - approach.wxDestPlan

        # Constraint 3
        self.A_ub[3,-1] = - approach.wxDestPlan

        # Eq Constraint 1
        self.A_eq[1,-1] = airport.distanceFromDest

    def addAlt1Ops(self, airport, approach, flight):
        # Append list of added approaches and their types
        self.approach.append(approach)
        self.type.append("Alt1Ops")
        self.A_ub = append(self.A_ub, zeros((17,1)), axis=1)
        self.A_eq = append(self.A_eq, zeros((5,1)), axis=1)

        # Append objective
        self.c = append(self.c, (approach.RVR + approach.visibility + approach.cloudbase) / 500 + airport.distanceFromDest)
        
        # Constraint 1: Alt1Ops at least one mile from destination
        self.A_ub[1,-1] = - airport.distanceFromDest

        # Constraint 5
        self.A_ub[5,-1] = 1

        # Constraint 6
        self.A_ub[6,-1] = 1 - approach.wxAlt1Ops

        # Constraint 9
        self.A_ub[9,-1] = max(approach.CAT1, approach.NPA)

        # Constraint 10
        self.A_ub[10,-1] = approach.NPA

        # Constraint 11
        self.A_ub[11,-1] = approach.circle

        # Constraint 15
        self.A_ub[15,-1] = 1 - approach.groudEquipment

        # Constraint 16
        self.A_ub[16,-1] = - airport.distanceFromDest

        # Eq Constraint 0
        self.A_eq[0,-1] = 1

        # Eq Constraint 2
        self.A_eq[2,-1] = - airport.distanceFromDest

    def addAlt1Plan(self, airport, approach, flight):
        # Append list of added approaches and their types
        self.approach.append(approach)
        self.type.append("Alt1Plan")
        self.A_ub = append(self.A_ub, zeros((17,1)), axis=1)
        self.A_eq = append(self.A_eq, zeros((5,1)), axis=1)

        # Append objective
        self.c = append(self.c, (approach.RVR + approach.visibility + approach.cloudbase) / 500)
    
        # Constraint 5
        self.A_ub[5,-1] = - approach.wxAlt1Plan

        # Constraint 9
        self.A_ub[9,-1] = - max(approach.NPA, approach.circle)

        # Constraint 10
        self.A_ub[10,-1] = - approach.wxAlt1Plan * approach.wxAlt1Worse * approach.NPA

        # Constraint 11
        self.A_ub[11,-1] = - approach.circle

        # Eq Constraint 2
        self.A_eq[2,-1] = airport.distanceFromDest

    def addAlt2Ops(self, airport, approach, flight):
        # Append list of added approaches and their types
        self.approach.append(approach)
        self.type.append("Alt2Ops")
        self.A_ub = append(self.A_ub, zeros((17,1)), axis=1)
        self.A_eq = append(self.A_eq, zeros((5,1)), axis=1)

        # Append objective
        self.c = append(self.c, (approach.RVR + approach.visibility + approach.cloudbase) / 500 + airport.distanceFromDest)
        
        # Constraint 2: Alt1Ops at least one mile from destination, if DestPlan in not OK
        self.A_ub[1,-1] = - airport.distanceFromDest

        # Constraint 3
        self.A_ub[3,-1] = - 1

        # Constraint 4
        self.A_ub[4,-1] = - 1

        # Constraint 7
        self.A_ub[7,-1] = 1

        # Constraint 8
        self.A_ub[8,-1] = 1 - approach.wxAlt2Ops

        # Constraint 12
        self.A_ub[12, -1] = approach.CAT1

        # Constraint 13
        self.A_ub[13,-1] = approach.NPA

        # Constraint 14
        self.A_ub[14,-1] = approach.circle

        # Constraint 16
        self.A_ub[16,-1] = airport.distanceFromDest

        # Eq Constraint 3
        self.A_eq[3,-1] = - airport.distanceFromDest

    def addAlt2Plan(self, airport, approach, flight):
        # Append list of added approaches and their types
        self.approach.append(approach)
        self.type.append("Alt2Plan")
        self.A_ub = append(self.A_ub, zeros((17,1)), axis=1)
        self.A_eq = append(self.A_eq, zeros((5,1)), axis=1)

        # Append objective
        self.c = append(self.c, (approach.RVR + approach.visibility + approach.cloudbase) / 500)

        # Constraint 7
        self.A_ub[7,-1] = - approach.wxAlt2Plan

        # Constraint 12
        self.A_ub[12,-1] = - max(approach.NPA, approach.circle)

        # Constraint 13
        self.A_ub[13,-1] = - approach.wxAlt2Plan * approach.wxAlt2Worse * approach.NPA

        # Constraint 14
        self.A_ub[14,-1] = - approach.circle

        # Eq Constraint 3
        self.A_eq[3,-1] = airport.distanceFromDest

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
        
class Solution():
  def __init__(self, solver):
    activeApproach = where(abs(solver.solution['x'] - 1)<0.05)
    
    for i in nditer(activeApproach):
      type = solver.type[i]
      approach = solver.approach[i]
      setattr(self, type, approach)
      
    self.print('DEST', self.DestOps, self.DestPlan)
    # TODO: Worsening?
    self.print('Alt1', self.Alt1Ops, self.Alt1Plan)
    if hasattr(self, 'Alt2Ops'):
        self.print('Alt2', self.Alt2Ops, self.Alt2Plan)
  
  def print(self, title, ops, plan):
    print('\n')
    print(title, ': ', ops.airportName)
    if plan.CAT1 == 1:
      cloudbase = '-'
    else:
      cloudbase = plan.cloudbase
    print('Plan:', plan.ID, ' ', plan.RVR, 'm /', cloudbase, 'ft')
    print('Ops: ', ops.ID, ' ', ops.RVR, 'm / - ft')

def main(ApproachDataFile, AirportDataFile, NOTAM_url, TAF_url, parameters, arg0, arg1, arg2):
    # Read parameters
    flight = Flight(parameters, arg0, arg1, arg2)

    # Read airport data 
    airports = Airports(AirportDataFile)
    
    # Read approach data 
    airports.addApproach(ApproachDataFile)
    
    # Read NOTAM opening hours for next 24h
    airports.readNOTAM(NOTAM_url)

    # Read day and night data for next 24h
    
    # Read TAF data
    #airports.readAvinorData(TAF_url, 'TAF')

    # Read METAR data
    #airports.readAvinorData(METAR_url, 'METAR')

    # Solve Takeoff alternates
    # Calculate alternate distances and fuel requirements
    #airports.calculateDistanceAndTime(flight)
    # Build input 
    #solver = Solver(airports, flight)
    # Optimize and print solution
    #solver.solve()

    # Solve destination and alternates    
    # Calculate alternate distances and fuel requirements
    airports.calculateDistanceAndTime(flight)
    # Build input 
    solver = Solver(airports, flight)
    # Optimize and print solution
    solver.solve()

if __name__ == '__main__':
    TAF_url = 'https://api.met.no/weatherapi/tafmetar/1.0/taf.txt?icao='
    METAR_url = 'https://api.met.no/weatherapi/tafmetar/1.0/metar.txt?icao='
    NOTAM_url = 'https://www.ais.fi/ais/bulletins/efinen.htm'
    ApproachDataFile = 'ApproachData.csv'
    AirportDataFile = 'AirportData.csv'
    parameters = {'maxTailwind': 10, 'maxCrosswind': 20, 'minRVR': 600, 'TOALTminRVR': 800, 'OEIXCSpeed': 120, 'XCSpeed': 140}
    AirportsInUse = 0
    arg0 = "EFPO2330"
    arg1 = "EFPO0045"
    arg2 = "0230"

    main(ApproachDataFile, AirportDataFile, NOTAM_url, TAF_url, parameters, arg0, arg1, arg2)