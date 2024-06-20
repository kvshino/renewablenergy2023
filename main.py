import asyncio
from functions import *
import warnings
from update_costs import *
from genetic import *
from consumptions import *
from plot import *
from update_battery import *

from freezegun import freeze_time


warnings.filterwarnings("ignore", category=FutureWarning)



async def main():
    ora=datetime.now()
    battery_coeff = battery_function()
    with freeze_time(datetime.now()) as frozen_datetime:

        dict={}
        prices = await get_future_day_market() #Checked OK

        sampling=0
        first_battery_value=0

        for i in range(24):

            data = setup(prices) #Checked OK, solo le formule predizione di produzione e load da controllare
            if(i==0):
                first_battery_value=data["socs"]
                print(first_battery_value)
            # plot_GME_prices(data)
            # plt.show()


            if i == 0:
                data["res"], data["history"] = start_genetic_algorithm(data=data, pop_size=50, n_gen=10, n_threads=1, sampling=None, verbose=False)  #Checked OK
            else:
                data["res"], data["history"] = start_genetic_algorithm(data=data, pop_size=50, n_gen=10, n_threads=1, sampling=sampling, verbose=False)

            # top_individuals = 5
            # all_populations = [a.pop for a in data["history"]]
            # last_population = all_populations[-1]
            # sorted_population = sorted(last_population, key=lambda p: p.F)
            # top_n_individuals = sorted_population[:top_individuals]
            # variables_values = [ind.X for ind in top_n_individuals]
            
            

            dict[f"b{i}"]=data["res"].X["b0"]
            dict[f"i{i}"]=data["res"].X["i0"]

        
            data = shifting_individuals(data)


            update_battery_values(data, "csv/socs.csv",  dict[f"b{i}"], dict[f"i{i}"], battery_coeff)
            all_populations = [a.pop for a in data["history"]]
            sampling=all_populations[-1]
            frozen_datetime.tick(delta=timedelta(hours=1))

        sum, actual_percentage, quantity_delta_battery = evaluate(data, dict, first_battery_value)
        simulation_plot(data, sum, actual_percentage, quantity_delta_battery) 


    print(datetime.now()-ora)

if __name__ == "__main__":
    asyncio.run(main())
