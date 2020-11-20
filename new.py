from datetime import datetime, time, date
from math import cos, sin, acos, pi
from numpy import zeros, append, where, nditer
import csv

# Step 1: Redesign optimization to loop-search, w48 
# Step 7: Publish as flask app via AWS w49

class Conditions():
    def __init__(self, row):
        self.start = row[1]
        self.end = row[2]
        self.data = row[3]
        
        if len(row) >= 4:
            self.type = row[4]
        
    def isValidAnyMoment(self, times):
        if time[0] > self.end or time[1] < self.start:
            return 0
        else:
            return 1
            
    def isValidAllTheTime(self, times):
        if time[0] >= self.start or time[1] <= self.end:
            return 0
        else:
            return 1

    def hasPassed(self, times):
        if time[0] > self.end:
            return 1
        else:
            return 0

class ScalarCondition(Conditions):
    def __init__(self, row):
        super().__init__(row)
        self.value = row[5]

    def isFeasible(limit, value):
        if value > limit:
            return False
        else:
            return True

class BooleanCondition(Conditions):
    def __init__(self, row):
        super().__init__(row)

    def isFeasible(limit, value):
        return True

class WindCondition(Conditions):
    def __init__(self, row):
        super().__init__(row)
        self.value = row[5]

    def isFeasible(limit, value):
        tailLimit = limit[0]
        xLimit = limit[1]
        runwayHeadin  = limit[2]
        if wind[0:3] == 'VRB':
            if int(wind[3:5]) < tailLimit:
                return True
            else:
                return False
        else:
            xrossWind =  sin((runwayHeading - int(wind[0:3]))/180*pi) * int(wind[3:5])
            tailWind = -1 * cos((runwayHeading - int(wind[0:3]))/180*pi) * int(wind[3:5])
            if xrossWind < xLimit and tailWind < tailLimit: 
                return True
            else:
                return False

