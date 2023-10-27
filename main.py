from functions import *
import asyncio
from mercati_energetici import MercatiElettrici




async def main():
    data = setup()
    energy_request(data)
    dataframe=pd.DataFrame(data)
    print(get_meteo_data())

    energy = await get_intra_day_market()
    plot_graph(energy, "ora", "prezzo","Hours", "Price", "Price", "#B55E60")
    plt.show()

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