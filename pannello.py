from meteo import *


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
        Calculate expected power production of a standard panel

        Returns:
            Power production
    """

    irradiance = get_effective_irradiance(data["f1"], data["f2"], data["SF"], direct_radiation, data["fd"],
                                          diffuse_radiation)
    temp_cell = get_temp_cell(temp_air, data["noct"], irradiance)

    return (irradiance / 1000) * data["pmax"] * (1 + data["gamma"] * (temp_cell - data["temp_ref"]))


def get_expected_power_production_from_pv_of_tomorrow(data):
    tomorrow_meteo = get_tomorrow_meteo_data()
    tomorrow_meteo["production"] = get_expected_power_production_from_pv(data, tomorrow_meteo["direct_radiation"],
                                                                         tomorrow_meteo["diffuse_radiation"],
                                                                         tomorrow_meteo["temperature_2m"])

    return tomorrow_meteo


def difference_of_production(data):
    """
        Estimate the difference between the future production
        and the future load

        Returns :
            Array with difference
    """
    twentyfour_meteo = get_expected_power_production_from_pv_24_hours_from_now(data)
    return twentyfour_meteo["production"] - data["estimate"]["consumo"].values



####################################################################

def get_expected_power_production_from_pv_24_hours_from_now(data):
    twentyfour_meteo = get_meteo_data_24_hours_from_now(data["latitude"], data["longitude"])
    twentyfour_meteo["production"] = get_expected_power_production_from_pv(data, twentyfour_meteo["direct_radiation"],
                                                                         twentyfour_meteo["diffuse_radiation"],
                                                                         twentyfour_meteo["temperature_2m"])

    return twentyfour_meteo