from datetime import datetime, time, date
from math import cos, sin, acos, pi
from numpy import zeros, append, where, nditer
import csv
import os
from lib.nightParser import *
from lib.notamParser import *
from lib.weatherParser import *
'''
TODO
- Step 1: Redesign optimization to loop-search, w48, to test
- Step 2: Update approach data
- Step 3: Merge to master branch
- Step 7: Publish as flask app via AWS
- Step 8: Code improvements: 
    - Commemts
    - Variable names
    - Function names
    - Error handling
    - Multiple argument passing practices
    - Hard coded parameters
    - Flag printing
    - Manual ALT assigment
    - Check logic for design/performance improvements
    - BECMG for FZ and TS groups
'''

class Conditions():
    def __init__(self, row):
        self.start = int(row[1])
        self.end = int(row[2])
        self.data = row[3]
        
        if len(row) >= 6:
            self.type = row[5]
        
    def isValidAnyMoment(self, times):
        if times[0] > self.end or times[1] < self.start:
            return 0
        else:
            return 1
            
    def isValidAllTheTime(self, times):
        if times[1] < self.start or times[0] > self.end:
            return 0
        else:
            return 1

    def hasPassed(self, times):
        if times[0] > self.end:
            return 1
        else:
            return 0

class ScalarCondition(Conditions):
    def __init__(self, row):
        super().__init__(row)
        self.value = row[4]

    def isFeasible(self, limit, value):
        if int(value) > int(limit):
            return True
        else:
            return False

class BooleanCondition(Conditions):
    def __init__(self, row):
        super().__init__(row)

    def isFeasible(self, limit, value):
        return True

class WindCondition(Conditions):
    def __init__(self, row):
        super().__init__(row)
        self.value = row[4]

    def isFeasible(self, limit, value):
        tailLimit = limit[0]
        xLimit = limit[1]
        runwayHeading  = limit[2]
        if value[0:3] == 'VRB':
            if int(value[3:5]) < tailLimit:
                return True
            else:
                return False
        else:
            xrossWind =  sin((runwayHeading - int(value[0:3]))/180*pi) * int(value[3:5])
            tailWind = -1 * cos((runwayHeading - int(value[0:3]))/180*pi) * int(value[3:5])
            if xrossWind < xLimit and tailWind < tailLimit: 
                return True
            else:
                return False

