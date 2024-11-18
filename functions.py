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
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import griddata
import os


def setup(polynomial_inverter, filename='csv/socs.csv') -> dict:
    """
    Takes the datas from the conf.yaml and stores them in data.

    Returns:
        data: struct containing all the datas
    """
    sns.set_theme()
    with open("conf.yaml") as f:
        data = yaml.load(f, Loader=yaml.FullLoader)

    df = pd.read_csv(filename)
    

    data["socs"] = df.iloc[-1][-3]
    data["cycles"] = df.iloc[-1][-2]
    

    #Checked OK, anche con grafico
    data["estimate"] = get_estimate_load_consumption(get_true_load_consumption(data))  # It gives an estimation of the load consumption
    
    data["polynomial_inverter"] = polynomial_inverter
    data["expected_production"] = get_expected_power_production_from_pv_24_hours_from_now(data)
    data["difference_of_production"] = difference_of_production(data)
    #data["production_not_rs"] = forecast_percentage_production_from_not_renewable_sources(api_key=data["api_key"])  
    

    with open(filename, 'r+') as file:
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
        ahead = client.query_intraday_wind_and_solar_forecast(zona, start=start, end=end)
        ahead["Ora"] = ahead.index.hour
        ahead["Sum"] = ahead["Solar"] + ahead["Wind Onshore"]
    except:
        ahead = client.query_intraday_wind_and_solar_forecast(zona, start=start-timedelta(days=1), end=end-timedelta(days=1))
        ahead["Ora"] = ahead.index.hour
        ahead["Sum"] = ahead["Solar"] + ahead["Wind Onshore"]


    try:
        total_today = client.query_generation_forecast(zona, start=start, end=end)
        total_today = total_today.to_frame(name='Generation')
        total_today["Ora"] = total_today.index.hour
    except:
        total_today = client.query_generation_forecast(zona, start=start-timedelta(days=1), end=end-timedelta(days=1))
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
        ahead.loc[ahead["Ora"] < (datetime.now().hour+1)%25, 'Sum'] = ahead['Sum'] + ahead['Sum'] * random.uniform(-0.10, 0.10)
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
        total_today.loc[total_today["Ora"] < (datetime.now().hour+1)%25, 'Generation'] = total_today['Generation'] + total_today['Generation'] * random.uniform(-0.10, 0.10)
        final_total = pd.concat([total_today[total_today["Ora"] >= (datetime.now().hour+1)%25], total_today[total_today["Ora"] < (datetime.now().hour+1)%25]], axis=0)
        # GIORNO DOPO PRODUZIONE TOTALE NON TROVATA
        #print("GIORNO DOPO PRODUZIONE TOTALE NON TROVATA")


    final_total = final_total.reset_index(drop=True)
    final = final.reset_index(drop=True)
    result = pd.DataFrame()
    result["Difference"] = final_total["Generation"] - final["Sum"]
    result["Difference"] = result["Difference"].clip(lower=0)
    result["Difference"] = result["Difference"] / final_total["Generation"]
    result = result.iloc[:24]

    return result


def dictionary_to_list(dictionary, string, number=24):
    lista = []
    i = 0  # Inizializza il contatore
    while True:
        key = string + str(i)
        value = dictionary.get(key)  # Usa get per evitare errori se la chiave non esiste

        if value is None:  # Interrompi il ciclo se il valore è `None`
            break

        lista.append(value)
        i += 1  # Passa alla chiave successiva

    return lista


def shift_ciclico(df, stringa):
    # Shift ciclico di una colonna
    app = df.iloc[0].copy()
    for i in range(len(df)):
        df.iloc[i] = df.iloc[(i+1) % len(df)] 

    app[stringa] = app[stringa] + (random.uniform(-0.10, 0.10) * app[stringa])
    df.iloc[len(df)-1] = app

    return df


