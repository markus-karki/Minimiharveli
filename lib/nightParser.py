
import csv
import json
from datetime import date, datetime
import requests 

class TwilightData():
    def __init__(self, dof, url, AirportDataFile):
        self.url = url
        self.dof = dof
        self.AirportDataFile = AirportDataFile

    def addAirports(self):
        # Open csv
        ifile  = open(self.AirportDataFile)
        read = csv.reader(ifile)
        
        # Add airports
        for row in read :  
            if len(row[0])==4:
                airport = row[0]
                lat = row[1]
                lon = row[2] 
                url = self.url + '&lat=' + str(lat) + '&lng=' + str(lon) + '&date=' + str(self.dof.year) + '-' + str(self.dof.month) + '-' + str(self.dof.day)
                data = requests.get(url).json()
                dayStart = data['results']['civil_twilight_begin']
                dayEnd = data['results']['civil_twilight_end']
                self.writeLine(airport, dayStart, dayEnd)
        
        ifile.close()

    def createCsv(self, fileName):
        f = open(fileName, 'w')
        self.writer = csv.writer(f)
        self.writer.writerow(['Airport', 'Start', 'End', 'Data'])
        self.addAirports()
        f.close()
    
    def writeLine(self, airport, startTime, endTime):
        self.writer.writerow([airport, self.str2datetime(startTime), self.str2datetime(endTime), 'Day'])

    def str2datetime(self, str):
        return int(datetime(int(str[0:4]), int(str[5:7]), int(str[8:10]),int(str[11:13]), int(str[14:16])).timestamp())

'''
AirportDataFile = 'AirportData.csv'
night_url = 'http://api.sunrise-sunset.org/json?formatted=0'

dof = date.today()
CivilTwilightDataFile = 'CivilTwilightData.csv'
TwilightData(dof, night_url, AirportDataFile).createCsv(CivilTwilightDataFile)
'''