class Flight():
    def __init__(self, airports, parameters, arg0, arg1, arg2):
        for p in parameters:
            setattr(self, p, parameters[p])

        currentTime = datetime.now()
        
        departureTimeValue = int(arg0[4:6]) * 3600 + int(arg0[6:8]) * 60 + self.taxiTime
        self.departureTime =  datetime(currentTime.year, currentTime.month, currentTime.day).timestamp() + departureTimeValue
        if departureTimeValue < (currentTime.hour * 3600 + currentTime.minute * 60):
            self.departureTime = self.departureTime + 24*60*60
        
        self.arrivalTime = self.departureTime + int(arg1[4:6]) * 3600 + int(arg1[6:8]) * 60 + self.approachTime

        self.departureAirport = airports.getAirport(arg0[0:4])
        self.destinationAirport = airports.getAirport(arg1[0:4])
        
        if len(arg2) >= 4:
            self.alternateAirport = airports.getAirport(arg2[0:4])
        else:
            self.alternateAirport = None
        
        if len(arg2) == 8:
            self.alternateArrivalTime = self.arrivalTime + int(arg2[4:6]) * 3600 + int(arg2[6:8]) * 60 + self.approachTime
        else:
            self.alternateArrivalTime = None
        
        self.departure = 0
        self.toAlt = 0
        self.destination = 0
        self.alt1 = 0
        self.alt2 = 0

    def solve(self, airports):
        # TO
        self.departure = Operation(self.departureAirport, self.departureTime)  
        self.departure.toMinimumsWithoutAlt(self)      
        if not(self.departure.feasibleAP):
            print('Departure airport not feasible!')
            #self.departure.printTO('Take-off')
        elif not(self.departure.feasibleWx):
            self.departure.toMinimumsWithAlt(self) # 400m if CLL, 500m otherwise
            if not(self.departure.feasibleWx):
                print('Weather not suitable for departure!')
            self.departure.printTO('Take-off')
            
            self.toAlt = airports.findToAlt(self)
            if self.toAlt == 0:
                print('No suitable takeoff alternate found!')
            else:
                self.toAlt.print('Take-off alternate')
        else:
            self.departure.printTO('Take-off')

        # DEST
        self.destination = Operation(self.destinationAirport, self.arrivalTime) 
        
        self.destination.destMinimums(self)
        if not(self.destination.feasibleAP):
            print('Destination airport not feasible!')
        self.destination.print('Destination')
        destName = self.destination.airport.name
        # ALT1
        self.alt1 = airports.findAlt(self, not(self.destination.opsMinimums.approach.groundEquipment), (destName,))
        if self.alt1 == 0:
            print('No suitable alternate found!')
        else:
            self.alt1.print('Alternate 1')
        
        # ALT2
        if not(self.destination.feasibleWx):
            if self.alt1 == 0:
                alt1Name = ''
            else:
                alt1Name = self.alt1.airport.name
            self.alt2 = airports.findAlt(self, 0, (alt1Name, destName))
            if self.alt2 == 0:
                print('No suitable 2nd alternate found!')
            else:
                self.alt2.print('Alternate 2')

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
            
    def addRunway(self, RunwayDataFile):
        # Open csv
        ifile  = open(RunwayDataFile)
        read = csv.reader(ifile)
        
        # Add runway
        current_airport = ""
        for row in read:  
            if len(row[0]) == 4:
                if row[0] != current_airport:
                    current_airport = self.getAirport(row[0])         
                current_airport.addRunway(row)

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
    
    def addData(self, dataFile):
        # Open csv
        ifile  = open(dataFile)
        read = csv.reader(ifile)
        
        # Add runway
        current_airport = ''
        for row in read:  
            if len(row[0]) == 4:
                if row[0] != current_airport:
                    current_airport = self.getAirport(row[0])         
                current_airport.addData(row)

    def getAirport(self, name):
        destination = 'None'
        for airport in self.airport:
            if airport.name == name:
                destination = airport
                break
        return destination
    
    def findToAlt(self, flight):
        # Find first slot, where ats is open (+-30') (max delay 1h)
        # Find first slot, where wx is feasible (+-1h) (max delay 1h)
        bestArrivalTime = flight.arrivalTime + 48*3600
        bestToAlt = 0

        for airport in self.airport:
            arrivalTime = airport.getFlightTime(flight, flight.departureAirport, flight.OEIXCSpeed)
            if arrivalTime < bestArrivalTime:
                alt = Operation(airport, arrivalTime)
                if alt.feasibleAP and alt.feasibleAts:
                    alt.toAltMinimums(flight)
                    if alt.planMinimums != 0:
                        bestAlt = alt
                        bestArrivalTime = arrivalTime
                
        return bestToAlt

    def findAlt(self, flight, groundEq, noGo = None):
        # Find first slot, where ats is open (+-30') (max delay 1h)
        # Find first slot, where wx is feasible (+-1h) (max delay 1h)
        bestArrivalTime = flight.arrivalTime + 48*3600
        bestAlt = 0

        if flight.alternateAirport is None:
            airport_list = self.airport
        else:
            airport_list = (flight.alternateAirport,)

        for airport in airport_list:
            if not(airport.name in noGo):
                if flight.alternateArrivalTime is None:
                    arrivalTime = flight.arrivalTime + airport.getFlightTime(flight, flight.destinationAirport, flight.XCSpeed)
                else:
                    arrivalTime = flight.alternateArrivalTime
                if arrivalTime < bestArrivalTime:
                    alt = Operation(airport, arrivalTime)
                    if alt.feasibleAP and alt.feasibleAts:
                        alt.altMinimums(flight, groundEq)
                        if alt.planMinimums != 0:
                            bestAlt = alt
                            bestArrivalTime = arrivalTime

                
        return bestAlt

