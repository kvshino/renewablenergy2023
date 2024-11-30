import os
import numpy as np
from functions import *
import json as jj
from test_inv import *
from gui import *
from freezegun import freeze_time
from multi_genetic import *


base="../../../Desktop/risultati/giornoPiovoso72h_650_NuovaPen_SPER/"
cartella = "../../../Desktop/risultati/giornoPiovoso72h_650_NuovaPen_SPER/Fronte_di_Pareto"  
grafici = cartella[:-17]

i=0


def pareto_front(solutions):
    # Crea un array booleano per tenere traccia delle soluzioni non dominate
    is_non_dominated = np.ones(solutions.shape[0], dtype=bool)

    # Confronta ogni soluzione con le altre
    for i, solution in enumerate(solutions):
        if is_non_dominated[i]:
            for j, other_solution in enumerate(solutions):
                if i != j and is_non_dominated[j]:
                    # Se la soluzione j domina la soluzione i, segna i come dominata
                    if all(other_solution <= solution) and any(other_solution < solution):
                        is_non_dominated[i] = False
                        break  # Non è più necessario confrontare la soluzione i

    # Restituisce solo le soluzioni non dominate
    return solutions[is_non_dominated]


def normalize_arrays(array1, array2):
    # Concateno i due array per calcolare massimo e minimo complessivi
    combined = np.vstack((array1, array2))
    
    # Calcolo dei minimi e massimi per ogni colonna
    min_vals = np.min(combined, axis=0)
    max_vals = np.max(combined, axis=0)
    
    # Normalizzazione degli array
    norm_array1 = (array1 - min_vals) / (max_vals - min_vals)
    norm_array2 = (array2 - min_vals) / (max_vals - min_vals)
    
    return norm_array1, norm_array2


def find_closest_to_utopia(array):
    # Calcola la distanza euclidea di ciascun punto dall'origine (0, 0)
    distances = np.linalg.norm(array, axis=1)
    
    # Trova l'indice della soluzione con distanza minima
    min_index = np.argmin(distances)
    
    return min_index


def plot_pareto_fronts(array1, array2, string1, string2, hour):
    # Normalizzo gli array
    norm_array1, norm_array2 = normalize_arrays(array1, array2)

    
    # Trova la soluzione più vicina all'origine per entrambi gli array
    closest_idx1 = find_closest_to_utopia(norm_array1)
    closest_idx2 = find_closest_to_utopia(norm_array2)
    
    # Plot delle soluzioni normalizzate
    plt.figure(figsize=(14, 8))
    
    # Plot dell'array1
    plt.scatter(norm_array1[:, 0], norm_array1[:, 1], c='blue', label=string1)
    plt.scatter(norm_array1[closest_idx1, 0], norm_array1[closest_idx1, 1], c='green', s=100, label=string1+"-Best Solution")
    
    # Plot dell'array2
    plt.scatter(norm_array2[:, 0], norm_array2[:, 1], c='red', label=string2)
    plt.scatter(norm_array2[closest_idx2, 0], norm_array2[closest_idx2, 1], c='yellow', s=100, label=string2+"-Best Solution")
    
    # Aggiunge dettagli al grafico
    plt.axhline(0, color='gray', linewidth=0.5)
    plt.axvline(0, color='gray', linewidth=0.5)
    plt.xlabel("Costs", fontsize=20)
    plt.ylabel("Battery Degradation", fontsize=20)
    plt.title('Confronto Fronti di Pareto Normalizzati')
    plt.legend()
    plt.grid(True)
    plt.savefig(base+f"_{hour}")
    plt.close()

for filename in os.listdir(cartella):
    if i == 0:
        t=int(filename[11:13])+1
        i=1

    if filename.endswith(".txt"):
        # Percorso completo del file
        file_path = os.path.join(cartella, filename)
        
        # Carica il contenuto del file .txt in un np.ndarray
        # try:
        #     F=np.loadtxt(file_path)
        #     F_min = np.min(F, axis=0)
        #     F_max = np.max(F, axis=0)
        #     F_norm = (F - F_min) / (F_max - F_min)
        #     F=pareto_front(F_norm)
        #     plot_and_save_2d_pareto(F, ["Costs", "Battery Degradation"], cartella, filename_full=f'grafico_2D_{filename[:-3]}.png', filename_zoom=f'grafico_2D_zoom_{filename[:-3]}png')
        #     print(f"Caricato {filename} con successo!")
        # except Exception as e:
        #     print(f"Errore nel caricare {filename}: {e}")



with freeze_time(datetime.now().replace(hour=t, minute=0, second=0, microsecond=0)) as frozen_datetime:
    with open(grafici+"/dictionary.json", "r") as file:
        dictionary = jj.load(file)

    dictionary["polynomial_inverter"] = inverter_function()

    # polynomial_batt = battery_function()
    # cycles=0

    data=setup(inverter_function())
    for i in range(0,72):
        dictionary[f"production{i}"] = dictionary[f"production{i}"] - random.uniform(0.3, 0.85)*dictionary[f"production{i}"]
        print(dictionary[f"production{i}"])
        dictionary[f"difference_of_production{i}"] = dictionary[f"production{i}"] - dictionary[f"load{i}"]
    
    dictionary["sum_algo"],dictionary["actual_percentage_algo"],dictionary["quantity_delta_battery_algo"],dictionary["co2_algo"], dictionary["ratio_algo"] = evaluate(data, dictionary,  0, battery_function(),72)
    
    # dictionary["sum_noalgo"],dictionary["actual_battery_level_noalgo"],dictionary["quantity_battery_degradation_noalgo"],dictionary["co2_noalgo"],dictionary["power_to_grid_noalgo"], dictionary["ratio_noalgo"] =simulation_no_algorithm(data,dictionary, cycles, polynomial_batt, 72)
    # dictionary["sum_nobattery"],dictionary["co2_nobattery"],dictionary["power_to_grid_nobattery"], dictionary["ratio_nobattery"]  = simulation_nobattery(data,dictionary)
    # dictionary["sum_noplant"],dictionary["co2_noplant"],dictionary["power_to_grid_noplant"]= simulation_noplant(data,dictionary)    
    save_plots(dictionary, grafici+"/Comparazione", False)
