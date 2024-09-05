from datetime import *
from pannello import *
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd



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


def simulation_plot(data, sum, actual_percentage, quantity_delta_battery):

    ########################################################################################
    # This is the part where we consider the whole plant#
    ########################################################################################
    plot_production(data)
    plot_load(data)
    plot_costi_plant(data,sum)
    plot_scambio_rete(data,quantity_delta_battery)
    plot_energia_batteria(data,actual_percentage)
    plot_percentage_battery(data,actual_percentage)
    plot_battery_status(data,quantity_delta_battery)
    plot_co2_plant(data,quantity_delta_battery)

    ########################################################################################
    # This is the part where we consider only the pv without taking into account the battery#
    ########################################################################################
    
    plot_costi_plant_nobattery(data)

    ########################################################################################
    # This is the part where we consider only the consumption and no PV and the battery#########
    ########################################################################################

    plot_co2_noplant(data)
    plot_costi_noplant(data)
    plot_cost_comparison(data,sum)
   
def simulation_plant(data, sum, actual_percentage, quantity_delta_battery):
    plot_load(data)
    plot_production(data)
    plot_costi_plant(data,sum)
    plot_scambio_rete(data,quantity_delta_battery)
    plot_energia_batteria(data,actual_percentage)
    plot_percentage_battery(data,actual_percentage)
    plot_battery_status(data,quantity_delta_battery)
    plot_co2_plant(data,quantity_delta_battery)
    plot_cost_comparison(data,sum)

def simulation_plant_nobattery(data):
    plot_load(data)
    plot_production(data)
    plot_costi_plant_nobattery(data)

def simulation_noplant(data):
    plot_load(data)
    plot_costi_noplant(data)
    plot_co2_noplant(data)



def plot_GME_prices(data):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column = pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')
    plt.figure("Prezzo energia nelle successive 24 ore", facecolor='#edf1ef')

    sns.set(font_scale=1.48)
    ax = sns.lineplot(data, x=time_column, y=data["prices"]["prezzo"], color="#577590")
    ax.plot(time_column, data["prices"]["prezzo"], color="#577590")

    plt.xticks(time_column, time_column.strftime('%d/%m Ore:%H:%M'), rotation=90)
    plt.title("Prezzo energia nelle successive 24 ore")
    plt.xlabel('Ora')
    plt.ylabel('Costo € per Watt')
    plt.ylim(0, abs(max( data["prices"]["prezzo"])) + abs(0.1 * max( data["prices"]["prezzo"])))


def plot_production(data):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')
    expected_production_dataframe = pd.DataFrame({'datetime': time_column, 'value': data["expected_production"]["production"].tolist()})
    plot_graph(expected_production_dataframe, "datetime", "value", "Stima Produzione PV", "#F3722C", "Wh")

def plot_load(data):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')
    expected_load_dataframe = pd.DataFrame({'datetime': time_column, 'value': data["estimate"]["consumo"].tolist()})
    plot_graph(expected_load_dataframe, "datetime", "value", "Stima Carico", "#F94144", "Wh")

def plot_costi_plant(data,sum):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')
    cost_dataframe = pd.DataFrame({'datetime': time_column, 'value': sum})
    cost_dataframe["value"] = cost_dataframe["value"].multiply(-1)
    plot_graph(cost_dataframe, "datetime", "value", "Stima costi in bolletta (guadagno positivo)", "#577590", "Euro €")

def plot_scambio_rete(data,quantity_delta_battery):

    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')

    quantity_delta_battery_dataframe = pd.DataFrame({'datetime': time_column, 'value': quantity_delta_battery})
    expected_load_dataframe = pd.DataFrame({'datetime': time_column, 'value': data["estimate"]["consumo"].tolist()})
    expected_production_dataframe = pd.DataFrame({'datetime': time_column, 'value': data["expected_production"]["production"].tolist()})

    quantity_delta_battery_dataframe2 = quantity_delta_battery_dataframe[1:].reset_index()    
    difference = expected_load_dataframe["value"] - (
            expected_production_dataframe["value"] - quantity_delta_battery_dataframe2["value"])
    
    difference_dataframe = pd.DataFrame({'datetime': time_column, 'value': difference})

    plot_graph_hist(difference_dataframe, "datetime", "value",
               "Stima scambio energetico con la rete elettrica (acquisto positivo)", "#43AA8B", "Wh")

