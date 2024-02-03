import asyncio
from costi import *
from functions import *
from sklearn.preprocessing import MinMaxScaler

import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

data = setup()
top_individuals = 10

async def main():
    data["prices"] = await get_intra_days_market()  # Bring the prices of energy from Mercati Elettrici
    data["res"], data["history"] = start_genetic_algorithm(data, 500, 10, 12)


    all_populations = [a.pop for a in data["history"]]
    last_population = all_populations[-1]

    tuple_array = []
    i = 0
    for ind in last_population:
        s, a, q = evaluate(data, ind.X)
        print(i)
        tuple_array.append((s,a,q))
        i = i+1

    s_min = min(tupla[0][23] for tupla in tuple_array)
    s_max = max(tupla[0][23] for tupla in tuple_array)
    q_min = min(tupla[2] for tupla in tuple_array)
    q_max = max(tupla[2] for tupla in tuple_array)


    sorted_population = sorted(tuple_array, key=lambda tupla: (tupla[0] - s_min) / (s_max - s_min) + (tupla[2] - q_min) / (q_max - q_min))
    for ind in sorted_population:
        print(ind)
    top_n_individuals = sorted_population[:top_individuals]
    variables_values = [ind.X for ind in top_n_individuals]



    """
    somma = []
    actual_percentage = []
    quantity_delta_battery = []
    for i in range(0, top_individuals):
        s, a, q = evaluate(data, variables_values[i])
        somma.append(s)
        actual_percentage.append(a)
        quantity_delta_battery.append(q)
    genetic_algorithm_graph_top(data, top_individuals, somma, quantity_delta_battery)

    genetic_algorithm_graph_convergence(data, all_populations)
    plt.show()

    for i in range(0, top_individuals):
        simulation_plot(data, somma[i], actual_percentage[i], quantity_delta_battery[i])

    """


if __name__ == "__main__":
    asyncio.run(main())
