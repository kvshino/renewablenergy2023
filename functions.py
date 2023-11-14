import os
import yaml
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from mercati_energetici import MercatiElettrici
from datetime import datetime, timedelta
from openmeteo_py import OWmanager
from openmeteo_py.Hourly.HourlyForecast import HourlyForecast
from openmeteo_py.Options.ForecastOptions import ForecastOptions
from openmeteo_py.Utils.constants import *
from suntime import Sun
import pytz


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

def energy_request(data):
    """
    Estimate grid consumption, daily energy production from solar panels, and the discharge/charge behavior of the battery.

    Args:
        data: struct containing all the datas

    Returns: 
        data: struct containing all the datas (now updated with the new values)
    """
    for i in data["hours"]:
        data["energy_delta"] = data["energy_pv"][i]- data["load_profile"][i]


        if(data["energy_delta"] >= 0):                   #produco più di quel che consumo
            if (i == 0):
                if(data["initial_battery_level"] + data["energy_delta"] >= data["maximum_battery_level"]):      #batteria piena ,vendo alla rete(in futuro accumulo sopra soglia)
                    data["energy_grid"][i] = data["initial_battery_level"] + data["energy_delta"] - data["maximum_battery_level"]
                    data["battery_levels"][i] = data["maximum_battery_level"]

                if(data["initial_battery_level"] + data["energy_delta"] < data["maximum_battery_level"]):        #batteria scarica ,la ricarico
                    data["battery_levels"][i] = data["initial_battery_level"] + data["energy_delta"]
            else:
                if(data["battery_levels"][i-1] + data["energy_delta"] >= data["maximum_battery_level"]):      #batteria piena ,vendo alla rete(in futuro accumulo sopra soglia)
                    data["energy_grid"][i] = data["battery_levels"][i-1] + data["energy_delta"] - data["maximum_battery_level"]
                    data["battery_levels"][i] = data["maximum_battery_level"]

                if(data["battery_levels"][i-1] + data["energy_delta"] < data["maximum_battery_level"]):        #batteria scarica ,la ricarico
                    data["battery_levels"][i] = data["battery_levels"][i-1] + data["energy_delta"]

        if(data["energy_delta"] < 0):                     #consumo più di quello che produco
            if(i == 0):
                if(data["initial_battery_level"] > data["minimum_battery_level"] + abs(data["energy_delta"]) ):       #la batteria ha sufficiente energia per alimentare il carico
                    data["battery_levels"][i] = data["initial_battery_level"] - abs(data["energy_delta"])
                    
                if(data["initial_battery_level"] < data["minimum_battery_level"] + abs(data["energy_delta"])):                #la batteria non ha sufficiente energia(totale), prendo energia dalla rete
                    data["energy_grid"][i] = - ( abs(data["energy_delta"]) - ( data["initial_battery_level"] - data["minimum_battery_level"] ) )
                    data["battery_levels"][i] = data["minimum_battery_level"]
            else:
                if(data["battery_levels"][i-1] > data["minimum_battery_level"] + abs(data["energy_delta"]) ):       #la batteria ha sufficiente energia per alimentare il carico
                    data["battery_levels"][i] = data["battery_levels"][i-1] - abs(data["energy_delta"])
                    
                if(data["battery_levels"][i-1] < data["minimum_battery_level"] + abs(data["energy_delta"])):                #la batteria non ha sufficiente energia(totale), prendo energia dalla rete
                    data["energy_grid"][i] = - ( abs(data["energy_delta"]) - ( data["battery_levels"][i-1] - data["minimum_battery_level"] ) )
                    data["battery_levels"][i] = data["minimum_battery_level"]

    return data


def plot_graph(data, x, y, xlabel, ylabel, title, color):
    """
    Plots a graph.

    Args:
        data: a dataframe containing x and y
        x: dataframe column for the x-coordinates
        y: dataframe column for the y-coordinates
        xlabel: label for the x-coordinates
        ylabel: label for the y-coordinates
        title: used for the window
        color: color of the line plot

    """
    plt.figure(title)
    sns.lineplot(data, x=x, y=y,  color=color)
    plt.title(title)
    plt.xticks(np.arange(0, 24, 1.0))
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)

def profit(data):
    """
    Returns how much the system takes from/gives to the grid in €.

    Args:
        data: struct containing all the datas
    Returns:
        profit: €
    """
    profit=0
    for index, item in enumerate(data["energy_grid"]):
        if item >=0:
            profit=profit+ (data["energy_grid"][index]*data["sold"])
        if item < 0:
            profit= profit +(data["energy_grid"][index]*data["price"][index])
    return profit

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


async def get_intra_days_market(days=1):
    """
    Fetches price datas from mercatoelettrico.com

    Returns: 
        sud: a dataframe containing prices data
    """
    async with MercatiElettrici() as mercati_elettrici:
        await mercati_elettrici.get_general_conditions()
        await mercati_elettrici.get_disclaimer()
        await mercati_elettrici.get_markets()

        pandasdati=pd.DataFrame()
        today=datetime.now()
        for i in range(days):
            dati = await mercati_elettrici.get_prices("MI-A2", today.strftime("%Y%m%d"))
            today= today - timedelta(days=1)
            pandasdati=pd.concat([pandasdati, pd.DataFrame(dati)])

        sud = pandasdati.loc[pandasdati['zona'] == "SUD"].drop(["mercato","zona"],axis=1)
        
        return sud
    

def energy_mean_price(energyCosts):
    return energyCosts["prezzo"].mean()


async def get_future_day_market():
    async with MercatiElettrici() as mercati_elettrici:
        await mercati_elettrici.get_general_conditions()
        await mercati_elettrici.get_disclaimer()
        await mercati_elettrici.get_markets()   
        try:
            price = await mercati_elettrici.get_prices("MI-A2", (datetime.now()+timedelta(days=1)).strftime("%Y%m%d"))
            priceDF = pd.DataFrame(price).drop(["mercato","zona"], axis=1)
        except:
            raise Exception("Tomorrow market data prices are not available yet")
        return priceDF
    
async def mean_difference(days=1):
    pastDF = await get_intra_days_market(days=days)
    pastMean= energy_mean_price(pastDF)

    try:
        futureDF = await get_future_day_market()
        futureMean= energy_mean_price(futureDF)
        return (futureMean-pastMean), futureMean, pastMean
    except Exception as error:
        print(error)
    return None,None,None

    
def battery_or_grid(data, percentage):    # difference > 0 --> costo futuro > costo passato
                                                         # difference < 0 --> costo futuro < costo passato
    
    meteo_DF = get_meteo_data()
    if(data["mean_difference"] > data["past_mean"]*percentage/100):     
        print("Bring energy from the battery")
        return 1
    
    tz = pytz.timezone(data["timezone"])
    sun = Sun(data["latitude"], data["longitude"])
    today_sr = sun.get_local_sunrise_time(datetime.today(), local_time_zone=tz) 
    today_ss = sun.get_local_sunset_time(datetime.today(), local_time_zone=tz)

    today_sr = today_sr - timedelta(minutes=today_sr.minute)
    today_ss = today_ss + timedelta(hours=1) - timedelta(minutes=today_ss.minute)

    meteo_DF = meteo_DF[(meteo_DF['time'] > today_sr) & (meteo_DF['time'] <  today_ss)]
    print(meteo_DF)
    