def plot_energia_batteria(data,actual_percentage):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column = pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1),
                                periods=25, freq='H')

    min_value = float(data["soc_min"] * data["battery_capacity"])
    max_value = float(data["soc_max"] * data["battery_capacity"])
    battery_wh = [min_value + (percentage * (max_value - min_value)) for percentage in actual_percentage]
    battery_wh_dataframe = pd.DataFrame({'datetime': time_column, 'value': battery_wh})
    plot_graph(battery_wh_dataframe, "datetime", "value", "Stima energia in batteria", "#90BE6D", "Wh")


def plot_percentage_battery(data,actual_percentage):
      
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column = pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1),
                                periods=25, freq='H')
    
    actual_percentage_dataframe = pd.DataFrame({'datetime': time_column, 'value': actual_percentage})
    actual_percentage_dataframe["value"] = actual_percentage_dataframe["value"].multiply(data["soc_max"] - data["soc_min"])
    actual_percentage_dataframe["value"] = actual_percentage_dataframe["value"].add(data["soc_min"])
    actual_percentage_dataframe["value"] = actual_percentage_dataframe["value"].multiply(100)
    plot_graph(actual_percentage_dataframe, "datetime", "value", "Stima percentuale batteria", "#90BE6D", "%")

def plot_battery_status(data,quantity_delta_battery):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')  
    quantity_delta_battery_dataframe = pd.DataFrame({'datetime': time_column, 'value': quantity_delta_battery})
    plot_graph_hist(quantity_delta_battery_dataframe, "datetime", "value", "Stima carica/scarica batteria (carica positiva)",
               "#4D908E", "Wh")

def plot_co2_plant(data,quantity_delta_battery):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H') 

    quantity_delta_battery_dataframe = pd.DataFrame({'datetime': time_column, 'value': quantity_delta_battery})
    expected_load_dataframe = pd.DataFrame({'datetime': time_column, 'value': data["estimate"]["consumo"].tolist()})
    expected_production_dataframe = pd.DataFrame({'datetime': time_column, 'value': data["expected_production"]["production"].tolist()})

    quantity_delta_battery_dataframe2 = quantity_delta_battery_dataframe[1:].reset_index()    
    difference = expected_load_dataframe["value"] - (
            expected_production_dataframe["value"] - quantity_delta_battery_dataframe2["value"]) 
    
    co2_plant_dataframe = pd.DataFrame({'datetime': time_column, 'value': co2_datas(difference)})
    plot_graph(co2_plant_dataframe, "datetime", "value",
                "Co2 immessa con impianto ", "#577590", "Grammi")

def plot_costi_plant_nobattery(data):

    result_only_pv = difference_of_production(data)
    result = []
    result.append(0)
    if result_only_pv[0] < 0:
        result.append((result_only_pv[0]) * data["prices"]["prezzo"][0])
    else:
        result.append((result_only_pv[0]) * data["sold"])

    for i in range(1, 24):
        if result_only_pv[i] < 0:
            result.append((result_only_pv[i]) * data["prices"]["prezzo"][i] + result[i])
        else:
            result.append((result_only_pv[i]) * data["sold"] + result[i])

    current_datetime = datetime.now() + timedelta(hours=1)
    time_column = pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')
    pv_only_dataframe = pd.DataFrame({'datetime': time_column, 'value': result[1:]})

    plot_graph(pv_only_dataframe, "datetime", "value", "Stima costi in bolletta (guadagno positivo) (senza batteria)",
               "#577590", "Euro €")

def plot_co2_noplant(data):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H') 
    consumption_list = []
    consumption_list.append(0)
    co2_list = []
    co2_list.append(0)
    i = 0
    consumo=0
    for value in data["estimate"]["consumo"].values:
        consumption_list.append((-value * data["prices"]["prezzo"][i]) + consumption_list[i])

        carbone = value * 0.0527 * 0.82     #mix energetico * quanto quel mix inquina(dati da cambaire forse)
        gas = value * 0.43 * 0.315
        co2_list.append(  carbone + gas +co2_list[i])
        i = i + 1
    co2_dataframe = pd.DataFrame({'datetime': time_column, 'value': co2_list[1:]})
    plot_graph(co2_dataframe, "datetime", "value",
               "Co2 immessa senza impianto ", "#577590", "Grammi ")

