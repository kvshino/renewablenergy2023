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


def setup(polynomial_inverter) -> dict:
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
    data["cycles"] = df.iloc[-1][-2]
    

    #Checked OK, anche con grafico
    data["estimate"] = get_estimate_load_consumption(get_true_load_consumption())  # It gives an estimation of the load consumption
    
    data["polynomial_inverter"] = polynomial_inverter
    data["expected_production"] = get_expected_power_production_from_pv_24_hours_from_now(data)
    data["difference_of_production"] = difference_of_production(data)


    #data["production_not_rs"] = forecast_percentage_production_from_not_renewable_sources(api_key=data["api_key"])
    

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


def dictionary_to_list(dictionary, string, number=24):
    lista = []
    for i in range(number):
        lista.append(dictionary[string + str(i)])
    
    return lista


def shift_ciclico(df):
    # Shift ciclico di una colonna
    app = df.iloc[0].copy()
    for i in range(len(df)):
        df.iloc[i] = df.iloc[(i+1) % len(df)] 

    df.iloc[len(df)-1] = app

    return df


def simulation_no_algorithm(data,dictionary, first_battery_value, cycles, polynomial):
    sum = []
    sum.append(0)
    co2_emissions = []
    co2_emissions.append(0)
    sold = dictionary["sold"]
    battery_level = []
    battery_capacity = polynomial(cycles) * dictionary["battery_nominal_capacity"]

    first_battery_value_in_w = first_battery_value * battery_capacity *dictionary["soc_max"]
    battery_degradation = []    
    battery_degradation.append(battery_capacity)
    battery_level.append(first_battery_value_in_w)


    for j in range(24):
        
        battery_capacity = polynomial(cycles) * dictionary["battery_nominal_capacity"]

        upper_limit = (dictionary["soc_max"] * battery_capacity)
        lower_limit = (dictionary["soc_min"] * battery_capacity)
        effettivo_in_batteria= battery_level[j]

        if dictionary[f"difference_of_production{j}"] >= 0:

            posso_caricare_di = upper_limit - effettivo_in_batteria

            if posso_caricare_di - dictionary[f"difference_of_production{j}"] >= 0:
                #metto tutto in batteria
                battery_level.append(effettivo_in_batteria+dictionary[f"difference_of_production{j}"])
                sum.append(sum[j])
                co2_emissions.append(co2_emissions[j])
                battery_degradation.append(battery_degradation[j])
            else:
                #vendo
                sum.append(sum[j] - ((dictionary[f"difference_of_production{j}"] - posso_caricare_di) * sold))
                battery_level.append(upper_limit)
                co2_emissions.append(co2_emissions[j])
                battery_degradation.append(battery_degradation[j])

        else:
            #mi serve corrente
            posso_scaricare_di=effettivo_in_batteria-lower_limit

            if posso_scaricare_di + dictionary[f"difference_of_production{j}"] >= 0:
                app = effettivo_in_batteria + dictionary[f"difference_of_production{j}"]
                battery_level.append(app)
                co2_emissions.append(co2_emissions[j])
                sum.append(sum[j])


            else:
                app = posso_scaricare_di
                battery_level.append(lower_limit)
                sum.append( sum[j] - (posso_scaricare_di + dictionary[f"difference_of_production{j}"]) * dictionary[f"prices{j}"] )
                co2_emissions.append(co2_emissions[j] + co2_quantity_emission(data,dictionary,(posso_scaricare_di + dictionary[f"difference_of_production{j}"]),j))

            cycles = round(cycles+(app/battery_capacity), 5)
            battery_degradation.append(battery_capacity)


    return sum[1:],battery_level,battery_degradation,co2_emissions


def co2_quantity_emission(data,dictionary,to_buy,ora):
    quantity_bought_from_not_renewable_sources =  to_buy * dictionary[f"production_not_rs{ora}"]
    co2_emissions = (quantity_bought_from_not_renewable_sources * data["coal_percentage"] * data["coal_pollution"]) 
    +(quantity_bought_from_not_renewable_sources * data["gas_percentage"] * data["gas_pollution"])  
    +(quantity_bought_from_not_renewable_sources * data["oil_percentage"] * data["oil_pollution"])
    return co2_emissions
