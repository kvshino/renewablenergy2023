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


async def get_h_parameter(data) -> float:

    price_week = await get_intra_days_market(7) #prende il costo degli ultimi 7 giornii e te lo mette in un df
    data = int(datetime.now().strftime("%Y%m%d"))
    ora = int(datetime.now().strftime("%H"))
    current_cost = price_week[(price_week['data'] == data) & (price_week['ora'] == ora)]["prezzo"].item()
    price_previous_week = price_week[price_week['data']!=data]
    media = price_previous_week["prezzo"].mean()
    return current_cost / media

async def get_k_parameter(data) -> float:
    # ora = int(datetime.now().strftime("%H"))
    ora = 0
    e_l = 0
    power = get_expected_power_production_from_pv_of_tomorrow(data)
    for i in range(ora, ora+24):
        e_l = e_l + data['load_profile'][i]


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








def StavaNelMainPlot():
    plot_graph(cost_dataframe, "datetime", "value", "Costo Grid", "Orange", "Cost")
    plot_graph(expected_load_dataframe, "datetime", "value", "Grafico", "Red", "Expected Load")
    plot_graph(expected_production_dataframe, "datetime", "value", "Grafico", "Blue", "Expected Production")
    plot_graph(battery_wh_dataframe, "datetime", "value", "Grafico", "Green", "Battery Level Wh")
    plot_graph(difference_dataframe, "datetime", "value", "Grafico", "Purple", "Difference")
    plot_graph(quantity_delta_battery_dataframe, "datetime", "value", "Grafico", "Yellow", "Delta Battery")
    plt.legend()

    plt.figure()
    plot_subgraph(cost_dataframe, "datetime", "value", "Orange", "Cost", 1)
    plot_subgraph(expected_load_dataframe, "datetime", "value", "Red", "Expected Load", 2)
    plot_subgraph(expected_production_dataframe, "datetime", "value", "Blue", "Expected Production", 3)
    plot_subgraph(battery_wh_dataframe, "datetime", "value", "Green", "Battery Level Wh", 4)
    plot_subgraph(difference_dataframe, "datetime", "value", "Purple", "Difference", 5)
    plot_subgraph(quantity_delta_battery_dataframe, "datetime", "value", "Yellow", "Delta Battery", 6)

    print("Best solution found: \nX = %s\nF = %s" % (res.X, res.F))

    # This part of code puts the update value of the battery in the file csv/socs.csv
    if res.X["b0"] == True:

        new_value = data["socs"] + ((1 - data["socs"]) * (res.X["i0"] / 100))
    else:
        new_value = data["socs"] - ((data["socs"]) * (res.X["i0"] / 100))
    df_nuovo = pd.DataFrame([new_value])
    df_nuovo.to_csv('csv/socs.csv', mode='a', header=False, index=False)