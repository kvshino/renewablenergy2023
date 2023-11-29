import yaml
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pannello import *
from costi import *
from meteo import *



def setup(disable_pv: bool = False, disable_battery: bool = False) -> dict:
    """
    Takes the datas from the conf.yaml and stores them in data.

    Args:
        disable_pv: when True disables the PV grid
        disable_battery: when True disables the battery (a plant without accumulators)

    Returns:
        data: struct containing all the datas
    """
    sns.set_theme()
    with open("conf.yaml") as f:
        data = yaml.load(f, Loader=yaml.FullLoader)

    if disable_pv:
        data["energy_pv"] = []

    if disable_battery:
        data["maximum_battery_level"] = 0
        data["minimum_battery_level"] = 0
        data["initial_battery_level"] = 0

    for i in range(0, 24):
        if disable_pv:
            data["energy_pv"].append(0)
        data["hours"].append(i)
        data["energy_grid"].append(0)
        data["battery_levels"].append(data["initial_battery_level"])

    return data


def plot_graph(data, x, y, x_label, y_label, title, color):
    """
    Plots a graph.

    Args:
        data: a dataframe containing x and y
        x: dataframe column for the x-coordinates
        y: dataframe column for the y-coordinates
        x_label: label for the x-coordinates
        y_label: label for the y-coordinates
        title: used for the window
        color: color of the line plot

    """
    plt.figure(title)
    sns.lineplot(data, x=x, y=y, color=color)
    plt.title(title)
    plt.xticks(np.arange(0, 24, 1.0))
    plt.xlabel(x_label)
    plt.ylabel(y_label)