class Flight():
    def __init__(self, airports, parameters, arg0, arg1):
        for p in parameters:
            setattr(self, p, parameters[p])

        currentTime = datetime.now()
        
        departureTimeValue = int(arg0[4:6]) * 3600 + int(arg0[6:8]) * 60 + self.taxiTime
        self.departureTime =  datetime(currentTime.year, currentTime.month, currentTime.day).timestamp() + departureTimeValue
        if departureTimeValue < (currentTime.hour * 3600 + currentTime.minute * 60):
            self.departureTime = self.departureTime + 24*60*60
        
        self.arrivalTime = self.departureTime + int(arg1[4:6]) * 3600 + int(arg1[6:8]) * 60 + self.approachtTime

        self.departureAirport = airports.getAirport(arg0[0:4])
        self.destinationAirport = airports.getAirport(arg1[0:4])

        self.departure = 0
        self.toAlt = 0
        self.destination = 0
        self.alt1 = 0
        self.alt2 = 0

    def solve(self, airports):
        # TO
        '''
        self.departure = Operation(self.departureAirport, self.departureTime)  
        
        self.departure.toMinimumsWithoutAlt(self)      
        if not(self.departure.feasibleAP):
            print('Departure airport not feasible!')
            self.departure.print('Take-off')
        else not(self.departure.opsMinimums.feasibleWx):
            self.departure.toMinimumsWithAlt(self) # 400m if CLL, 500m otherwise
            if not(self.departure.opsMinimums.feasibleWx):
                print('Weather not suitable for departure!')
            self.departure.print('Take-off')
            
            self.toAlt = airports.findToAlt(self)
            if self.toAlt == 0:
                print('No suitable takeoff alternate found!')
            else:
                self.toAlt.print('Take-off alternate')
        '''

        # DEST
        self.destination = Operation(self.destinationAirport, self.arrivalTime) 
        
        self.destination.destMinimums(self)
        if not(self.departure.feasibleAP):
            print('Destination airport not feasible!')
        self.departure.print('Destination')

        # ALT1
        self.alt1 = airports.findAlt(self, not(self.destination.opsMinimums.approach.groundEq))
        if self.alt1 == 0:
            print('No suitable alternate found!')
        else:
            self.alt1.print('Alternate 1')
        
        # ALT2
        if not(self.destination.planMinimums.feasibleWx):
            
            self.alt2 = airports.findALT(self, 0, self.alt1.airport.name)
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
    
    def findToAlt(self, flight, groundEq):
        # Find first slot, where ats is open (+-30') (max delay 1h)
        # Find first slot, where wx is feasible (+-1h) (max delay 1h)
        bestMinimums = Minimums(flight.departureTime + 48*3600)

        for airport in self.airport:
            arrivalTime = airport.getFlightTime(flight, flight.departureAirport, flight.OEIXCSpeed)
            if arrivalTime < bestMinimums.time:
                minimums = airport.toAltMinimums(flight, arrivalTime)
                if minimums.isFeasible and minimums.objective < bestMinimums.objective:
                    bestMinimums = minimums
                
        return bestMinimums

    def findAlt(self, flight, groundEq, noGo = None):
        # Find first slot, where ats is open (+-30') (max delay 1h)
        # Find first slot, where wx is feasible (+-1h) (max delay 1h)
        bestArrivalTime = flight.arrivalTime + 48*3600
        bestAlt = 0

        for airport in self.airport:
            if airport.name != noGo:
                arrivalTime = airport.getFlightTime(flight, flight.destinationAirport, flight.XCSpeed)
                if arrivalTime < bestArrivalTime:
                    alt = Operation(airport, arrivalTime)
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

        timeFromDest = (self.distanceFromDest / speed) * 3600 + flight.sidTime + flight.approachtTime
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
        elif row[4] == 'Wind':
            self.wind.append(WindCondition(row))
        elif row[4] == 'Visibility':
            self.visibility.append(ScalarCondition(row))
        elif row[4] == 'Cloudbase':
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

                    if ('NPA' in requirements) and approach.type != 'NPA':
                        continue

                    if ('CIRCLE' in requirements) and approach.type != 'CIRCLE':
                        continue

                    if ('groundEq' in requirements) and approach.groudEquipment == 0:
                        continue
                    
                    if ('worseMinimums' in requirements):
                        cMinimums = Minimums(approach, approach.visibility + 1000, approach.cloudbase + 200)
                    elif ('feasibleVisibilityOEI' in requirements):
                        cMinimums = Minimums(approach, max(approach.visibility, 800), approach.cloudbase)
                    else:
                        cMinimums = Minimums(approach, approach.visibility, approach.cloudbase)
                    
                    self.feasibleVisibility(cMinimums, times)
                    self.feasibleCloudbase(cMinimums, times)


                    if ('feasibleVis' in requirements) and cMinimums.feasibleVisibility:
                        continue
            
                    if ('feasibleCloudbase' in requirements) and cMinimums.feasibleCloudbase:
                        continue

                    if bestMinimums.approach == 0:
                        bestMinimums = cMinimums
                    elif ('feasibleVis' in preferences) and cMinimums.feasibleVisibility and not(bestMinimums.feasibleVisibility):
                        bestMinimums = cMinimums
                    elif ('feasibleCloudbase' in preferences) and cMinimums.feasibleCloudbase and not(bestMinimums.feasibleCloudbase):
                        bestMinimums = cMinimums
                    elif ('Type' in preferences) and cMinimums.hasHigherCat(bestMinimums):
                        bestMinimums = cMinimums
                    elif ('OpsMin' in preferences) and (cMinimums.visibility < bestMinimums.visibility):
                        bestMinimums = cMinimums
        return bestMinimums

    def getToMinimums(self, time):
        '''
        Returns Minimums object
        '''
        # Check iff cll, in feasible runway
        minimums = Minimums()
        
        for runway in self.runway:
            if runway.isFeasible(time):
                if runway.hasCLL():
                    visibility = 400
                elif self.isDay(time):
                    visibility = 500
                else:
                    visibility = 500
                
                if visibility < minimums.visibility:
                    minimums.visibility = visibility

        
        minimums.checkWeather(self.conditions)
        
        return minimums

    def feasibleVisibility(self, minimums, times, runway):
        # Take account converted visibility in minimums of approach
        if minimums.visibility >= 800:
            if self.isNight(times):
                if runway.HIALS:
                    converted_visibility = minimums.visibility / 2
                else:
                    converted_visibility = minimums.visibility / 1.5
            else:
                if runway.HIALS:
                    converted_visibility = minimums.visibility / 1.5
                else:
                    converted_visibility = minimums.visibility
        else:
            converted_visibility = minimums.visibility

        # if high intensity lights (installed, ats open)
        value = self.feasibleCondition('visibility', converted_visibility, times)
        minimums.setFeasibleVisibility(value) 

    def feasibleCloudbase(self, minimums, times):
        value = self.feasibleCondition('cloudbase', minimums.cloudbase, times)
        minimums.setFeasibleCloudbase(value)

    def feasibleCondition(self, attr, limit, times):    
        if len(getattr(self, attr)) == 0:
            return 0
        
        for cond in getattr(self, attr): 
            # Check if condition is relevant by type
            if cond.type != 'PROB' and cond.type != 'PROB TEMPO':
                continue
            elif cond.type == 'TEMPO':
                if cond.isValidAnyMoment(times):
                    if not(cond.isFeasible(limit, value)):
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

    def isNight(self, times):
        for cond in self.day: 
            if cond.isValidAllTheTime(times):
                return True

    def isActive(self, times, attr):
        for cond in getattr(self, attr): 
            if cond.isValidAllTheTime(times):
                return True

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
        self.groudEquipment = int(row[3])
        self.type = row[4]
        self.cloudbase = row[5]
        self.visibility = row[6]

