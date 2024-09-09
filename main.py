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
        first_battery_value=0

        pop_size =50
        gen = 12

        data = setup(polynomial_inverter)
        prices = await get_future_day_italian_market(data)
        production_not_rs = forecast_percentage_production_from_not_renewable_sources(api_key=data["api_key"], zona=data["entsoe_timezone"])

        for i in range(24):

            data = setup(polynomial_inverter)
            data["prices"] = prices 
            data["production_not_rs"] = production_not_rs  
            
            if(i==0):
                first_battery_value=data["socs"]
                cycles = data["cycles"]
       
            if i == 0:
                data["res"], data["history"] = start_genetic_algorithm(data=data, pop_size=pop_size, n_gen=gen, n_threads=24, sampling=None, verbose=False)  #Checked OK
            else:
                data["res"], data["history"] = start_genetic_algorithm(data=data, pop_size=pop_size, n_gen=gen, n_threads=24, sampling=sampling, verbose=False)
            
            print("Fine Esecuzione Ora " + str(i+1))

            # top_individuals = 5
            # all_populations = [a.pop for a in data["history"]]
            # last_population = all_populations[-1]
            # sorted_population = sorted(last_population, key=lambda p: p.F)
            # top_n_individuals = sorted_population[:top_individuals]
            # variables_values = [ind.X for ind in top_n_individuals]

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
            dict[f"battery_capacity{i}"] = update_battery_values(data, "csv/socs.csv", dict[f"b{i}"], dict[f"i{i}"], polynomial_batt)

            frozen_datetime.tick(delta=timedelta(hours=1))

        sum, actual_percentage, quantity_delta_battery = evaluate(data, dict, first_battery_value)
        #simulation_plot(data, sum, actual_percentage, quantity_delta_battery) 
    dict["soc_min"] = data["soc_min"]
    dict["soc_max"] = data["soc_max"]
    dict["sold"] = data["sold"]
    dict["battery_nominal_capacity"] = data["battery_nominal_capacity"]
    init_gui(dict, sum, actual_percentage, quantity_delta_battery, first_battery_value)
    print(datetime.now()-ora)

if __name__ == "__main__":
    asyncio.run(main())
