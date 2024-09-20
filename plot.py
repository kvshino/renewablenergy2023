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
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')
    prices_list = dictionary_to_list(dictionary, "prices")

    expected_prices_dataframe = pd.DataFrame({'datetime': time_column, 'value':prices_list})
    plot_graph(expected_prices_dataframe, "datetime", "value", "Stima Prezzi Energia", "#F3722C", "€")


def plot_production(dictionary):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')

    lista = dictionary_to_list(dictionary, "production")
    expected_production_dataframe = pd.DataFrame({'datetime': time_column, 'value': lista})
    plot_graph(expected_production_dataframe, "datetime", "value", "Stima Produzione PV", "#F3722C", "Wh")

def plot_load(dictionary):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')

    lista = dictionary_to_list(dictionary, "load")
    expected_load_dataframe = pd.DataFrame({'datetime': time_column, 'value': lista})
    plot_graph(expected_load_dataframe, "datetime", "value", "Stima Carico", "#F94144", "Wh")

def plot_costi_plant(dictionary):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')

    cost_dataframe = pd.DataFrame({'datetime': time_column, 'value': dictionary["sum_algo"]})
    cost_dataframe["value"] = cost_dataframe["value"].multiply(-1)
    plot_graph(cost_dataframe, "datetime", "value", "Stima costi in bolletta (guadagno positivo)", "#577590", "Euro €")

def plot_scambio_rete(dictionary):

    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')

    lista_quantity = dictionary["quantity_delta_battery_algo"]
    lista_load = dictionary_to_list(dictionary, "load")
    lista_production = dictionary_to_list(dictionary, "production")
    for i in range(len(lista_production)):
        lista_production[i] = lista_production[i] * dictionary["polynomial_inverter"](dictionary["ratio_algo"][i])

    quantity_delta_battery_dataframe = pd.DataFrame({'datetime': time_column, 'value': lista_quantity})
    expected_load_dataframe = pd.DataFrame({'datetime': time_column, 'value': lista_load})
    expected_production_dataframe = pd.DataFrame({'datetime': time_column, 'value': lista_production})

    quantity_delta_battery_dataframe2 = quantity_delta_battery_dataframe[1:].reset_index()    
    difference = expected_load_dataframe["value"] - (
            expected_production_dataframe["value"] - quantity_delta_battery_dataframe2["value"])
    
    difference_dataframe = pd.DataFrame({'datetime': time_column, 'value': difference})

    plot_graph_hist(difference_dataframe, "datetime", "value",
               "Stima scambio energetico con la rete elettrica (acquisto positivo)", "#43AA8B", "Wh")

def plot_energia_batteria(dictionary):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column = pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1),
                                periods=25, freq='H')
    
    actual_percentage_algo = dictionary["actual_percentage_algo"]
    
    battery_wh = [float(dictionary["soc_min"] * dictionary[f"battery_capacity{i}"]) + (percentage * (float(dictionary["soc_max"] * dictionary[f"battery_capacity{i}"]) - float(dictionary["soc_min"] * dictionary[f"battery_capacity{i}"]))) for i,percentage in enumerate(actual_percentage_algo)]
    battery_wh_dataframe = pd.DataFrame({'datetime': time_column, 'value': battery_wh})
    plot_graph(battery_wh_dataframe, "datetime", "value", "Stima energia in batteria", "#90BE6D", "Wh")


def plot_percentage_battery(dictionary):
      
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column = pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1),
                                periods=25, freq='H')
    
    list_actual_percentage = dictionary["actual_percentage_algo"]

    actual_percentage_dataframe = pd.DataFrame({'datetime': time_column, 'value': list_actual_percentage})
    actual_percentage_dataframe["value"] = actual_percentage_dataframe["value"].multiply(dictionary["soc_max"] - dictionary["soc_min"])
    actual_percentage_dataframe["value"] = actual_percentage_dataframe["value"].add(dictionary["soc_min"])
    actual_percentage_dataframe["value"] = actual_percentage_dataframe["value"].multiply(100)
    plot_graph(actual_percentage_dataframe, "datetime", "value", "Stima percentuale batteria", "#90BE6D", "%")

def plot_battery_status(dictionary):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')  

    quantity_delta_battery = dictionary["quantity_delta_battery_algo"]

    quantity_delta_battery_dataframe = pd.DataFrame({'datetime': time_column, 'value': quantity_delta_battery})
    plot_graph_hist(quantity_delta_battery_dataframe, "datetime", "value", "Stima carica/scarica batteria (carica positiva)",
               "#4D908E", "Wh")

