import numpy as np
from scipy.optimize import curve_fit
import yaml
# Dati estratti dal grafico a mano
# cycles = np.array([0, 1000, 2000, 3000, 4000, 5000, 6000])
# SOH = np.array([100, 97, 93, 89, 85, 82, 80]) / 100  # convertito in frazione

# # Calcolo del CLL come perdita di capacità
# CLL_BA = 1 - SOH

# # Definizione della funzione parabolica
# def parabolic(N, alpha_BA, beta_BA, delta_BA):
#     return alpha_BA + beta_BA * N + delta_BA * N**2

# # Fitting della curva
# params, covariance = curve_fit(parabolic, cycles, CLL_BA)

# # Estrazione dei coefficienti
# alpha_BA, beta_BA, delta_BA = params

# def get_SOH(N, alpha_BA, beta_BA, delta_BA):
#     CLL = parabolic(N, alpha_BA, beta_BA, delta_BA)
#     SOH = np.round(1 - CLL, 2)
#     return SOH


# N_values = np.array([100, 200, 800, 1200, 90, 32, 10])  # Inserisci qui le ascisse desiderate
# SOH_values = get_SOH(N_values, alpha_BA, beta_BA, delta_BA)
# print(SOH_values)





def battery_function():
    x = np.array([0, 1000, 2000, 3000, 4000, 5000, 6000])
    y = np.array([100, 97, 93, 89, 85, 82, 80]) / 100
    coeff = np.polyfit(x, y, deg=1)  # deg=1 per una regressione lineare
    polynomial = np.poly1d(coeff)
    return polynomial


def update_battery_values(data, file_name, carica, percentuale, polynomial):
    with open(file_name, 'r+') as file:
        # Leggi tutte le linee e trova l'ultimo valore numerico
        lines = file.read().split()

        upper_limit = (data["soc_max"] * data["battery_capacity"])
        lower_limit = (data["soc_min"] * data["battery_capacity"])
        effettivo_in_batteria=lower_limit+(float(lines[-3].replace(",", ""))*(upper_limit-lower_limit))
        cycles = float(lines[-2].replace(",", ""))

        if carica == 0:
            posso_scaricare_di=effettivo_in_batteria-lower_limit
            scarico=(posso_scaricare_di*percentuale)/100
            batteria= (effettivo_in_batteria-scarico) 
            result=(batteria-lower_limit)/(upper_limit-lower_limit) 
            result=round(result, 4)
            new_cycles = round(cycles+(scarico/data["battery_capacity"]), 5)
            y = polynomial(new_cycles) * data["battery_nominal_capacity"]
            file.write('\n' + str(result) + ", " + str(new_cycles) + ", " + str(round(y,4)))
            
        else:
            carico = ((upper_limit - effettivo_in_batteria) * percentuale) / 100
            batteria=effettivo_in_batteria+carico
            result=(batteria-lower_limit)/(upper_limit-lower_limit) 
            result=round(result, 4)
            # new_cycles = round(cycles+(carico/data["battery_capacity"]), 5)
            # y = polynomial(cycles) * data["battery_nominal_capacity"]
            file.write('\n' + str(result) + ", " + str(cycles)  + ", " + str(round(data["battery_capacity"],4)))

        file.close()

    return round(data["battery_capacity"],4)

        

