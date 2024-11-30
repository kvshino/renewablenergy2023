import os
import numpy as np
from functions import *
import json as jj
from test_inv import *
from gui import *
from freezegun import freeze_time
from multi_genetic import *


base="../../../Desktop/risultati/confronto_3_dimensioni/"
cartella = "../../../Desktop/risultati/confronto_3_dimensioni/MVGA/Fronte_di_Pareto"  
cartella_NSGA = "../../../Desktop/risultati/confronto_3_dimensioni/NSGAII/Fronte_di_Pareto"  # Modifica con il percorso della tua cartella
grafici = cartella[:-17]
color_ga ="#004aad"
color_mixed ="#ff5757"

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

i=0
for filename in os.listdir(cartella):
    if i == 0:
        t=int(filename[11:13])
        i=1

    if filename.endswith(".txt"):
        # Percorso completo del file
        file_path = os.path.join(cartella, filename)
        
        # Carica il contenuto del file .txt in un np.ndarray
        try:
            F=np.loadtxt(file_path)
            F_min = np.min(F, axis=0)
            F_max = np.max(F, axis=0)
            F_norm = (F - F_min) / (F_max - F_min)
            pf=pareto_front(F_norm)
            plot_and_save_results(pf, ["Costs", "Battery Degradation", "Pollution"], cartella, filename_2d=f'grafici_2D_{filename[:13]}.png', filename_3d=f'grafico_3D_{filename[:13]}.png')

            print(f"Caricato {filename} con successo!")
        except Exception as e:
            print(f"Errore nel caricare {filename}: {e}")


grafici_NSGA = cartella_NSGA[:-17]
color_ga ="#004aad"
color_mixed ="#ff5757"
# Lista per contenere gli array numpy letti dai file

# Itera su tutti i file nella cartella
for filename in os.listdir(cartella_NSGA):
    if filename.endswith(".txt"):
        # Percorso completo del file
        file_path = os.path.join(cartella_NSGA, filename)
        
        # Carica il contenuto del file .txt in un np.ndarray
        try:
            F=np.loadtxt(file_path)
            F_min = np.min(F, axis=0)
            F_max = np.max(F, axis=0)
            F_norm = (F - F_min) / (F_max - F_min)
            pf=pareto_front(F_norm)
            plot_and_save_results(pf, ["Costs", "Battery Degradation", "Pollution"], cartella_NSGA, filename_2d=f'grafici_2D_{filename[:13]}.png', filename_3d=f'grafico_3D_{filename[:13]}.png')
            print(f"Caricato {filename} con successo!")
        except Exception as e:
            print(f"Errore nel caricare {filename}: {e}")



