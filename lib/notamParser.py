from html.parser import HTMLParser
import csv
from datetime import date, datetime
from urllib.request import urlopen


class NOTAMparser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.dataList = list()

    def handle_data(self, data):
        self.dataList.append(data)

class OprHrData():
    def __init__(self, NOTAM_url, dof):
        self.url = NOTAM_url
        self.dof = dof
    
    def createCsv(self, fileName):
        f = open(fileName, 'w')
        self.writer = csv.writer(f)
        self.writer.writerow(['Airport', 'Start', 'End','Data'])
        self.readNOTAMS()
        f.close()

    def writeLine(self, airport, startTime, endTime):
        self.writer.writerow([airport, int(startTime), int(endTime), 'atsOpen'])
        
    def readNOTAMS(self):
        #Import HTML from a URL
        url = urlopen(self.url)
        html = url.read().decode('latin1')
        url.close()

        p = NOTAMparser()
        p.feed(html)

        print_all = 0
        oprhrdata = 0
        closed = 0
        currentAirport = ''
        currentNOTAM = ''
        for row in p.dataList:    
            if (row[0:2] == 'EF') and len(row)>7:
                    if (row[5] == '-'):
                        if oprhrdata:
                            self.addLines(currentNOTAM, currentAirport)
                        elif closed:
                            pass
                            #self.writeLine(currentAirport,0,0)
                        elif currentAirport != '' and currentAirport != 'EFIN':
                            ctime = datetime(self.dof.year, self.dof.month, self.dof.day).timestamp()
                            self.writeLine(currentAirport,ctime,ctime+48*3600)
                        currentAirport = row[0:4]
                        currentNOTAM = ''
                        oprhrdata = 0
                        closed = 0
            if 'OPR HR' in row:
                print_all = 1
                oprhrdata = 1
            if 'FROM' in row:
                print_all = 0
                currentNOTAM = currentNOTAM + '\n'
            if ('TWR CLSD' in row) or ('AFIS CLSD' in row) or ('AFIS CLOSED' in row):
                closed = 1
            if print_all:
                currentNOTAM = currentNOTAM + row.replace('-','\n').replace(',','')
    
    def addLines(self, NOTAM, AirportName):
        if AirportName == '' or AirportName == 'EFIN':
            return

        if NOTAM == '':
            self.writeLine(AirportName, 0, 1)
            return
        
        NOTAM = NOTAM.split()

        months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
        weekdays = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]

        month = list()
        day = list()
        weekday = list()
        time = list()
        timeMode = 0

        for group in NOTAM:
            if (group in months or group in weekdays) and timeMode == 1:
                    self.add(AirportName, month, weekday, day, time, self.dof)
                    self.add(AirportName, month, weekday, day, time, self.dof, 1)
                    timeMode = 0
                    month = list()
                    day = list()
                    weekday = list()
                    time = list()            
            
            if group in months:
                month.append(months.index(group) + 1)
            elif group in weekdays:
                weekday.append(weekdays.index(group) + 1)
            elif len(group) <= 2 and group.isnumeric():
                day.append(int(group))
            elif len(group) == 4 and group.isnumeric():
                time.append(int(group[0:2])*3600 + int(group[2:4]) * 60)
                timeMode = 1
            elif 'CLSD' in group:
                #self.writeLine(AirportName, 0, 0)
                month = list()
                day = list()
                weekday = list()
                time = list()
    
    def add(self, AirportName, month, weekday, day, time, dof, inc = 0):
            
        ctime = datetime(dof.year, dof.month, dof.day + inc)

        if len(month)==1:
            if ctime.month != month[0]:
                return self
        elif len(month)==1:
            if ctime.month < month[0] or ctime.month > month[1]:
                return self
        
        if len(weekday)==1:
            if (ctime.weekday() + 1) != weekday[0]:
                return self
        elif len(weekday)==2:
            if (ctime.weekday() + 1) < weekday[0] or (ctime.weekday() + 1) > weekday[1]:  
                return self      

        if len(day) == 1:
            if ctime.day != day[0]:
                return self
        elif len(day) == 2:
            if ctime.day < day[0] and ctime.day > day[1]:
                return self
        
        start = 1
        for t in time:
            if start:
                start = 0
                startTime = ctime.timestamp() + t
            else:
                start = 1
                endTime = ctime.timestamp() + t
                self.writeLine(AirportName, startTime, endTime)

dof = date.today()
NOTAM_url = 'https://www.ais.fi/ais/bulletins/efinen.htm'
OprHrDataFile = 'OprHrData.csv'
OprHrData(NOTAM_url, dof).createCsv(OprHrDataFile)
