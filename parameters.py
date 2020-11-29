# Parameters

# Wind limits
maxTailwind = 10
maxCrosswind = 20

# RVR limits
minRVR = 600
OEIminRVR = 800
#toRVRwCLL = 400
#toRVRwoCLL = 500

# Speeds
OEIXCSpeed = 120
XCSpeed = 140

# Times for flight planning
taxiTime = 10 * 60
approachTime = 10 * 60
sidTime = 2 * 60

# URLS
url = 'https://api.met.no/weatherapi/tafmetar/1.0/metar.txt?icao='
url = 'https://api.met.no/weatherapi/tafmetar/1.0/taf.txt?icao='
url = 'https://www.ais.fi/ais/bulletins/efinen.htm'
url = 'http://api.sunrise-sunset.org/json?formatted=0'

# File names
TafDataFile = 'TafData.csv'
MetarDataFile = 'MetarData.csv'
CivilTwilightDataFile = 'CivilTwilightData.csv'
ApproachDataFile = 'ApproachData.csv'
RunwayDataFile = 'RunwayData.csv'
AirportDataFile = 'AirportData.csv'
OprHrDataFile = 'OprHrData.csv'

# Buffer times
#ats_buffer = (-30*60, 30*60) 
#night_buffer = (-30*60, 30*60)
#wx_buffer_plan = (-60 * 60, 60 * 60)
#wx_buffer_ops = (0, 5 * 60)  
