from functions import *

coords = {'longitude': 14.7680965, 'latitude': 40.6824404}

latitude = 40.8553996
longitude = 14.2744036


tz = pytz.timezone('Europe/Rome')

sun = Sun(latitude, longitude)

# print(sun.get_local_sunset_time(datetime.today()).replace(tzinfo=pytz.utc).astimezone(pytz.timezone('Europe/Rome')))
# Get today's sunrise and sunset in UTC
# today_sr = sun.get_local_sunrise_time(datetime.today(), local_time_zone=tz)
# today_ss = sun.get_local_sunset_time(datetime.today(), local_time_zone=tz)
# print(today_sr)
# print(today_ss)
# today_sr = today_sr - timedelta(minutes=today_sr.minute)
# today_ss = today_ss + timedelta(hours=1) - timedelta(minutes=today_ss.minute)
# print(today_ss)
# print(today_sr)


hourly = HourlyForecast()
options = ForecastOptions(latitude, longitude, False, celsius, kmh, mm, iso8601, utc)
mgr = OWmanager(options, OWmanager.forecast, hourly.temperature_2m().direct_radiation().diffuse_radiation())
meteo = mgr.get_data(1)
# pandasmeteo = pd.DataFrame(meteo["hourly"])
# print(pandasmeteo[(pd.to_datetime(pandasmeteo['time']).dt.hour > 8) & (pd.to_datetime(pandasmeteo['time']).dt.hour <  14)])
data = setup()
print(difference_of_production(data))

# print(get_meteo_data())

# energyCosts = await get_intra_days_market(1)
# plot_graph(energyCosts, "ora", "prezzo","Hours", "Price", "Price", "#B55E60")
# plt.show()


# try:
#     data["mean_difference"], data["future_mean"], data["past_mean"] = await mean_difference()
#     print(data["mean_difference"], data["future_mean"], data["past_mean"])
#     battery_or_grid(data,10)

# except Exception as error:
#     print(error)


"""
plot_graph(data, "hours", "load_profile", "kW", "Load profile", "#B55E60")
plot_graph(data, "hours", "battery_levels", "kWh", "Battery Level", "#609E6E")
plot_graph(data, "hours", "energy_grid", "kW", "Power from/to Grid", "#5975A5")
plot_graph(data, "hours", "energy_pv", "kW", "Power from PV", "#CC8962")
plot_graph(data, "hours", "price","$","Energy Cost","green")

print("L'utente ha speso/guadagnato avendo i pannelli solari e la batteria:")
print(profit(data))
#disabilito sia la batteria che il pannello, costi se non avessi i pannellis
data = setup(disablePV=True, disableBattery=True)
energy_request(data)
print("L'utente ha speso/guadagnato non avendo i pannelli solari e la batteria:")
print(profit(data))
"""