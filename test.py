from datetime import datetime, timedelta
from suntime import Sun
import pytz

coords = {'longitude' : 14.7680965, 'latitude' : 40.6824404 }

latitude = 40.6824404
longitude =  14.7680965


tz = pytz.timezone('Europe/Rome')

sun = Sun(latitude, longitude)
#print(sun.get_local_sunset_time(datetime.today()).replace(tzinfo=pytz.utc).astimezone(pytz.timezone('Europe/Rome')))
# Get today's sunrise and sunset in UTC
today_sr = sun.get_local_sunrise_time(datetime.today(), local_time_zone=tz)
today_ss = sun.get_local_sunset_time(datetime.today(), local_time_zone=tz)
print(today_sr)
print(today_ss)
today_sr = today_sr - timedelta(minutes=today_sr.minute)
today_ss = today_ss + timedelta(hours=1) - timedelta(minutes=today_ss.minute)
print(today_ss)
print(today_sr)