class Airport():
    def __init__(self, name, latitude, longitude):
        self.name = name
        self.latitude = float(latitude) / 360 * 2 * pi
        self.longitude = float(longitude) / 360 * 2 * pi

        self.runway = list() 
        #self.conditions = list()

        self.wind = list()
        self.day = list()
        self.ats = list()
        self.visibility = list()
        self.cloudbase = list()
        self.wx = list()
 
    def getFlightTime(self, flight, origin, speed):
        if self.name == origin.name:
            self.distanceFromDest = 0
        else:
            self.distanceFromDest = 3440 * acos(sin(self.latitude)*sin(origin.latitude)+cos(self.latitude)*cos(origin.latitude)*cos(self.longitude-origin.longitude))

        timeFromDest = (self.distanceFromDest / speed) * 3600 + flight.sidTime + flight.approachTime
        return timeFromDest

    def addRunway(self, row):
        self.runway.append(Runway(row))

    def addApproach(self, row):
        # Add approaches
        for runway in self.runway:  
            if runway.name == row[1]:
                runway.addApproach(row)

    def addData(self, row):
        if row[3] == 'atsOpen':
            self.ats.append(BooleanCondition(row))
        elif row[3] == 'Day':
            self.day.append(BooleanCondition(row))
        elif row[3] == 'Wind':
            self.wind.append(WindCondition(row))
        elif row[3] == 'Visibility':
            self.visibility.append(ScalarCondition(row))
        elif row[3] == 'Cloudbase':
            self.cloudbase.append(ScalarCondition(row))
        else:
            self.wx.append(BooleanCondition(row))

    def getMinimums(self, requirements, preferences, times):
        '''
        Returns Minimums object
        '''
        bestMinimums = Minimums()
        for runway in self.runway:
            if self.feasibleWind(runway, times):
                for approach in runway.approach:
                    visibility_type = approach.visibility[0]
                    visibility_value = int(approach.visibility[1:])
                    if ('NPA' in requirements) and approach.type != 'NPA':
                        continue

                    if ('CIRCLE' in requirements) and approach.type != 'CIRCLE':
                        continue

                    if ('groundEq' in requirements) and approach.groundEquipment == 0:
                        continue
                    
                    if ('worseMinimums' in requirements):
                        min_visibility = visibility_type + str(visibility_value + 1000)
                        min_cloudbase = str(int(approach.cloudbase) + 200)
                        cMinimums = Minimums(approach, min_visibility,  min_cloudbase)
                    elif ('feasibleVisibilityOEI' in requirements):
                        min_visibility = visibility_type + str(max(visibility_value, 800))
                        cMinimums = Minimums(approach, min_visibility, approach.cloudbase)
                    else:
                        if runway.RCLL and runway.RTZL:
                            min_visibility = approach.visibility
                        else:
                            min_visibility = visibility_type + str(max(visibility_value, 600))

                        cMinimums = Minimums(approach, min_visibility, approach.cloudbase)
                    
                    self.feasibleVisibility(cMinimums, times, runway)
                    self.feasibleCloudbase(cMinimums, times)


                    if ('feasibleVis' in requirements) and not(cMinimums.feasibleVisibility):
                        continue
            
                    if ('feasibleCloudbase' in requirements) and not(cMinimums.feasibleCloudbase):
                        continue

                    if ('feasibleVisibilityOEI' in requirements) and not(cMinimums.feasibleVisibility):
                        continue

                    if bestMinimums.approach == '':
                        bestMinimums = cMinimums
                    elif ('feasibleVis' in preferences) and cMinimums.feasibleVisibility and not(bestMinimums.feasibleVisibility):
                        bestMinimums = cMinimums
                    elif ('feasibleCloudbase' in preferences) and cMinimums.feasibleCloudbase and not(bestMinimums.feasibleCloudbase):
                        bestMinimums = cMinimums
                    elif ('Type' in preferences) and cMinimums.hasHigherCat(bestMinimums):
                        bestMinimums = cMinimums
                    elif ('OpsMin' in preferences) and (int(cMinimums.visibility[1:]) < int(bestMinimums.visibility[1:])):
                        bestMinimums = cMinimums
        return bestMinimums

    def getToMinimums(self, times):
        '''
        Returns Minimums object
        '''
        # Check iff cll, in feasible runway
        minimums = Minimums()
        
        for runway in self.runway:
            if self.feasibleWind(runway, times):
                if runway.RCLL:
                    visibility = 'R400'
                elif self.isDay(times):
                    visibility = 'R500'
                else:
                    visibility = 'R500'
                
                if int(visibility[1:]) < int(minimums.visibility[1:]):
                    minimums.visibility = visibility
                    best_runway = runway

        self.feasibleVisibility(minimums, times, best_runway)
        self.feasibleCloudbase(minimums, times)
        
        return minimums

    def feasibleVisibility(self, minimums, times, runway):
        # Take account converted visibility in minimums of approach
        visibility_type = minimums.visibility[0]
        visibility_value = int(minimums.visibility[1:])
        
        if visibility_type == 'R':
            if visibility_value >= 800:
                if self.isNight(times):
                    if runway.HIALS:
                        visibility_value = visibility_value / 2
                    else:
                        visibility_value = visibility_value / 1.5
                else:
                    if runway.HIALS:
                        visibility_value = visibility_value / 1.5

        # if high intensity lights (installed, ats open)
        value = self.feasibleCondition('visibility', visibility_value, times)
        minimums.setFeasibleVisibility(value) 

    def feasibleCloudbase(self, minimums, times):
        value = self.feasibleCondition('cloudbase', minimums.cloudbase, times)
        minimums.setFeasibleCloudbase(value)

    def feasibleCondition(self, attr, limit, times):    
        if len(getattr(self, attr)) <= 1 and attr != 'wx':
            return 0
        
        for cond in getattr(self, attr): 
            # Check if condition is relevant by type
            if cond.type == 'PROB' and cond.type == 'PROB TEMPO':
                continue
            elif cond.type == 'TEMPO':
                if cond.isValidAnyMoment(times):
                    if not(cond.isFeasible(limit, cond.value)):
                        print('HOX: TEMPO group')
            elif cond.type == 'BECMG':
                if cond.hasPassed(times):
                    value = cond.value
                elif cond.isValidAnyMoment(times):
                    if not(cond.isFeasible(limit, value)):
                        return False
                    value = cond.value
                    if not(cond.isFeasible(limit, value)):
                        return False
            else:
                if cond.isValidAnyMoment(times):
                    value = cond.value
                    if not(cond.isFeasible(limit, value)):
                        return False
                    
        return True

    def feasibleWx(self, times):
        return self.feasibleCondition('wx', False, times) 
    
    def feasibleWind(self, runway, times):
        limit = (10, 20, runway.heading)
        return self.feasibleCondition('wind', limit, times) 
    
    def isDay(self, times):
        for cond in self.day: 
            if cond.isValidAllTheTime(times):
                return True
        return False

    def isNight(self, times):
        for cond in self.day: 
            if cond.isValidAllTheTime(times):
                return True
        return False

    def atsOpen(self, times):
        for cond in self.ats: 
            if cond.isValidAllTheTime(times):
                return True
        return False