def plot_co2_plant(dictionary):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H') 

    co2_algo = dictionary["co2_algo"]
    co2_plant_dataframe = pd.DataFrame({'datetime': time_column, 'value': co2_algo})
    plot_graph(co2_plant_dataframe, "datetime", "value",
                "Co2 immessa con impianto ", "#577590", "Grammi")
    
def plot_degradation(dictionary):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H') 
        
    lista = dictionary_to_list(dictionary,"battery_capacity")
    co2_plant_dataframe = pd.DataFrame({'datetime': time_column, 'value': lista})
    plot_graph(co2_plant_dataframe, "datetime", "value",
                "Degradazione Impianto", "#577590", "Wha")

def plot_production_algo_inverter(dictionary):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')

    lista = dictionary_to_list(dictionary, "production")
    for i in range(len(lista)):
        lista[i] = lista[i] * dictionary["polynomial_inverter"](dictionary["ratio_algo"][i])

    expected_production_dataframe = pd.DataFrame({'datetime': time_column, 'value': lista})
    plot_graph(expected_production_dataframe, "datetime", "value", "Stima Produzione PV con efficienza Inverter", "#F3722C", "Wh")

def plot_inverter_efficency(dictionary):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')

    risultato = []
    for i in range(len(dictionary["ratio_algo"])):
        risultato.append(dictionary["polynomial_inverter"](dictionary["ratio_algo"][i]))

    efficiency_dataframe = pd.DataFrame({'datetime': time_column, 'value': risultato})
    plot_graph(efficiency_dataframe, "datetime", "value", "Efficienza Inverter", "#F3722C", "%")

########################################################################################
#       NO BATTERY FUNCTION
########################################################################################
def plot_scambio_rete_nobattery(dictionary):

    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')

    power_to_grid_df = pd.DataFrame({'datetime': time_column, 'value': dictionary["power_to_grid_nobattery"]})
    power_to_grid_df["value"] = power_to_grid_df["value"].multiply(-1)

    plot_graph_hist(power_to_grid_df, "datetime", "value",
               "Stima scambio energetico con la rete elettrica (Acquisto positivo) senza Batteria", "#43AA8B", "Wh")

def plot_co2_nobattery(dictionary):

    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H') 

    co2_plant_dataframe = pd.DataFrame({'datetime': time_column, 'value': dictionary["co2_nobattery"]})
    plot_graph(co2_plant_dataframe, "datetime", "value",
                "Co2 immessa con impianto senza Batteria ", "#577590", "Grammi")
    
def plot_costi_plant_nobattery(dictionary):

    current_datetime = datetime.now() + timedelta(hours=1)
    time_column = pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')
    pv_only_dataframe = pd.DataFrame({'datetime': time_column, 'value': dictionary["sum_nobattery"]})

    plot_graph(pv_only_dataframe, "datetime", "value", "Stima costi in bolletta (guadagno positivo) (senza batteria)",
               "#577590", "Euro €")    
    
########################################################################################
#       NO PLANT
########################################################################################
def plot_co2_noplant(dictionary):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H') 

    co2_dataframe = pd.DataFrame({'datetime': time_column, 'value': dictionary["co2_noplant"]})
    co2_dataframe["value"] = co2_dataframe["value"].multiply(-1)                             
    plot_graph(co2_dataframe, "datetime", "value",
               "Co2 immessa senza impianto ", "#577590", "Grammi ")

def plot_costi_noplant(dictionary):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')

    consumption_only_dataframe = pd.DataFrame({'datetime': time_column, 'value': dictionary["sum_noplant"]})
    plot_graph(consumption_only_dataframe, "datetime", "value",
               "Stima costi in bolletta (guadagno positivo) (senza batteria e senza PV)", "#577590", "Euro €")

def plot_scambio_rete_noplant(dictionary):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H') 

    power_to_grid_df = pd.DataFrame({'datetime': time_column, 'value': dictionary["power_to_grid_noplant"]})

    plot_graph_hist(power_to_grid_df, "datetime", "value",
               "Stima scambio energetico con la rete elettrica (Acquisto positivo) senza Impianto", "#43AA8B", "Wh")

########################################################################################
#       NO ALGORITHM FUNCTION
########################################################################################

def plot_scambio_rete_noalgo(dictionary):

    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')
    power_to_grid_df = pd.DataFrame({'datetime': time_column, 'value': dictionary["power_to_grid_noalgo"]})

    power_to_grid_df["value"] = power_to_grid_df["value"].multiply(-1)

    plot_graph_hist(power_to_grid_df, "datetime", "value",
               "Stima scambio energetico con la rete elettrica (Acquisto positivo) senza Algoritmo", "#43AA8B", "Wh")

