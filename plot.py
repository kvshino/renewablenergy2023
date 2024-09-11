from datetime import *
from pannello import *
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from functions import *



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

    plt.figure(title, facecolor='#edf1ef')

    sns.set(font_scale=1.48)
    ax = sns.lineplot(data, x=x, y=y, color=color)
    ax.plot(data[x], data[y], color=color)
    plt.ylabel(label)
    plt.xticks(data['datetime'], data['datetime'].dt.strftime('%d/%m Ore:%H:%M'), rotation=90)
    plt.title(title, weight='bold')

def plot_graph_hist(data, x, y, title, color, label):
    plt.figure(title,facecolor='#edf1ef')
    colors = ['#F94144' if value < 0 else '#90BE6D' for value in data['value']]
    plt.bar(data['datetime'], data['value'], width=0.02, color=colors)
    plt.xticks(data['datetime'], data['datetime'].dt.strftime('%d/%m Ore:%H:%M'), rotation=90)
    plt.ylabel(label)
    plt.title(title, weight='bold')

def plot_subgraph(data, x, y, color, label, position):
    plt.subplot(1, 1, position)
    plt.plot(data[x], data[y], color=color, label=label)
    plt.xticks(data['datetime'], data['datetime'].dt.strftime('%H'), rotation=10)
    plt.title(label)

    if label != "Cost" or label != "Cost without Battery":
        plt.ylim(-10000, 10000)
    else:
        plt.ylim(-2, 2)


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


def simulation_plot(data, dictionary, sum, actual_percentage, quantity_delta_battery, first_battery_value,co2_algo):

    ########################################################################################
    # This is the part where we consider the whole plant#
    ########################################################################################
    plot_production(dictionary, "production")
    plot_load(dictionary, "load")
    plot_costi_plant(sum)
    plot_scambio_rete(dictionary, "load", "production", quantity_delta_battery)
    plot_energia_batteria(dictionary,actual_percentage, first_battery_value)
    plot_percentage_battery(dictionary, actual_percentage)
    plot_battery_status(quantity_delta_battery)
    plot_co2_plant(co2_algo)

    ########################################################################################
    # This is the part where we consider only the pv without taking into account the battery#
    ########################################################################################
    
    plot_costi_plant_nobattery(dictionary)

    ########################################################################################
    # This is the part where we consider only the consumption and no PV and the battery#########
    ########################################################################################

    plot_co2_noplant(data, dictionary, "load")
    plot_costi_noplant(dictionary, "load")
    plt.figure("Cost Comparison",facecolor='#edf1ef')
    plot_cost_comparison(dictionary, "load", "prices", sum)
   
def simulation_plant(dictionary, sum, actual_percentage, quantity_delta_battery, first_battery_value):
    plot_load(dictionary, "load")
    plot_production(dictionary, "production")
    plot_costi_plant(sum)
    plot_scambio_rete(dictionary, "load", "production", quantity_delta_battery)
    plot_energia_batteria(dictionary,actual_percentage, first_battery_value)
    plot_percentage_battery(dictionary,actual_percentage)
    plot_battery_status(quantity_delta_battery)
    plot_co2_plant(dictionary, "load", "production", quantity_delta_battery)
    plot_cost_comparison(dictionary, "load", "prices", sum)
    plot_degradation(dictionary)


def simulation_plant_nobattery(dictionary):
    plot_load(dictionary, "load")
    plot_production(dictionary, "production")
    plot_costi_plant_nobattery(dictionary)

def simulation_noplant(dictionary):
    plot_load(dictionary, "load")
    plot_costi_noplant(dictionary, "load")
    plot_co2_noplant(dictionary, "load")



def plot_GME_prices(dictionary, string):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')
    prices_list = dictionary_to_list(dictionary, string)

    expected_prices_dataframe = pd.DataFrame({'datetime': time_column, 'value':prices_list})
    plot_graph(expected_prices_dataframe, "datetime", "value", "Stima Prezzi Energia", "#F3722C", "€")


def plot_production(dictionary, string):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')

    lista = dictionary_to_list(dictionary, string)
    expected_production_dataframe = pd.DataFrame({'datetime': time_column, 'value': lista})
    plot_graph(expected_production_dataframe, "datetime", "value", "Stima Produzione PV", "#F3722C", "Wh")

def plot_load(dictionary, string):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')

    lista = dictionary_to_list(dictionary, string)
    expected_load_dataframe = pd.DataFrame({'datetime': time_column, 'value': lista})
    plot_graph(expected_load_dataframe, "datetime", "value", "Stima Carico", "#F94144", "Wh")

