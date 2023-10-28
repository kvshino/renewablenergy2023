import os
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np




def energy_request(data):
    """
    Estimate grid consumption, daily energy production from solar panels, and the discharge/charge behavior of the battery.

    Args:
        data: struct containing all the datas

    Returns: 
        data: struct containing all the datas (now updated with the new values)
    """
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


def plot_graph(data, x, y, xlabel, ylabel, title, color):
    """
    Plots a graph.

    Args:
        data: a dataframe containing x and y
        x: dataframe column for the x-coordinates
        y: dataframe column for the y-coordinates
        xlabel: label for the x-coordinates
        ylabel: label for the y-coordinates
        title: used for the window
        color: color of the line plot

    """
    plt.figure(title)
    sns.lineplot(data, x=x, y=y,  color=color)
    plt.title(title)
    plt.xticks(np.arange(0, 24, 1.0))
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)

def profit(data):
    """
    Returns how much the system takes from/gives to the grid in €.

    Args:
        data: struct containing all the datas
    Returns:
        profit: €
    """
    profit=0
    for index, item in enumerate(data["energy_grid"]):
        if item >=0:
            profit=profit+ (data["energy_grid"][index]*data["sold"])
        if item < 0:
            profit= profit +(data["energy_grid"][index]*data["price"][index])
    return profit