def simulation_no_algorithm(data,dictionary, cycles, polynomial, hours=24):
    sum = []
    sum.append(0)
    co2_emissions = []
    co2_emissions.append(0)
    sold = dictionary["sold"]
    battery_level = []
    battery_capacity = round(polynomial(cycles) * dictionary["battery_nominal_capacity"], 4)
    ratio_list = []

    upper_limit = (dictionary["soc_max"] * battery_capacity)
    lower_limit = (dictionary["soc_min"] * battery_capacity)
    first_battery_value_in_w = lower_limit + (dictionary["first_battery_value"]*(upper_limit-lower_limit))
    battery_degradation = []    
    battery_degradation.append(battery_capacity)

    battery_level.append(first_battery_value_in_w)

    power_to_grid = []

    for j in range(hours):
        
        upper_limit = (dictionary["soc_max"] * battery_capacity)
        lower_limit = (dictionary["soc_min"] * battery_capacity)
        effettivo_in_batteria= battery_level[j]

        if dictionary[f"difference_of_production{j}"] >= 0:

            posso_caricare_di = upper_limit - effettivo_in_batteria
            
            ratio = min((dictionary[f"load{j}"] + dictionary[f"difference_of_production{j}"]) / data["inverter_nominal_power"], 1)

            dictionary[f"difference_of_production{j}"] = dictionary[f"production{j}"]*data["polynomial_inverter"](ratio) - dictionary[f"load{j}"]
            if posso_caricare_di - (dictionary[f"difference_of_production{j}"]*dictionary["battery_charging_efficiency"]*data["polynomial_inverter"](ratio)) >= 0:
                #metto tutto in batteria
                battery_level.append(effettivo_in_batteria+(dictionary[f"difference_of_production{j}"]*dictionary["battery_charging_efficiency"]*data["polynomial_inverter"](ratio)))
                sum.append(sum[j])
                power_to_grid.append(0)
            else:
                #vendo

                sum.append(sum[j] - ((dictionary[f"difference_of_production{j}"] - posso_caricare_di/dictionary["battery_charging_efficiency"]/data["polynomial_inverter"](ratio)) * sold))
                battery_level.append(upper_limit)
                power_to_grid.append(dictionary[f"difference_of_production{j}"] - posso_caricare_di/dictionary["battery_charging_efficiency"]/data["polynomial_inverter"](ratio))

            co2_emissions.append(co2_emissions[j])
            battery_degradation.append(battery_degradation[j])
        else:
            #mi serve corrente
            posso_scaricare_di=effettivo_in_batteria-lower_limit

            ratio = (dictionary[f"load{j}"]) / data["inverter_nominal_power"]

            dictionary[f"difference_of_production{j}"] = dictionary[f"production{j}"]*data["polynomial_inverter"](ratio) - dictionary[f"load{j}"]
            if posso_scaricare_di + (dictionary[f"difference_of_production{j}"]/dictionary["battery_discharging_efficiency"]/data["polynomial_inverter"](ratio)) >= 0:
                app = -(dictionary[f"difference_of_production{j}"]/dictionary["battery_discharging_efficiency"]/data["polynomial_inverter"](ratio))
                battery_level.append(effettivo_in_batteria + (dictionary[f"difference_of_production{j}"]/dictionary["battery_discharging_efficiency"]/data["polynomial_inverter"](ratio)))
                co2_emissions.append(co2_emissions[j])
                sum.append(sum[j])
                power_to_grid.append(0)

            else:
                app = posso_scaricare_di
                battery_level.append(lower_limit)
                sum.append( sum[j] - (posso_scaricare_di*dictionary["battery_discharging_efficiency"]*data["polynomial_inverter"](ratio) + dictionary[f"difference_of_production{j}"]) * dictionary[f"prices{j}"] )
                co2_emissions.append(co2_emissions[j] + co2_quantity_emission(data,dictionary,(posso_scaricare_di*dictionary["battery_discharging_efficiency"]*data["polynomial_inverter"](ratio) + dictionary[f"difference_of_production{j}"]),j))
                power_to_grid.append(posso_scaricare_di*dictionary["battery_discharging_efficiency"]*data["polynomial_inverter"](ratio) + dictionary[f"difference_of_production{j}"])

            cycles = round(cycles+(app/battery_capacity), 5)
            battery_capacity = round(polynomial(cycles) * dictionary["battery_nominal_capacity"], 4)
            battery_degradation.append(battery_capacity)
        ratio_list.append(ratio)


    return sum[1:],battery_level,battery_degradation[1:],co2_emissions[1:], power_to_grid, ratio_list

def simulation_nobattery(data,dictionary):
    costo = []
    co2_nobattery = []
    power_togrid = []

    costo.append(0)
    co2_nobattery.append(0)
    ratio_list = []

    list_diff = dictionary_to_list(dictionary,"difference_of_production")


    for i in range(len(list_diff)):

        if dictionary[f"difference_of_production{i}"] < 0:
            ratio = 1
            costo.append((dictionary[f"difference_of_production{i}"]) * dictionary[f"prices{i}"] + costo[i])
            power_togrid.append(dictionary[f"difference_of_production{i}"])
            co2_nobattery.append(co2_nobattery[i] + co2_quantity_emission(data,dictionary,(dictionary[f"difference_of_production{i}"]),i) )

        else:
            ratio = min(dictionary[f"load{i}"] + dictionary[f"difference_of_production{i}"] / data["inverter_nominal_power"], 1)
            costo.append((dictionary[f"difference_of_production{i}"]*data["polynomial_inverter"](ratio)) * dictionary["sold"] + costo[i])
            power_togrid.append(dictionary[f"difference_of_production{i}"]*data["polynomial_inverter"](ratio))
            co2_nobattery.append(co2_nobattery[i] )
        ratio_list.append(ratio)

    return costo[1:],co2_nobattery[1:],power_togrid, ratio_list

def simulation_noplant(data,dictionary):
    costo = []
    co2_noplant = []
    power_togrid = []

    costo.append(0)
    co2_noplant.append(0)

    list_load = dictionary_to_list(dictionary,"load")

    for i in range (len (list_load)):
        costo.append((-list_load[i] * dictionary[f"prices{i}"]) + costo[i])
        co2_noplant.append(co2_noplant[i] + co2_quantity_emission(data,dictionary,list_load[i],i))
        power_togrid.append(list_load[i])  


    return costo[1:],co2_noplant[1:],power_togrid