def plot_costi_plant(sum):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')
    cost_dataframe = pd.DataFrame({'datetime': time_column, 'value': sum})
    cost_dataframe["value"] = cost_dataframe["value"].multiply(-1)
    plot_graph(cost_dataframe, "datetime", "value", "Stima costi in bolletta (guadagno positivo)", "#577590", "Euro €")

def plot_scambio_rete(dictionary, string_load, string_production, quantity_delta_battery):

    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')

    lista_load = dictionary_to_list(dictionary, string_load)
    lista_production = dictionary_to_list(dictionary, string_production)


    quantity_delta_battery_dataframe = pd.DataFrame({'datetime': time_column, 'value': quantity_delta_battery})
    expected_load_dataframe = pd.DataFrame({'datetime': time_column, 'value': lista_load})
    expected_production_dataframe = pd.DataFrame({'datetime': time_column, 'value': lista_production})

    quantity_delta_battery_dataframe2 = quantity_delta_battery_dataframe[1:].reset_index()    
    difference = expected_load_dataframe["value"] - (
            expected_production_dataframe["value"] - quantity_delta_battery_dataframe2["value"])
    
    difference_dataframe = pd.DataFrame({'datetime': time_column, 'value': difference})

    plot_graph_hist(difference_dataframe, "datetime", "value",
               "Stima scambio energetico con la rete elettrica (acquisto positivo)", "#43AA8B", "Wh")

def plot_energia_batteria(dictionary,actual_percentage, first_battery_value):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column = pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1),
                                periods=25, freq='H')

    app = {}
    app["battery_capacity0"] = first_battery_value * dictionary["battery_capacity0"]
    for i in range(24):
        app[f"battery_capacity{i+1}"] = dictionary[f"battery_capacity{i}"]

    battery_wh = [float(dictionary["soc_min"] * app[f"battery_capacity{i}"]) + (percentage * (float(dictionary["soc_max"] * app[f"battery_capacity{i}"]) - float(dictionary["soc_min"] * app[f"battery_capacity{i}"]))) for i,percentage in enumerate(actual_percentage)]
    battery_wh_dataframe = pd.DataFrame({'datetime': time_column, 'value': battery_wh})
    plot_graph(battery_wh_dataframe, "datetime", "value", "Stima energia in batteria", "#90BE6D", "Wh")


def plot_percentage_battery(dictionary,actual_percentage):
      
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column = pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1),
                                periods=25, freq='H')
    
    actual_percentage_dataframe = pd.DataFrame({'datetime': time_column, 'value': actual_percentage})
    actual_percentage_dataframe["value"] = actual_percentage_dataframe["value"].multiply(dictionary["soc_max"] - dictionary["soc_min"])
    actual_percentage_dataframe["value"] = actual_percentage_dataframe["value"].add(dictionary["soc_min"])
    actual_percentage_dataframe["value"] = actual_percentage_dataframe["value"].multiply(100)
    plot_graph(actual_percentage_dataframe, "datetime", "value", "Stima percentuale batteria", "#90BE6D", "%")

def plot_battery_status(quantity_delta_battery):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')  


    quantity_delta_battery_dataframe = pd.DataFrame({'datetime': time_column, 'value': quantity_delta_battery})
    plot_graph_hist(quantity_delta_battery_dataframe, "datetime", "value", "Stima carica/scarica batteria (carica positiva)",
               "#4D908E", "Wh")

def plot_co2_plant(co2_algo):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H') 

    co2_plant_dataframe = pd.DataFrame({'datetime': time_column, 'value': co2_algo})
    plot_graph(co2_plant_dataframe, "datetime", "value",
                "Co2 immessa con impianto ", "#577590", "Grammi")
    
def plot_degradation(dictionary):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H') 
        
    lista = dictionary_to_list(dictionary, "battery_capacity")
    
    co2_plant_dataframe = pd.DataFrame({'datetime': time_column, 'value': lista})
    plot_graph(co2_plant_dataframe, "datetime", "value",
                "Degradazione Impianto", "#577590", "Wha")

def plot_costi_plant_nobattery(dictionary):

    result = []
    result.append(0)
    if dictionary["difference_of_production0"] < 0:
        result.append((dictionary["difference_of_production0"]) * dictionary["prices0"])
    else:
        result.append((dictionary["difference_of_production0"]) * dictionary["sold"])

    for i in range(1, 24):
        if dictionary[f"difference_of_production{i}"] < 0:
            result.append((dictionary[f"difference_of_production{i}"]) * dictionary[f"prices{i}"] + result[i])
        else:
            result.append((dictionary[f"difference_of_production{i}"]) * dictionary["sold"] + result[i])

    current_datetime = datetime.now() + timedelta(hours=1)
    time_column = pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')
    pv_only_dataframe = pd.DataFrame({'datetime': time_column, 'value': result[1:]})

    plot_graph(pv_only_dataframe, "datetime", "value", "Stima costi in bolletta (guadagno positivo) (senza batteria)",
               "#577590", "Euro €")

