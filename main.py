from functions import *
import pandas as pd
import asyncio
from mercati_energetici import MercatiElettrici
from datetime import datetime, timedelta
from openmeteo_py import OWmanager
from openmeteo_py.Hourly.HourlyForecast import HourlyForecast
from openmeteo_py.Options.ForecastOptions import ForecastOptions
from openmeteo_py.Utils.constants import *

# Latitude, Longitude 
longitude = 33.89
latitude =  -6.31

hourly = HourlyForecast()


#here we provide a bit more information as we want to pull also the data of past days
options = ForecastOptions(latitude,longitude,False,celsius,kmh,mm,iso8601,utc)

#notice that we had to give the value "None" for the hourly parameter,otherwise you'll be filling the hourly parameter instead of the daily one.
mgr = OWmanager(options,OWmanager.forecast,hourly.temperature_2m().direct_radiation().diffuse_radiation())


# Download data
meteo = mgr.get_data(1)

pandasmeteo = pd.DataFrame(meteo["hourly"])

today = str(datetime.now())[:-16]+"T00:00"
aftertomorrow = str(datetime.now() + timedelta(days=2))[:-16]+"T24:00"
print(pandasmeteo[(pandasmeteo['time'] > today) & (pandasmeteo['time'] < aftertomorrow)])

"""




data = setup()

energy_request(data)

pandasmeteo = pd.DataFrame(meteo)

print(pandasmeteo.columns)
async def main():
    async with MercatiElettrici() as mercati_elettrici:
        await mercati_elettrici.get_general_conditions()
        await mercati_elettrici.get_disclaimer()
        await mercati_elettrici.get_markets()
        dati = await mercati_elettrici.get_prices("MI-A2", "20221001")
        pandasdati = pd.DataFrame(dati)
        sud = pandasdati.loc[pandasdati['zona'] == "SUD"]
        plot_graph(sud, "ora", "prezzo","", "", "#B55E60")

dataframe=pd.DataFrame(data)




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


if __name__ == "__main__":
    asyncio.run(main())
"""