class Runway():
    def __init__(self, row):
        self.name = row[1]
        self.heading = int(row[2])
        self.RTZL = int(row[3])
        self.RCLL = int(row[4])
        self.HIALS = int(row[5])
        self.REDL = int(row[6])
        self.CL_MARK = int(row[7])
        self.approach = list()

    def addApproach(self, row):
        self.approach.append(Approach(row))

class Approach():
    def __init__(self, row):
        self.ID = row[2]
        self.groundEquipment = int(row[3])
        self.type = row[4]
        self.cloudbase = row[5]
        self.visibility = row[6]

class Minimums():
    def __init__(self, approach = '', visibility = 'V9999', cloudbase = 5000):
        self.approach = approach
        self.visibility = visibility
        self.cloudbase = cloudbase

        self.feasibleVisibility = 0
        self.feasibleCloudbase = 0
    
    def plan2ops(self):
        minimums = self
        if self.approach.type == 'CAT1':
            minimums.cloudbase = 0
        return minimums

    def hasHigherCat(self, anotherMinimums):
        if self.approach.type == 'CAT1' and anotherMinimums.approach.type != 'CAT1':
            return 1
        elif self.approach.type == 'NPA' and anotherMinimums.approach.type == 'CIRCLE':
            return 1
        else:
            return 0

    def setFeasibleVisibility(self, value):
        self.feasibleVisibility = value

    def setFeasibleCloudbase(self, value):
        self.feasibleCloudbase = value

