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


    # ASCISSA TEMPORALE DEI GRAFICI
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column = pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')

    # COSTI ESPRESSI IN EURO                                - Controllati OK   - Fino a 23  - Negativo quando pago, Positivo quando mi rimborsano  -  Ogni punto è la somma dei precedenti
    cost_dataframe = pd.DataFrame({'datetime': time_column, 'value': sum})
    cost_dataframe["value"] = cost_dataframe["value"].multiply(-1)
    # STIMA DEL CARICO NELLE PROSSIME 24H                   - Controllati OK   - Fino a 23   - Positivo
    expected_load_dataframe = pd.DataFrame({'datetime': time_column, 'value': data["estimate"]["consumo"].tolist()})

    # STIMA DELLA PRODUZIONE NELLE PROSSIME 24 H            - Controllati OK   - Fino a 23   - Positivo
    expected_production_dataframe = pd.DataFrame(
        {'datetime': time_column, 'value': data["expected_production"]["production"].tolist()})
    # QUANTA ENERGIA STIMATA ENTRA ED ESCE DALLA BATTERIA   - Controllati OK   - Fino a 23   - Positivo quando entra, negativo quando esce
    quantity_delta_battery_dataframe = pd.DataFrame({'datetime': time_column, 'value': quantity_delta_battery})
    # QUANTA ENERGIA HO IN BATTERIA                         - Controllati OK   - Fino a 24   - Positivo
    time_column = pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1),
                                periods=25, freq='H')

    min_value = float(data["soc_min"] * data["battery_capacity"])
    max_value = float(data["soc_max"] * data["battery_capacity"])
    battery_wh = [min_value + (percentage * (max_value - min_value)) for percentage in actual_percentage]
    battery_wh_dataframe = pd.DataFrame({'datetime': time_column, 'value': battery_wh})

    print(battery_wh_dataframe)

    # PERCENTUALE BATTERIA
    actual_percentage_dataframe = pd.DataFrame({'datetime': time_column, 'value': actual_percentage})
    actual_percentage_dataframe["value"] = actual_percentage_dataframe["value"].multiply(data["soc_max"] - data["soc_min"])
    actual_percentage_dataframe["value"] = actual_percentage_dataframe["value"].add(data["soc_min"])
    actual_percentage_dataframe["value"] = actual_percentage_dataframe["value"].multiply(100)

    # SCAMBIO ENERGETICO CON LA RETE                        - Controllati OK   - Fino a 23   - Positivo quando prendo, negativo quando vendo
    quantity_delta_battery_dataframe2 = quantity_delta_battery_dataframe[1:].reset_index()
    time_column = pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')
    difference = expected_load_dataframe["value"] - (
            expected_production_dataframe["value"] - quantity_delta_battery_dataframe2["value"])
    difference_dataframe = pd.DataFrame({'datetime': time_column, 'value': difference})

    # Grafici

    plot_graph(expected_production_dataframe, "datetime", "value", "Stima Produzione PV", "#F3722C", "Wh")


    plot_graph(expected_load_dataframe, "datetime", "value", "Stima Carico", "#F94144", "Wh")


    plot_graph_hist(difference_dataframe, "datetime", "value",
               "Stima scambio energetico con la rete elettrica (acquisto positivo)", "#43AA8B", "Wh")

    plot_graph(cost_dataframe, "datetime", "value", "Stima costi in bolletta (guadagno positivo)", "#577590", "Euro €")

    plot_graph_hist(quantity_delta_battery_dataframe, "datetime", "value", "Stima carica/scarica batteria (carica positiva)",
               "#4D908E", "Wh")

    plot_graph(battery_wh_dataframe, "datetime", "value", "Stima energia in batteria", "#90BE6D", "Wh")


    plot_graph(actual_percentage_dataframe, "datetime", "value", "Stima percentuale batteria", "#90BE6D", "%")
    plt.ylim(-5, 100)

    ########################################################################################
    # This is the part where we consider only the pv without taking into account the battery#
    ########################################################################################

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


    ########################################################################################
    # This is the part where we consider only the consumption and PV and the battery#########
    ########################################################################################

    consumption_list = []
    consumption_list.append(0)
    i = 0
    for value in data["estimate"]["consumo"].values:
        consumption_list.append((-value * data["prices"]["prezzo"][i]) + consumption_list[i])
        i = i + 1

    consumption_only_dataframe = pd.DataFrame({'datetime': time_column, 'value': consumption_list[1:]})
    plot_graph(consumption_only_dataframe, "datetime", "value",
               "Stima costi in bolletta (guadagno positivo) (senza batteria e senza PV)", "#577590", "Euro €")


    plt.figure(facecolor='#edf1ef')

    plot_subgraph(cost_dataframe, "datetime", "value", "#577590", "With PV and battery", 1)
    plot_subgraph(pv_only_dataframe, "datetime", "value", "#90BE6D", "With PV", 1)

    plot_subgraph(consumption_only_dataframe, "datetime", "value", "#F94144", "Without PV", 1)
    plt.ylabel("Euro €")
    plt.legend()
    plt.ylim(-1.5,1.5)
    plt.show()


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

