import asyncio
from costi import *
from functions import *
import warnings
from update_costs import *

from freezegun import freeze_time


warnings.filterwarnings("ignore", category=FutureWarning)



async def main():
    with freeze_time(datetime.now()) as frozen_datetime:

        dict={}
        prices = await get_future_day_market() #Checked OK

        sampling=0

        for i in range(24):

            data = setup(prices) #Checked OK, solo le formule predizione di produzione e load da controllare
            

            # plot_GME_prices(data)
            # plt.show()


            if i == 0:
                data["res"], data["history"] = start_genetic_algorithm(data=data, pop_size=1, n_gen=1, n_threads=12, sampling=None, verbose=False)  #Checked OK
            else:
                data["res"], data["history"] = start_genetic_algorithm(data=data, pop_size=1, n_gen=1, n_threads=12, sampling=sampling, verbose=False)

            

            top_individuals = 5
            all_populations = [a.pop for a in data["history"]]
            last_population = all_populations[-1]
            sorted_population = sorted(last_population, key=lambda p: p.F)
            top_n_individuals = sorted_population[:top_individuals]
            variables_values = [ind.X for ind in top_n_individuals]
            
            

            dict[f"b{i}"]=variables_values[0]["b0"]
            dict[f"i{i}"]=variables_values[0]["i0"]


            data = shifting_individuals(data)


            update_battery_value(data, "csv/socs.csv", variables_values[0]["b0"], variables_values[0]["i0"])
            sampling=data["res"]
            frozen_datetime.tick(delta=timedelta(hours=1))


        #sum, actual_percentage, quantity_delta_battery = evaluate(data, dict)
        #simulation_plot(data, sum, actual_percentage, quantity_delta_battery) 




if __name__ == "__main__":
    asyncio.run(main())
