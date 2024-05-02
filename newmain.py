import asyncio
from costi import *
from functions import *
import warnings
from update_costs import *

warnings.filterwarnings("ignore", category=FutureWarning)



async def main():

    data = setup()
    data["prices"] = await get_future_day_market() 

    # plot_GME_prices(data)
    # plt.show()


    data["res"], data["history"] = start_genetic_algorithm(data, 10, 10, 1)


    top_individuals = 5

    all_populations = [a.pop for a in data["history"]]
    last_population = all_populations[-1]
    sorted_population = sorted(last_population, key=lambda p: p.F)
    top_n_individuals = sorted_population[:top_individuals]
    variables_values = [ind.X for ind in top_n_individuals]

    array_sum=[]
    array_qb=[]
    for i in range(0, top_individuals):
        sum, actual_percentage, quantity_delta_battery = evaluate(data, variables_values[i])
        array_sum.append(-sum[23])

        app=0
        for value in quantity_delta_battery:
            app+=abs(value)

        array_qb.append(app)

    genetic_algorithm_graph(data, array_sum, array_qb)

    for i in range(0, top_individuals):
        sum, actual_percentage, quantity_delta_battery = evaluate(data, variables_values[i])
        simulation_plot(data, sum, actual_percentage, quantity_delta_battery)







    # for individuo in data["res"].pop.get("X"):
    #     for i in range(23):
    #         individuo[f"b{i}"] = individuo[f"b{i+1}"]
    #         individuo[f"i{i}"] = individuo[f"i{i+1}"]

    #     random_bit =  random.choice([True, False])
    #     random_number = random.randint(0, 100)
    #     individuo["b23"] = random_bit
    #     individuo["i23"] = random_number
    #     print(individuo)
    #     print("---------"*10)
    
    # print("\n\n\n")

    # data["res"], data["history"] = start_genetic_algorithm(data, 10, 10, 1, data["res"])


    # top_individuals = 5

    # all_populations = [a.pop for a in data["history"]]
    # last_population = all_populations[-1]
    # sorted_population = sorted(last_population, key=lambda p: p.F)
    # top_n_individuals = sorted_population[:top_individuals]
    # variables_values = [ind.X for ind in top_n_individuals]

    # array_sum=[]
    # array_qb=[]
    # for i in range(0, top_individuals):
    #     sum, actual_percentage, quantity_delta_battery = evaluate(data, variables_values[i])
    #     array_sum.append(-sum[23])

    #     app=0
    #     for value in quantity_delta_battery:
    #         app+=abs(value)

    #     array_qb.append(app)

    # genetic_algorithm_graph(data, array_sum, array_qb)


    # for i in range(0, top_individuals):
    #     sum, actual_percentage, quantity_delta_battery = evaluate(data, variables_values[i])
    #     simulation_plot(data, sum, actual_percentage, quantity_delta_battery)




if __name__ == "__main__":
    asyncio.run(main())
