import asyncio
from costi import *
from functions import *
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

data = setup()


async def main():
    data["prices"] = await get_intra_days_market()  # Bring the prices of energy from Mercati Elettrici
    current_datetime = datetime.now() + timedelta(hours=1)
    time_column = pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')
    app_list = []


    for value in time_column.strftime('%H'):
        value = int(value)
        if (value != 00):
            app_list.append(data["prices"]["prezzo"][int(value - 1)])
        else:
            app_list.append(data["prices"]["prezzo"][23])
    data["prices"]["prezzo"] = app_list

    plot_GME_prices(data)
    plt.show()


    data["res"], data["history"] = start_genetic_algorithm(data, 500, 130, 24)


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




if __name__ == "__main__":
    asyncio.run(main())
