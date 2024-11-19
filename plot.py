from datetime import *
from pannello import *
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from functions import *

color_algo ="#004aad"
color_noalgo="#ff5757"
color_nobatt="#2e9438"
color_noplant="#dbc818"

def plot_graph(data, x, y, title, color, label):
    """
    Plots a graph.

    Args:
        data: a dataframe containing x and y
        x: dataframe column for the x-coordinates
        y: dataframe column for the y-coordinates
        x_label: label for the x-coordinates
        y_label: label for the y-coordinates
        title: used for the window
        color: color of the line plot

    """
    sns.set(rc={'axes.facecolor': '#edf1ef', 'figure.facecolor': '#edf1ef'})

    plt.figure(title,figsize=(14, 8), facecolor='#edf1ef')

    sns.set(font_scale=1.48)
    ax = sns.lineplot(data, x=x, y=y, color=color)
    ax.plot(data[x], data[y], color=color)
    plt.ylabel(label, fontsize=20)
    plt.xticks(data['datetime'], data['datetime'].dt.strftime('%H:%M'), rotation=90, fontsize=20)
    plt.yticks(fontsize=20)
    plt.xlabel("")
    plt.title(title, weight='bold', fontsize=20)

def plot_graph_hist(data, x, y, title, color, label):
    plt.figure(title,figsize=(14, 8),facecolor='#edf1ef')
    colors = ['#F94144' if value < 0 else '#90BE6D' for value in data['value']]
    plt.bar(data['datetime'], data['value'], width=0.02, color=colors)
    plt.xticks(data['datetime'], data['datetime'].dt.strftime('%H:%M'), rotation=90, fontsize=20)
    plt.yticks(fontsize=20)
    plt.xlabel("")
    plt.ylabel(label, fontsize=20)
    plt.title(title, weight='bold', fontsize=20)

def plot_subgraph(data, x, y, color, label, position):
    plt.subplot(1, 1, position)
    plt.plot(data[x], data[y], color=color, label=label)
    plt.xticks(data['datetime'], data['datetime'].dt.strftime('%H:M'), rotation=90, fontsize=20)
    plt.xlabel("")
    plt.yticks(fontsize=20)
    plt.title(label, fontsize=20)



def genetic_algorithm_graph(data, array_sum, array_qb):
    plt.figure("Convergenza dell'algoritmo", facecolor='#edf1ef')
    history = [(e.opt[0].F[0]) for e in data["history"]]
    plt.plot(history, color ="#577590")
    #plt.xticks(range(0, len(data["history"])+1))
    plt.title("Convergenza dell'algoritmo")
    plt.xlabel('Generazione')
    plt.ylabel('Score')

    asse_x= range(1, len(array_sum)+1)


    plt.figure("Punteggio normalizzato dei primi "+ str(len(array_sum)) + " individui", facecolor='#edf1ef')
    respop = [(2-x[0])/2 for x in data["res"].pop.get("F")][:len(array_sum)]
    plt.bar(asse_x, respop, width=0.2, color="#577590")
    plt.xticks(asse_x)
    plt.title("Punteggio normalizzato dei primi "+ str(len(array_sum)) + " individui")
    plt.xlabel('Individuo n°')
    plt.ylabel('Score dell\'individuo')
    plt.ylim(0, abs(max(respop))+abs(0.1*max(respop)))
    

    plt.figure("Costo bolletta dei primi "+ str(len(array_sum)) + " individui", facecolor='#edf1ef')
    plt.bar(asse_x, array_sum, width=0.2, color ="#577590")
    plt.xticks(asse_x)
    plt.title("Costo in bolletta dei primi "+ str(len(array_sum)) + " individui")
    plt.xlabel('Individuo n°')
    plt.ylabel('Costo in bolletta in €')
    plt.ylim(-abs(min(array_sum))-abs(0.3*min(array_sum)), abs(min(array_sum))+abs(0.1*min(array_sum)))
    

    plt.figure("Flusso energetico della batteria dei primi "+ str(len(array_qb)) + " individui", facecolor='#edf1ef')
    plt.bar(asse_x, array_qb, width=0.2, color ="#577590")
    plt.xticks(asse_x)
    plt.title("Flusso energetico della batteria dei primi "+ str(len(array_qb)) + " individui")
    plt.xlabel('Individuo n°')
    plt.ylabel('Flusso energetico in Wh')
    plt.ylim(-100, abs(max(array_qb))+abs(0.1*max(array_qb)))

    plt.show()


