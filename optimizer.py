from pymoo.core.problem import ElementwiseProblem
from pymoo.core.variable import Binary, Integer
from pymoo.core.mixed import MixedVariableGA
from pymoo.optimize import minimize
from functions import *
import numpy as np
import random

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
        prices = get_intra_days_market(data)
        sold = data["sold"]
        #valori negativi indicano consumi ,positivi guadagni
        for j in range(24):
            charge = X[f"b{j}"]
            percentage = X[f"i{j}"]
            if charge:
                quantity_charging_battery = ((data["soc_max"]-data["socs"][j])*percentage)/100
                data["socs"].append(data["socs"][j] +quantity_charging_battery)

                if quantity_charging_battery - delta_production < 0:
                                                       #devo vendere
                    sum = sum + ((quantity_charging_battery - delta_production) *sold )                  #sum = sum - rimborso
                else:
                    sum = sum + (quantity_charging_battery - delta_production ) * prices[j]
            else:
                quantity_discharging_battery = ((data["socs"][j] -  data["soc_min"])*percentage)/100
                data["socs"].append(data["socs"][j] - quantity_discharging_battery)

                if delta_production + quantity_discharging_battery > 0:
                    #sto scaricando la batteria  con surplus di energia
                    #vendo alla rete MA dalla batteria
                    if delta_production > 0 :
                        #vendo alla rete quello del fotovoltaico
                        sum = sum - delta_production * sold
                    else:
                       # in questo else teoricamente potrei vendere enegia della batteria ma invece sovrascrivo il valore
                       data ["socs"][j+1] = data ["socs"][j] + delta_production
                else:
                    sum = sum + (- (delta_production + quantity_discharging_battery ) * prices[j])

        out["F"] = sum



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
