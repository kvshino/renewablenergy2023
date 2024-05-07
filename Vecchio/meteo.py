from openmeteo_py import OWmanager
from openmeteo_py.Hourly.HourlyForecast import HourlyForecast
from openmeteo_py.Options.ForecastOptions import ForecastOptions
from openmeteo_py.Utils.constants import *
from suntime import Sun
from datetime import datetime, timedelta
import pandas as pd
import pytz


def get_meteo_data(latitude: float = 40.6824404, longitude: float = 14.7680965) -> pd.core.frame.DataFrame:
    """
    Fetches meteo datas from Open-Meteo.com
    The datas are hour by hour until the day after tomorrow.

    Args:
        latitude
        longitude

    Returns:
        pandas_meteo: a dataframe containing the temperature and the direct/diffuse radiation
    """
    hourly = HourlyForecast()
    options = ForecastOptions(latitude, longitude, False, celsius, kmh, mm, iso8601, utc)
    mgr = OWmanager(options, OWmanager.forecast, hourly.temperature_2m().direct_radiation().diffuse_radiation())
    meteo = mgr.get_data(1)
    pandas_meteo = pd.DataFrame(meteo["hourly"])
    today = str(datetime.now())[:-16] + "T00:00"   #DA RIVEDERE
    after_tomorrow = str(datetime.now() + timedelta(days=2))[:-16] + "T24:00"

    return pandas_meteo[(pandas_meteo['time'] > today) & (pandas_meteo['time'] < after_tomorrow)]


def get_tomorrow_meteo_data(latitude: float = 40.6824404, longitude: float = 14.7680965) -> pd.core.frame.DataFrame:
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
    mgr = OWmanager(options, OWmanager.forecast, hourly.temperature_2m().direct_radiation().diffuse_radiation())
    meteo = mgr.get_data(1)
    pandas_meteo = pd.DataFrame(meteo["hourly"])
    today = str(datetime.now())[:-16] + "T23:00"
    tomorrow = str(datetime.now() + timedelta(days=1))[:-16] + "T24:00"

    return pandas_meteo[(pandas_meteo['time'] > today) & (pandas_meteo['time'] < tomorrow)]


def filter_meteo_between_ss_and_sr(data) -> pd.core.frame.DataFrame:
    """
        Filter the meteo data between sunrise and sunset

        Args:
            data : Dataframe with local informations

        Returns:
            Filtered dataFrame
    """
    meteo_df = get_meteo_data()
    sun = Sun(data["latitude"], data["longitude"])
    tz = pytz.timezone(data["timezone"])
    today_sr = sun.get_local_sunrise_time(datetime.today(), local_time_zone=tz)
    today_ss = sun.get_local_sunset_time(datetime.today(), local_time_zone=tz)

    today_sr = int((today_sr - timedelta(minutes=today_sr.minute)).strftime("%H"))
    today_ss = int((today_ss + timedelta(hours=1) - timedelta(minutes=today_ss.minute)).strftime("%H"))

    return meteo_df[
        (pd.to_datetime(meteo_df['time']).dt.hour > today_sr) & (pd.to_datetime(meteo_df['time']).dt.hour < today_ss)]





############################################################

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
    mgr = OWmanager(options, OWmanager.forecast, hourly.temperature_2m().direct_radiation().diffuse_radiation())
    meteo = mgr.get_data(1)
    pandas_meteo = pd.DataFrame(meteo["hourly"])
    
    

    now=str(datetime.now() + timedelta(hours=1) - timedelta(minutes=datetime.now().minute))[:-10].replace(" ", "T")
    twentyfour=str(datetime.now() + timedelta(hours=23) +  timedelta(hours=1) - timedelta(minutes=datetime.now().minute))[:-10].replace(" ", "T")
    
   


    return pandas_meteo[(pandas_meteo['time'] >= now) & (pandas_meteo['time'] <= twentyfour)]