import asyncio
import random

from pymoo.core.mixed import MixedVariableGA
from pymoo.core.problem import ElementwiseProblem
from pymoo.core.variable import Binary, Integer
from pymoo.optimize import minimize

from costi import *
from functions import *

import warnings


warnings.filterwarnings("ignore", category=FutureWarning)

data = setup()


class MixedVariableProblem(ElementwiseProblem):

    def __init__(self, n_couples=24, **kwargs):
        variables = {}
        for j in range(n_couples):
            variables[f"b{j}"] = Binary()
            variables[f"i{j}"] = Integer(bounds=(0, 100))
        super().__init__(vars=variables, n_obj=1, **kwargs)

    def _evaluate(self, X, out, *args, **kwargs):
        # Your evaluation logic here
        # 1 carico batteria ,0 la scarico
        # 000 123 076 123 099 135
        # Cosa dobbiamo fare?
        # Ora per ora
        sum = 0
        delta_production = difference_of_production(data)
        sold = data["sold"]
        upper_limit = (data["soc_max"] * data["battery_capacity"])
        lower_limit = (data["soc_min"] * data["battery_capacity"])
        actual_percentage = [data["socs"][-1]]
        # valori negativi indicano consumi ,positivi guadagni
        for j in range(24):
            charge = X[f"b{j}"]
            percentage = X[f"i{j}"]
            if charge:

                quantity_charging_battery = ((upper_limit - actual_percentage[j] * upper_limit) * percentage) / 100
                actual_percentage.append(actual_percentage[j] + quantity_charging_battery / upper_limit)

                if quantity_charging_battery - delta_production.iloc[j] < 0:
                    # devo vendere
                    sum = sum + ((quantity_charging_battery - delta_production.iloc[j]) * sold)  # sum = sum - rimborso

                else:
                    sum = sum + (quantity_charging_battery - delta_production.iloc[j]) * data["prices"]["prezzo"].iloc[
                        j]
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
                    sum = sum - ((delta_production.iloc[j] + quantity_discharging_battery) * sold)
                else:
                    sum = sum + (- (delta_production.iloc[j] + quantity_discharging_battery) *
                                 data["prices"]["prezzo"].iloc[j])

        out["F"] = sum