def plot_costi_noalgo(dictionary):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')
    cost_dataframe = pd.DataFrame({'datetime': time_column, 'value': dictionary["sum_noalgo"]})
    cost_dataframe["value"] = cost_dataframe["value"].multiply(-1)
    plot_graph(cost_dataframe, "datetime", "value", "Stima costi in bolletta (guadagno positivo) senza Algoritmo", "#577590", "Euro €")

def plot_energia_batteria_noalgo(dictionary):    
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column = pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1),
                                periods=25, freq='H')

    battery_wh_dataframe = pd.DataFrame({'datetime': time_column, 'value': dictionary["actual_battery_level_noalgo"]})
    plot_graph(battery_wh_dataframe, "datetime", "value", "Stima energia in batteria senza Algoritmo", "#90BE6D", "Wh")

def plot_co2_noalgo(dictionary):

    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H') 
    co2_plant_dataframe = pd.DataFrame({'datetime': time_column, 'value': dictionary["co2_noalgo"]})
    plot_graph(co2_plant_dataframe, "datetime", "value",
                "Co2 immessa con impianto senza Algoritmo ", "#577590", "Grammi")


def plot_degradation_noalgo(dictionary):

    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H') 
    co2_plant_dataframe = pd.DataFrame({'datetime': time_column, 'value':dictionary["quantity_battery_degradation_noalgo"]})
    plot_graph(co2_plant_dataframe, "datetime", "value",
                "Degradazione Impianto senza Algoritmo ", "#577590", "Wh")
    
########################################################################################
#       Comparison Plots
########################################################################################

def plot_co2_comparison_algo(dictionary):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H') 

    co2_plant_dataframe = pd.DataFrame({'datetime': time_column, 'value': dictionary["co2_algo"]})
    co2_plant_dataframe_nobattery = pd.DataFrame({'datetime': time_column, 'value': dictionary["co2_nobattery"]})
    co2_plant_dataframe_noplant = pd.DataFrame({'datetime': time_column, 'value': dictionary["co2_noplant"]})
    co2_plant_dataframe_noalgo = pd.DataFrame({'datetime': time_column, 'value': dictionary["co2_noalgo"]})
    co2_plant_dataframe_noplant["value"] = co2_plant_dataframe_noplant["value"].multiply(-1)                             

   # Creazione della figura
    plt.figure(figsize=(10, 6))

    # Tracciare tutte le curve sullo stesso grafico
    plt.plot(co2_plant_dataframe["datetime"], co2_plant_dataframe["value"], color="#577590", label="With PV and battery")
    plt.plot(co2_plant_dataframe_nobattery["datetime"], co2_plant_dataframe_nobattery["value"], color="#90BE6D", label="With PV")
    plt.plot(co2_plant_dataframe_noplant["datetime"], co2_plant_dataframe_noplant["value"], color="#F94144", label="Without PV")
    plt.plot(co2_plant_dataframe_noalgo["datetime"], co2_plant_dataframe_noalgo["value"], color="#F8961E", label="With PV and battery NO ALGORITHM")

    # Impostazioni del grafico
    plt.xlabel("Datetime")
    plt.ylabel("Grammi di Co2")
    plt.legend()  # Mostra la legenda per distinguere le curve
    plt.xticks(rotation=45)  # Ruota le etichette dell'asse x per una migliore leggibilità
    plt.grid(True)  # Aggiungi una griglia per facilitare la lettura
    plt.xticks(co2_plant_dataframe_noalgo["datetime"], co2_plant_dataframe_noalgo["datetime"].dt.strftime('%H'), rotation=10)
    plt.title("Confronto emissioni di Co2")
    # Mostra il grafico
    plt.tight_layout()


