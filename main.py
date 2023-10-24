from functions import *

data = setup(disablePV=True)

energy_request(data)

plot_graph(data["hours"], data["load_profile"], "Time", "kW/h", "Load profile", "red")
plot_graph(data["hours"], data["battery_levels"], "Time", "kW/h", "Battery Level", "green")
plot_graph(data["hours"], data["energy_grid"], "Time", "kW/h", "Energy from/to Grid", "blue")
plot_graph(data["hours"], data["energy_pv"], "Time", "kW/h", "Energy from PV", "yellow")
print(data["load_profile"])
print(data["battery_levels"])
print(data["energy_grid"])
print(data["energy_pv"])
plt.show()