def simulation_plot_plant_algo(dictionary):

    ########################################################################################
    # This is the part where we consider the whole plant with Algoritm#
    ########################################################################################
    plot_production(dictionary)
    plot_load(dictionary)
    plot_costi_plant(dictionary)
    plot_scambio_rete(dictionary)
    plot_energia_batteria(dictionary)
    plot_percentage_battery(dictionary)
    plot_battery_status(dictionary)
    plot_co2_plant(dictionary)
    plot_degradation(dictionary)


def simulation_plot_plant_nobattery(dictionary):
    ########################################################################################
    # This is the part where we consider the plant without battery
    ########################################################################################
    plot_load(dictionary)
    plot_production(dictionary)
    plot_scambio_rete_nobattery(dictionary)
    plot_co2_nobattery(dictionary)
    plot_costi_plant_nobattery(dictionary)


def simulation_plot_noplant(dictionary):
    ########################################################################################
    # This is the part where we consider House without a plant
    ########################################################################################
    plot_load(dictionary)
    plot_scambio_rete_noplant(dictionary)
    plot_costi_noplant(dictionary)
    plot_co2_noplant(dictionary)

def simulation_plot_no_algorithm(dictionary):
    ########################################################################################
    # This is the part where we consider the whole plant without Algoritm#
    ########################################################################################
    plot_production(dictionary)
    plot_load(dictionary)
    plot_energia_batteria_noalgo(dictionary)
    plot_scambio_rete_noalgo(dictionary)
    plot_degradation_noalgo(dictionary)
    plot_costi_noalgo(dictionary)
    plot_co2_noalgo(dictionary)


########################################################################################
# Whole plant Algoritms
########################################################################################


def plot_GME_prices(dictionary):
    current_datetime = datetime.now() + timedelta(hours=1)
    prices_list = dictionary_to_list(dictionary, "prices")
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=len(prices_list), freq='h')
    expected_prices_dataframe = pd.DataFrame({'datetime': time_column, 'value':prices_list})
    plot_graph(expected_prices_dataframe, "datetime", "value", "Energy Price Estimate", "#F3722C", "€/Wh")

def plot_co2_percentuali(dictionary):
    current_datetime = datetime.now() + timedelta(hours=1)
    production_not_rs_list = dictionary_to_list(dictionary, "production_not_rs")
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=len(production_not_rs_list), freq='h')
    expected_production_not_rs_dataframe = pd.DataFrame({'datetime': time_column, 'value':production_not_rs_list})
    plot_graph(expected_production_not_rs_dataframe, "datetime", "value", "Percentage NOT renewable energy", "#F3722C", "%")
    


def plot_production(dictionary):
    current_datetime = datetime.now() + timedelta(hours=1)
    lista = dictionary_to_list(dictionary, "production")
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=len(lista), freq='h')
    expected_production_dataframe = pd.DataFrame({'datetime': time_column, 'value': lista})
    plot_graph(expected_production_dataframe, "datetime", "value", "Estimated PV Production", "#F3722C", "Wh")

def plot_load(dictionary):
    current_datetime = datetime.now() + timedelta(hours=1)
    lista = dictionary_to_list(dictionary, "load")
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=len(lista), freq='h')
    expected_load_dataframe = pd.DataFrame({'datetime': time_column, 'value': lista})        
    plot_graph(expected_load_dataframe, "datetime", "value", "Estimated Load", "#F94144", "Wh")

def plot_costi_plant(dictionary):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=len(dictionary["sum_algo"]), freq='h')
    cost_dataframe = pd.DataFrame({'datetime': time_column, 'value': dictionary["sum_algo"]})
    cost_dataframe["value"] = cost_dataframe["value"].multiply(-1)    
    plot_graph(cost_dataframe, "datetime", "value", "Cost Comparison (Positive Earnings)", color_algo, "€")

def plot_scambio_rete(dictionary):

    current_datetime = datetime.now() + timedelta(hours=1)

    lista_quantity = dictionary["quantity_delta_battery_algo"]
    lista_load = dictionary_to_list(dictionary, "load")
    lista_production = dictionary_to_list(dictionary, "production")
    for i in range(len(lista_production)):
        lista_production[i] = lista_production[i] * dictionary["polynomial_inverter"](dictionary["ratio_algo"][i])


    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=len(lista_load), freq='h')
    quantity_delta_battery_dataframe = pd.DataFrame({'datetime': time_column, 'value': lista_quantity})
    expected_load_dataframe = pd.DataFrame({'datetime': time_column, 'value': lista_load})
    expected_production_dataframe = pd.DataFrame({'datetime': time_column, 'value': lista_production})

    quantity_delta_battery_dataframe2 = quantity_delta_battery_dataframe.reset_index()    
    difference = expected_load_dataframe["value"] - (
            expected_production_dataframe["value"] - quantity_delta_battery_dataframe2["value"])
    
    difference_dataframe = pd.DataFrame({'datetime': time_column, 'value': difference})

    plot_graph_hist(difference_dataframe, "datetime", "value",
               "Estimated energy exchange with the electricity grid (positive purchase)", "#43AA8B", "Wh")

