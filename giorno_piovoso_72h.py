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

from freezegun import freeze_time

import numpy as np
import json


warnings.filterwarnings("ignore", category=FutureWarning)


cartella="../../../Desktop/risultati/giornoPiovoso72h_650_NuovaPen_SPER3/"


async def main():
    ora=datetime.now()
    polynomial_batt = battery_function()
    polynomial_inverter = inverter_function()

    with freeze_time(datetime.now()-timedelta(hours=7)) as frozen_datetime:

        dictionary={}

        sampling=0

        pop_size=650
        n_gen=250

        data = setup(polynomial_inverter)
        prices = await get_future_day_italian_market(data)
        production=pd.read_csv("production.csv", skipinitialspace=True)
        #prices = pd.read_csv("prices.csv", skipinitialspace=True)
        production_not_rs = forecast_percentage_production_from_not_renewable_sources(api_key=data["api_key"], zona=data["entsoe_timezone"])
        print(datetime.now() )
        for i in range(72):

            data = setup(polynomial_inverter)
            data["prices"] = prices 
            data["production_not_rs"] = production_not_rs
            data["polynomial"] = polynomial_batt
            data["expected_production"]=pd.DataFrame(pd.date_range(start=datetime.now().replace(minute=0, second=0, microsecond=0) - timedelta(hours=1),
                                periods=24, freq='h'))
            data["expected_production"] = production.iloc[i:i+24]
            data["expected_production"] = data["expected_production"].reset_index()
            data["difference_of_production"] = difference_of_production(data)

            
            if(i==0):
                cycles = data["cycles"]
                dictionary["first_battery_value"]=data["socs"]
                dictionary[f"battery_capacity{i}"] = data["battery_capacity"]

            if i == 0:
                data["res"], data["history"] = start_nsga2_genetic_algorithm(data=data, pop_size=pop_size, n_gen=n_gen, n_threads=12, sampling=None, verbose=False) 
            else:
                data["res"], data["history"] = start_nsga2_genetic_algorithm(data=data, pop_size=pop_size, n_gen=n_gen, n_threads=12, sampling=sampling, verbose=False)

            print("Fine Esecuzione Ora " + str(i+1))

            F=pareto_front(data["res"].F)
            print(len(F))

            now=datetime.now().strftime("%Y-%m-%d_%H")
            if not os.path.exists(f"{cartella}Fronte_di_Pareto"):
                os.makedirs(cartella+"Fronte_di_Pareto")  
            np.savetxt(f"{cartella}Fronte_di_Pareto/{now}_NON_normalizzato.txt", F, fmt="%.8f") 

            F_min = np.min(F, axis=0)
            F_max = np.max(F, axis=0)
            F_norm = (F - F_min) / (F_max - F_min)
            #F_norm[:,1] = F_norm[:,1] / 3           
            distances = np.linalg.norm(F_norm, axis=1)
            best_index = np.argmin(distances)

                
            dictionary[f"b{i}"]=round(data["res"].X[best_index][0])
            dictionary[f"i{i}"]=round(data["res"].X[best_index][1])


            dictionary[f"difference_of_production{i}"] = data["difference_of_production"][0]  
            dictionary[f"prices{i}"] = data["prices"]["prezzo"][0]
            dictionary[f"production_not_rs{i}"] = data[f"production_not_rs"]["Difference"][0]
            dictionary[f"load{i}"] = data["estimate"]["consumo"][0]
            dictionary[f"production{i}"] = data["expected_production"]["production"][0]

            prices = shift_ciclico(prices, "prezzo")
            production_not_rs = shift_ciclico(production_not_rs, "Difference")
            production_not_rs['Difference'] = production_not_rs['Difference'].clip(upper=1)

            
            sampling = shifting_nsga2_individuals(data["res"])

            dictionary[f"battery_capacity{i+1}"] = update_battery_values(data, "csv/socs.csv", dictionary[f"b{i}"], dictionary[f"i{i}"], polynomial_batt)

            with open(f"{cartella}dictionary.json", "w") as file:
                json.dump(dictionary, file, indent=4)  
            frozen_datetime.tick(delta=timedelta(hours=1))


        dictionary["soc_min"] = data["soc_min"]
        dictionary["soc_max"] = data["soc_max"]
        dictionary["sold"] = data["sold"]
        dictionary["battery_nominal_capacity"] = data["battery_nominal_capacity"]
        dictionary["battery_charging_efficiency"] = data["battery_charging_efficiency"]
        dictionary["battery_discharging_efficiency"] = data["battery_discharging_efficiency"]
        dictionary["polynomial_inverter"] = polynomial_inverter

        dictionary["sum_algo"],dictionary["actual_percentage_algo"],dictionary["quantity_delta_battery_algo"],dictionary["co2_algo"], dictionary["ratio_algo"] = evaluate(data, dictionary,  cycles, polynomial_batt, 72)
        dictionary["sum_noalgo"],dictionary["actual_battery_level_noalgo"],dictionary["quantity_battery_degradation_noalgo"],dictionary["co2_noalgo"],dictionary["power_to_grid_noalgo"], dictionary["ratio_noalgo"] =simulation_no_algorithm(data,dictionary, cycles, polynomial_batt, 72)
        dictionary["sum_nobattery"],dictionary["co2_nobattery"],dictionary["power_to_grid_nobattery"], dictionary["ratio_nobattery"]  = simulation_nobattery(data,dictionary)
        dictionary["sum_noplant"],dictionary["co2_noplant"],dictionary["power_to_grid_noplant"]= simulation_noplant(data,dictionary)    

        print(datetime.now())
        
        del dictionary["polynomial_inverter"]
        with open(f"{cartella}dictionary.json", "w") as file:
            json.dump(dictionary, file, indent=4)  

    print(datetime.now()-ora)

if __name__ == "__main__":
    asyncio.run(main())
