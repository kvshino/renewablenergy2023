import asyncio
import random

from pymoo.core.mixed import MixedVariableGA
from pymoo.core.problem import ElementwiseProblem
from pymoo.core.variable import Binary, Integer
from pymoo.optimize import minimize

from functions import *

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
        # valori negativi indicano consumi ,positivi guadagni
        for j in range(24):
            charge = X[f"b{j}"]
            percentage = X[f"i{j}"]
            if charge:
                quantity_charging_battery = ((data["soc_max"] - data["socs"][j]) * percentage) / 100
                data["socs"].append(data["socs"][j] + quantity_charging_battery)

                if quantity_charging_battery - delta_production.iloc[j] < 0:
                    # devo vendere
                    sum = sum + ((quantity_charging_battery - delta_production.iloc[j]) * sold)  # sum = sum - rimborso
                else:
                    sum = sum + (quantity_charging_battery - delta_production.iloc[j]) * data["prices"]["prezzo"].iloc[
                        j]
            else:
                quantity_discharging_battery = ((data["socs"][j] - data["soc_min"]) * percentage) / 100
                data["socs"].append(data["socs"][j] - quantity_discharging_battery)

                if delta_production.iloc[j] + quantity_discharging_battery > 0:
                    # sto scaricando la batteria  con surplus di energia
                    # vendo alla rete MA dalla batteria
                    if delta_production.iloc[j] > 0:
                        # vendo alla rete quello del fotovoltaico
                        sum = sum - delta_production.iloc[j] * sold
                    else:
                        # in questo else teoricamente potrei vendere enegia della batteria ma invece sovrascrivo il valore
                        data["socs"][j + 1] = data["socs"][j] + delta_production.iloc[j]
                else:
                    sum = sum + (- (delta_production.iloc[j] + quantity_discharging_battery) *
                                 data["prices"]["prezzo"].iloc[j])

        out["F"] = sum


async def main():
    # energy_request(data)

    meteo_df = filter_meteo_between_ss_and_sr(data)
    delta_production = difference_of_production(data)

    meteo_df["expected_power_production"] = get_expected_power_production_from_pv(data, meteo_df["direct_radiation"],
                                                                                  meteo_df["diffuse_radiation"],
                                                                                  meteo_df["temperature_2m"])

    data["prices"] = await get_intra_days_market()

    get_estimate_load_consumption(get_true_load_consumption())
    """
       problem = MixedVariableProblem()

    # Set the population size to 1
    pop_size = 100
    algorithm = MixedVariableGA(pop_size)

    res = minimize(problem,
                   algorithm,
                   termination=('n_evals', 2),
                   seed=random.randint(0, 99999),
                   verbose=False)

    print("Best solution found: \nX = %s\nF = %s" % (res.X, res.F))
    """

if __name__ == "__main__":
    asyncio.run(main())