def plot_energia_batteria(dictionary):
    current_datetime = datetime.now() + timedelta(hours=1)
    
    actual_percentage_algo = dictionary["actual_percentage_algo"]
    time_column = pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1),
                                periods=len(actual_percentage_algo), freq='h')
    battery_wh = [float(dictionary["soc_min"] * dictionary[f"battery_capacity{i}"]) + (percentage * (float(dictionary["soc_max"] * dictionary[f"battery_capacity{i}"]) - float(dictionary["soc_min"] * dictionary[f"battery_capacity{i}"]))) for i,percentage in enumerate(actual_percentage_algo)]
    battery_wh_dataframe = pd.DataFrame({'datetime': time_column, 'value': battery_wh})
    plot_graph(battery_wh_dataframe, "datetime", "value", "Battery energy estimate", color_algo, "Wh")


def plot_percentage_battery(dictionary):
      
    current_datetime = datetime.now() + timedelta(hours=1)
    
    
    list_actual_percentage = dictionary["actual_percentage_algo"]

    time_column = pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1),
                                periods=len(list_actual_percentage), freq='h')

    actual_percentage_dataframe = pd.DataFrame({'datetime': time_column, 'value': list_actual_percentage})
    actual_percentage_dataframe["value"] = actual_percentage_dataframe["value"].multiply(dictionary["soc_max"] - dictionary["soc_min"])
    actual_percentage_dataframe["value"] = actual_percentage_dataframe["value"].add(dictionary["soc_min"])
    actual_percentage_dataframe["value"] = actual_percentage_dataframe["value"].multiply(100)
    plot_graph(actual_percentage_dataframe, "datetime", "value", "Battery energy percentage estimate", color_algo, "%")

def plot_battery_status(dictionary):
    current_datetime = datetime.now() + timedelta(hours=1)

    quantity_delta_battery = dictionary["quantity_delta_battery_algo"]
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=len(quantity_delta_battery), freq='h')  

    quantity_delta_battery_dataframe = pd.DataFrame({'datetime': time_column, 'value': quantity_delta_battery})
    plot_graph_hist(quantity_delta_battery_dataframe, "datetime", "value", "Battery charge/discharge estimate (positive charge)",
               color_algo, "Wh")

def plot_co2_plant(dictionary):
    current_datetime = datetime.now() + timedelta(hours=1)

    co2_algo = dictionary["co2_algo"]
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=len(co2_algo), freq='h') 
    co2_plant_dataframe = pd.DataFrame({'datetime': time_column, 'value': co2_algo})
    plot_graph(co2_plant_dataframe, "datetime", "value",
                "Co2 introduced with the system ", color_algo, "gCO2")
    
def plot_degradation(dictionary):
    current_datetime = datetime.now() + timedelta(hours=1)
        
    lista = dictionary_to_list(dictionary,"battery_capacity")
    lista = lista[1:]
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=len(lista), freq='h') 
    co2_plant_dataframe = pd.DataFrame({'datetime': time_column, 'value': lista})
    plot_graph(co2_plant_dataframe, "datetime", "value",
                "Plant degradation", color_algo, "Wh")

def plot_production_algo_inverter(dictionary):
    current_datetime = datetime.now() + timedelta(hours=1)

    lista = dictionary_to_list(dictionary, "production")
    for i in range(len(lista)):
        lista[i] = lista[i] * dictionary["polynomial_inverter"](dictionary["ratio_algo"][i])

    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=len(lista), freq='h')

    expected_production_dataframe = pd.DataFrame({'datetime': time_column, 'value': lista})
    plot_graph(expected_production_dataframe, "datetime", "value", "Estimate of PV production with inverter efficiency", color_algo, "Wh")

