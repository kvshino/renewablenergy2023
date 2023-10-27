from functions import *
import pandas as pd
import asyncio
from mercati_energetici import MercatiElettrici, MercatiGas, MercatiAmbientali, MGP
data = setup()

energy_request(data)
async def main():
    async with MercatiElettrici() as mercati_elettrici:
        await mercati_elettrici.get_general_conditions()
        await mercati_elettrici.get_disclaimer()
        await mercati_elettrici.get_markets()
        dati = await mercati_elettrici.get_prices("MI-A2", "20221001")
        pandasdati = pd.DataFrame(dati)
        sud = pandasdati.loc[pandasdati['zona'] == "SUD"]
        print(sud)
        plot_graph(sud, "ora", "prezzo","", "", "#B55E60")
        plt.show()
dataframe=pd.DataFrame(data)



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

plt.show()
"""

if __name__ == "__main__":
    asyncio.run(main())