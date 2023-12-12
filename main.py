import asyncio
import random

from pymoo.core.mixed import MixedVariableGA
from pymoo.core.problem import ElementwiseProblem
from pymoo.core.variable import Binary, Integer
from pymoo.optimize import minimize

from functions import *

import csv

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
        sold = 0.2/1000
        upper_limit = (data["soc_max"] * data["battery_capacity"])
        lower_limit = (data["soc_min"] * data["battery_capacity"])
        actual_percentage=[]
        actual_percentage.append(data["socs"][-1])
        # valori negativi indicano consumi ,positivi guadagni
        for j in range(24):
            charge = X[f"b{j}"]
            percentage = X[f"i{j}"]
            if charge:

                quantity_charging_battery = ((upper_limit - actual_percentage[j]*upper_limit) * percentage) / 100
                actual_percentage.append(actual_percentage[j]  + quantity_charging_battery/upper_limit)

                if quantity_charging_battery - delta_production.iloc[j] < 0:
                    # devo vendere
                    sum = sum + ((quantity_charging_battery - delta_production.iloc[j]) * sold)  # sum = sum - rimborso
                    
                else:
                    sum = sum + (quantity_charging_battery - delta_production.iloc[j]) * data["prices"]["prezzo"].iloc[j]
            else:
                quantity_discharging_battery = ((actual_percentage[j] * upper_limit - lower_limit) * percentage) / 100
                actual_percentage.append(actual_percentage[j] - quantity_discharging_battery/upper_limit)

                if delta_production.iloc[j] + quantity_discharging_battery > 0:
                    # sto scaricando la batteria  con surplus di energia
                    # vendo alla rete MA dalla batteria
                                # if delta_production.iloc[j] > 0:
                                #     # vendo alla rete quello del fotovoltaico
                                #     sum = sum - delta_production.iloc[j] * sold
                                # else:
                                #     # in questo else teoricamente potrei vendere enegia della batteria ma invece sovrascrivo il valore
                                #     data["socs"][j + 1] = data["socs"][j] + delta_production.iloc[j] / upper_limit  # DA VEDERE: Non superare lo 0% di socs
                    sum=sum-((delta_production.iloc[j] + quantity_discharging_battery)*sold)
                else:
                    sum = sum + (- (delta_production.iloc[j] + quantity_discharging_battery) *data["prices"]["prezzo"].iloc[j])


        out["F"] = sum


async def main():
    # energy_request(data)

    meteo_df = filter_meteo_between_ss_and_sr(data)

    meteo_df["expected_power_production"] = get_expected_power_production_from_pv(data, meteo_df["direct_radiation"],
                                                                                  meteo_df["diffuse_radiation"],
                                                                                  meteo_df["temperature_2m"])

    data["prices"] = await get_intra_days_market()

    get_estimate_load_consumption(get_true_load_consumption())

    problem = MixedVariableProblem()

    # Set the population size to 1
    pop_size = 1
    algorithm = MixedVariableGA(pop_size)

    res = minimize(problem,
                   algorithm,
                   termination=('n_evals', 2),
                   seed=random.randint(0, 99999),
                   verbose=False) 

    expected_production=get_expected_power_production_from_pv_of_tomorrow(data)

    plot_graph(expected_production,expected_production["time"],expected_production["production"], "time", "production", "Expected Production", "Blue")
    



    sum = []
    sum.append(0)
    delta_production = difference_of_production(data)
    sold = data["sold"]
    sold = 0.2/1000
    upper_limit = (data["soc_max"] * data["battery_capacity"])
    lower_limit = (data["soc_min"] * data["battery_capacity"])
    actual_percentage=[]
    actual_percentage.append(data["socs"][-1])
    # valori negativi indicano consumi ,positivi guadagni
    for j in range(24):
        charge = res.X[f"b{j}"]
        percentage = res.X[f"i{j}"]
        if charge:

            quantity_charging_battery = ((upper_limit - actual_percentage[j]*upper_limit) * percentage) / 100
            actual_percentage.append(actual_percentage[j]  + quantity_charging_battery/upper_limit)

            if quantity_charging_battery - delta_production.iloc[j] < 0:
                # devo vendere
                sum.append(sum[j] + ((quantity_charging_battery - delta_production.iloc[j]) * sold))  # sum = sum - rimborso
                
            else:
                sum.append(sum[j] + (quantity_charging_battery - delta_production.iloc[j]) * data["prices"]["prezzo"].iloc[j])
        else:
            quantity_discharging_battery = ((actual_percentage[j] * upper_limit - lower_limit) * percentage) / 100
            actual_percentage.append(actual_percentage[j] - quantity_discharging_battery/upper_limit)

            if delta_production.iloc[j] + quantity_discharging_battery > 0:
                # sto scaricando la batteria  con surplus di energia
                # vendo alla rete MA dalla batteria
                            # if delta_production.iloc[j] > 0:
                            #     # vendo alla rete quello del fotovoltaico
                            #     sum = sum - delta_production.iloc[j] * sold
                            # else:
                            #     # in questo else teoricamente potrei vendere enegia della batteria ma invece sovrascrivo il valore
                            #     data["socs"][j + 1] = data["socs"][j] + delta_production.iloc[j] / upper_limit  # DA VEDERE: Non superare lo 0% di socs
                sum.append(sum[j]-((delta_production.iloc[j] + quantity_discharging_battery)*sold))
            else:
                sum.append(sum[j] + (- (delta_production.iloc[j] + quantity_discharging_battery) *data["prices"]["prezzo"].iloc[j]))

            


    soc_dataframe=pd.DataFrame({"time": np.arange(len(actual_percentage)), "soc": actual_percentage})
    sum_dataframe=pd.DataFrame({"time": np.arange(len(sum)), "sum": sum})

    plot_graph(soc_dataframe,soc_dataframe["time"],soc_dataframe["soc"], "time", "soc", "Expected Soc", "Green")
    plot_graph(sum_dataframe,sum_dataframe["time"],sum_dataframe["sum"], "time", "Pecunia", "Expected Money", "Red")
    

    plt.show()




    print("Best solution found: \nX = %s\nF = %s" % (res.X, res.F))


if __name__ == "__main__":
    asyncio.run(main())