def plot_inverter_efficency(dictionary):
    current_datetime = datetime.now() + timedelta(hours=1)

    risultato = []
    for i in range(len(dictionary["ratio_algo"])):
        risultato.append(dictionary["polynomial_inverter"](dictionary["ratio_algo"][i]))

    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=len(risultato), freq='h')

    efficiency_dataframe = pd.DataFrame({'datetime': time_column, 'value': risultato})
    plot_graph(efficiency_dataframe, "datetime", "value", "Inverter Efficency", color_algo, "%")

########################################################################################
#       NO BATTERY FUNCTION
########################################################################################
def plot_scambio_rete_nobattery(dictionary):

    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=len(dictionary["power_to_grid_nobattery"]), freq='h')

    power_to_grid_df = pd.DataFrame({'datetime': time_column, 'value': dictionary["power_to_grid_nobattery"]})
    power_to_grid_df["value"] = power_to_grid_df["value"].multiply(-1)

    plot_graph_hist(power_to_grid_df, "datetime", "value",
               "Estimated energy exchange with the electricity grid (Positive purchase) without battery", "#43AA8B", "Wh")

def plot_co2_nobattery(dictionary):

    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=len(dictionary["co2_nobattery"]), freq='h') 

    co2_plant_dataframe = pd.DataFrame({'datetime': time_column, 'value': dictionary["co2_nobattery"]})
    plot_graph(co2_plant_dataframe, "datetime", "value",
                "Co2 introduced with system without battery ", color_nobatt, "Grams")
    
def plot_costi_plant_nobattery(dictionary):

    current_datetime = datetime.now() + timedelta(hours=1)
    time_column = pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=len(dictionary["sum_nobattery"]), freq='h')
    pv_only_dataframe = pd.DataFrame({'datetime': time_column, 'value': dictionary["sum_nobattery"]})

    plot_graph(pv_only_dataframe, "datetime", "value", "Estimated costs on the bill (positive profit) (without battery)",
               color_nobatt, "Euro €")    
    
########################################################################################
#       NO PLANT
########################################################################################
def plot_co2_noplant(dictionary):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=len(dictionary["co2_noplant"]), freq='h') 

    co2_dataframe = pd.DataFrame({'datetime': time_column, 'value': dictionary["co2_noplant"]})
    co2_dataframe["value"] = co2_dataframe["value"].multiply(-1)                             
    plot_graph(co2_dataframe, "datetime", "value",
               "Co2 introduced without system", color_noplant, "Grams ")

def plot_costi_noplant(dictionary):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=len(dictionary["sum_noplant"]), freq='h')

    consumption_only_dataframe = pd.DataFrame({'datetime': time_column, 'value': dictionary["sum_noplant"]})
    plot_graph(consumption_only_dataframe, "datetime", "value",
               "Estimated costs on the bill (positive profit) (without battery and without PV)", color_noplant, "Euro €")

def plot_scambio_rete_noplant(dictionary):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=len(dictionary["power_to_grid_noplant"]), freq='h') 

    power_to_grid_df = pd.DataFrame({'datetime': time_column, 'value': dictionary["power_to_grid_noplant"]})

    plot_graph_hist(power_to_grid_df, "datetime", "value",
               "Estimated energy exchange with the electricity grid (Positive purchase) without system", "#43AA8B", "Wh")

########################################################################################
#       NO ALGORITHM FUNCTION
########################################################################################

def plot_scambio_rete_noalgo(dictionary):

    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=len(dictionary["power_to_grid_noalgo"]), freq='h')
    power_to_grid_df = pd.DataFrame({'datetime': time_column, 'value': dictionary["power_to_grid_noalgo"]})

    power_to_grid_df["value"] = power_to_grid_df["value"].multiply(-1)

    plot_graph_hist(power_to_grid_df, "datetime", "value",
               "Estimated energy exchange with the electricity grid (Positive purchase) without Algorithm", "#43AA8B", "Wh")

def plot_costi_noalgo(dictionary):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=len(dictionary["sum_noalgo"]), freq='h')
    cost_dataframe = pd.DataFrame({'datetime': time_column, 'value': dictionary["sum_noalgo"]})
    cost_dataframe["value"] = cost_dataframe["value"].multiply(-1)
    plot_graph(cost_dataframe, "datetime", "value", "Estimate costs on the bill (positive profit) without Algorithm", color_noalgo, "Euro €")

def plot_energia_batteria_noalgo(dictionary):    
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column = pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1),
                                periods=len(dictionary["actual_battery_level_noalgo"]), freq='h')

    battery_wh_dataframe = pd.DataFrame({'datetime': time_column, 'value': dictionary["actual_battery_level_noalgo"]})
    plot_graph(battery_wh_dataframe, "datetime", "value", "Estimate battery energy without Algorithm", color_noalgo, "Wh")

