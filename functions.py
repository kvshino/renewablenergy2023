import yaml
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from mercati_energetici import MercatiElettrici
from datetime import datetime, timedelta
from openmeteo_py import OWmanager
from openmeteo_py.Hourly.HourlyForecast import HourlyForecast
from openmeteo_py.Options.ForecastOptions import ForecastOptions
from openmeteo_py.Utils.constants import *
from suntime import Sun
import pytz
import statistics


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


def energy_request(data) -> dict:
    """
    Estimate grid consumption, daily energy production from solar panels,
    and the discharge/charge behavior of the battery.

    Args:
        data: struct containing all the datas

    Returns:
        data: struct containing all the datas (now updated with the new values)
    """
    for i in data["hours"]:
        data["energy_delta"] = data["energy_pv"][i] - data["load_profile"][i]

        if data["energy_delta"] >= 0:  # produco più di quel che consumo
            if i == 0:
                if data["initial_battery_level"] + data["energy_delta"] >= data[
                    "maximum_battery_level"]:  # batteria piena ,vendo alla rete(in futuro accumulo sopra soglia)
                    data["energy_grid"][i] = data["initial_battery_level"] + data["energy_delta"] - data[
                        "maximum_battery_level"]
                    data["battery_levels"][i] = data["maximum_battery_level"]

                if data["initial_battery_level"] + data["energy_delta"] < data[
                    "maximum_battery_level"]:  # batteria scarica ,la ricarico
                    data["battery_levels"][i] = data["initial_battery_level"] + data["energy_delta"]
            else:
                if data["battery_levels"][i - 1] + data["energy_delta"] >= data[
                    "maximum_battery_level"]:  # batteria piena ,vendo alla rete(in futuro accumulo sopra soglia)
                    data["energy_grid"][i] = data["battery_levels"][i - 1] + data["energy_delta"] - data[
                        "maximum_battery_level"]
                    data["battery_levels"][i] = data["maximum_battery_level"]

                if data["battery_levels"][i - 1] + data["energy_delta"] < data[
                    "maximum_battery_level"]:  # batteria scarica ,la ricarico
                    data["battery_levels"][i] = data["battery_levels"][i - 1] + data["energy_delta"]

        if data["energy_delta"] < 0:  # consumo più di quello che produco
            if i == 0:
                if data["initial_battery_level"] > data["minimum_battery_level"] + abs(
                        data["energy_delta"]):  # la batteria ha sufficiente energia per alimentare il carico
                    data["battery_levels"][i] = data["initial_battery_level"] - abs(data["energy_delta"])

                if data["initial_battery_level"] < data["minimum_battery_level"] + abs(data[
                                                                                           "energy_delta"]):  # la batteria non ha sufficiente energia(totale), prendo energia dalla rete
                    data["energy_grid"][i] = - (abs(data["energy_delta"]) - (
                                data["initial_battery_level"] - data["minimum_battery_level"]))
                    data["battery_levels"][i] = data["minimum_battery_level"]
            else:
                if data["battery_levels"][i - 1] > data["minimum_battery_level"] + abs(
                        data["energy_delta"]):  # la batteria ha sufficiente energia per alimentare il carico
                    data["battery_levels"][i] = data["battery_levels"][i - 1] - abs(data["energy_delta"])

                if data["battery_levels"][i - 1] < data["minimum_battery_level"] + abs(data[
                                                                                           "energy_delta"]):  # la batteria non ha sufficiente energia(totale), prendo energia dalla rete
                    data["energy_grid"][i] = - (abs(data["energy_delta"]) - (
                                data["battery_levels"][i - 1] - data["minimum_battery_level"]))
                    data["battery_levels"][i] = data["minimum_battery_level"]

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


def profit(data) -> float:
    """
    Returns how much the system takes from/gives to the grid in €.

    Args:
        data: struct containing all the datas
    Returns:
        profit: €
    """
    earning = 0
    for index, item in enumerate(data["energy_grid"]):
        if item >= 0:
            earning = earning + (data["energy_grid"][index] * data["sold"])
        if item < 0:
            earning = earning + (data["energy_grid"][index] * data["price"][index])
    return earning


def get_meteo_data(latitude: float = 40.6824404, longitude: float = 14.7680965) -> pd.core.frame.DataFrame:
    """
    Fetches meteo datas from Open-Meteo.com
    The datas are hour by hour until the day after tomorrow.

    Args:
        latitude
        longitude

    Returns:
        pandasmeteo: a dataframe containing the temperature and the direct/diffuse radiation
    """
    hourly = HourlyForecast()
    options = ForecastOptions(latitude, longitude, False, celsius, kmh, mm, iso8601, utc)
    mgr = OWmanager(options, OWmanager.forecast, hourly.temperature_2m().direct_radiation().diffuse_radiation())
    meteo = mgr.get_data(1)
    pandasmeteo = pd.DataFrame(meteo["hourly"])
    today = str(datetime.now())[:-16] + "T00:00"
    aftertomorrow = str(datetime.now() + timedelta(days=2))[:-16] + "T24:00"
    return pandasmeteo[(pandasmeteo['time'] > today) & (pandasmeteo['time'] < aftertomorrow)]


