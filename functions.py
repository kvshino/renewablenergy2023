import matplotlib.pyplot as plt
import seaborn as sns
import yaml

from pannello import *


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


def plot_graph(data, x, y, title, color, label):
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
    ax=sns.lineplot(data, x=x, y=y, color=color)
    ax.plot(data[x], data[y], label=label, color=color)

    plt.xticks(data['datetime'], data['datetime'].dt.strftime('%d/%m Ore:%H:%M'), rotation=45)
    plt.title(title)



def plot_subgraph(data, x, y, color, label, position):

    plt.subplot(2, 3, position)
    plt.plot(data[x],data[y], color=color)
    plt.xticks(data['datetime'], data['datetime'].dt.strftime('%H'), rotation=10)
    plt.title(label)
    if label != "Cost":
        plt.ylim(-10000, 10000)


def get_true_load_consumption():
    """
        Returns a dataframe containing the load consumption history.
        From the actual hour back to the earliest ones.
        """

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
    """
        Returns the consumption estimate of the load.

        df.loc[1, 'consumo']

        From the next hour up to the 24h.
    """

    media_oraria = dataframe.groupby("ora")["consumo"].mean()

    dataframe['data'] = pd.to_datetime(dataframe['data'], format='%Y%m%d')

    dataframe['giorno'] = dataframe['data'].dt.day_name()

    next_hour = datetime.now() + timedelta(hours=1) - timedelta(minutes=datetime.now().minute)
    oggi = (next_hour).strftime("%A")
    domani = (next_hour + timedelta(days=1)).strftime("%A")

    dataframe = dataframe[(dataframe['giorno'] == oggi) | (dataframe['giorno'] == domani)]

    media_giorno_target = dataframe.groupby("ora")["consumo"].mean()

    df = pd.DataFrame((media_oraria + media_giorno_target) / 2).reset_index()
    df = pd.concat([df.iloc[next_hour.hour:], df.iloc[:next_hour.hour]])

    df.reset_index(drop=True, inplace=True)
    return df


def evaluate(data, res):
    sum = []
    sum.append(0)
    delta_production = difference_of_production(data)
    sold = data["sold"]
    upper_limit = (data["soc_max"] * data["battery_capacity"])
    lower_limit = (data["soc_min"] * data["battery_capacity"])
    actual_percentage = []
    actual_percentage.append(data["socs"][-1])
    
    quantity_delta_battery=[]
    # valori negativi indicano consumi ,positivi guadagni
    for j in range(24):
        charge = res.X[f"b{j}"]
        percentage = res.X[f"i{j}"]
        quantity_charging_battery=None
        quantity_discharging_battery=None
        if charge:

            quantity_charging_battery = ((upper_limit - actual_percentage[j] * upper_limit) * percentage) / 100
            actual_percentage.append(actual_percentage[j] + quantity_charging_battery / upper_limit)

            if quantity_charging_battery - delta_production.iloc[j] < 0:
                # devo vendere
                sum.append(
                    sum[j] + ((quantity_charging_battery - delta_production.iloc[j]) * sold))  # sum = sum - rimborso

            else:
                sum.append(
                    sum[j] + (quantity_charging_battery - delta_production.iloc[j]) * data["prices"]["prezzo"].iloc[j])
        else:
            quantity_discharging_battery = ((actual_percentage[j] * upper_limit - lower_limit) * percentage) / 100
            actual_percentage.append(actual_percentage[j] - quantity_discharging_battery / upper_limit)

            if delta_production.iloc[j] + quantity_discharging_battery > 0:
                # sto scaricando la batteria  con surplus di energia
                # vendo alla rete MA dalla batteria
                # if delta_production.iloc[j] > 0:
                #     # vendo alla rete quello del fotovoltaico
                #     sum = sum - delta_production.iloc[j] * sold
                # else:
                #     # in questo else teoricamente potrei vendere enegia della batteria ma invece sovrascrivo il valore
                #     data["socs"][j + 1] = data["socs"][j] + delta_production.iloc[j] / upper_limit  # DA VEDERE: Non superare lo 0% di socs
                sum.append(sum[j] - ((delta_production.iloc[j] + quantity_discharging_battery) * sold))
            else:
                sum.append(sum[j] + (
                        - (delta_production.iloc[j] + quantity_discharging_battery) * data["prices"]["prezzo"].iloc[j]))
                
        if quantity_charging_battery != None:
            quantity_delta_battery.append(+quantity_charging_battery)
        else:
            quantity_delta_battery.append(-quantity_discharging_battery)

    return sum[1:], actual_percentage, quantity_delta_battery