def plot_co2_noalgo(dictionary):

    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=len(dictionary["co2_noalgo"]), freq='h') 
    co2_plant_dataframe = pd.DataFrame({'datetime': time_column, 'value': dictionary["co2_noalgo"]})
    plot_graph(co2_plant_dataframe, "datetime", "value",
                "Co2 introduced with system without Algorithm", color_noalgo, "Grams")


def plot_degradation_noalgo(dictionary):

    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=len(dictionary["quantity_battery_degradation_noalgo"]), freq='h') 
    co2_plant_dataframe = pd.DataFrame({'datetime': time_column, 'value':dictionary["quantity_battery_degradation_noalgo"]})
    plot_graph(co2_plant_dataframe, "datetime", "value",
                "System Degradation without Algorithm ", color_noalgo, "Wh")
    
########################################################################################
#       Comparison Plots
########################################################################################

def plot_co2_comparison_algo(dictionary):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=len(dictionary["co2_algo"]), freq='h') 

    co2_plant_dataframe = pd.DataFrame({'datetime': time_column, 'value': dictionary["co2_algo"]})
    co2_plant_dataframe_nobattery = pd.DataFrame({'datetime': time_column, 'value': dictionary["co2_nobattery"]})
    co2_plant_dataframe_noplant = pd.DataFrame({'datetime': time_column, 'value': dictionary["co2_noplant"]})
    co2_plant_dataframe_noalgo = pd.DataFrame({'datetime': time_column, 'value': dictionary["co2_noalgo"]})
    co2_plant_dataframe_noplant["value"] = co2_plant_dataframe_noplant["value"].multiply(-1)                             

   # Creazione della figura
    plt.figure(figsize=(14, 8),facecolor='#edf1ef')

    # Tracciare tutte le curve sullo stesso grafico
    plt.plot(co2_plant_dataframe["datetime"], co2_plant_dataframe["value"], color=color_algo, label="Pv and battery with EMS")
    plt.plot(co2_plant_dataframe_nobattery["datetime"], co2_plant_dataframe_nobattery["value"], color=color_nobatt, label="PV")
    plt.plot(co2_plant_dataframe_noplant["datetime"], co2_plant_dataframe_noplant["value"], color=color_noplant, label="Nothing")
    plt.plot(co2_plant_dataframe_noalgo["datetime"], co2_plant_dataframe_noalgo["value"], color=color_noalgo, label="PV and battery without EMS")

    # Impostazioni del grafico
    plt.xlabel("")
    plt.ylabel("gCO2", fontsize=20)
    plt.legend()  # Mostra la legenda per distinguere le curve
    plt.grid(True)  # Aggiungi una griglia per facilitare la lettura
    plt.xticks(co2_plant_dataframe_noalgo["datetime"], co2_plant_dataframe_noalgo["datetime"].dt.strftime('%H:%M'), rotation=90, fontsize=20)
    plt.yticks(fontsize=20)
    title ="Co2 Emissions Comparison"
    plt.title(title, weight='bold', fontsize=20)

    # Mostra il grafico
    plt.tight_layout()


def plot_cost_comparison(dictionary):
    # Imposta l'ora corrente e crea la colonna del tempo
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column = pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=len(dictionary["sum_algo"]), freq='h')

    # Creazione dei DataFrame con i dati
    cost_dataframe_algo = pd.DataFrame({'datetime': time_column, 'value': dictionary["sum_algo"]})
    cost_dataframe_algo["value"] = cost_dataframe_algo["value"].multiply(-1)

    cost_dataframe_nobattery = pd.DataFrame({'datetime': time_column, 'value': dictionary["sum_nobattery"]})
    cost_dataframe_noplant = pd.DataFrame({'datetime': time_column, 'value': dictionary["sum_noplant"]})

    cost_dataframe_noalgo = pd.DataFrame({'datetime': time_column, 'value': dictionary["sum_noalgo"]})
    cost_dataframe_noalgo["value"] = cost_dataframe_noalgo["value"].multiply(-1)

    # Creazione della figura
    plt.figure(figsize=(14, 8),facecolor='#edf1ef')

    # Tracciare tutte le curve sullo stesso grafico
    plt.plot(cost_dataframe_algo["datetime"], cost_dataframe_algo["value"], color=color_algo, label="Pv and battery with EMS")
    plt.plot(cost_dataframe_nobattery["datetime"], cost_dataframe_nobattery["value"], color=color_nobatt, label="PV")
    plt.plot(cost_dataframe_noplant["datetime"], cost_dataframe_noplant["value"], color=color_noplant, label="Nothing")
    plt.plot(cost_dataframe_noalgo["datetime"], cost_dataframe_noalgo["value"], color=color_noalgo, label="Pv and battery without EMS")

    # Impostazioni del grafico
    plt.xlabel("")
    plt.ylabel("€", fontsize=20)
    plt.legend()  # Mostra la legenda per distinguere le curve
    #plt.ylim(-2, 2)  # Puoi regolare o rimuovere questi limiti
    plt.grid(True)  # Aggiungi una griglia per facilitare la lettura
    plt.xticks(cost_dataframe_algo["datetime"], cost_dataframe_algo["datetime"].dt.strftime('%H:%M'), rotation=90, fontsize=20)
    plt.yticks(fontsize=20)
    
    title ="Cost Comparison (Positive Earnings)"
    plt.title(title, weight='bold', fontsize=20)


    # Mostra il grafico
    plt.tight_layout()



