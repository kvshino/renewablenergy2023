import asyncio
from functions import *
import warnings
from update_costs import *
from multi_genetic import *
from multi_genetic_nsga import *
from consumptions import *
from plot import *
from update_battery import *
from test_inv import *
from freezegun import freeze_time
import time as tm
from pymoo.visualization.scatter import Scatter
from gui import *
import threading
import json as jj

warnings.filterwarnings("ignore", category=FutureWarning)

color_ga ="#004aad"
color_mixed ="#ff5757"

cartella_MVGA=cartella="../../../Desktop/risultati/confronto/MVGA/"
cartella_NSGAII=cartella="../../../Desktop/risultati/confronto/NSGAII/"



async def mixed(frozen_datetime):
    polynomial_batt = battery_function()
    polynomial_inverter = inverter_function()

    print("Inizio mixed: " + str(datetime.now()))
    dict = {}
    sampling = 0
    pop_size = 650
    gen = 300
    data = setup(polynomial_inverter,"csv/socsmixed.csv")
    prices = await get_future_day_italian_market(data)
    production_not_rs = forecast_percentage_production_from_not_renewable_sources(api_key=data["api_key"], zona=data["entsoe_timezone"])
    for i in range(24):
        data = setup(polynomial_inverter,"csv/socsmixed.csv")
        data["prices"] = prices
        data["production_not_rs"] = production_not_rs  
        data["polynomial"] = polynomial_batt
        
        if(i == 0):
            dict["first_battery_value"] = data["socs"]
            cycles = data["cycles"]
            dict[f"battery_capacity{i}"] = data["battery_capacity"]

        if i == 0:
            data["res"], data["history"] = start_genetic_algorithm(data=data, pop_size=pop_size, n_gen=gen, n_threads=12, sampling=None, verbose=False)  
        else:
            data["res"], data["history"] = start_genetic_algorithm(data=data, pop_size=pop_size, n_gen=gen, n_threads=12, sampling=sampling, verbose=False)
        
        print("Fine Esecuzione Ora " + str(i+1))

        F=data["res"].F
        F_min = np.min(F, axis=0)
        F_max = np.max(F, axis=0)
        F_norm = (F - F_min) / (F_max - F_min)
        distances = np.linalg.norm(F_norm, axis=1)
        best_index = np.argmin(distances)

        now=datetime.now().strftime("%Y-%m-%d_%H")
        if not os.path.exists(f"{cartella_MVGA}Fronte_di_Pareto"):
            os.makedirs(cartella_MVGA+"Fronte_di_Pareto")  
        np.savetxt(f"{cartella_MVGA}Fronte_di_Pareto/{now}.txt", F_norm, fmt="%.8f") 

        dict[f"b{i}"]= bool(data["res"].X[best_index]["b0"])
        dict[f"i{i}"]=int(data["res"].X[best_index]["i0"])

        dict[f"difference_of_production{i}"] = data["difference_of_production"][0]
        dict[f"prices{i}"] = data["prices"]["prezzo"][0]
        dict[f"production_not_rs{i}"] = data[f"production_not_rs"]["Difference"][0]
        dict[f"load{i}"] = data["estimate"]["consumo"][0]
        dict[f"production{i}"] = data["expected_production"]["production"][0]
        
        prices = shift_ciclico(prices, "prezzo")
        production_not_rs = shift_ciclico(production_not_rs, "Difference")
    
        # all_populations = [a.pop for a in data["history"]]
        sampling = shifting_individuals(data["res"])
        dict[f"battery_capacity{i+1}"] = update_battery_values(data, "csv/socsmixed.csv", dict[f"b{i}"], dict[f"i{i}"], polynomial_batt)
        frozen_datetime.tick(delta=timedelta(hours=1))
    
    print("Fine mixed: " + str(datetime.now()))
    
    dict["soc_min"] = data["soc_min"]
    dict["soc_max"] = data["soc_max"]
    dict["sold"] = data["sold"]
    dict["battery_nominal_capacity"] = data["battery_nominal_capacity"]
    dict["battery_charging_efficiency"] = data["battery_charging_efficiency"]
    dict["battery_discharging_efficiency"] = data["battery_discharging_efficiency"]
    dict["polynomial_inverter"] = polynomial_inverter

    dict["sum_algo"], dict["actual_percentage_algo"], dict["quantity_delta_battery_algo"], dict["co2_algo"], dict["ratio_algo"] = evaluate(data, dict, cycles, polynomial_batt)
    lista = dictionary_to_list(dict,"battery_capacity")

    del dict["polynomial_inverter"]
    with open(f"{cartella_MVGA}dictionary.json", "w") as file:
        jj.dump(dict, file, indent=4)  

    return dict["sum_algo"], dict["actual_percentage_algo"], dict["co2_algo"], lista

