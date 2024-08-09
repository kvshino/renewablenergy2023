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
    polynomial = battery_function()
    with freeze_time(datetime.now()) as frozen_datetime:

        dict={}
        prices = await get_future_day_market(mercato="MI-A2") #Checked OK

        sampling=0
        first_battery_value=0

        for i in range(24):

            data = setup(prices) #Checked OK, solo le formule predizione di produzione e load da controllare
            if(i==0):
                first_battery_value=data["socs"]            

            if i == 0:
                data["res"], data["history"] = start_genetic_algorithm(data=data, pop_size=130, n_gen=20, n_threads=24, sampling=None, verbose=False)  #Checked OK
            else:
                data["res"], data["history"] = start_genetic_algorithm(data=data, pop_size=130, n_gen=20, n_threads=24, sampling=sampling, verbose=False)

            
            # distance = (data["res"].F[0][0]**2) + ((data["res"].F[0][1]**2))
            # number = 0
            # for j,coordinate in enumerate(data["res"].F[1:]):
            #     distance2 = (coordinate[0]**2) + (coordinate[1]**2)
            #     if(distance2 < distance):
            #         distance = distance2
            #         number = j+1
            
            number = int(len(data["res"].F)/2)
            dict[f"b{i}"]=data["res"].X[number]["b0"]
            dict[f"i{i}"]=data["res"].X[number]["i0"]
            print(str(dict[f"b{i}"]) + "  " + str(dict[f"i{i}"]))
            
            # plot = Scatter()
            # plot.add(data["res"].F, facecolor="none", edgecolor="red")
            # plot.show()

            all_populations = [a.pop for a in data["history"]]
            sampling = shifting_individuals(all_populations[-1])

            update_battery_values(data, "csv/socs.csv", dict[f"b{i}"], dict[f"i{i}"], polynomial)

            frozen_datetime.tick(delta=timedelta(hours=1))

        sum, actual_percentage, quantity_delta_battery = evaluate(data, dict, first_battery_value)
        simulation_plot(data, sum, actual_percentage, quantity_delta_battery) 


    print(datetime.now()-ora)

if __name__ == "__main__":
    asyncio.run(main())
