from functions import *


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
        print(result)
        file.write('\n' + str(result))

      

data=setup()
update_battery_value(data, "csv/socs.csv", 0, 100)