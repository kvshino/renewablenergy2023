from datetime import datetime, timedelta
from suntime import Sun
import pytz
from openmeteo_py import OWmanager
from openmeteo_py.Hourly.HourlyForecast import HourlyForecast
from openmeteo_py.Options.ForecastOptions import ForecastOptions
from openmeteo_py.Utils.constants import *
import pandas as pd
from functions import *

coords = {'longitude' : 14.7680965, 'latitude' : 40.6824404 }

latitude = 40.8553996
longitude =  14.2744036


tz = pytz.timezone('Europe/Rome')

sun = Sun(latitude, longitude)
#print(sun.get_local_sunset_time(datetime.today()).replace(tzinfo=pytz.utc).astimezone(pytz.timezone('Europe/Rome')))
# Get today's sunrise and sunset in UTC
# today_sr = sun.get_local_sunrise_time(datetime.today(), local_time_zone=tz)
# today_ss = sun.get_local_sunset_time(datetime.today(), local_time_zone=tz)
# print(today_sr)
# print(today_ss)
# today_sr = today_sr - timedelta(minutes=today_sr.minute)
# today_ss = today_ss + timedelta(hours=1) - timedelta(minutes=today_ss.minute)
# print(today_ss)
# print(today_sr)


hourly = HourlyForecast()
options = ForecastOptions(latitude,longitude,False,celsius,kmh,mm,iso8601,utc)
mgr = OWmanager(options,OWmanager.forecast,hourly.temperature_2m().direct_radiation().diffuse_radiation())
meteo = mgr.get_data(1)
#pandasmeteo = pd.DataFrame(meteo["hourly"])
#print(pandasmeteo[(pd.to_datetime(pandasmeteo['time']).dt.hour > 8) & (pd.to_datetime(pandasmeteo['time']).dt.hour <  14)])
data = setup()
print(difference_of_production(data))
