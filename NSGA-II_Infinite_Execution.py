import asyncio
from functions import *
import warnings
from update_costs import *
from multi_genetic import *
from multi_genetic_nsga import *
from consumptions import *
from plot import *
from gui import *
from test_inv import *
import time
from datetime import timedelta

#################################################################################################
## Code used to exectute the EMS in the environment of Salerno for an undefined amount of time ##
#################################################################################################


import numpy as np

warnings.filterwarnings("ignore", category=FutureWarning)

async def main():
    polynomial_batt = battery_function()
    polynomial_inverter = inverter_function()
    run=0
    dictionary={}
    while(1):

        data = setup(polynomial_inverter)
        data["prices"] = await get_future_day_italian_market(data)
        data["production_not_rs"] = forecast_percentage_production_from_not_renewable_sources(api_key=data["api_key"], zona=data["entsoe_timezone"])
        data["polynomial"] = polynomial_batt
        

        if run == 0:
                dictionary[f"battery_capacity{run}"] = data["battery_capacity"]
                cycles = data["cycles"]
                dictionary["first_battery_value"]=data["socs"]
                data["res"], data["history"] = start_nsga2_genetic_algorithm(data=data, pop_size=20, n_gen=10, n_threads=12, sampling=None, verbose=False) 
        else:
            data["res"], data["history"] = start_nsga2_genetic_algorithm(data=data, pop_size=20, n_gen=10, n_threads=12, sampling=sampling, verbose=False)

        print("Fine Esecuzione Ora " + datetime.now().strftime("%Y-%m-%d_%H:%M"))

        F=data["res"].F
        F_min = np.min(F, axis=0)
        F_max = np.max(F, axis=0)
        F_norm = (F - F_min) / (F_max - F_min)
        distances = np.linalg.norm(F_norm, axis=1)
        best_index = np.argmin(distances)

        dictionary[f"b{run}"]=round(data["res"].X[best_index][0])
        dictionary[f"i{run}"]=round(data["res"].X[best_index][1])
        dictionary[f"difference_of_production{run}"] = data["difference_of_production"][0]  
        dictionary[f"prices{run}"] = data["prices"]["prezzo"][0]
        dictionary[f"production_not_rs{run}"] = data[f"production_not_rs"]["Difference"][0]
        dictionary[f"load{run}"] = data["estimate"]["consumo"][0]
        dictionary[f"production{run}"] = data["expected_production"]["production"][0]
        dictionary["soc_min"] = data["soc_min"]
        dictionary["soc_max"] = data["soc_max"]
        dictionary["sold"] = data["sold"]
        dictionary["battery_nominal_capacity"] = data["battery_nominal_capacity"]
        dictionary["battery_charging_efficiency"] = data["battery_charging_efficiency"]
        dictionary["battery_discharging_efficiency"] = data["battery_discharging_efficiency"]
        dictionary["polynomial_inverter"] = polynomial_inverter

        plot_and_save_results(F_norm, ["Costs", "Battery Degradation", "Pollution"], "../../../Desktop/risultati/Prova_Infinite_Loop/Fronte_di_Pareto",filename_2d='NSGAII_Fronte2D_Scenario_X'+str(run)+'.png', filename_3d='NSGAII_Fronte3D_Scenario_X'+str(run)+'.png')

        sampling = shifting_nsga2_individuals(data["res"])
        run+=1

        dictionary[f"battery_capacity{run}"] =update_battery_values(data, "csv/socs.csv", round(data["res"].X[best_index][0]), round(data["res"].X[best_index][1]), polynomial_batt)


        dictionary["sum_algo"],dictionary["actual_percentage_algo"],dictionary["quantity_delta_battery_algo"],dictionary["co2_algo"], dictionary["ratio_algo"] = evaluate(data, dictionary,  cycles, polynomial_batt, hours=run)
        dictionary["sum_noalgo"],dictionary["actual_battery_level_noalgo"],dictionary["quantity_battery_degradation_noalgo"],dictionary["co2_noalgo"],dictionary["power_to_grid_noalgo"], dictionary["ratio_noalgo"] =simulation_no_algorithm(data,dictionary, cycles, polynomial_batt, hours=run)
        dictionary["sum_nobattery"],dictionary["co2_nobattery"],dictionary["power_to_grid_nobattery"], dictionary["ratio_nobattery"]  = simulation_nobattery(data,dictionary)
        dictionary["sum_noplant"],dictionary["co2_noplant"],dictionary["power_to_grid_noplant"]= simulation_noplant(data,dictionary)    
        save_plots(dictionary, "../../../Desktop/risultati/Prova_Infinite_Loop")

        new_time=datetime.now().replace(minute=0, second=0, microsecond=0)+timedelta(hours=1)
        time.sleep((new_time-datetime.now()).total_seconds())

if __name__ == "__main__":
    asyncio.run(main())
