import asyncio
from costi import *
from functions import *
from sklearn.preprocessing import MinMaxScaler

import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

data = setup()
top_individuals = 5

async def main():
    data["prices"] = await get_intra_days_market()  # Bring the prices of energy from Mercati Elettrici
    data["res"], data["history"] = start_genetic_algorithm(data, 500, 500, 24)


    def sort_key(p):
        normalized_p = scaler.transform([p.F])[0]
        return sum(normalized_p)

    all_populations = [a.pop for a in data["history"]]
    last_population = all_populations[-1]
    objective_values = [ind.F for ind in last_population]
    scaler = MinMaxScaler()
    normalized_values = scaler.fit_transform(objective_values)
    sorted_population = sorted(last_population, key=sort_key)
    top_n_individuals = sorted_population[:top_individuals]
    variables_values = [ind.X for ind in top_n_individuals]



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




if __name__ == "__main__":
    asyncio.run(main())