class Operation():
    def __init__(self, airport, time):
        self.airport = airport
        self.time = time
        
        self.isDay = airport.isDay([self.time, self.time + 1800])
        self.feasibleAts = airport.atsOpen([self.time, self.time + 1800])
        self.feasibleAP = self.isDay or self.feasibleAts
        self.feasibleWx = False
        
        self.opsMinimums = 0
        self.planMinimums = 0

    def toMinimumsWithAlt(self, flight):
        self.opsMinimums = self.airport.getToMinimums([self.time, self.time + 5 * 60])
        self.feasibleWx = self.airport.feasibleWx([self.time, self.time + 5*60]) * self.opsMinimums.feasibleVisibility

    def toMinimumsWithoutAlt(self, flight):
        requirements = ['feasibleVisibilityOEI']
        preferences = ['visibility']
        self.opsMinimums = self.airport.getMinimums(requirements, preferences, [self.time,self.time + 5*60])
        self.feasibleWx = self.airport.feasibleWx([self.time, self.time + 5*60]) * self.opsMinimums.feasibleVisibility

    def destMinimums(self, flight):
        requirements = []
        preferences = ['feasibleVis','feasibleCloudbase', 'groundEq', 'opsMin']

        self.planMinimums = self.airport.getMinimums(requirements, preferences, [self.time - 3600, self.time + 3600])
        self.opsMinimums = self.planMinimums.plan2ops()
        self.feasibleWx = self.airport.feasibleWx([self.time - 3600, self.time + 3600]) * self.opsMinimums.feasibleVisibility * self.planMinimums.feasibleVisibility * self.planMinimums.feasibleCloudbase

    def altMinimums(self, flight, groundEq):
        preferences = ['OpsMin', 'type']
        requirements = ['feasibleVis']
        if groundEq == 1:   
            requirements.append('groundEq')
        self.opsMinimums = self.airport.getMinimums(requirements, preferences, [self.time - 3600, self.time + 3600])
        if self.opsMinimums.approach == '':
            return

        preferences = ['OpsMin']
        requirements = ['feasibleVis','feasibleCloudbase']
        opsApproachType = self.opsMinimums.approach.type
        if opsApproachType == 'CAT1':
            requirements.append('NPA')
        elif opsApproachType == 'NPA':
            requirements.append('NPA')
            requirements.append('worseMinimums')

        elif opsApproachType == 'CIRCLE':
            requirements.append('CIRCLE')
        self.planMinimums = self.airport.getMinimums(requirements, preferences, [self.time - 3600, self.time + 3600])
        self.feasibleWx = self.airport.feasibleWx([self.time - 3600, self.time + 3600]) * self.opsMinimums.feasibleVisibility * self.planMinimums.feasibleVisibility * self.planMinimums.feasibleCloudbase

    def toAltMinimums(self, flight):
        preferences = ['opsMin']
        requirements = ['feasibleVisibilityOEI', 'feasibleCloudbase', 'groundEq']
        self.planMinimums = self.airport.getMinimums(requirements, preferences, [self.time - 3600, self.time + 3600])
        self.opsMinimums = self.planMinimums.plan2ops()
        self.feasibleWx = self.airport.feasibleWx([self.time - 3600, self.time + 3600]) * self.opsMinimums.feasibleVisibility * self.planMinimums.feasibleVisibility * self.planMinimums.feasibleCloudbase

    def print(self, title):
        time = datetime.fromtimestamp(self.time)
        print('\n')
        print(title, ': ', self.airport.name, ' ', time.hour, time.minute,'Z')
        if self.planMinimums.approach.type == 'CAT1':
            cloudbase = '-'
        else:
            cloudbase = self.planMinimums.approach.cloudbase
        print('Plan:', self.planMinimums.approach.ID, ' ', self.planMinimums.visibility[1:], 'm /', cloudbase, 'ft')
        print('Ops: ', self.opsMinimums.approach.ID, ' ', self.opsMinimums.visibility[1:], 'm / - ft')

    def printTO(self, title):
        print(title, ': ', self.airport.name)
        print('Ops: ', self.opsMinimums.visibility[1:], 'm / - ft')

