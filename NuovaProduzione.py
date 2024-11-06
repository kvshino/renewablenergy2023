import pvlib

import pandas as pd

import matplotlib.pyplot as plt


from pvlib.temperature import *

from pvlib.pvsystem import *
from pvlib.location import Location
from openmeteo_py import OWmanager
from openmeteo_py.Hourly.HourlyForecast import HourlyForecast
from openmeteo_py.Options.ForecastOptions import ForecastOptions
from openmeteo_py.Utils.constants import *
from suntime import Sun
from datetime import datetime, timedelta
import pandas as pd
import pytz
import pvlib
import warnings
from freezegun import freeze_time
import math

warnings.filterwarnings("ignore", category=FutureWarning)




surface_tilt=3
surface_azimuth=167

cittadella = 1  # 1 per Cittadella, 0 per Salerno

# Imposta le coordinate e il valore di pdc0 in base al valore di 'cittadella'
if cittadella == 1:
    # Coordinate e pdc0 di Cittadella
    latitude = 45.666751773759295   # Latitudine di Cittadella (Italia)
    longitude = 11.745264693183467  # Longitudine di Cittadella (Italia)
    module_parameters={'temp_ref': 25, 'pdc0': 6560, 'gamma_pdc': -0.0029, 'A0': 0.935823, 'A1': 0.054289, 'A2': -0.008677, 'A3':0.000527, 'A4':-0.000011, 'B0': 1.000341, 'B1': -0.005557, 'B2': 6.553e-4, 'B3': -2.730e-5, 'B4': 4.641e-7, 'B5': -2.806e-9, 'FD': 1}
else:
    # Coordinate e pdc0 di Salerno
    latitude = 40.6824   # Latitudine di Salerno (Italia)
    longitude = 14.7681  # Longitudine di Salerno (Italia)
    module_parameters={'temp_ref': 25, 'pdc0': 6000, 'gamma_pdc': -0.0026, 'A0': 0.935823, 'A1': 0.054289, 'A2': -0.008677, 'A3':0.000527, 'A4':-0.000011, 'B0': 1.000341, 'B1': -0.005557, 'B2': 6.553e-4, 'B3': -2.730e-5, 'B4': 4.641e-7, 'B5': -2.806e-9, 'FD': 1}


altitude=pvlib.location.lookup_altitude(latitude=latitude, longitude=longitude)
noct=45
location = pvlib.location.Location(latitude=latitude, longitude=longitude, altitude=altitude, tz='UTC')

with freeze_time(datetime.now()-timedelta(hours=10)) as frozen_datetime:

    hourly = HourlyForecast()
    options = ForecastOptions(latitude, longitude, False, celsius, kmh, mm, iso8601, utc)
    mgr = OWmanager(options, OWmanager.forecast, hourly.temperature_2m().direct_normal_irradiance().diffuse_radiation().shortwave_radiation())
    meteo = mgr.get_data(1)
    pandas_meteo = pd.DataFrame(meteo["hourly"])


    now=str(datetime.now() + timedelta(hours=1) - timedelta(minutes=datetime.now().minute))[:-10].replace(" ", "T")
    twentyfour=str(datetime.now() + timedelta(hours=23) +  timedelta(hours=1) - timedelta(minutes=datetime.now().minute) +timedelta(minutes=2))[:-10].replace(" ", "T")
    time = pd.date_range(datetime.now()+timedelta(hours=1)-timedelta(minutes=datetime.now().minute)-timedelta(seconds=datetime.now().second), periods=24, freq='H', tz='UTC')
    
    now1=str(datetime.now() + timedelta(hours=0) - timedelta(minutes=datetime.now().minute))[:-10].replace(" ", "T")
    twentyfour1=str(datetime.now() + timedelta(hours=23)  - timedelta(minutes=datetime.now().minute) +timedelta(minutes=2))[:-10].replace(" ", "T")
    temp= pandas_meteo[(pandas_meteo['time'] >= now1) & (pandas_meteo['time'] <= twentyfour1)]
    temp=temp.reset_index(drop=True)

    temp=temp.drop(["time"], axis=1)

    pandas_meteo = pandas_meteo[(pandas_meteo['time'] >= now) & (pandas_meteo['time'] <= twentyfour)]
    pandas_meteo=pandas_meteo.reset_index(drop=True)
    pandas_meteo["direct_normal_irradiance"] = temp["direct_normal_irradiance"]
    pandas_meteo["diffuse_radiation"] = temp["diffuse_radiation"]    
    pandas_meteo["shortwave_radiation"] = temp["shortwave_radiation"] 
    

    solpos = pvlib.solarposition.get_solarposition(
        time=time,
        latitude=latitude,
        longitude=longitude,
        altitude=altitude,
        temperature=pandas_meteo["temperature_2m"],
        pressure=pvlib.atmosphere.alt2pres(altitude),
    )
    solpos=solpos.reset_index(drop=True)
    dni_extra = pvlib.irradiance.get_extra_radiation(time)
    airmass = pvlib.atmosphere.get_relative_airmass(solpos['apparent_zenith'])
    pressure = pvlib.atmosphere.alt2pres(altitude)
    am_abs = pvlib.atmosphere.get_absolute_airmass(airmass, pressure)


    aoi = pvlib.irradiance.aoi( # rimane questa
        surface_tilt,
        surface_azimuth,
        solpos["apparent_zenith"],
        solpos["azimuth"],
    )
    total_irradiance = pvlib.irradiance.get_total_irradiance( # rimane questa
        surface_tilt,
        surface_azimuth,
        solpos['apparent_zenith'],
        solpos['azimuth'],
        pandas_meteo['direct_normal_irradiance'],
        pandas_meteo['shortwave_radiation'],
        pandas_meteo['diffuse_radiation'],
        dni_extra=dni_extra,
    )
    cell_temperature = pvlib.temperature.ross( # usa ross
        total_irradiance['poa_global'],
        pandas_meteo["temperature_2m"],
        noct,
    )
    effective_irradiance = pvlib.pvsystem.sapm_effective_irradiance(  # rimane questa
        total_irradiance['poa_direct'],
        total_irradiance['poa_diffuse'],
        am_abs,
        aoi,
        module_parameters,
    )
    dc = pvlib.pvsystem.pvwatts_dc(effective_irradiance, cell_temperature, module_parameters["pdc0"], module_parameters['gamma_pdc'], module_parameters['temp_ref']) # Usa pvwatts_dc

    
    pandas_meteo["production"] = dc
    print(pandas_meteo)







# energies.plot(kind='bar', rot=0)


# plt.ylabel('Yearly energy yield (W hr)')