class Minimums():
    def __init__(self, approach = '', visibility = 9999, cloudbase = 5000):
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
        
        self.isDay = airport.isActive([self.time, self.time + 1800], 'day')
        self.feasibleAts = airport.isActive([self.time, self.time + 1800], 'ats')
        self.feasibleAP = self.isDay or self.feasibleAts
        self.feasibleWx = 0
        
        self.opsMinimums = 0
        self.planMinimums = 0

    def toMinimumsWithAlt(self, flight):
        self.opsMinimums = self.airport.getToMinimums()

    def toMinimumsWithoutAlt(self, flight):
        requirements = ['visibilityOkOEI']
        preferences = ['visibility']
        self.opsMinimums = self.airport.getMinimums(requirements, preferences, [self.time - 3600,self.time + 3600])

    def destMinimums(self, flight):
        requirements = []
        preferences = ['feasibleVis','feasibleCloudbase', 'groundEq', 'opsMin']

        self.planMinimums = self.airport.getMinimums(requirements, preferences, [self.time - 3600, self.time + 3600])
        self.opsMinimums = self.planMinimums.plan2ops()

    def altMinimums(self, flight, groundEq):
        preferences = ['OpsMin', 'type']
        requirements = ['feasibleVis']
        if groundEq == 1:   
            requirement.append('groundEq')
        self.opsMinimums = self.airport.getMinimums(requirements, preferences, [self.time - 3600, self.time + 3600])

        preferences = ['OpsMin']
        requirements = ['feasibleVis','feasibleCloudbase']
        opsApproachType = self.opsMinimums.approach.type
        if opsApproachType == 'CAT1':
            requirement.append('NPA')
        elif opsApproachType == 'NPA':
            requirement.append('NPA')
            requirement.append('worseMinimums')

        elif opsApproachType == 'CIRCLE':
            requirement.append('CIRCLE')
        self.planMinimums = self.airport.getMinimums(requirements, preferences, [self.time - 3600, self.time + 3600])

    def toAltMinimums(self, flight):
        preferences = ['opsMin']
        requirements = ['feasibleVisibilityOEI', 'feasibleCloudbase', 'groundEq']
        self.planMinimums = self.airport.getMinimums(requirements, preferences, [self.time - 3600, self.time + 3600])
        self.opsMinimums = self.planMinimums.plan2ops()

    def print(self, title):
        print('\n')
        print(title, ': ', self.airport.name)
        if self.planMinimums.approach.type == 'CAT1':
            cloudbase = '-'
        else:
            cloudbase = self.planMinimums.approach.cloudbase
        print('Plan:', self.planMinimums.approach.ID, ' ', self.planMinimums.RVR, 'm /', cloudbase, 'ft')
        print('Ops: ', self.opsMinimums.approach.ID, ' ', self.opsMinimums.RVR, 'm / - ft')

def main(ApproachDataFile, RunwayDataFile, AirportDataFile, OprHrDataFile, TafDataFile, MetarDataFile, CivilTwilightDataFile, parameters, arg0, arg1):
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
    flight = Flight(airports, parameters, arg0, arg1)
    
    # Solve and print solution
    flight.solve(airports)

if __name__ == '__main__':
    dof = date.today()

    ApproachDataFile = 'ApproachData.csv'
    RunwayDataFile = 'RunwayData.csv'
    AirportDataFile = 'AirportData.csv'
    OprHrDataFile = 'OprHrData.csv'
    TafDataFile = 'TafData.csv'
    MetarDataFile = 'MetarData.csv'
    CivilTwilightDataFile = 'CivilTwilightData.csv'
    
    parameters = {'maxTailwind': 10, 'maxCrosswind': 20, 'minRVR': 600, 'OEIminRVR': 800, 'OEIXCSpeed': 120, 'XCSpeed': 140, 'taxiTime': 10 * 60, 'approachtTime': 10 * 60, 'sidTime': 2 * 60}
    #rules to add: ats_buffer, night_buffer, wx_buffer, toRVRcll, toRVR
    arg0 = "EFPO1330" # 
    arg1 = "EFPO0045" #
    arg2 = "" #varakenttä / toiminta-aika

    main(ApproachDataFile, RunwayDataFile, AirportDataFile, OprHrDataFile, TafDataFile, MetarDataFile, CivilTwilightDataFile, parameters, arg0, arg1)

# OPS
        # required: feasible wx, 
        # preference: opsMin

# OPS
        # required: feasible wx, 
        # preference: opsMin

# OPS & PLAN
        # required: - 
		# preference: feasible wx, groudEq, opsMin 

# OPS
        # required: groundEq(opt), 
        # preference: cat, ops min 

# Plan
        # required: feasible wx, groundEq(opt), worsening(cat1/npa/circle)
        # preference: ops min 

# OPS & PLAN
        # required: feasible wx, groundEq(opt)?, worsening(0)
        # preference: ops min 

# Requirement_options = {feasibleVis, feasibleCloudbase, groundEq(0/1), worsening(0/cat1/npa/circle)}
# Preference_options = {feasibleVis, feasibleCloudbase, CAT, OpsMin}