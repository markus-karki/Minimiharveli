import csv
from datetime import date, datetime
from urllib.request import urlopen

class WeatherData():
    def __init__(self, url, AirportDataFile):
        self.url = url
        self.airports = list()
        self.addAirports(AirportDataFile)

    def addAirports(self, AirportDataFile):
        # Open csv
        ifile  = open(AirportDataFile)
        read = csv.reader(ifile)
        
        # Add airports
        for row in read :  
            if len(row[0])==4:
                self.airports.append(row[0])
        
        ifile.close()

    def createCsv(self, fileName):
        f = open(fileName, 'w')
        self.writer = csv.writer(f)
        self.writer.writerow(['Airport', 'Start', 'End', 'Data', 'Value', 'Type'])
        self.readData()
        f.close()

    def readData(self):
        # Get data from Avinor
        url = self.url
        for airport in self.airports:
            url = url + airport + ","
        
        file = urlopen(url)
        new_line = '\n'
        for line in file:
            old_line = new_line
            new_line = line.decode("utf-8")
            if (old_line[0:4] != new_line[0:4]) and (old_line != '\n'):
                airport = old_line[0:4]
                self.data2lines(old_line, airport)
                # setattr(airport,data,old_line)

    def writeLine(self, airport, startTime, endTime, datatype, data, value):
        self.writer.writerow([airport, int(startTime), int(endTime), data, value, datatype])

class TafData(WeatherData):
    def __init__(self, url, AirportDataFile):
        super().__init__(url, AirportDataFile)
    
    def data2lines(self, line, airport):
        TAF = line.split()
        year = datetime.now().year
        month = datetime.now().month
        groupType = 'TAF'
        probTempo = 0

        for group in TAF:
            if 'KT' in group[5:]:
                self.writeLine(airport, startTime, endTime, groupType, 'Wind', group[0:5])
            elif (len(group) == 4) and group.isdigit():
                self.writeLine(airport, startTime, endTime, groupType, 'Visibility', int(group))
            elif group[0:3] == 'OVC' or group[0:3] == 'BKN':
                self.writeLine(airport, startTime, endTime, groupType, 'Cloudbase', int(group[3:6]) * 100)
            elif group[0:3] == 'SCT' or group[0:3] == 'FEW':
                self.writeLine(airport, startTime, endTime, groupType, 'Cloudbase',  5000)
            elif group[0:2] == 'VV':
                self.writeLine(airport, startTime, endTime, groupType, 'Cloudbase', int(group[2:5]) * 100)
            elif group == 'TEMPO': 
                if probTempo:
                    groupType = 'PROB TEMPO'
                else:
                    groupType = 'TEMPO'
            elif group[0:4] == 'PROB':
                groupType = 'PROB'
                probTempo = 1
            elif group[0:5] == 'BECMG':
                groupType = 'BECMG'                
            #elif group[0:2] == 'FM':
            #    wx.groupType = 'NORM'
            #elif group[0:2] == 'TL':
            #    wx.weather = nextWeather.addTL()
            #elif group[0:2] == 'AT':
            #    wx.weather = weather.addAT()
            elif group[0:5] == 'CAVOK' or group[0:3] == 'SKC' or group[0:3] == 'NSC':
                self.writeLine(airport, startTime, endTime, groupType, 'Visibility', 9999)
                self.writeLine(airport, startTime, endTime, groupType, 'Cloudbase', 5000)
            elif 'FZ' in group:
                self.writeLine(airport, startTime, endTime, groupType, 'FZ', True)
            elif 'TS' in group:
                self.writeLine(airport, startTime, endTime, groupType, 'TS', True)
            elif len(group)>4:
                if group[4] == '/':
                    startTime = datetime(year, month, int(group[0:2])).timestamp() + int(group[2:4]) * 3600
                    if int(group[0:2]) > int(group[5:7]):
                        endTime = datetime(year, month + 1, int(group[5:7])).timestamp() + int(group[7:9]) * 3600
                    else: 
                        endTime = datetime(year, month, int(group[5:7])).timestamp() + int(group[7:9]) * 3600
                    probTempo = 0

class MetarData(WeatherData):
    def __init__(self, url, AirportDataFile):
        super().__init__(url, AirportDataFile)

    def data2lines(self, line, airport):
        METAR = line.split()
        year = datetime.now().year
        month = datetime.now().month
        groupType = 'METAR'

        for group in METAR:
            if 'KT' in group[5:]:
                self.writeLine(airport, startTime, endTime, groupType, 'Wind', group[0:5])
            elif (len(group) == 4) and group.isdigit():
                self.writeLine(airport, startTime, endTime, groupType, 'Visibility', int(group))
            elif group[0:3] == 'OVC' or group[0:3] == 'BKN':
                self.writeLine(airport, startTime, endTime, groupType, 'Cloudbase', int(group[3:6]) * 100)
            elif group[0:3] == 'SCT' or group[0:3] == 'FEW':
                self.writeLine(airport, startTime, endTime, groupType, 'Cloudbase', 5000)
            elif group[0:2] == 'VV':
                self.writeLine(airport, startTime, endTime, groupType, 'Cloudbase', int(group[2:5]) * 100)
            elif group[0:5] == 'CAVOK' or group[0:3] == 'SKC' or group[0:3] == 'NSC':
                self.writeLine(airport, startTime, endTime, groupType, 'Visibility', 9999)
                self.writeLine(airport, startTime, endTime, groupType, 'Cloudbase', 5000)
            elif 'FZ' in group:
                self.writeLine(airport, startTime, endTime, groupType, 'FZ', 'True')
            elif 'TS' in group:
                self.writeLine(airport, startTime, endTime, groupType, 'TS', 'True')
            elif group[0] == 'R' and ('/' in group):
                pass
                #self.writeLine(airport, startTime, endTime, groupType, 'RVR', group[1:])
            elif len(group) == 7 and group[-1] == 'Z':
                    startTime = datetime(year, month, int(group[0:2])).timestamp() + int(group[2:4]) * 3600 + int(group[4:6]) * 60 - 3600
                    endTime = startTime + 3600

'''
dof = date.today()
TAF_url = 'https://api.met.no/weatherapi/tafmetar/1.0/taf.txt?icao='
METAR_url = 'https://api.met.no/weatherapi/tafmetar/1.0/metar.txt?icao='
TafDataFile = 'TafData.csv'
AirportDataFile = 'AirportData.csv'
MetarDataFile = 'MetarData.csv'

TafData(TAF_url, AirportDataFile).createCsv(TafDataFile)
MetarData(METAR_url, AirportDataFile).createCsv(MetarDataFile)
'''