async def nsga(frozen_datetime):
    polynomial_batt = battery_function()
    polynomial_inverter = inverter_function()


    dict={}
    sampling=0
    pop_size =650
    gen = 280
    data = setup(polynomial_inverter,"csv/socsga.csv")
    prices = await get_future_day_italian_market(data)
    production_not_rs = forecast_percentage_production_from_not_renewable_sources(api_key=data["api_key"], zona=data["entsoe_timezone"])
    print("Inizio nsga: " + str(datetime.now()))
    for i in range(24):

        data = setup(polynomial_inverter,"csv/socsga.csv")
        data["prices"] = prices 
        data["production_not_rs"] = production_not_rs  
        data["polynomial"] = polynomial_batt

        if(i==0):
            dict["first_battery_value"]=data["socs"]
            cycles = data["cycles"]
            dict[f"battery_capacity{i}"] = data["battery_capacity"]

        if i == 0:
            data["res"], data["history"] = start_nsga2_genetic_algorithm(data=data, pop_size=pop_size, n_gen=gen, n_threads=12, sampling=None, verbose=False)  #Checked OK
        else:
            data["res"], data["history"] = start_nsga2_genetic_algorithm(data=data, pop_size=pop_size, n_gen=gen, n_threads=12, sampling=sampling, verbose=False)
        
        print("Fine Esecuzione Ora " + str(i+1))

        F=data["res"].F
        F_min = np.min(F, axis=0)
        F_max = np.max(F, axis=0)
        F_norm = (F - F_min) / (F_max - F_min)
        distances = np.linalg.norm(F_norm, axis=1)
        best_index = np.argmin(distances)


        now=datetime.now().strftime("%Y-%m-%d_%H")
        if not os.path.exists(f"{cartella_MVGA}Fronte_di_Pareto"):
            os.makedirs(cartella_NSGAII+"Fronte_di_Pareto")  
        np.savetxt(f"{cartella_NSGAII}Fronte_di_Pareto/{now}.txt", F_norm, fmt="%.8f") 


        dict[f"b{i}"]=round(data["res"].X[best_index][0])
        dict[f"i{i}"]=round(data["res"].X[best_index][1])


        dict[f"difference_of_production{i}"] = data["difference_of_production"][0]
        dict[f"prices{i}"] = data["prices"]["prezzo"][0]
        dict[f"production_not_rs{i}"] = data[f"production_not_rs"]["Difference"][0]
        dict[f"load{i}"] = data["estimate"]["consumo"][0]
        dict[f"production{i}"] = data["expected_production"]["production"][0]
        
        prices = shift_ciclico(prices, "prezzo")
        production_not_rs = shift_ciclico(production_not_rs, "Difference")
    
        # all_populations = [a.pop for a in data["history"]]
        sampling = shifting_nsga2_individuals(data["res"])
        dict[f"battery_capacity{i+1}"] = update_battery_values(data, "csv/socsga.csv", dict[f"b{i}"], dict[f"i{i}"], polynomial_batt)

        frozen_datetime.tick(delta=timedelta(hours=1))

    print("Fine nsga: " + str(datetime.now()))

    dict["soc_min"] = data["soc_min"]
    dict["soc_max"] = data["soc_max"]
    dict["sold"] = data["sold"]
    dict["battery_nominal_capacity"] = data["battery_nominal_capacity"]
    dict["battery_charging_efficiency"] = data["battery_charging_efficiency"]
    dict["battery_discharging_efficiency"] = data["battery_discharging_efficiency"]
    dict["polynomial_inverter"] = polynomial_inverter
    lista = dictionary_to_list(dict,"battery_capacity")

    dict["sum_algo"],dict["actual_percentage_algo"],dict["quantity_delta_battery_algo"],dict["co2_algo"] ,dict["ratio_algo"]= evaluate(data, dict,cycles,polynomial_batt)
    
    del dict["polynomial_inverter"]
    with open(f"{cartella_NSGAII}dictionary.json", "w") as file:
        jj.dump(dict, file, indent=4) 

    return dict["sum_algo"], dict["actual_percentage_algo"],  dict["co2_algo"],lista






async def main():
    # Await the mixed function since it is asynchronous
    os.makedirs("../../../Desktop/risultati/confronto/", exist_ok=True)
    dictionary ={}
    start_time = tm.time()
    t=datetime.now()-timedelta(hours=4)
    with freeze_time(t) as frozen_datetime:
        dictionary["sum_mixed"],dictionary["apercentage_mixed"] , dictionary["co2_mixed"] , lista1 = await mixed(frozen_datetime)
    end_time = tm.time()
    execution_time_mixed = end_time - start_time
    print(f"Execution_time MixedVariableGa: {execution_time_mixed} seconds")

    start_time = tm.time()
    with freeze_time(t) as frozen_datetime:
        dictionary["sum_ga"], dictionary["apercentage_ga"],  dictionary["co2_ga"], lista2 = await nsga(frozen_datetime)
    end_time = tm.time()
    execution_time_ga = end_time - start_time
    print(f"Execution_time Ga: {execution_time_ga} seconds")

    with open(cartella_MVGA+'lista1.json', 'w') as f:
        jj.dump(lista1, f, indent=4)  # `indent=4` per un formato leggibile

    with open(cartella_NSGAII+'lista2.json', 'w') as f:
        jj.dump(lista2, f, indent=4)  # `indent=4` per un formato leggibile

    with open(cartella_NSGAII+'confronto.json', 'w') as f:
        jj.dump(dictionary, f, indent=4)  # `indent=4` per un formato leggibile

    
    
    print("fine")

def run_asyncio():
    asyncio.run(main())

if __name__ == "__main__":
# Now we run the async main function
    asyncio.run(main())