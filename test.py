

from functions import *
from pannello import *

data=setup()
print(get_meteo_data_24_hours_from_now())
print(get_expected_power_production_from_pv_24_hours_from_now(data))
print(difference_of_production(data))

print(get_estimate_load_consumption(get_true_load_consumption()))