def main(ApproachDataFile, RunwayDataFile, AirportDataFile, OprHrDataFile, TafDataFile, MetarDataFile, CivilTwilightDataFile, parameters, arg0, arg1, arg2):
    # Read airport data 
    airports = Airports(AirportDataFile)
    
    # Read runway data
    airports.addRunway(RunwayDataFile)
    
    # Read approach data 
    airports.addApproach(ApproachDataFile)

    # Read opr hr data
    airports.addData(OprHrDataFile)
    
    # Read TAF data
    airports.addData(TafDataFile)

    # Read METAR data
    airports.addData(MetarDataFile)
    
    # Read day-night data
    airports.addData(CivilTwilightDataFile)

    # Create flight
    flight = Flight(airports, parameters, arg0, arg1, arg2)
    
    # Solve and print solution
    flight.solve(airports)

if __name__ == '__main__':
    dof = date.today()
    timestamp = datetime.now().timestamp()

    ApproachDataFile = 'ApproachData.csv'
    RunwayDataFile = 'RunwayData.csv'
    AirportDataFile = 'AirportData.csv'
    
    # Scrape ats opening hours if current file is old
    OprHrDataFile = 'OprHrData.csv'
    time_from_edit = timestamp - os.path.getctime(OprHrDataFile)
    if time_from_edit > 12*3600:
        url = 'https://www.ais.fi/ais/bulletins/efinen.htm'
        OprHrData(url, dof).createCsv(OprHrDataFile)

    # Scrape TAF and METAR if current file is old
    TafDataFile = 'TafData.csv'
    MetarDataFile = 'MetarData.csv'
    time_from_edit = timestamp - os.path.getctime(TafDataFile)
    if time_from_edit > 30*60:
        url = 'https://api.met.no/weatherapi/tafmetar/1.0/taf.txt?icao='
        TafData(url, AirportDataFile).createCsv(TafDataFile)
        url = 'https://api.met.no/weatherapi/tafmetar/1.0/metar.txt?icao='
        MetarData(url, AirportDataFile).createCsv(MetarDataFile)

    # Scrape day/night data if current file is old
    CivilTwilightDataFile = 'CivilTwilightData.csv'
    time_from_edit = timestamp - os.path.getctime(CivilTwilightDataFile)
    if time_from_edit > 12*3600:
        url = 'http://api.sunrise-sunset.org/json?formatted=0'
        TwilightData(dof, url, AirportDataFile).createCsv(CivilTwilightDataFile)

    # Collect parameters to dict
    parameters = {'maxTailwind': 10, 'maxCrosswind': 20, 'minRVR': 600, 'OEIminRVR': 800, 'OEIXCSpeed': 120, 'XCSpeed': 140, 'taxiTime': 10 * 60, 'approachTime': 10 * 60, 'sidTime': 2 * 60}
    #rules to add: ats_buffer, night_buffer, wx_buffer, toRVRcll, toRVR
    arg0 = "EFTP2000" # 
    arg1 = "EFTU0030" #
    arg2 = "" #optio: varakenttä ja aika

    main(ApproachDataFile, RunwayDataFile, AirportDataFile, OprHrDataFile, TafDataFile, MetarDataFile, CivilTwilightDataFile, parameters, arg0, arg1, arg2)
