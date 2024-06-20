import seaborn as sns
import yaml

from consumptions import *
from pannello import *

from update_battery import *



def setup(prices) -> dict:
    """
    Takes the datas from the conf.yaml and stores them in data.

    Returns:
        data: struct containing all the datas
    """
    sns.set_theme()
    with open("conf.yaml") as f:
        data = yaml.load(f, Loader=yaml.FullLoader)

    df = pd.read_csv('csv/socs.csv')

    data["socs"] = df.iloc[-1][-3]
    #string="battery_level, cycles\n"+str(df.iloc[-1][-2]) + ", " + str(int(df.iloc[-1][-1]))
    

    #Checked OK, anche con grafico
    data["estimate"] = get_estimate_load_consumption(get_true_load_consumption())  # It gives an estimation of the load consumption
    
    
    data["expected_production"] = get_expected_power_production_from_pv_24_hours_from_now(data)
    data["difference_of_production"] = difference_of_production(data)
    data["prices"] = prices



    with open('csv/socs.csv', 'r+') as file:
        lines = file.read().split()
        data["battery_capacity"] = float(lines[-1])
        file.close()

    return data







