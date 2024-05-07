import seaborn as sns
import yaml

from consumptions import *
from pannello import *





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
    # Prendi l'ultimo valore
    data["socs"] = df.iloc[-1]

    #Checked OK, anche con grafico
    data["estimate"] = get_estimate_load_consumption(get_true_load_consumption())  # It gives an estimation of the load consumption
    
    
    data["expected_production"] = get_expected_power_production_from_pv_24_hours_from_now(data)
    data["difference_of_production"] = difference_of_production(data)
    data["prices"] = prices

    return data



def update_battery_value(data, file_name, carica, percentuale):
    with open(file_name, 'r+') as file:
        # Leggi tutte le linee e trova l'ultimo valore numerico
        lines = file.read().split()

        upper_limit = (data["soc_max"] * data["battery_capacity"])
        lower_limit = (data["soc_min"] * data["battery_capacity"])
        effettivo_in_batteria=lower_limit+(float(lines[-1])*(upper_limit-lower_limit))



        if carica == 0:
            posso_scaricare_di=effettivo_in_batteria-lower_limit
            scarico=(posso_scaricare_di*percentuale)/100
            batteria= (effettivo_in_batteria-scarico) 
        else:
            carico = ((upper_limit - effettivo_in_batteria) * percentuale) / 100
            batteria=effettivo_in_batteria+carico


        result=(batteria-lower_limit)/(upper_limit-lower_limit) 
        result=round(result, 4)
        file.write('\n' + str(result))
        file.close()





