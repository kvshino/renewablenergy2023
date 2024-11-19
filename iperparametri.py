import optuna
import numpy as np
import optuna

# Collegati allo storage dove hai salvato lo studio
study_name = "no-name-55755460-53ab-457b-93a9-24e70128a3cb"  # Sostituisci con il nome del tuo studio
storage_url = "sqlite:///nsga.db"  # Adatta a dove hai memorizzato i dati

# Carica lo studio
study = optuna.load_study(study_name=study_name, storage=storage_url)


# Ottieni i trial che fanno parte del fronte di Pareto
# Optuna ha una funzione built-in per ottenere il fronte di Pareto
pareto_trials = study.best_trials

# Estrai gli iperparametri dai trial che fanno parte del fronte di Pareto
params_list = [trial.params for trial in pareto_trials]

# Verifica gli iperparametri (in un formato adatto alla media)
# Supponiamo che tutti gli iperparametri siano numerici per calcolarne la media.
# Se ci sono iperparametri categoriali, dovremo gestirli diversamente.

# Organizza gli iperparametri in un dizionario {param_name: [valori]}

print("MVGA")
print("Numero soluzioni fronte: " + str(len(params_list)))
param_dict = {}
for params in params_list:
    for param_name, param_value in params.items():
        if param_name not in param_dict:
            param_dict[param_name] = []
        param_dict[param_name].append(param_value)

# Calcola la media per ogni iperparametro
param_means = {param_name: np.mean(values) for param_name, values in param_dict.items()}

# Mostra le medie degli iperparametri
print("Media degli iperparametri per i trial nel fronte di Pareto:")
print('pop_size: ' + str(np.max(param_dict['pop_size'])))
print('n_gen: ' + str(np.max(param_dict['n_gen'])))
print('prob_mut_bit: ' + str(np.mean(param_dict['prob_mut_bit'])))
print('prob_mut_int: ' + str(np.mean(param_dict['prob_mut_int'])))

# for param_name, param_mean in param_means.items():
#     print(f"{param_name}: {param_mean}")
# print("**************"*5)

# study_name = "no-name-7d1d0c14-52f5-456f-b66d-36951b3a5b99"  # Sostituisci con il nome del tuo studio
# storage_url = "sqlite:///nsga.db"  # Adatta a dove hai memorizzato i dati

# # Carica lo studio
# study = optuna.load_study(study_name=study_name, storage=storage_url)


# # Ottieni i trial che fanno parte del fronte di Pareto
# # Optuna ha una funzione built-in per ottenere il fronte di Pareto
# pareto_trials = study.best_trials

# # Estrai gli iperparametri dai trial che fanno parte del fronte di Pareto
# params_list = [trial.params for trial in pareto_trials]

# # Verifica gli iperparametri (in un formato adatto alla media)
# # Supponiamo che tutti gli iperparametri siano numerici per calcolarne la media.
# # Se ci sono iperparametri categoriali, dovremo gestirli diversamente.

# # Organizza gli iperparametri in un dizionario {param_name: [valori]}

# print("NSGA")
# print("Numero soluzioni fronte: " + str(len(params_list)))
# param_dict = {}
# for params in params_list:
#     for param_name, param_value in params.items():
#         if param_name not in param_dict:
#             param_dict[param_name] = []
#         param_dict[param_name].append(param_value)

# # Calcola la media per ogni iperparametro
# param_means = {param_name: np.mean(values) for param_name, values in param_dict.items()}

# # Mostra le medie degli iperparametri
# print("Media degli iperparametri per i trial nel fronte di Pareto:")
# print('pop_size: ' + str(np.max(param_dict['pop_size'])))
# print('n_gen: ' + str(np.max(param_dict['n_gen'])))
# print('prob_mut_bit: ' + str(np.mean(param_dict['prob_mut_bit'])))
# print('prob_mut_int: ' + str(np.mean(param_dict['prob_mut_int'])))
# print('prob_cross: ' + str(np.mean(param_dict['prob_cross'])))

