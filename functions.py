import seaborn as sns
import yaml

from consumptions import *
from pannello import *

from update_battery import *
from update_costs import * 

from entsoe import EntsoePandasClient
import pandas as pd
from datetime import datetime, timedelta


import pandas as pd


def setup() -> dict:
    """
    Takes the datas from the conf.yaml and stores them in data.

    Returns:
        data: struct containing all the datas
    """
    sns.set_theme()
    with open("conf.yaml") as f:
        data = yaml.load(f, Loader=yaml.FullLoader)

    df = pd.read_csv('csv/socs.csv')
    

    data["socs"] = df.iloc[-1][-3]
    

    #Checked OK, anche con grafico
    data["estimate"] = get_estimate_load_consumption(get_true_load_consumption())  # It gives an estimation of the load consumption
    
    
    data["expected_production"] = get_expected_power_production_from_pv_24_hours_from_now(data)
    data["difference_of_production"] = data["expected_production"]["production"] - data["estimate"]["consumo"].values


    data["production_not_rs"] = forecast_percentage_production_from_not_renewable_sources(api_key=data["api_key"])
    

    with open('csv/socs.csv', 'r+') as file:
        lines = file.read().split()
        data["battery_capacity"] = float(lines[-1])
        file.close()

    return data


def forecast_percentage_production_from_not_renewable_sources(api_key, zona="IT_CSUD") -> pd.core.frame.DataFrame:

    client = EntsoePandasClient(api_key=api_key)

    today = pd.Timestamp(datetime.now(), tz='Europe/Rome')
    start = pd.Timestamp(today.strftime('%Y%m%d'), tz='Europe/Rome')
    end = start + timedelta(days=1)

    try:
        ahead = client.query_wind_and_solar_forecast(zona, start=start, end=end)
        ahead["Ora"] = ahead.index.hour
        ahead["Sum"] = ahead["Solar"] + ahead["Wind Onshore"]

        total_today = client.query_generation_forecast(zona, start=start, end=end)
        total_today = total_today.to_frame(name='Generation')
        total_today["Ora"] = total_today.index.hour
    except:
        ahead = client.query_wind_and_solar_forecast(zona, start=start-timedelta(days=1), end=end)
        ahead["Ora"] = ahead.index.hour
        ahead["Sum"] = ahead["Solar"] + ahead["Wind Onshore"]

        total_today = client.query_generation_forecast(zona, start=start-timedelta(days=1), end=end)
        total_today = total_today.to_frame(name='Generation')
        total_today["Ora"] = total_today.index.hour
    

    try:
        ahead_tomorrow = client.query_wind_and_solar_forecast(zona, start=start+timedelta(days=1), end=end+timedelta(days=2))
        ahead_tomorrow["Ora"] = ahead_tomorrow.index.hour
        ahead_tomorrow["Sum"] = ahead_tomorrow["Solar"] + ahead_tomorrow["Wind Onshore"]
        final= pd.concat([ahead[ahead["Ora"] >= (datetime.now().hour+1)%25], ahead_tomorrow[ahead_tomorrow["Ora"] < (datetime.now().hour+1)%25]], axis=0)
        #print("GIORNO DOPO RENEWABLE TROVATO")
        # GIORNO DOPO RENEWABLE TROVATO
    except:
        final= pd.concat([ahead[ahead["Ora"] >= (datetime.now().hour+1)%25], ahead[ahead["Ora"] < (datetime.now().hour+1)%25]], axis=0)
        # GIORNO DOPO RENEWABLE NON TROVATO
        #print("GIORNO DOPO RENEWABLE NON TROVATO")


    try:
        total_tomorrow = client.query_generation_forecast(zona, start=start+timedelta(days=1), end=end+timedelta(days=2))
        total_tomorrow = total_tomorrow.to_frame(name='Generation')
        total_tomorrow["Ora"] = total_tomorrow.index.hour
        final_total = pd.concat([total_today[total_today["Ora"] >= (datetime.now().hour+1)%25], total_tomorrow[total_tomorrow["Ora"] < (datetime.now().hour+1)%25]], axis=0)
        # GIORNO DOPO PRODUZIONE TOTALE TROVATA 
        #print("GIORNO DOPO PRODUZIONE TOTALE TROVATA")
    except:
        final_total = pd.concat([total_today[total_today["Ora"] >= (datetime.now().hour+1)%25], total_today[total_today["Ora"] < (datetime.now().hour+1)%25]], axis=0)
        # GIORNO DOPO PRODUZIONE TOTALE NON TROVATA
        #print("GIORNO DOPO PRODUZIONE TOTALE NON TROVATA")


    final_total = final_total.reset_index(drop=True)
    final = final.reset_index(drop=True)
    result = pd.DataFrame()
    result["Difference"] = final_total["Generation"] - final["Sum"]
    result["Difference"] = result["Difference"].clip(lower=0)
    result["Difference"] = result["Difference"] / final_total["Generation"]
    
    return result