def plot_co2_noplant(data,dictionary, string_load):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H') 
    
    lista_consumi = dictionary_to_list(dictionary, string_load)

    co2_emissions_noplant=[]
    co2_emissions_noplant.append(0)
    for i in range(len(lista_consumi)):
        co2_emissions_noplant.append(co2_emissions_noplant[i] + co2_quantity_emission(data,dictionary,(-lista_consumi[i]),i))

    co2_dataframe = pd.DataFrame({'datetime': time_column, 'value': co2_emissions_noplant[1:]})
    plot_graph(co2_dataframe, "datetime", "value",
               "Co2 immessa senza impianto ", "#577590", "Grammi ")

def plot_costi_noplant(dictionary, string_load):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')
    consumption_list = []
    consumption_list.append(0)
    i=0

    lista = dictionary_to_list(dictionary, string_load)
    
    for value in lista:
        consumption_list.append((-value * dictionary[f"prices{i}"]) + consumption_list[i])
        i = i + 1

    consumption_only_dataframe = pd.DataFrame({'datetime': time_column, 'value': consumption_list[1:]})
    plot_graph(consumption_only_dataframe, "datetime", "value",
               "Stima costi in bolletta (guadagno positivo) (senza batteria e senza PV)", "#577590", "Euro €")

def plot_cost_comparison(dictionary, string_load, string_prices, sum):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')

    consumption_list = []
    consumption_list.append(0)
    i=0

    lista_load = dictionary_to_list(dictionary, string_load)
    lista_prices = dictionary_to_list(dictionary, string_prices)

    for value in lista_load:
        consumption_list.append((-value * lista_prices[i]) + consumption_list[i])
        i = i + 1

    consumption_only_dataframe = pd.DataFrame({'datetime': time_column, 'value': consumption_list[1:]})

    result = []
    result.append(0)
    if dictionary["difference_of_production0"] < 0:
        result.append((dictionary["difference_of_production0"]) * dictionary["prices0"])
    else:
        result.append((dictionary["difference_of_production0"]) * dictionary["sold"])

    for i in range(1, 24):
        if dictionary[f"difference_of_production{i}"] < 0:
            result.append((dictionary[f"difference_of_production{i}"]) * dictionary[f"prices{i}"] + result[i])
        else:
            result.append((dictionary[f"difference_of_production{i}"]) * dictionary["sold"] + result[i])

    pv_only_dataframe = pd.DataFrame({'datetime': time_column, 'value': result[1:]})

    cost_dataframe = pd.DataFrame({'datetime': time_column, 'value': sum})
    cost_dataframe["value"] = cost_dataframe["value"].multiply(-1)

    plot_subgraph(cost_dataframe, "datetime", "value", "#577590", "With PV and battery", 1)
    plot_subgraph(pv_only_dataframe, "datetime", "value", "#90BE6D", "With PV", 1)
    plot_subgraph(consumption_only_dataframe, "datetime", "value", "#F94144", "Without PV", 1)
    plt.ylabel("Euro €")
    plt.legend()
    plt.ylim(-3,3)

def plot_co2_comparison(dictionary,data,co2_algo):

    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H') 
    co2_plant_dataframe = pd.DataFrame({'datetime': time_column, 'value': co2_algo})


    lista_consumi = dictionary_to_list(dictionary,"load")
    co2_emissions_noplant=[]
    co2_emissions_noplant.append(0)
    print(lista_consumi)
    for i in range(len(lista_consumi)):
        co2_emissions_noplant.append(co2_emissions_noplant[i] + co2_quantity_emission(data,dictionary,(-lista_consumi[i]),i))


    co2_dataframe = pd.DataFrame({'datetime': time_column, 'value': co2_emissions_noplant[1:]})

    plot_subgraph(co2_plant_dataframe, "datetime", "value", "#90BE6D", "With Algoritm", 1)
    plot_subgraph(co2_dataframe, "datetime", "value", "#577590", "Without PV and battery", 1)
    plt.ylabel("Co2 in Grammi")
    plt.legend()


