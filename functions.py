import matplotlib.pyplot as plt
import seaborn as sns
import yaml

from pannello import *

import random
import numpy as np
from multiprocessing.pool import ThreadPool
from pymoo.core.problem import StarmapParallelization
from pymoo.core.mixed import MixedVariableGA
from pymoo.core.problem import ElementwiseProblem
from pymoo.core.variable import Binary, Integer
from pymoo.optimize import minimize
from pymoo.util.display.output import Output
from pymoo.util.display.column import Column

from dateutil.relativedelta import relativedelta


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
    # Prendi l'ultimo valore
    data["socs"] = df.iloc[-1]


    data["estimate"] = get_estimate_load_consumption(get_true_load_consumption())  # It gives an estimation of the load consumption
    data["expected_production"] = get_expected_power_production_from_pv_24_hours_from_now(data)
    data["difference_of_production"] = difference_of_production(data)
    return data


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


def get_true_load_consumption():
    """
        Returns a dataframe containing the load consumption history.
        From the actual hour back to the earliest ones.
        """

    # Legge il CSV in un DataFrame
    df = pd.read_csv("csv/loadnew.csv")

    # Ottiene la data e l'ora attuali
    now = datetime.now()

    # Filtra il DataFrame fino alla data e all'ora attuali
    df_troncato = df[(pd.to_datetime(df['data'], format='%Y%m%d') < pd.to_datetime(now.strftime('%Y%m%d'))) |
                     ((pd.to_datetime(df['data'], format='%Y%m%d') == pd.to_datetime(now.strftime('%Y%m%d'))) &
                      (df['ora'] <= now.hour))]
    one_month_ago=now-relativedelta(months=1) 
    print(one_month_ago)
    #df_troncato = df_troncato[(pd.to_datetime(df['data'], format='%Y%m%d') > pd.to_datetime(one_month_ago.strftime('%Y%m%d')))]
    print(df_troncato)
    return df_troncato


def get_estimate_load_consumption(dataframe: pd.DataFrame):
    """
        Returns the consumption estimate of the load.

        df.loc[1, 'consumo']

        From the next hour up to the 24h.
    """

    media_oraria = dataframe.groupby("ora")["consumo"].mean()

    dataframe['data'] = pd.to_datetime(dataframe['data'], format='%Y%m%d')

    dataframe['giorno'] = dataframe['data'].dt.day_name()

    next_hour = datetime.now() + timedelta(hours=1) - timedelta(minutes=datetime.now().minute)
    oggi = (next_hour).strftime("%A")
    domani = (next_hour + timedelta(days=1)).strftime("%A")

    dataframe = dataframe[(dataframe['giorno'] == oggi) | (dataframe['giorno'] == domani)]

    media_giorno_target = dataframe.groupby("ora")["consumo"].mean()

    df = pd.DataFrame((media_oraria + media_giorno_target) / 2).reset_index()
    df = pd.concat([df.iloc[next_hour.hour:], df.iloc[:next_hour.hour]])

    df.reset_index(drop=True, inplace=True)
    return df


def evaluate(data, variables_values):
    sum = []
    sum.append(0)
    delta_production = difference_of_production(data)
    sold = data["sold"]
    upper_limit = (data["soc_max"] * data["battery_capacity"])
    lower_limit = (data["soc_min"] * data["battery_capacity"])
    actual_percentage = []
    actual_percentage.append(data["socs"][-1])

    quantity_delta_battery = []

    # valori negativi indicano consumi ,positivi guadagni
    for j in range(24):
        charge = variables_values[f"b{j}"]
        percentage = variables_values[f"i{j}"]
        quantity_charging_battery = None
        quantity_discharging_battery = None
        if charge:

            quantity_charging_battery = ((upper_limit - actual_percentage[j] * upper_limit) * percentage) / 100

            if quantity_charging_battery - delta_production.iloc[j] < 0:
                # devo vendere
                sum.append(
                    sum[j] + ((quantity_charging_battery - delta_production.iloc[j]) * sold))  # sum = sum - rimborso

            else:
                if (quantity_charging_battery > data["maximum_power_absorption"] + delta_production.iloc[j]):
                    quantity_charging_battery = data["maximum_power_absorption"] + delta_production.iloc[j]
                sum.append(
                    sum[j] + (quantity_charging_battery - delta_production.iloc[j]) * data["prices"]["prezzo"].iloc[j])
                
            actual_percentage.append(actual_percentage[j] + quantity_charging_battery / upper_limit)
            
        else:
            quantity_discharging_battery = ((actual_percentage[j] * upper_limit - lower_limit) * percentage) / 100
            actual_percentage.append(actual_percentage[j] - quantity_discharging_battery / upper_limit)

            if delta_production.iloc[j] + quantity_discharging_battery > 0:
                # sto scaricando la batteria  con surplus di energia
                # vendo alla rete MA dalla batteria
                # if delta_production.iloc[j] > 0:
                #     # vendo alla rete quello del fotovoltaico
                #     sum = sum - delta_production.iloc[j] * sold
                # else:
                #     # in questo else teoricamente potrei vendere enegia della batteria ma invece sovrascrivo il valore
                #     data["socs"][j + 1] = data["socs"][j] + delta_production.iloc[j] / upper_limit  # DA VEDERE: Non superare lo 0% di socs
                sum.append(sum[j] - ((delta_production.iloc[j] + quantity_discharging_battery) * sold))
            else:
                sum.append(sum[j] + (
                        - (delta_production.iloc[j] + quantity_discharging_battery) * data["prices"]["prezzo"].iloc[j]))
            

        if quantity_charging_battery != None:
            quantity_delta_battery.append(+quantity_charging_battery)
        else:
            quantity_delta_battery.append(-quantity_discharging_battery)

    return sum[1:], actual_percentage, quantity_delta_battery


