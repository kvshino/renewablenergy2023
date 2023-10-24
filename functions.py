import os
import yaml
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def energy_request(data):
    for i in data["hours"]:
        data["energy_delta"] = data["energy_pv"][i]- data["load_profile"][i]


        if(data["energy_delta"] >= 0):                   #produco più di quel che consumo
            if (i == 0):
                if(data["initial_battery_level"] + data["energy_delta"] >= data["maximum_battery_level"]):      #batteria piena ,vendo alla rete(in futuro accumulo sopra soglia)
                    data["energy_grid"][i] = data["initial_battery_level"] + data["energy_delta"] - data["maximum_battery_level"]
                    data["battery_levels"][i] = data["maximum_battery_level"]

                if(data["initial_battery_level"] + data["energy_delta"] < data["maximum_battery_level"]):        #batteria scarica ,la ricarico
                    data["battery_levels"][i] = data["initial_battery_level"] + data["energy_delta"]
            else:
                if(data["battery_levels"][i-1] + data["energy_delta"] >= data["maximum_battery_level"]):      #batteria piena ,vendo alla rete(in futuro accumulo sopra soglia)
                    data["energy_grid"][i] = data["battery_levels"][i-1] + data["energy_delta"] - data["maximum_battery_level"]
                    data["battery_levels"][i] = data["maximum_battery_level"]

                if(data["battery_levels"][i-1] + data["energy_delta"] < data["maximum_battery_level"]):        #batteria scarica ,la ricarico
                    data["battery_levels"][i] = data["battery_levels"][i-1] + data["energy_delta"]

        if(data["energy_delta"] < 0):                     #consumo più di quello che produco
            if(i == 0):
                if(data["initial_battery_level"] > data["minimum_battery_level"] + abs(data["energy_delta"]) ):       #la batteria ha sufficiente energia per alimentare il carico
                    data["battery_levels"][i] = data["initial_battery_level"] - abs(data["energy_delta"])
                    
                if(data["initial_battery_level"] < data["minimum_battery_level"] + abs(data["energy_delta"])):                #la batteria non ha sufficiente energia(totale), prendo energia dalla rete
                    data["energy_grid"][i] = - ( abs(data["energy_delta"]) - ( data["initial_battery_level"] - data["minimum_battery_level"] ) )
                    data["battery_levels"][i] = data["minimum_battery_level"]
            else:
                if(data["battery_levels"][i-1] > data["minimum_battery_level"] + abs(data["energy_delta"]) ):       #la batteria ha sufficiente energia per alimentare il carico
                    data["battery_levels"][i] = data["battery_levels"][i-1] - abs(data["energy_delta"])
                    
                if(data["battery_levels"][i-1] < data["minimum_battery_level"] + abs(data["energy_delta"])):                #la batteria non ha sufficiente energia(totale), prendo energia dalla rete
                    data["energy_grid"][i] = - ( abs(data["energy_delta"]) - ( data["battery_levels"][i-1] - data["minimum_battery_level"] ) )
                    data["battery_levels"][i] = data["minimum_battery_level"]

    return data


def setup(disablePV=0, disableBattery=0):
    sns.set_theme()
    with open("conf.yaml") as f:
        data = yaml.load(f, Loader=yaml.FullLoader)

    if disablePV:
        data["energy_pv"] = []
    
    if disableBattery:
        data["maximum_battery_level"] = 0
        data["minimum_battery_level"] = 0
        data["initial_battery_level"] = 0

    for i in range(0,24):
        if disablePV:
            data["energy_pv"].append(0)
        data["hours"].append(i)
        data["energy_grid"].append(0)
        data["battery_levels"].append(data["initial_battery_level"])

    return data


def plot_graph(data, y, ylabel, title, color):
    plt.figure(title)
    sns.lineplot(data, x="hours", y=y,  color=color)
    plt.title(title)
    plt.xticks(np.arange(0, 24, 1.0))
    plt.xlabel("Hours")
    plt.ylabel(ylabel)

def profit(data):
    profit=0
    for index, item in enumerate(data["energy_grid"]):
        if item >=0:
            profit=profit+ (data["energy_grid"][index]*data["sold"])
        if item < 0:
            profit= profit +(data["energy_grid"][index]*data["price"][index])
    return profit