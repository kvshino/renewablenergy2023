from functions import *
import asyncio
from mercati_energetici import MercatiElettrici




async def main():
    data = setup()
    energy_request(data)
    dataframe=pd.DataFrame(data)
    #print(get_meteo_data())

    energyCosts = await get_intra_days_market(1)
    #plot_graph(energyCosts, "ora", "prezzo","Hours", "Price", "Price", "#B55E60")
    #plt.show()
    

    # try:
    #     data["mean_difference"], data["future_mean"], data["past_mean"] = await mean_difference()
    #     print(data["mean_difference"], data["future_mean"], data["past_mean"])
    #     battery_or_grid(data,10)
        
    # except Exception as error:
    #     print(error)



    meteo_DF = filter_meteo_between_ss_and_sr(data)
    
    meteo_DF["expected_power_production"] = get_expected_power_production_from_PV(data, meteo_DF["direct_radiation"], meteo_DF["diffuse_radiation"], meteo_DF["temperature_2m"])
    print(meteo_DF)















    

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