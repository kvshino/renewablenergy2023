import asyncio
from functions import *
import warnings
from update_costs import *
from multi_genetic import *
from consumptions import *
from plot import *
from gui import *
from test_inv import *

from freezegun import freeze_time

import matplotlib.pyplot as plt
import numpy as np

warnings.filterwarnings("ignore", category=FutureWarning)



async def main():
    ora=datetime.now()
    polynomial_batt = battery_function()
    polynomial_inverter = inverter_function()

    with freeze_time(datetime.now()) as frozen_datetime:

        dictionary={}

        sampling=0

        pop_size=120
        n_gen=35

        data = setup(polynomial_inverter)
        prices = await get_future_day_italian_market(data)
        production_not_rs = forecast_percentage_production_from_not_renewable_sources(api_key=data["api_key"], zona=data["entsoe_timezone"])

        for i in range(24):

            data = setup(polynomial_inverter)
            data["prices"] = prices 
            data["production_not_rs"] = production_not_rs

            if(i==0):
                cycles = data["cycles"]
                dictionary["first_battery_value"]=data["socs"]
                dictionary[f"battery_capacity{i}"] = data["battery_capacity"]


            if i == 0:
                data["res"], data["history"] = start_genetic_algorithm(data=data, pop_size=pop_size, n_gen=n_gen, n_threads=24, sampling=None, verbose=False) 
            else:
                data["res"], data["history"] = start_genetic_algorithm(data=data, pop_size=pop_size, n_gen=n_gen, n_threads=24, sampling=sampling, verbose=False)
            
            print("Fine Esecuzione Ora " + str(i+1))

            F=data["res"].F
            F_min = np.min(F, axis=0)
            F_max = np.max(F, axis=0)
            F_norm = (F - F_min) / (F_max - F_min)
            distances = np.linalg.norm(F_norm, axis=1)
            best_index = np.argmin(distances)

            
            dictionary[f"b{i}"]=data["res"].X[best_index]["b0"]
            dictionary[f"i{i}"]=data["res"].X[best_index]["i0"]


            dictionary[f"difference_of_production{i}"] = data["difference_of_production"][0]  
            dictionary[f"prices{i}"] = data["prices"]["prezzo"][0]
            dictionary[f"production_not_rs{i}"] = data[f"production_not_rs"]["Difference"][0]
            dictionary[f"load{i}"] = data["estimate"]["consumo"][0]
            dictionary[f"production{i}"] = data["expected_production"]["production"][0]

            prices = shift_ciclico(prices)
            production_not_rs = shift_ciclico(production_not_rs)
            
            all_populations = [a.pop for a in data["history"]]
            sampling = shifting_individuals(all_populations[-1])

            dictionary[f"battery_capacity{i+1}"] = update_battery_values(data, "csv/socs.csv", dictionary[f"b{i}"], dictionary[f"i{i}"], polynomial_batt)

            frozen_datetime.tick(delta=timedelta(hours=1))


    #dictionary["co2_emissions"] = co2_emissions
    dictionary["soc_min"] = data["soc_min"]
    dictionary["soc_max"] = data["soc_max"]
    dictionary["sold"] = data["sold"]
    dictionary["battery_nominal_capacity"] = data["battery_nominal_capacity"]
    dictionary["battery_charging_efficiency"] = data["battery_charging_efficiency"]
    dictionary["battery_discharging_efficiency"] = data["battery_discharging_efficiency"]

    dictionary["sum_algo"],dictionary["actual_percentage_algo"],dictionary["quantity_delta_battery_algo"],dictionary["co2_algo"] = evaluate(data, dictionary,  cycles, polynomial_batt)
    dictionary["sum_noalgo"],dictionary["actual_battery_level_noalgo"],dictionary["quantity_battery_degradation_noalgo"],dictionary["co2_noalgo"],dictionary["power_to_grid_noalgo"] =simulation_no_algorithm(data,dictionary, cycles, polynomial_batt)
    dictionary["sum_nobattery"],dictionary["co2_nobattery"],dictionary["power_to_grid_nobattery"]  = simulation_nobattery(data,dictionary)
    dictionary["sum_noplant"],dictionary["co2_noplant"],dictionary["power_to_grid_noplant"]= simulation_noplant(data,dictionary)    

    init_gui(data,dictionary)
    print(datetime.now()-ora)

if __name__ == "__main__":
    asyncio.run(main())