def get_tomorrow_meteo_data(latitude: float = 40.6824404, longitude: float = 14.7680965) -> pd.core.frame.DataFrame:
    """

    Fetches tomorrow meteo datas from Open-Meteo.com
    The datas are hour by hour until the day after tomorrow.

    Args:
        latitude
        longitude

    Returns:
        pandasmeteo: a dataframe containing the temperature and the direct/diffuse radiation
    """
    hourly = HourlyForecast()
    options = ForecastOptions(latitude, longitude, False, celsius, kmh, mm, iso8601, utc)
    mgr = OWmanager(options, OWmanager.forecast, hourly.temperature_2m().direct_radiation().diffuse_radiation())
    meteo = mgr.get_data(1)
    pandasmeteo = pd.DataFrame(meteo["hourly"])
    today = str(datetime.now())[:-16] + "T23:00"
    tomorrow = str(datetime.now() + timedelta(days=1))[:-16] + "T24:00"
    return pandasmeteo[(pandasmeteo['time'] > today) & (pandasmeteo['time'] < tomorrow)]


async def get_intra_days_market(days=1) -> pd.core.frame.DataFrame:
    """
    Fetches price datas from mercatoelettrico.com

    Returns:
        sud: a dataframe containing prices data
    """
    async with MercatiElettrici() as mercati_elettrici:
        await mercati_elettrici.get_general_conditions()
        await mercati_elettrici.get_disclaimer()
        await mercati_elettrici.get_markets()

        pandasdati = pd.DataFrame()
        today = datetime.now()
        for i in range(days):
            dati = await mercati_elettrici.get_prices("MI-A2", today.strftime("%Y%m%d"))
            today = today - timedelta(days=1)
            pandasdati = pd.concat([pandasdati, pd.DataFrame(dati)])

        sud = pandasdati.loc[pandasdati['zona'] == "SUD"].drop(["mercato", "zona"], axis=1)

        return sud


def energy_mean_price(energy_costs) -> float:
    """
        Calculate the average energy price.

        Args:
            energy_costs : Dataframe with column "prezzo"

        Returns:
            Mean of energy price
    """
    return energy_costs["prezzo"].mean()


async def get_future_day_market() -> pd.core.frame.DataFrame:
    """
        Fetches future price datas from mercatoelettrico.com

        Returns:
            price_df: a dataframe containing future prices data
    """
    async with MercatiElettrici() as mercati_elettrici:
        await mercati_elettrici.get_general_conditions()
        await mercati_elettrici.get_disclaimer()
        await mercati_elettrici.get_markets()
        try:
            price = await mercati_elettrici.get_prices("MI-A2", (datetime.now() + timedelta(days=1)).strftime("%Y%m%d"))
            price_df = pd.DataFrame(price).drop(["mercato", "zona"], axis=1)
        except:
            raise Exception("Tomorrow market data prices are not available yet")
        return price_df


def filter_meteo_between_ss_and_sr(data) -> pd.core.frame.DataFrame:
    """
        Filter the meteo data between sunrise and sunset

        Args:
            data : Dataframe with local informations

        Returns:
            Filtered dataFrame
    """
    meteo_df = get_meteo_data()
    sun = Sun(data["latitude"], data["longitude"])
    tz = pytz.timezone(data["timezone"])
    today_sr = sun.get_local_sunrise_time(datetime.today(), local_time_zone=tz)
    today_ss = sun.get_local_sunset_time(datetime.today(), local_time_zone=tz)

    today_sr = int((today_sr - timedelta(minutes=today_sr.minute)).strftime("%H"))
    today_ss = int((today_ss + timedelta(hours=1) - timedelta(minutes=today_ss.minute)).strftime("%H"))

    return meteo_df[
        (pd.to_datetime(meteo_df['time']).dt.hour > today_sr) & (pd.to_datetime(meteo_df['time']).dt.hour < today_ss)]


def get_temp_cell(temp_air, noct, irradiance) -> float:
    """
        Calculate temperature of cell

        Args:
            temp_air : air temperature
            noct : Standard value
            irradiance : irradiance

        Returns:
           Cell temperature
    """
    return temp_air + (((noct - 20) / 800) * irradiance)


def get_effective_irradiance(f1, f2, sf, g_b, f_d, g_d) -> float:
    return f1 * sf * (g_b * f2 + f_d * g_d)