def plot_cost_comparison(dictionary):
    # Imposta l'ora corrente e crea la colonna del tempo
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column = pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')

    # Creazione dei DataFrame con i dati
    cost_dataframe_algo = pd.DataFrame({'datetime': time_column, 'value': dictionary["sum_algo"]})
    cost_dataframe_algo["value"] = cost_dataframe_algo["value"].multiply(-1)

    cost_dataframe_nobattery = pd.DataFrame({'datetime': time_column, 'value': dictionary["sum_nobattery"]})
    cost_dataframe_noplant = pd.DataFrame({'datetime': time_column, 'value': dictionary["sum_noplant"]})

    cost_dataframe_noalgo = pd.DataFrame({'datetime': time_column, 'value': dictionary["sum_noalgo"]})
    cost_dataframe_noalgo["value"] = cost_dataframe_noalgo["value"].multiply(-1)

    # Creazione della figura
    plt.figure(figsize=(10, 6))

    # Tracciare tutte le curve sullo stesso grafico
    plt.plot(cost_dataframe_algo["datetime"], cost_dataframe_algo["value"], color="#577590", label="With PV and battery")
    plt.plot(cost_dataframe_nobattery["datetime"], cost_dataframe_nobattery["value"], color="#90BE6D", label="With PV")
    plt.plot(cost_dataframe_noplant["datetime"], cost_dataframe_noplant["value"], color="#F94144", label="Without PV")
    plt.plot(cost_dataframe_noalgo["datetime"], cost_dataframe_noalgo["value"], color="#F8961E", label="With PV and battery NO ALGORITHM")

    # Impostazioni del grafico
    plt.xlabel("Datetime")
    plt.ylabel("Euro €")
    plt.legend()  # Mostra la legenda per distinguere le curve
    plt.ylim(-2, 2)  # Puoi regolare o rimuovere questi limiti
    plt.xticks(rotation=45)  # Ruota le etichette dell'asse x per una migliore leggibilità
    plt.grid(True)  # Aggiungi una griglia per facilitare la lettura
    plt.xticks(cost_dataframe_algo["datetime"], cost_dataframe_algo["datetime"].dt.strftime('%H'), rotation=10)
    plt.title("Confronto costi (Guadagno Positivo)")
    # Mostra il grafico
    plt.tight_layout()



def plot_comparison_degradation(dictionary):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H') 

    lista = dictionary_to_list(dictionary, "battery_capacity")
    degradation_plant_dataframe = pd.DataFrame({'datetime': time_column, 'value': lista})
    degradation_plant_dataframe_noalgo = pd.DataFrame({'datetime': time_column, 'value': dictionary["quantity_battery_degradation_noalgo"]})

    # Tracciare tutte le curve sullo stesso grafico
    plt.plot(degradation_plant_dataframe["datetime"], degradation_plant_dataframe["value"], color="#577590", label="With Algoritm")
    plt.plot(degradation_plant_dataframe_noalgo["datetime"], degradation_plant_dataframe_noalgo["value"], color="#F8961E", label="With PV and battery NO ALGORITHM")

    # Impostazioni del grafico
    plt.xlabel("Datetime")
    plt.ylabel("Wh")
    plt.legend()  # Mostra la legenda per distinguere le curve
    plt.xticks(rotation=45)  # Ruota le etichette dell'asse x per una migliore leggibilità
    plt.grid(True)  # Aggiungi una griglia per facilitare la lettura
    plt.xticks(degradation_plant_dataframe["datetime"], degradation_plant_dataframe["datetime"].dt.strftime('%H'), rotation=10)
    plt.title("Confronto Degradazione Batteria")
    # Mostra il grafico
    plt.tight_layout()

def plot_comparison_battery(dictionary):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1), periods=25, freq='H') 

    actual_percentage_algo = dictionary["actual_percentage_algo"]
    
    battery_wh = [float(dictionary["soc_min"] * dictionary[f"battery_capacity{i}"]) + (percentage * (float(dictionary["soc_max"] * dictionary[f"battery_capacity{i}"]) - float(dictionary["soc_min"] * dictionary[f"battery_capacity{i}"]))) for i,percentage in enumerate(actual_percentage_algo)]
    battery_wh_dataframe = pd.DataFrame({'datetime': time_column, 'value': battery_wh})

    battery_dataframe_noalgo = pd.DataFrame({'datetime': time_column, 'value': dictionary["actual_battery_level_noalgo"]})

    plt.figure(figsize=(10, 6))

    # Tracciare tutte le curve sullo stesso grafico
    plt.plot(battery_wh_dataframe["datetime"], battery_wh_dataframe["value"], color="#577590", label="With Algoritm")
    plt.plot(battery_dataframe_noalgo["datetime"], battery_dataframe_noalgo["value"], color="#F8961E", label="With PV and battery NO ALGORITHM")

    # Impostazioni del grafico
    plt.xlabel("Datetime")
    plt.ylabel("Wh")
    plt.legend()  # Mostra la legenda per distinguere le curve
    plt.xticks(rotation=45)  # Ruota le etichette dell'asse x per una migliore leggibilità
    plt.grid(True)  # Aggiungi una griglia per facilitare la lettura
    plt.xticks(battery_wh_dataframe["datetime"], battery_wh_dataframe["datetime"].dt.strftime('%H'), rotation=10)
    plt.title("Confronto Energia in Batteria")
    # Mostra il grafico
    plt.tight_layout()
