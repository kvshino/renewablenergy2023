import asyncio
from functions import *
import warnings
from update_costs import *
from genetic import *
from consumptions import *
from plot import *
from update_battery import *
from test_inv import *
from gui import *
from freezegun import freeze_time


warnings.filterwarnings("ignore", category=FutureWarning)


async def main():
    ora=datetime.now()
    polynomial_batt = battery_function()
    polynomial_inverter = inverter_function()

    with freeze_time(datetime.now()) as frozen_datetime:

        dict={}
        sampling=0
        pop_size =80
        gen = 30

        data = setup(polynomial_inverter)
        prices = await get_future_day_italian_market(data)
        production_not_rs = forecast_percentage_production_from_not_renewable_sources(api_key=data["api_key"], zona=data["entsoe_timezone"])

        for i in range(24):

            data = setup(polynomial_inverter)
            data["prices"] = prices 
            data["production_not_rs"] = production_not_rs  
            
            if(i==0):
                dict["first_battery_value"]=data["socs"]
                cycles = data["cycles"]
                dict[f"battery_capacity{i}"] = data["battery_capacity"]

       
            if i == 0:
                data["res"], data["history"] = start_genetic_algorithm(data=data, pop_size=pop_size, n_gen=gen, n_threads=24, sampling=None, verbose=False)  #Checked OK
            else:
                data["res"], data["history"] = start_genetic_algorithm(data=data, pop_size=pop_size, n_gen=gen, n_threads=24, sampling=sampling, verbose=False)
            
            print("Fine Esecuzione Ora " + str(i+1))



            dict[f"b{i}"]=data["res"].X["b0"]
            dict[f"i{i}"]=data["res"].X["i0"]
            dict[f"difference_of_production{i}"] = data["difference_of_production"][0]
            dict[f"prices{i}"] = data["prices"]["prezzo"][0]
            dict[f"production_not_rs{i}"] = data[f"production_not_rs"]["Difference"][0]
            dict[f"load{i}"] = data["estimate"]["consumo"][0]
            dict[f"production{i}"] = data["expected_production"]["production"][0]

            prices = shift_ciclico(prices)
            production_not_rs = shift_ciclico(production_not_rs)
        
            all_populations = [a.pop for a in data["history"]]
            sampling = shifting_individuals(all_populations[-1])
            dict[f"battery_capacity{i+1}"] = update_battery_values(data, "csv/socs.csv", dict[f"b{i}"], dict[f"i{i}"], polynomial_batt)

            frozen_datetime.tick(delta=timedelta(hours=1))

    dict["sum_algo"],dict["actual_percentage_algo"],dict["quantity_delta_battery_algo"],dict["co2_algo"] = evaluate(data, dict,cycles,polynomial_batt)

    dict["soc_min"] = data["soc_min"]
    dict["soc_max"] = data["soc_max"]
    dict["sold"] = data["sold"]
    dict["battery_nominal_capacity"] = data["battery_nominal_capacity"]
    dict["battery_charging_efficiency"] = data["battery_charging_efficiency"]
    dict["battery_discharging_efficiency"] = data["battery_discharging_efficiency"]

    dict["sum_noalgo"],dict["actual_battery_level_noalgo"],dict["quantity_battery_degradation_noalgo"],dict["co2_noalgo"],dict["power_to_grid_noalgo"] =simulation_no_algorithm(data,dict, cycles, polynomial_batt)
    dict["sum_nobattery"],dict["co2_nobattery"],dict["power_to_grid_nobattery"]  = simulation_nobattery(data,dict)
    dict["sum_noplant"],dict["co2_noplant"],dict["power_to_grid_noplant"]= simulation_noplant(data,dict)

    init_gui(data,dict)
    print(datetime.now()-ora)


if __name__ == "__main__":
    asyncio.run(main())