def start_genetic_algorithm(data, pop_size, n_gen, n_threads):
    class MixedVariableProblem(ElementwiseProblem):

        def __init__(self, n_couples=24, **kwargs):
            variables = {}
            for j in range(n_couples):
                variables[f"b{j}"] = Binary()
                variables[f"i{j}"] = Integer(bounds=(0, 100))
            super().__init__(vars=variables, n_obj=1, **kwargs)

        def _evaluate(self, X, out, *args, **kwargs):
            # 1 carico batteria ,0 la scarico
            # 000 123 076 123 099 135
            # Cosa dobbiamo fare?
            # Ora per ora
            sum = 0
            delta_production = data["difference_of_production"]
            sold = data["sold"]
            upper_limit = (data["soc_max"] * data["battery_capacity"])
            lower_limit = (data["soc_min"] * data["battery_capacity"])
            actual_percentage = [data["socs"][-1]]
            quantity_battery=0
            # valori negativi indicano consumi ,positivi guadagni
            for j in range(24):
                charge = X[f"b{j}"]
                percentage = X[f"i{j}"]
                if charge:

                    quantity_charging_battery = ((upper_limit - actual_percentage[j] * upper_limit) * percentage) / 100


                    if quantity_charging_battery - delta_production.iloc[j] < 0:
                        # devo vendere
                        sum = sum + ((quantity_charging_battery - delta_production.iloc[
                            j]) * sold)  # sum = sum - rimborso

                    else:
                        if( quantity_charging_battery > data["maximum_power_absorption"] + delta_production.iloc[j]):
                            quantity_charging_battery = data["maximum_power_absorption"] + delta_production.iloc[j]

                        sum = sum + (quantity_charging_battery - delta_production.iloc[j]) * \
                              data["prices"]["prezzo"].iloc[j]
                    
                    quantity_battery+=abs(quantity_charging_battery)
                    actual_percentage.append(actual_percentage[j] + quantity_charging_battery / upper_limit)

                else:
                    quantity_discharging_battery = ((actual_percentage[
                                                         j] * upper_limit - lower_limit) * percentage) / 100
                    actual_percentage.append(actual_percentage[j] - quantity_discharging_battery / upper_limit)

                    if delta_production.iloc[j] + quantity_discharging_battery > 0:
                        # sto scaricando la batteria  con surplus di energia
                        # vendo alla rete MA dalla batteria
                        # if delta_production.iloc[j] > 0:
                        #     # vendo alla rete quello del fotovoltaico
                        #     sum = sum - delta_production.iloc[j] * sold
                        # else:
                        #     # in questo else teoricamente potrei vendere enegia della batteria ma invece sovrascrivo il valore
                        #     data["socs"][j + 1] = data["socs"][j] + delta_production.iloc[j] / upper_limit  # DA VEDERE: Non superare lo 0% di socs
                        sum = sum - ((delta_production.iloc[j] + quantity_discharging_battery) * sold)
                    else:
                        sum = sum + (- (delta_production.iloc[j] + quantity_discharging_battery) *
                                     data["prices"]["prezzo"].iloc[j])
                    
                    quantity_battery+=abs(quantity_discharging_battery)

            

            out["F"] = sum+quantity_battery/(data["battery_capacity"]*5)


    class MyOutput(Output):

        def __init__(self):
            super().__init__()
            self.f_min = Column("score", width=8)
            self.columns += [self.f_min]

        def update(self, algorithm):
            super().update(algorithm)
            self.f_min.set('{:.3F}'.format(-np.min(algorithm.pop.get("F"))))

    pool = ThreadPool(n_threads)
    runner = StarmapParallelization(pool.starmap)
    problem = MixedVariableProblem(elementwise_runner=runner)

    algorithm = MixedVariableGA(pop_size)

    res = minimize(problem,
                   algorithm,
                   termination=('n_gen', n_gen),
                   seed=104,  # random.randint(0, 99999),
                   verbose=True,
                   output=MyOutput(),
                   save_history=True)

    print("Tempo:", res.exec_time)

    return res, res.history


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



    # PERCENTUALE BATTERIA
    actual_percentage_dataframe = pd.DataFrame({'datetime': time_column, 'value': actual_percentage})
    actual_percentage_dataframe["value"] = actual_percentage_dataframe["value"].multiply(100 * data["soc_max"])

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