def plot_costi_noplant(data):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')
    consumption_list = []
    consumption_list.append(0)
    i=0
    
    for value in data["estimate"]["consumo"].values:
        consumption_list.append((-value * data["prices"]["prezzo"][i]) + consumption_list[i])
        i = i + 1

    consumption_only_dataframe = pd.DataFrame({'datetime': time_column, 'value': consumption_list[1:]})
    plot_graph(consumption_only_dataframe, "datetime", "value",
               "Stima costi in bolletta (guadagno positivo) (senza batteria e senza PV)", "#577590", "Euro €")

def plot_cost_comparison(data,sum):
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')

    consumption_list = []
    consumption_list.append(0)
    i=0
    for value in data["estimate"]["consumo"].values:
        consumption_list.append((-value * data["prices"]["prezzo"][i]) + consumption_list[i])
        i = i + 1

    consumption_only_dataframe = pd.DataFrame({'datetime': time_column, 'value': consumption_list[1:]})

    result_only_pv = difference_of_production(data)
    result = []
    result.append(0)
    if result_only_pv[0] < 0:
        result.append((result_only_pv[0]) * data["prices"]["prezzo"][0])
    else:
        result.append((result_only_pv[0]) * data["sold"])

    for i in range(1, 24):
        if result_only_pv[i] < 0:
            result.append((result_only_pv[i]) * data["prices"]["prezzo"][i] + result[i])
        else:
            result.append((result_only_pv[i]) * data["sold"] + result[i])

    pv_only_dataframe = pd.DataFrame({'datetime': time_column, 'value': result[1:]})

    cost_dataframe = pd.DataFrame({'datetime': time_column, 'value': sum})
    cost_dataframe["value"] = cost_dataframe["value"].multiply(-1)

    plot_subgraph(cost_dataframe, "datetime", "value", "#577590", "With PV and battery", 1)
    plot_subgraph(pv_only_dataframe, "datetime", "value", "#90BE6D", "With PV", 1)
    plot_subgraph(consumption_only_dataframe, "datetime", "value", "#F94144", "Without PV", 1)
    plt.ylabel("Euro €")
    plt.legend()
    plt.ylim(-3,3)

def plot_co2_comparison(data,quantity_delta_battery):

    current_datetime = datetime.now() + timedelta(hours=1)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H') 
    consumption_list = []
    consumption_list.append(0)
    co2_list = []
    co2_list.append(0)
    i = 0
    consumo=0
    for value in data["estimate"]["consumo"].values:
        consumption_list.append((-value * data["prices"]["prezzo"][i]) + consumption_list[i])

        carbone = value * 0.0527 * 0.82     #mix energetico * quanto quel mix inquina(dati da cambaire forse)
        gas = value * 0.43 * 0.315
        co2_list.append(  carbone + gas +co2_list[i])
        i = i + 1
    co2_dataframe = pd.DataFrame({'datetime': time_column, 'value': co2_list[1:]})

    quantity_delta_battery_dataframe = pd.DataFrame({'datetime': time_column, 'value': quantity_delta_battery})
    expected_load_dataframe = pd.DataFrame({'datetime': time_column, 'value': data["estimate"]["consumo"].tolist()})
    expected_production_dataframe = pd.DataFrame({'datetime': time_column, 'value': data["expected_production"]["production"].tolist()})

    quantity_delta_battery_dataframe2 = quantity_delta_battery_dataframe[1:].reset_index()    
    difference = expected_load_dataframe["value"] - (
            expected_production_dataframe["value"] - quantity_delta_battery_dataframe2["value"]) 

    co2_plant_dataframe = pd.DataFrame({'datetime': time_column, 'value': co2_datas(difference)})

    plot_subgraph(co2_dataframe, "datetime", "value", "#577590", "Without PV and battery", 1)
    plot_subgraph(co2_plant_dataframe, "datetime", "value", "#90BE6D", "With PV and battery", 1)
    plt.ylabel("Co2 in Grammi")
    plt.legend()
    plt.ylim(-10,3800)




def co2_datas(difference):
    
    co2_list_plant = []
    co2_list_plant.append(0)
    i=0
    for value in difference:
        if value > 0:
            carbone = value * 0.0527 * 0.82     #mix energetico * quanto quel mix inquina(dati da cambaire forse)
            gas = value * 0.43 * 0.315
            co2_list_plant.append(  carbone + gas +co2_list_plant[i])
        else:
            co2_list_plant.append(co2_list_plant[i])
        i=i+1
    return co2_list_plant[1:]