wind = {
    'maxTailwind' : 10,
    'preferedWind' : 5,
    'maxCrosswind' : 20
}

#RVR = {
#    'minRVR' : 600,
#    'OEIminRVR' : 800,
#    'toRVRwCLL' : 400,
#    'toRVRwoCLL' : 500
#}

flight = {
    # Speeds
    'OEIXCSpeed' : 120,
    'XCSpeed' : 140,

    # Times for flight planning
    'taxiTime' : 10 * 60,
    'approachTime' : 10 * 60,
    'sidTime' : 2 * 60,
}

data = {
    # URLS
    'url_metar' : 'https://api.met.no/weatherapi/tafmetar/1.0/metar.txt?icao=',
    'url_taf' : 'https://api.met.no/weatherapi/tafmetar/1.0/taf.txt?icao=',
    'url_notam' : 'https://www.ais.fi/ais/bulletins/efinen.htm',
    'url_day' : 'http://api.sunrise-sunset.org/json?formatted=0',

    # File names
    'TafDataFile' : './data/TafData.csv',
    'MetarDataFile' : './data/MetarData.csv',
    'CivilTwilightDataFile' : './data/CivilTwilightData.csv',
    'ApproachDataFile' : './data/ApproachData.csv',
    'RunwayDataFile' : './data/RunwayData.csv',
    'AirportDataFile' : './data/AirportData.csv',
    'OprHrDataFile' : './data/OprHrData.csv',

    # Update
    'weather_update' : 10 * 60,
    'notam_update' : 12 * 3600,
    'day_update' : 12 * 3600
    }

#operation = {
#    # Buffer times
#    'ats_buffer' : (-30*60, 30*60), 
#    'night_buffer' : (-30*60, 30*60),
#    'wx_buffer_plan' : (-60 * 60, 60 * 60),
#    'wx_buffer_ops' : (0, 5 * 60),
#}  
