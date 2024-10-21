from meteo import *
import math

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
    result=[0]*24
    for i in range(0,24):
        result[i]= temp_air[i] + (((noct - 20) / 800) * irradiance[i])
    
    return result


def get_effective_irradiance(sf, a, b, beta, thetaPV, f_d, g_bh, g_dh, zenith, azimuth) -> float:

    beta=math.radians(beta)
    thetaPV=math.radians(thetaPV)

    f1=[0]*24
    f2=[0]*24
    g_b=[0]*24
    g_d=[0]*24
    g=[0]*24
    for i in range(24):
        thetaZ=math.radians(zenith[i])   
        thetaA=math.radians(azimuth[i])
        angle=math.acos(math.cos(thetaZ)*math.cos(beta)+math.sin(thetaZ)*math.sin(beta)*math.cos(thetaA-thetaPV))
        
        if math.degrees(thetaZ) <= 90: 
            am=1/(math.cos(thetaZ)+0.5057*(96.080-thetaZ)**(-1.634))
        else:
            am=0

        for value in a:
            f1[i]+= value*am
        for value in b:
            f2[i]+= value*angle
        
        
        g_b[i]=(g_bh[i]*math.cos(angle)/math.cos(thetaZ))
        g_d[i]=(g_dh[i]*((1+math.cos(beta))/2))

        
        

        g[i]=f1[i] * sf * (g_b[i] * f2[i] + f_d * g_d[i])   

        

    
    return g


def get_expected_power_production_from_pv(data, meteo) -> float:
    """
        Calculate expected power production of a standard panel

        Returns:
            Power production
    """
    module_parameters={'temp_ref': data["temp_ref"], 'pdc0': data["pmax"], 'gamma_pdc': data["gamma"], 'A0': data["a"][0], 'A1': data["a"][1], 'A2': data["a"][2], 'A3': data["a"][3], 'A4': data["a"][4], 'B0': data["b"][0], 'B1': data["b"][1], 'B2': data["b"][2], 'B3': data["b"][3], 'B4': data["b"][4], 'B5': data["b"][5], 'FD': data["fd"]}
    time = pd.date_range(datetime.now()+timedelta(hours=1)-timedelta(minutes=datetime.now().minute)-timedelta(seconds=datetime.now().second), periods=24, freq='H', tz='UTC')
    altitude=pvlib.location.lookup_altitude(latitude=data["latitude"], longitude=data["longitude"])
    solpos = pvlib.solarposition.get_solarposition(
        time=time,
        latitude=data["latitude"],
        longitude=data["longitude"],
        altitude=altitude,
        temperature=meteo["temperature_2m"],
        pressure=pvlib.atmosphere.alt2pres(altitude),
    )
    solpos=solpos.reset_index(drop=True)
    dni_extra = pvlib.irradiance.get_extra_radiation(time)
    airmass = pvlib.atmosphere.get_relative_airmass(solpos['apparent_zenith'])
    pressure = pvlib.atmosphere.alt2pres(altitude)
    am_abs = pvlib.atmosphere.get_absolute_airmass(airmass, pressure)


    aoi = pvlib.irradiance.aoi( # rimane questa
        data["tilt"],
        data["azimuth"],
        solpos["apparent_zenith"],
        solpos["azimuth"],
    )
    total_irradiance = pvlib.irradiance.get_total_irradiance( # rimane questa
        data["tilt"],
        data["azimuth"],
        solpos['apparent_zenith'],
        solpos['azimuth'],
        meteo['direct_normal_irradiance'],
        meteo['shortwave_radiation'],
        meteo['diffuse_radiation'],
        dni_extra=dni_extra,
    )
    cell_temperature = pvlib.temperature.ross( # usa ross
        total_irradiance['poa_global'],
        meteo["temperature_2m"],
        data["noct"],
    )
    effective_irradiance = pvlib.pvsystem.sapm_effective_irradiance(  # rimane questa
        total_irradiance['poa_direct'],
        total_irradiance['poa_diffuse'],
        am_abs,
        aoi,
        module_parameters,
    )
    effective_irradiance=effective_irradiance*data["SF"]

    dc = pvlib.pvsystem.pvwatts_dc(effective_irradiance, cell_temperature, module_parameters["pdc0"], module_parameters['gamma_pdc'], module_parameters['temp_ref']) # Usa pvwatts_dc
    
    return dc





    # irradiance = get_effective_irradiance(data["SF"], data["a"], data["b"], data["Beta"], data["ThetaPV"], data["fd"], direct_radiation, 
    #                                       diffuse_radiation, zenith, azimuth)
    # temp_cell = get_temp_cell(temp_air, data["noct"], irradiance)


    # result=[0]*24
    # for i in range(24):
    #     result[i]=(irradiance[i] / 1000) * data["pmax"] * (1 + data["gamma"] * (temp_cell[i] - data["temp_ref"]))
    # r=pd.DataFrame(result)
    # return r


def difference_of_production(data):
    """
        Estimate the difference between the future production
        and the future load

        Returns :
            Array with difference
    """

    # ratio =  data["expected_production"]["production"]/data["inverter_nominal_power"]
    # #rimetto il valore in expected per facilità di plot
    # data["expected_production"]["production"] = data["expected_production"]["production"] * data["polynomial_inverter"](ratio)
    return data["expected_production"]["production"] - data["estimate"]["consumo"].values




def get_expected_power_production_from_pv_24_hours_from_now(data):
    twentyfour_meteo = get_meteo_data_24_hours_from_now(data["latitude"], data["longitude"])
    twentyfour_meteo["production"] = get_expected_power_production_from_pv(data, twentyfour_meteo)
    return twentyfour_meteo