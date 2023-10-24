from functions import *

data = setup()

energy_request(data)

plot_graph(data["hours"], data["load_profile"], "Time", "kW/h", "Load profile", "red")
plot_graph(data["hours"], data["battery_levels"], "Time", "kW/h", "Battery Level", "green")
plot_graph(data["hours"], data["energy_grid"], "Time", "kW/h", "Energy from/to Grid", "blue")
plot_graph(data["hours"], data["energy_pv"], "Time", "kW/h", "Energy from PV", "yellow")
#plt.show()

print("L'utente ha speso/guadagnato avendo i pannelli solari e la batteria:")
print(profit(data))
#disabilito sia la batteria che il pannello, costi se non avessi i pannellis
data = setup(disablePV=True, disableBattery=True)
energy_request(data)
print("L'utente ha speso/guadagnato non avendo i pannelli solari e la batteria:")
print(profit(data))