def co2_quantity_emission(data,dictionary,to_buy,ora):
    quantity_bought_from_not_renewable_sources =  -to_buy * dictionary[f"production_not_rs{ora}"]
    co2_emissions = (quantity_bought_from_not_renewable_sources * data["coal_percentage"] * data["coal_pollution"]) 
    +(quantity_bought_from_not_renewable_sources * data["gas_percentage"] * data["gas_pollution"])  
    +(quantity_bought_from_not_renewable_sources * data["oil_percentage"] * data["oil_pollution"])
    return co2_emissions

def co2_quantity_emission_algo(data,perc,to_buy):
    quantity_bought_from_not_renewable_sources =  -to_buy * perc
    co2_emissions = (quantity_bought_from_not_renewable_sources * data["coal_percentage"] * data["coal_pollution"]) 
    +(quantity_bought_from_not_renewable_sources * data["gas_percentage"] * data["gas_pollution"])  
    +(quantity_bought_from_not_renewable_sources * data["oil_percentage"] * data["oil_pollution"])
    return co2_emissions


def plot_and_save_results(solutions, objective_names, folder_name, filename_2d='grafici_2D.png', filename_3d='grafico_3D.png'): 
    if solutions.shape[1] != 3:
        raise ValueError("Le soluzioni devono avere esattamente 3 colonne per gli obiettivi.")
    if len(objective_names) != 3:
        raise ValueError("Devi fornire esattamente 3 nomi per gli obiettivi.")
    
    # Creazione della cartella se non esiste
    os.makedirs(folder_name, exist_ok=True)

    # Creazione dei percorsi completi per i file
    path_2d = os.path.join(folder_name, filename_2d)
    path_3d = os.path.join(folder_name, filename_3d)
    path_3d_zoom = os.path.join(folder_name, "zoom"+filename_3d)

    # Estrazione degli obiettivi
    f1, f2, f3 = solutions[:, 0], solutions[:, 1], solutions[:, 2]
    nome_f1, nome_f2, nome_f3 = objective_names

    # --- Grafici 2D a due a due ---
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # Plot (f1, f2)
    axes[0].scatter(f1, f2, c='blue', alpha=0.7)
    axes[0].set_xlabel(nome_f1)
    axes[0].set_ylabel(nome_f2)
    axes[0].set_title(f'{nome_f1} vs {nome_f2}')

    # Plot (f2, f3)
    axes[1].scatter(f2, f3, c='green', alpha=0.7)
    axes[1].set_xlabel(nome_f2)
    axes[1].set_ylabel(nome_f3)
    axes[1].set_title(f'{nome_f2} vs {nome_f3}')

    # Plot (f1, f3)
    axes[2].scatter(f1, f3, c='red', alpha=0.7)
    axes[2].set_xlabel(nome_f1)
    axes[2].set_ylabel(nome_f3)
    axes[2].set_title(f'{nome_f1} vs {nome_f3}')

    # Salva il grafico 2D
    plt.tight_layout()
    plt.savefig(path_2d)
    plt.close()

    # --- Grafico 3D con superficie ---
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    # Scatter dei punti
    ax.scatter(f1, f2, f3, c='purple', alpha=0.8)

    # Creazione di una griglia per la superficie
    grid_x, grid_y = np.mgrid[
        np.min(f1):np.max(f1):50j,
        np.min(f2):np.max(f2):50j
    ]

    # Interpolazione dei valori f3
    grid_z = griddata((f1, f2), f3, (grid_x, grid_y), method='linear')

    # Plot della superficie (opzionale)
    if grid_z is not None:
        ax.plot_surface(grid_x, grid_y, grid_z, alpha=0.3, cmap='viridis')

    ax.set_xlabel(nome_f1)
    ax.set_ylabel(nome_f2)
    ax.set_zlabel(nome_f3)
    ax.set_title('3D Pareto Front')

    # Salva il grafico 3D
    plt.savefig(path_3d)
    plt.close()

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    # Scatter dei punti
    ax.scatter(f1, f2, f3, c='purple', alpha=0.8)

    # Creazione di una griglia per la superficie
    grid_x, grid_y = np.mgrid[
        np.min(f1):np.max(f1):50j,
        np.min(f2):np.max(f2):50j
    ]

    # Interpolazione dei valori f3
    grid_z = griddata((f1, f2), f3, (grid_x, grid_y), method='linear')

    # Plot della superficie (opzionale)
    if grid_z is not None:
        ax.plot_surface(grid_x, grid_y, grid_z, alpha=0.3, cmap='viridis')

    ax.set_xlim([0, 0.5])
    ax.set_ylim([0, 0.5])
    ax.set_zlim([0, 0.5])

    ax.set_xlabel(nome_f1)
    ax.set_ylabel(nome_f2)
    ax.set_zlabel(nome_f3)
    ax.set_title('Zoom 3D Pareto Front')

    # Salva il grafico 3D
    plt.savefig(path_3d_zoom)
    plt.close()
    