def get_expected_power_production_from_pv(data, direct_radiation, diffuse_radiation, temp_air) -> float:
    """
        Calculate expected power production of a standard pannel

        Returns:
            Power production

    """

    irradiance = get_effective_irradiance(data["f1"], data["f2"], data["SF"], direct_radiation, data["fd"],
                                          diffuse_radiation)
    temp_cell = get_temp_cell(temp_air, data["noct"], irradiance)

    return (irradiance / 1000) * data["pmax"] * (1 + data["gamma"] * (temp_cell - data["temp_ref"]))


async def mean_difference(days=1) -> float:
    """

        Calculate the difference between the mean of past energy prices
        and the mean of future prices

        Returns:
            Difference between the prices

    """
    past_df = await get_intra_days_market(days=days)
    past_mean = energy_mean_price(past_df)

    try:
        future_df = await get_future_day_market()
        future_mean = energy_mean_price(future_df)
        return (future_mean - past_mean), future_mean, past_mean
    except Exception as error:
        print(error)


def battery_or_grid(data, price_percentage):
    # difference > 0 --> costo futuro > costo passato
    # difference < 0 --> costo futuro < costo passato

    meteo_df = filter_meteo_between_ss_and_sr(data)

    if data["mean_difference"] > data[
        "past_mean"] * price_percentage / 100:  # Se il costo energia della rete è troppo alto rispetto al passato, a prescindere prendo dalla batteria
        print("Bring energy from the battery")


def funzione():
    """
    Faccio questi calcoli solo per capire come comportarmi tra un'ora

    Sto attualmente producendo di più:
        - prendo dal fotovoltaico, carico la batteria


    Sto attualmente producendo di meno:
        in ogni caso controllo i prezzi
        - prendo dalla rete
            - quando la batteria è scarica
            - quando domani la differenza produzione-consumo è negativa && quando domani il costo è elevato (preservo la batteria per domani)
            - ##quando la batteria è scarica && quando il costo odierno è basso && il costo della rete domani è alto
        - prendo dalla batteria
            - quando domani la differenza produzione-consumo è positiva && quando domani il costo è elevato
            - quando domani la differenza produzione-consumo è negativa && quando domani il costo è basso
            - quando domani la differenza produzione-consumo è positiva && quando domani il costo è basso

        PERCENTUALE PRODUZIONE-CONSUMO     threshold
        Influenzata da:
        - costo dell'energia di domani,
        - energia in batteria,
        - differenza produzione-consumo del futuro (sia fra un ora che domani)
    """
    pass


def current_hour_strategy(data, hour):
    energy_delta = data["energy_pv"][hour] - data["load_profile"][hour]
    battery_level = data["battery_levels"][hour]
    minimum_battery_level = data["minimum_battery_level"]
    if energy_delta > 0:  # produco più di quel che consumo
        pass
    else:  # produco meno di quel che consumo
        if battery_level < minimum_battery_level:  # se la batteria è scarica
            print("prendo dalla rete")

    return 0


def difference_of_production(data):
    """
        Estime the difference between the future production
        and the future load

        Returns :
            Array with difference


    """
    tomorrow_meteo = get_tomorrow_meteo_data()
    tomorrow_meteo["production"] = get_expected_power_production_from_pv(data, tomorrow_meteo["direct_radiation"],
                                                                         tomorrow_meteo["diffuse_radiation"],
                                                                         tomorrow_meteo["temperature_2m"])

    return tomorrow_meteo["production"] - data["load_profile"]


def k_parameter(data) -> float:
    return statistics.mean(data["energy_pv"]) / statistics.mean(data.get("load_profile")) #Si dovrà cambiare

async def h_parameter(data):

    price_week = await get_intra_days_market(7) #prende il costo degli ultimi 7 giornii e te lo mette in un df
    data = int(datetime.now().strftime("%Y%m%d"))
    ora = int(datetime.now().strftime("%H"))
    current_cost = price_week[(price_week['data'] == data) & (price_week['ora'] == ora)]["prezzo"].item()
    price_previous_week = price_week[price_week['data']!=data]
    media = price_previous_week["prezzo"].mean()
    return current_cost / media




def logic(data):
    #1 -> prendo energia dalla rete
    #0 -> prendo energia dalla batteria
    #2 -> prendo energia dalla batteria fino a quando possibile, poi dalla rete


    hour = datetime.now().hour()
    if data["battery_levels"][hour] - (data["load_profile"][hour] - data["energy_pv"])[hour] < data["minimum_battery_level"]:
        print("Bring energy from the grid")
        return 1
    else:
        k= k_parameter(data)
        if k < data["k_min"]:
            pass
        else:
            print("Bring energy from the grid")
            return 1


