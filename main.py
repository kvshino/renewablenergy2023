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
    pop_size =50
    gen = 12
    ora=datetime.now()
    polynomial_batt = battery_function()
    polynomial_inverter = inverter_function()

    with freeze_time(datetime.now()) as frozen_datetime:

        dict={}
       

        sampling=0
        first_battery_value=0

        for i in range(24):

            data = setup(polynomial_inverter) #Checked OK, solo le formule predizione di produzione e load da controllare
            data["prices"] = await get_future_day_italian_market(data)  
            
            if(i==0):
                first_battery_value=data["socs"]
       
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
        
            all_populations = [a.pop for a in data["history"]]
            sampling = shifting_individuals(all_populations[-1])
            update_battery_values(data, "csv/socs.csv",  dict[f"b{i}"], dict[f"i{i}"], polynomial_batt)

            frozen_datetime.tick(delta=timedelta(hours=1))

        sum, actual_percentage, quantity_delta_battery = evaluate(data, dict, first_battery_value)
        #simulation_plot(data, sum, actual_percentage, quantity_delta_battery) 
    init_gui(data, sum, actual_percentage, quantity_delta_battery)
    print(datetime.now()-ora)

if __name__ == "__main__":
    asyncio.run(main())