def plot_comparison_degradation(dictionary):
    current_datetime = datetime.now() + timedelta(hours=1)

    lista = dictionary_to_list(dictionary, "battery_capacity")
    lista=lista[1:]
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=len(lista), freq='h') 

    degradation_plant_dataframe = pd.DataFrame({'datetime': time_column, 'value': lista})
    degradation_plant_dataframe_noalgo = pd.DataFrame({'datetime': time_column, 'value': dictionary["quantity_battery_degradation_noalgo"]})
   
    plt.figure(figsize=(14, 8),facecolor='#edf1ef')

    # Tracciare tutte le curve sullo stesso grafico
    plt.plot(degradation_plant_dataframe["datetime"], degradation_plant_dataframe["value"], color=color_algo, label="Pv and battery with EMS")
    plt.plot(degradation_plant_dataframe_noalgo["datetime"], degradation_plant_dataframe_noalgo["value"], color=color_noalgo, label="Pv and battery without EMS")

    # Impostazioni del grafico
    plt.xlabel("")
    plt.ylabel("Wh", fontsize=20)
    plt.legend()  # Mostra la legenda per distinguere le curve
    plt.grid(True)  # Aggiungi una griglia per facilitare la lettura
    plt.xticks(degradation_plant_dataframe["datetime"], degradation_plant_dataframe["datetime"].dt.strftime('%H:%M'), rotation=90, fontsize=20)
    plt.yticks(fontsize=20)
    title ="Battery Degradation Comparison"
    plt.title(title, weight='bold', fontsize=20)

    # Mostra il grafico
    plt.tight_layout()

def plot_comparison_battery(dictionary):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1), periods=len(dictionary["actual_percentage_algo"]), freq='h') 

    actual_percentage_algo = dictionary["actual_percentage_algo"]
    
    battery_wh = [float(dictionary["soc_min"] * dictionary[f"battery_capacity{i}"]) + (percentage * (float(dictionary["soc_max"] * dictionary[f"battery_capacity{i}"]) - float(dictionary["soc_min"] * dictionary[f"battery_capacity{i}"]))) for i,percentage in enumerate(actual_percentage_algo)]
    battery_wh_dataframe = pd.DataFrame({'datetime': time_column, 'value': battery_wh})

    battery_dataframe_noalgo = pd.DataFrame({'datetime': time_column, 'value': dictionary["actual_battery_level_noalgo"]})

    plt.figure(figsize=(14, 8),facecolor='#edf1ef')

    # Tracciare tutte le curve sullo stesso grafico
    plt.plot(battery_wh_dataframe["datetime"], battery_wh_dataframe["value"], color=color_algo, label="Pv and battery with EMS")
    plt.plot(battery_dataframe_noalgo["datetime"], battery_dataframe_noalgo["value"], color=color_noalgo, label="Pv and battery without EMS")

    # Impostazioni del grafico
    plt.xlabel("")
    plt.ylabel("Wh", fontsize=20)
    plt.legend()  # Mostra la legenda per distinguere le curve
    plt.grid(True)  # Aggiungi una griglia per facilitare la lettura
    plt.xticks(battery_wh_dataframe["datetime"], battery_wh_dataframe["datetime"].dt.strftime('%H:%M'), rotation=90, fontsize=20)
    plt.yticks(fontsize=20)
    title ="Energy in Battery Comparison"
    plt.title(title, weight='bold', fontsize=20)

    # Mostra il grafico
    plt.tight_layout()
