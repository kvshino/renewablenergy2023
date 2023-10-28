import yaml
import asyncio
import pandas as pd
import seaborn as sns
import numpy as np
from mercati_energetici import MercatiElettrici
from datetime import datetime, timedelta
from openmeteo_py import OWmanager
from openmeteo_py.Hourly.HourlyForecast import HourlyForecast
from openmeteo_py.Options.ForecastOptions import ForecastOptions
from openmeteo_py.Utils.constants import *







def setup(disablePV:bool=False, disableBattery:bool=False):
    """
    Takes the datas from the conf.yaml and stores them in data.

    Args:
        disablePV: when True disables the PV grid
        disableBattery: when True disables the battery (a plant without accumulators)

    Returns:
        data: struct containing all the datas
    """
    sns.set_theme()
    with open("conf.yaml") as f:
        data = yaml.load(f, Loader=yaml.FullLoader)

    if disablePV:
        data["energy_pv"] = []
    
    if disableBattery:
        data["maximum_battery_level"] = 0
        data["minimum_battery_level"] = 0
        data["initial_battery_level"] = 0

    for i in range(0,24):
        if disablePV:
            data["energy_pv"].append(0)
        data["hours"].append(i)
        data["energy_grid"].append(0)
        data["battery_levels"].append(data["initial_battery_level"])

    return data







def get_meteo_data(latitude:float=40.6824404,longitude:float=14.7680965):
    """
    Fetches meteo datas from Open-Meteo.com
    The datas are hour by hour until the day after tomorrow.

    Args:
        latitude
        longitude
    
    Returns:
        pandasmeteo: a dataframe containing the temperature and the direct/diffuse radiation
    """
    hourly = HourlyForecast()
    options = ForecastOptions(latitude,longitude,False,celsius,kmh,mm,iso8601,utc)
    mgr = OWmanager(options,OWmanager.forecast,hourly.temperature_2m().direct_radiation().diffuse_radiation())
    meteo = mgr.get_data(1)
    pandasmeteo = pd.DataFrame(meteo["hourly"])
    today = str(datetime.now())[:-16]+"T00:00"
    aftertomorrow = str(datetime.now() + timedelta(days=2))[:-16]+"T24:00"
    return pandasmeteo[(pandasmeteo['time'] > today) & (pandasmeteo['time'] < aftertomorrow)]


async def get_intra_day_market():
    """
    Fetches price datas from mercatoelettrico.com

    Returns: 
        sud: a dataframe containing prices data
    """
    async with MercatiElettrici() as mercati_elettrici:
        await mercati_elettrici.get_general_conditions()
        await mercati_elettrici.get_disclaimer()
        await mercati_elettrici.get_markets()
        dati = await mercati_elettrici.get_prices("MI-A2", "20221001")
        pandasdati = pd.DataFrame(dati)
        sud = pandasdati.loc[pandasdati['zona'] == "SUD"]
        return sud