async def main():

    data["prices"] = await get_intra_days_market()  #Bring the prices of energy from Mercati Elettrici
    data["estimate"] = get_estimate_load_consumption(get_true_load_consumption()) #It gives an estimation of the load consumption
    expected_production = get_expected_power_production_from_pv_24_hours_from_now(data)

    problem = MixedVariableProblem()
    pop_size = 1
    algorithm = MixedVariableGA(pop_size)

    res = minimize(problem,
                algorithm,
                termination=('n_evals', 5),
                seed=1, #random.randint(0, 99999),
                verbose=False)       
    
    sum, actual_percentage, quantity_delta_battery = evaluate(data, res)


    ### Start Code for Plots ##

    #ASCISSA TEMPORALE DEI GRAFICI
    current_datetime = datetime.now()+timedelta(hours=1)
    time_column = pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0),periods=24, freq='H')

    #COSTI ESPRESSI IN EURO                                - Controllati OK   - Fino a 23  - Negativo quando pago, Positivo quando mi rimborsano  -  Ogni punto è la somma dei precedenti
    cost_dataframe = pd.DataFrame({'datetime': time_column, 'value': sum})
    
    #STIMA DEL CARICO NELLE PROSSIME 24H                   - Controllati OK   - Fino a 23   - Positivo
    expected_load_dataframe = pd.DataFrame({'datetime': time_column, 'value': data["estimate"]["consumo"].tolist()})
    
    #STIMA DELLA PRODUZIONE NELLE PROSSIME 24 H            - Controllati OK   - Fino a 23   - Positivo
    expected_production_dataframe = pd.DataFrame({'datetime': time_column, 'value': expected_production["production"].tolist()})
    
    #QUANTA ENERGIA STIMATA ENTRA ED ESCE DALLA BATTERIA   - Controllati OK   - Fino a 23   - Positivo quando entra, negativo quando esce
    quantity_delta_battery_dataframe = pd.DataFrame({'datetime': time_column, 'value': quantity_delta_battery})

    #QUANTA ENERGIA HO IN BATTERIA                         - Controllati OK   - Fino a 24   - Positivo
    time_column = pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1),
                                periods=25, freq='H')
    battery_wh = [percentage * float(data["soc_max"] * data["battery_capacity"]) for percentage in actual_percentage]
    battery_wh_dataframe = pd.DataFrame({'datetime': time_column, 'value': battery_wh})
    
    #SCAMBIO ENERGETICO CON LA RETE                        - Controllati OK   - Fino a 24   - Positivo quando prendo, negativo quando vendo
    time_column = pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')
    difference = expected_load_dataframe["value"] - (expected_production_dataframe["value"] - quantity_delta_battery_dataframe["value"])
    difference_dataframe = pd.DataFrame({'datetime': time_column, 'value': difference})



    plot_graph(cost_dataframe, "datetime", "value",  "Costo Grid", "Orange", "Cost")
    plot_graph(expected_load_dataframe, "datetime", "value", "Grafico", "Red", "Expected Load")
    plot_graph(expected_production_dataframe, "datetime", "value", "Grafico","Blue", "Expected Production")
    plot_graph(battery_wh_dataframe, "datetime", "value", "Grafico", "Green", "Battery Level Wh")    
    plot_graph(difference_dataframe, "datetime", "value", "Grafico", "Purple", "Difference")
    plot_graph(quantity_delta_battery_dataframe, "datetime", "value", "Grafico", "Yellow", "Delta Battery")
    plt.legend()

    plt.figure()
    plot_subgraph(cost_dataframe, "datetime", "value", "Orange", "Cost", 1)
    plot_subgraph(expected_load_dataframe, "datetime", "value", "Red", "Expected Load", 2)
    plot_subgraph(expected_production_dataframe, "datetime", "value", "Blue", "Expected Production", 3)
    plot_subgraph(battery_wh_dataframe, "datetime", "value", "Green", "Battery Level Wh", 4)
    plot_subgraph(difference_dataframe, "datetime", "value", "Purple", "Difference", 5)
    plot_subgraph(quantity_delta_battery_dataframe, "datetime", "value", "Yellow", "Delta Battery", 6)


    print("Best solution found: \nX = %s\nF = %s" % (res.X, res.F))


    #This part of code puts the update value of the battery in the file csv/socs.csv
    if res.X["b0"] == True:

        new_value = data["socs"]+( (1 - data["socs"])*(res.X["i0"]/100))
    else:
        new_value = data["socs"]-( (data["socs"])*(res.X["i0"]/100))
    df_nuovo = pd.DataFrame([new_value])
    df_nuovo.to_csv('csv/socs.csv', mode='a', header=False, index=False)


    ########################################################################################
    #This is the part where we consider only the pv without taking into account the battery#
    ########################################################################################


    result_only_pv = difference_of_production(data)
    result = []
    result.append(0)
    if result_only_pv[0] < 0:
        result.append((-result_only_pv[0])*data["prices"]["prezzo"][0])
    else:
        result.append((-result_only_pv[0])*data["sold"])


    for i in range(1,24):
        if result_only_pv[i] < 0:
            result.append((-result_only_pv[i])*data["prices"]["prezzo"][i]+result[i])
        else:
            result.append((-result_only_pv[i])*data["sold"]+result[i])
    

    current_datetime = datetime.now()+timedelta(hours=1)
    time_column = pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0),periods=24, freq='H')
    pv_only_dataframe = pd.DataFrame({'datetime': time_column, 'value': result[1:]})

    plt.figure()

    plt.subplot(1, 3, 1)
    plt.plot(pv_only_dataframe["datetime"],pv_only_dataframe["value"], color="Orange")
    plt.xticks(pv_only_dataframe['datetime'], pv_only_dataframe['datetime'].dt.strftime('%H'), rotation=10)
    plt.title("Cost without Battery")

    plt.subplot(1, 3, 2)
    plt.plot(expected_load_dataframe["datetime"],expected_load_dataframe["value"], color="Green")
    plt.xticks(expected_load_dataframe['datetime'], expected_load_dataframe['datetime'].dt.strftime('%H'), rotation=10)
    plt.title("Expected Load")
    plt.ylim(-10000, 10000)

    plt.subplot(1, 3, 3)
    plt.plot(expected_production_dataframe["datetime"],expected_production_dataframe["value"], color="Blue")
    plt.xticks(expected_production_dataframe['datetime'], expected_production_dataframe['datetime'].dt.strftime('%H'), rotation=10)
    plt.title("Expected Production")
    plt.ylim(-10000, 10000)


    


    ########################################################################################
    #This is the part where we consider only the consumption and PV and the battery#########
    ########################################################################################

    consumption_list=[]
    consumption_list.append(0)
    i=0
    for value in data["estimate"]["consumo"].values:
        consumption_list.append((-value*data["prices"]["prezzo"][i])+consumption_list[i])
        i=i+1
    

    consumption_only_dataframe = pd.DataFrame({'datetime': time_column, 'value': consumption_list[1:]})
    plot_graph(consumption_only_dataframe, "datetime", "value",  "Solo Consumo", "Orange", "Only Cost")



    plt.show()



if __name__ == "__main__":
    asyncio.run(main())
