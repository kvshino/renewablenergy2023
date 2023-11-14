from functions import *
import asyncio
from mercati_energetici import MercatiElettrici




async def main():
    data = setup()
    energy_request(data)
    dataframe=pd.DataFrame(data)
    print(get_meteo_data())

    energyCosts = await get_intra_days_market(1)
    plot_graph(energyCosts, "ora", "prezzo","Hours", "Price", "Price", "#B55E60")
    plt.show()


    try:
        data["mean_difference"], data["future_mean"], data["past_mean"] = await mean_difference()
        battery_or_grid(data,10)
    except Exception as error:
        print(error)


    try:
        futurePrices = await get_future_day_market()

    except Exception as error:
        print(error)

    

"""
plot_graph(data, "hours", "load_profile", "kW", "Load profile", "#B55E60")
plot_graph(data, "hours", "battery_levels", "kWh", "Battery Level", "#609E6E")
plot_graph(data, "hours", "energy_grid", "kW", "Power from/to Grid", "#5975A5")
plot_graph(data, "hours", "energy_pv", "kW", "Power from PV", "#CC8962")
plot_graph(data, "hours", "price","$","Energy Cost","green")

print("L'utente ha speso/guadagnato avendo i pannelli solari e la batteria:")
print(profit(data))
#disabilito sia la batteria che il pannello, costi se non avessi i pannellis
data = setup(disablePV=True, disableBattery=True)
energy_request(data)
print("L'utente ha speso/guadagnato non avendo i pannelli solari e la batteria:")
print(profit(data))
"""

if __name__ == "__main__":
    asyncio.run(main())