def plot_costi_noalgo(sum):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')
    cost_dataframe = pd.DataFrame({'datetime': time_column, 'value': sum})
    cost_dataframe["value"] = cost_dataframe["value"].multiply(-1)
    plot_graph(cost_dataframe, "datetime", "value", "Stima costi in bolletta (guadagno positivo) senza Algoritmo", "#577590", "Euro €")

def plot_energia_batteria_noalgo(actual_battery_level_noalgo):    
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column = pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1),
                                periods=25, freq='H')

    battery_wh_dataframe = pd.DataFrame({'datetime': time_column, 'value': actual_battery_level_noalgo})
    plot_graph(battery_wh_dataframe, "datetime", "value", "Stima energia in batteria senza Algoritmo", "#90BE6D", "Wh")

def plot_co2_noalgo(co2):

    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H') 
    co2_plant_dataframe = pd.DataFrame({'datetime': time_column, 'value': co2})
    plot_graph(co2_plant_dataframe, "datetime", "value",
                "Co2 immessa con impianto senza Algoritmo ", "#577590", "Grammi")


def plot_degradation_noalgo(quantity_battery_degradation_noalgo):

    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H') 
    co2_plant_dataframe = pd.DataFrame({'datetime': time_column, 'value': quantity_battery_degradation_noalgo})
    plot_graph(co2_plant_dataframe, "datetime", "value",
                "Degradazione Impianto senza Algoritmo ", "#577590", "Wh")
    
def plot_cost_comparison_algo(sum,sum_noalgo):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')        

    cost_dataframe = pd.DataFrame({'datetime': time_column, 'value': sum})
    cost_dataframe["value"] = cost_dataframe["value"].multiply(-1)

    cost_dataframe_noalgo = pd.DataFrame({'datetime': time_column, 'value': sum_noalgo})
    cost_dataframe_noalgo["value"] = cost_dataframe_noalgo["value"].multiply(-1)

    plot_subgraph(cost_dataframe, "datetime", "value", "#577590", "With Algoritm", 1)
    plot_subgraph(cost_dataframe_noalgo, "datetime", "value", "#90BE6D", "Without Algoritm", 1)
    plt.ylabel("Euro €")
    plt.legend()
    plt.ylim(-3,3)

def plot_comparison_degradation_algo(dictionary,quantity_battery_degradation_noalgo):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H') 

    lista = dictionary_to_list(dictionary, "battery_capacity")
    degradation_plant_dataframe = pd.DataFrame({'datetime': time_column, 'value': lista})
    degradation_plant_dataframe_noalgo = pd.DataFrame({'datetime': time_column, 'value': quantity_battery_degradation_noalgo})

    plot_subgraph(degradation_plant_dataframe, "datetime", "value", "#577590", "With Algoritm", 1)
    plot_subgraph(degradation_plant_dataframe_noalgo, "datetime", "value", "#90BE6D", "Without Algoritm", 1)
    plt.ylabel("Wh")
    plt.legend()
    plt.ylim(9000,10000)


def plot_co2_comparison_algo(co2_algo,co2_noalgo):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H') 

    co2_plant_dataframe = pd.DataFrame({'datetime': time_column, 'value': co2_algo})
    co2_plant_dataframe_noalgo = pd.DataFrame({'datetime': time_column, 'value': co2_noalgo})

    plot_subgraph(co2_plant_dataframe, "datetime", "value", "#577590", "With Algoritm", 1)
    plot_subgraph(co2_plant_dataframe_noalgo, "datetime", "value", "#90BE6D", "Without Algoritm", 1)
    plt.ylabel("Grammi")
    plt.legend()


def plot_scambio_rete_noalgo(power_to_grid):

    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')
    power_to_grid_df = pd.DataFrame({'datetime': time_column, 'value': power_to_grid})

    power_to_grid_df["value"] = power_to_grid_df["value"].multiply(-1)

    plot_graph_hist(power_to_grid_df, "datetime", "value",
               "Stima scambio energetico con la rete elettrica (Acquisto positivo) senza Algoritmo", "#43AA8B", "Wh")
    
def simulation_plot_no_algorithm(dictionary,sum_noalgo,actual_battery_level_noalgo,quantity_battery_degradation_noalgo,co2,power_to_grid):
    plot_GME_prices(dictionary, "prices")
    plot_load(dictionary, "load")
    plot_production(dictionary, "production")
    plot_costi_noalgo(sum_noalgo)
    plot_energia_batteria_noalgo(actual_battery_level_noalgo)
    plot_co2_noalgo(co2)
    plot_degradation_noalgo(quantity_battery_degradation_noalgo)
    plot_scambio_rete_noalgo(power_to_grid)



