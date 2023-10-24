from functions import *
import pandas as pd

data = setup()

energy_request(data)

dataframe=pd.DataFrame(data)


plot_graph(data, "load_profile", "kW/h", "Load profile", "#B55E60")
plot_graph(data, "battery_levels", "kW/h", "Battery Level", "#609E6E")
plot_graph(data, "energy_grid", "kW/h", "Energy from/to Grid", "#5975A5")
plot_graph(data, "energy_pv", "kW/h", "Energy from PV", "#CC8962")
plt.show()

"""
print("L'utente ha speso/guadagnato avendo i pannelli solari e la batteria:")
print(profit(data))
#disabilito sia la batteria che il pannello, costi se non avessi i pannellis
data = setup(disablePV=True, disableBattery=True)
energy_request(data)
print("L'utente ha speso/guadagnato non avendo i pannelli solari e la batteria:")
print(profit(data))"""