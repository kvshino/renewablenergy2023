from openmeteo_py import OWmanager
from openmeteo_py.Hourly.HourlyForecast import HourlyForecast
from openmeteo_py.Options.ForecastOptions import ForecastOptions
from openmeteo_py.Utils.constants import *
from suntime import Sun
from datetime import datetime, timedelta
import pandas as pd
import pytz
import pvlib



def get_meteo_data_24_hours_from_now(latitude: float = 40.6824404, longitude: float = 14.7680965) -> pd.core.frame.DataFrame:
    """
    Fetches tomorrow meteo datas from Open-Meteo.com
    The datas are hour by hour until the day after tomorrow.

    Args:
        latitude
        longitude

    Returns:
        pandas_meteo: a dataframe containing the temperature and the direct/diffuse radiation
    """
    hourly = HourlyForecast()
    options = ForecastOptions(latitude, longitude, False, celsius, kmh, mm, iso8601, utc)
    mgr = OWmanager(options, OWmanager.forecast, hourly.temperature_2m().direct_normal_irradiance().diffuse_radiation().shortwave_radiation())
    meteo = mgr.get_data(1)
    pandas_meteo = pd.DataFrame(meteo["hourly"])


    now=str(datetime.now() + timedelta(hours=1) - timedelta(minutes=datetime.now().minute))[:-10].replace(" ", "T")
    twentyfour=str(datetime.now() + timedelta(hours=23) +  timedelta(hours=1) - timedelta(minutes=datetime.now().minute) +timedelta(minutes=2))[:-10].replace(" ", "T")
    
    now1=str(datetime.now() + timedelta(hours=0) - timedelta(minutes=datetime.now().minute))[:-10].replace(" ", "T")
    twentyfour1=str(datetime.now() + timedelta(hours=23)  - timedelta(minutes=datetime.now().minute) +timedelta(minutes=2))[:-10].replace(" ", "T")
    temp= pandas_meteo[(pandas_meteo['time'] >= now1) & (pandas_meteo['time'] <= twentyfour1)]
    temp=temp.reset_index(drop=True)

    temp=temp.drop(["time"], axis=1)

    pandas_meteo = pandas_meteo[(pandas_meteo['time'] >= now) & (pandas_meteo['time'] <= twentyfour)]
    pandas_meteo=pandas_meteo.reset_index(drop=True)
    pandas_meteo["direct_normal_irradiance"] = temp["direct_normal_irradiance"]
    pandas_meteo["diffuse_radiation"] = temp["diffuse_radiation"]    
    pandas_meteo["shortwave_radiation"] = temp["shortwave_radiation"] 

    return pandas_meteo