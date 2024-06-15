import asyncio
from functions import *
import warnings
from update_costs import *
from multi_genetic import *
from consumptions import *
from plot import *

from freezegun import freeze_time
from pymoo.visualization.scatter import Scatter


warnings.filterwarnings("ignore", category=FutureWarning)



async def main():
    ora=datetime.now()
    with freeze_time(datetime.now()) as frozen_datetime:

        dict={}
        prices = await get_future_day_market(mercato="MI-A1") #Checked OK

        sampling=0
        first_battery_value=0

        for i in range(24):

            data = setup(prices) #Checked OK, solo le formule predizione di produzione e load da controllare
            if(i==0):
                first_battery_value=data["socs"][-1]
            # plot_GME_prices(data)
            # plt.show()


            if i == 0:
                data["res"], data["history"] = start_genetic_algorithm(data=data, pop_size=100, n_gen=100, n_threads=1, sampling=None, verbose=False)  #Checked OK
            else:
                data["res"], data["history"] = start_genetic_algorithm(data=data, pop_size=100, n_gen=100, n_threads=1, sampling=sampling, verbose=False)

            
            
            numero = int(len(data["res"].F)/2)
            
            

            dict[f"b{i}"]=data["res"].X[numero]["b0"]
            dict[f"i{i}"]=data["res"].X[numero]["i0"]


            data = shifting_individuals(data)


            update_battery_value(data, "csv/socs.csv", data["res"].X[numero]["b0"], data["res"].X[numero]["i0"])
            all_populations = [a.pop for a in data["history"]]
            sampling=all_populations[-1]

            frozen_datetime.tick(delta=timedelta(hours=1))

        print(dict)
        sum, actual_percentage, quantity_delta_battery = evaluate(data, dict, first_battery_value)
        simulation_plot(data, sum, actual_percentage, quantity_delta_battery) 


    print(datetime.now()-ora)

if __name__ == "__main__":
    asyncio.run(main())
