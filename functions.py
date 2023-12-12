import yaml
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from pannello import *
from costi import *
from meteo import *
import itertools
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX
import matplotlib.pyplot as plt


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
        data["soc_max"] = 0
        data["soc_min"] = 0
        data["socs"] = 0

    for i in range(0, 24):
        if disable_pv:
            data["energy_pv"].append(0)
        data["hours"].append(i)
        data["energy_grid"].append(0)
        # data["battery_levels"].append(data["initial_battery_level"])

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


def get_true_load_consumption():
    # Legge il CSV in un DataFrame
    df = pd.read_csv("csv/load_profile.csv")

    # Ottiene la data e l'ora attuali
    now = datetime.now()

    # Filtra il DataFrame fino alla data e all'ora attuali
    df_troncato = df[(pd.to_datetime(df['data'], format='%Y%m%d') < pd.to_datetime(now.strftime('%Y%m%d'))) |
                     ((pd.to_datetime(df['data'], format='%Y%m%d') == pd.to_datetime(now.strftime('%Y%m%d'))) &
                      (df['ora'] <= now.hour))]

    return df_troncato


def get_estimate_load_consumption(dataframe: pd.DataFrame):
    media_oraria = dataframe.groupby("ora")["consumo"].mean()

    # Convertire la colonna 'data' al formato datetime
    dataframe['data'] = pd.to_datetime(dataframe['data'], format='%Y%m%d')

    # Aggiungere una colonna 'giorno' con il nome del giorno
    dataframe['giorno'] = dataframe['data'].dt.day_name()

    oggi = datetime.now().strftime("%A")
    domani = (datetime.now() + timedelta(days=1)).strftime("%A")


    # Filtrare il DataFrame per mantenere solo le righe con date uguali a oggi o domani
    dataframe = dataframe[(dataframe['giorno'] == oggi) | (dataframe['giorno'] == domani)]

    media_giorno_target = dataframe.groupby("ora")["consumo"].mean()

    return (media_oraria + media_giorno_target) / 2


def shift_result_estimation_consumption(dataframe: pd.DataFrame):
    pass
