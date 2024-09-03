import asyncio
from functions import *
import warnings
from update_costs import *
from multi_genetic import *
from consumptions import *
from plot import *

from freezegun import freeze_time

import matplotlib.pyplot as plt
import numpy as np

warnings.filterwarnings("ignore", category=FutureWarning)



async def main():
    ora=datetime.now()
    polynomial = battery_function()
    with freeze_time(datetime.now()) as frozen_datetime:

        dictionary={}

        sampling=0
        first_battery_value=0

        pop_size=200
        n_gen=40

        for i in range(24):

            data = setup()
            data["prices"] = await get_future_day_italian_market()  
            
            if(i==0):
                first_battery_value=data["socs"]            

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

            # plot = Scatter()
            # plot.add(F_norm, facecolor="none", edgecolor="red")
            # plot.show()

            

            dictionary[f"b{i}"]=data["res"].X[best_index]["b0"]
            dictionary[f"i{i}"]=data["res"].X[best_index]["i0"]
            dictionary[f"difference_of_production{i}"] = data["difference_of_production"][0]


            all_populations = [a.pop for a in data["history"]]
            sampling = shifting_individuals(all_populations[-1])

            update_battery_values(data, "csv/socs.csv", dictionary[f"b{i}"], dictionary[f"i{i}"], polynomial)

            frozen_datetime.tick(delta=timedelta(hours=1))

        sum, actual_percentage, quantity_delta_battery, co2_emissions = evaluate(data, dictionary, first_battery_value)
        simulation_plot(data, sum, actual_percentage, quantity_delta_battery, co2_emissions) 


    print(datetime.now()-ora)

if __name__ == "__main__":
    asyncio.run(main())