with freeze_time(datetime.now().replace(hour=t, minute=0, second=0, microsecond=0)) as frozen_datetime:
    with open(grafici+"/dictionary.json", "r") as file:
        dictionary = jj.load(file)

    dictionary["polynomial_inverter"] = inverter_function()


    # data=setup(inverter_function())
    # for i in range(0,24):
    #     dictionary[f"production{i}"] = dictionary[f"production{i}"] - 0.5*dictionary[f"production{i}"]
    #     dictionary[f"difference_of_production{i}"] = dictionary[f"production{i}"] - dictionary[f"load{i}"]
    
    # dictionary["sum_algo"],dictionary["actual_percentage_algo"],dictionary["quantity_delta_battery_algo"],dictionary["co2_algo"], dictionary["ratio_algo"] = evaluate(data, dictionary,  0, battery_function())
    
    save_plots(dictionary, grafici, False)


    with open(grafici_NSGA+"/dictionary.json", "r") as file:
            dictionary = jj.load(file)

    dictionary["polynomial_inverter"] = inverter_function()

    save_plots(dictionary, grafici_NSGA, False)





    ######################################################################################
    ######################################################################################
    ######################################################################################
    ######################################################################################


    def plot_cost_comparison(dictionary):
        # Imposta l'ora corrente e crea la colonna del tempo
        current_datetime = datetime.now() + timedelta(hours=1)
        time_column = pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')

        # Creazione dei DataFrame con i dati
        cost_dataframe_mixed = pd.DataFrame({'datetime': time_column, 'value': dictionary["sum_mixed"]})
        cost_dataframe_mixed["value"] = cost_dataframe_mixed["value"].multiply(-1)

        cost_dataframe_ga = pd.DataFrame({'datetime': time_column, 'value': dictionary["sum_ga"]})
        cost_dataframe_ga["value"] = cost_dataframe_ga["value"].multiply(-1)

        # Creazione della figura
        plt.figure(figsize=(14, 8))

        # Tracciare tutte le curve sullo stesso grafico
        plt.plot(cost_dataframe_mixed["datetime"], cost_dataframe_mixed["value"], color=color_mixed, label="MVGA")

        plt.plot(cost_dataframe_ga["datetime"], cost_dataframe_ga["value"], color=color_ga, label="NSGAII")

        # Impostazioni del grafico
        plt.xlabel("Datetime")
        plt.ylabel("€")
        plt.legend()  # Mostra la legenda per distinguere le curve
        plt.ylim(-2, 2)  # Puoi regolare o rimuovere questi limiti
        plt.yticks(fontsize=20)
        plt.grid(True)  # Aggiungi una griglia per facilitare la lettura
        plt.xticks(cost_dataframe_mixed["datetime"], cost_dataframe_mixed["datetime"].dt.strftime('%H:%M'), rotation=90, fontsize=20)
        plt.title("Cost Comparison (Positive Earnings)")
        # Mostra il grafico
        plt.tight_layout()


    def plot_co2_comparison_algo(dictionary):
        current_datetime = datetime.now() + timedelta(hours=1)
        time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H') 

        co2_mixed_dataframe = pd.DataFrame({'datetime': time_column, 'value': dictionary["co2_mixed"]})
        co2_ga_dataframe = pd.DataFrame({'datetime': time_column, 'value': dictionary["co2_ga"]})


    # Creazione della figura
        plt.figure(figsize=(14, 8))

        # Tracciare tutte le curve sullo stesso grafico
        plt.plot(co2_mixed_dataframe["datetime"], co2_mixed_dataframe["value"], color=color_mixed, label="MVGA")
        plt.plot(co2_ga_dataframe["datetime"], co2_ga_dataframe["value"], color=color_ga, label="NSGAII")


        # Impostazioni del grafico
        plt.xlabel("")
        plt.ylabel("gCO2")
        plt.legend()  # Mostra la legenda per distinguere le curve
        plt.yticks(fontsize=20)
        plt.grid(True)  # Aggiungi una griglia per facilitare la lettura
        plt.xticks(co2_mixed_dataframe["datetime"], co2_mixed_dataframe["datetime"].dt.strftime('%H:%M'), rotation=90, fontsize=20)
        plt.title("Co2 Emissions Comparison")
        # Mostra il grafico
        plt.tight_layout()

    def plot_comparison_degradation(lista1,lista2):
        current_datetime = datetime.now() 
        time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=25, freq='H') 

        degradation_plant_dataframe_mixed = pd.DataFrame({'datetime': time_column, 'value': lista1})

        degradation_plant_dataframe_ga = pd.DataFrame({'datetime': time_column, 'value':lista2})
        plt.figure(figsize=(14, 8))
        # Tracciare tutte le curve sullo stesso grafico
        plt.plot(degradation_plant_dataframe_mixed["datetime"], degradation_plant_dataframe_mixed["value"], color=color_mixed, label="MVGA")
        plt.plot(degradation_plant_dataframe_ga["datetime"], degradation_plant_dataframe_ga["value"], color=color_ga, label="NSGAII")

        
        # Impostazioni del grafico
        plt.xlabel("")
        plt.ylabel("Wh")
        plt.legend()  # Mostra la legenda per distinguere le curve
        plt.yticks(fontsize=20)
        plt.grid(True)  # Aggiungi una griglia per facilitare la lettura
        plt.xticks(degradation_plant_dataframe_ga["datetime"], degradation_plant_dataframe_ga["datetime"].dt.strftime('%H:%M'), rotation=90, fontsize=20)
        plt.title("Battery Degradation Comparison")
        # Mostra il grafico
        plt.tight_layout()


    def plot_comparison_battery(dictionary,lista1,lista2):
        current_datetime = datetime.now() 
        time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0) , periods=25, freq='H') 


        actual_percentage_mixed = dictionary["apercentage_mixed"]
        battery_wh_mixed = [float(0.2 * lista1[i]) + (percentage * (float(0.8 * lista1[i] ) - float(0.2 * lista1[i]))) for i,percentage in enumerate(actual_percentage_mixed)]
        battery_wh_dataframe_mixed = pd.DataFrame({'datetime': time_column, 'value': battery_wh_mixed})


        actual_percentage_ga = dictionary["apercentage_ga"]
        battery_wh_ga = [float(0.2 * lista2[i]) + (percentage * (float(0.8 *lista2[i] ) - float(0.2 * lista2[i]))) for i,percentage in enumerate(actual_percentage_ga)]
        battery_wh_dataframe_ga = pd.DataFrame({'datetime': time_column, 'value': battery_wh_ga})

        
        plt.figure(figsize=(14, 8))
        # Tracciare tutte le curve sullo stesso grafico
        plt.plot(battery_wh_dataframe_mixed["datetime"], battery_wh_dataframe_mixed["value"], color=color_mixed, label="MVGA")
        plt.plot(battery_wh_dataframe_ga["datetime"], battery_wh_dataframe_ga["value"], color=color_ga, label="NSGAII")

        #plt.figure(figsize=(14, 8))
        # Impostazioni del grafico
        plt.xlabel("")
        plt.ylabel("Wh")
        plt.legend()  # Mostra la legenda per distinguere le curve
        plt.yticks(fontsize=20)
        plt.grid(True)  # Aggiungi una griglia per facilitare la lettura
        plt.xticks(battery_wh_dataframe_ga["datetime"], battery_wh_dataframe_ga["datetime"].dt.strftime('%H:%M'), rotation=90, fontsize=20)
        plt.title("Battery Energy Comparison")
        # Mostra il grafico
        plt.tight_layout()

    def plot_time(time1,time2):
        input_sizes = ['']  # Aggiorna l'input con un'etichetta valida
        algorithm1_times_mixed = [time1]  # Tempi per Algoritmo 1
        algorithm2_times_ga = [time2]  # Tempi per Algoritmo 2

        # Creiamo un array per la posizione delle barre sull'asse X
        bar_width = 0.15  # Larghezza delle barre
        index = np.arange(len(input_sizes))  # Posizioni per l'asse X

        # Creazione del grafico
        fig, ax = plt.subplots()

        # Barre per Algoritmo 1 (spostate leggermente a sinistra)
        bar1 = ax.bar(index - bar_width*0.7, algorithm2_times_ga, bar_width, color=color_ga, label='Nsga2')

        # Barre per Algoritmo 2 (spostate leggermente a destra)
        bar2 = ax.bar(index + bar_width*0.7, algorithm1_times_mixed, bar_width, color=color_mixed, label='MixedVariableGa')

        # Aggiunta delle etichette e del titolo
        ax.set_ylabel('Execution time (s)')
        ax.set_title('Comparison of the execution times')
        ax.set_xticks(index)
        ax.set_xticklabels(input_sizes)
        ax.set_xlim([-0.5, 0.5])

        # Aggiungere le etichette sotto le barre
        ax.text(index[0] - bar_width * 0.7, -0.55, 'NSGA2', ha='center', va='top', fontsize=12)
        ax.text(index[0] + bar_width * 0.7, -0.55, 'MVGA', ha='center', va='top', fontsize=12)

        # Mostrare il grafico
        plt.tight_layout()


    with open( grafici+"/lista1.json", "r") as file:
        lista1 = jj.load(file)

    with open( grafici_NSGA+"/lista2.json", "r") as file:
        lista2 = jj.load(file)

    with open( grafici_NSGA+"/confronto.json", "r") as file:
        conf = jj.load(file)

    print(len(lista1))
    plot_cost_comparison(conf)
    plt.tight_layout()
    plt.savefig(os.path.join(base, "Cost Comparison"))
    plt.close()

    plot_co2_comparison_algo(conf)
    plt.tight_layout()
    plt.savefig(os.path.join(base, "CO2 Comparison"))
    plt.close()

    plot_comparison_degradation(lista1,lista2)
    plt.tight_layout()
    plt.savefig(os.path.join(base, "Battery Degradation Comparison"))
    plt.close()

    plot_comparison_battery(conf,lista1,lista2)
    plt.tight_layout()
    plt.savefig(os.path.join(base, "Battery Level Comparison"))
    plt.close()

    plot_time(3956.3548707962036,4235.723348140717)
    plt.tight_layout()
    plt.savefig(os.path.join(base, "Time"))
    plt.close()