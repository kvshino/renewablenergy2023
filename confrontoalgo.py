import asyncio
from functions import *
import warnings
from update_costs import *
from genetic import *
from genetic_ga import *
from consumptions import *
from plot import *
from update_battery import *
from test_inv import *
from freezegun import freeze_time
import time

warnings.filterwarnings("ignore", category=FutureWarning)

color_ga ="#a066cb"
color_mixed =color="#86c7ed"
delta =10
async def mixed():
    polynomial_batt = battery_function()
    polynomial_inverter = inverter_function()

    with freeze_time(datetime.now() - timedelta(hours=delta)) as frozen_datetime:
        dict = {}
        sampling = 0
        pop_size = 500
        gen = 200

        data = setup(polynomial_inverter,"csv/socsmixed.csv")
        prices = await get_future_day_italian_market(data)
        production_not_rs = forecast_percentage_production_from_not_renewable_sources(api_key=data["api_key"], zona=data["entsoe_timezone"])

        for i in range(24):
            data = setup(polynomial_inverter,"csv/socsmixed.csv")
            data["prices"] = prices
            data["production_not_rs"] = production_not_rs  
            data["polynomial"] = polynomial_batt
            
            if(i == 0):
                dict["first_battery_value"] = data["socs"]
                cycles = data["cycles"]
                dict[f"battery_capacity{i}"] = data["battery_capacity"]

            if i == 0:
                data["res"], data["history"] = start_genetic_algorithm(data=data, pop_size=pop_size, n_gen=gen, n_threads=24,prob_mut_bit=0.14,prob_mut_pm=0.75, sampling=None, verbose=False)  
            else:
                data["res"], data["history"] = start_genetic_algorithm(data=data, pop_size=pop_size, n_gen=gen, n_threads=24,prob_mut_bit=0.14,prob_mut_pm=0.75, sampling=sampling, verbose=False)
            
            print("Fine Esecuzione Ora " + str(i+1))

            dict[f"b{i}"] = data["res"].X["b0"]
            dict[f"i{i}"] = data["res"].X["i0"]
            dict[f"difference_of_production{i}"] = data["difference_of_production"][0]
            dict[f"prices{i}"] = data["prices"]["prezzo"][0]
            dict[f"production_not_rs{i}"] = data[f"production_not_rs"]["Difference"][0]
            dict[f"load{i}"] = data["estimate"]["consumo"][0]
            dict[f"production{i}"] = data["expected_production"]["production"][0]
            
            prices = shift_ciclico(prices, "prezzo")
            production_not_rs = shift_ciclico(production_not_rs, "Difference")
        
            all_populations = [a.pop for a in data["history"]]
            sampling = shifting_individuals(all_populations[-1])
            dict[f"battery_capacity{i+1}"] = update_battery_values(data, "csv/socsmixed.csv", dict[f"b{i}"], dict[f"i{i}"], polynomial_batt)

            frozen_datetime.tick(delta=timedelta(hours=1))

    dict["soc_min"] = data["soc_min"]
    dict["soc_max"] = data["soc_max"]
    dict["sold"] = data["sold"]
    dict["battery_nominal_capacity"] = data["battery_nominal_capacity"]
    dict["battery_charging_efficiency"] = data["battery_charging_efficiency"]
    dict["battery_discharging_efficiency"] = data["battery_discharging_efficiency"]
    dict["polynomial_inverter"] = polynomial_inverter

    dict["sum_algo"], dict["actual_percentage_algo"], dict["quantity_delta_battery_algo"], dict["co2_algo"], dict["ratio_algo"] = evaluate(data, dict, cycles, polynomial_batt)
    lista = dictionary_to_list(dict,"battery_capacity")

    return dict["sum_algo"], dict["actual_percentage_algo"], dict["co2_algo"], lista 

async def ga():
    polynomial_batt = battery_function()
    polynomial_inverter = inverter_function()

    with freeze_time(datetime.now()- timedelta(hours=delta)) as frozen_datetime:

        dict={}
        sampling=0
        pop_size =500
        gen = 200

        data = setup(polynomial_inverter,"csv/socsga.csv")
        prices = await get_future_day_italian_market(data)
        production_not_rs = forecast_percentage_production_from_not_renewable_sources(api_key=data["api_key"], zona=data["entsoe_timezone"])
        for i in range(24):

            data = setup(polynomial_inverter,"csv/socsga.csv")
            data["prices"] = prices 
            data["production_not_rs"] = production_not_rs  
            data["polynomial"] = polynomial_batt

            if(i==0):
                dict["first_battery_value"]=data["socs"]
                cycles = data["cycles"]
                dict[f"battery_capacity{i}"] = data["battery_capacity"]

            if i == 0:
                data["res"], data["history"] = start_GA_genetic_algorithm(data=data, pop_size=pop_size, n_gen=gen, n_threads=24,prob_cross=0.72,prob_mut_bit=0.102,prob_mut_int=0.47, sampling=None, verbose=False)  #Checked OK
            else:
                data["res"], data["history"] = start_GA_genetic_algorithm(data=data, pop_size=pop_size, n_gen=gen, n_threads=24,prob_cross=0.72,prob_mut_bit=0.102,prob_mut_int=0.47, sampling=sampling, verbose=False)
            
            print("Fine Esecuzione Ora " + str(i+1))

            dict[f"b{i}"]=data["res"].X[0]
            dict[f"i{i}"]=data["res"].X[1]


            dict[f"difference_of_production{i}"] = data["difference_of_production"][0]
            dict[f"prices{i}"] = data["prices"]["prezzo"][0]
            dict[f"production_not_rs{i}"] = data[f"production_not_rs"]["Difference"][0]
            dict[f"load{i}"] = data["estimate"]["consumo"][0]
            dict[f"production{i}"] = data["expected_production"]["production"][0]
            
            prices = shift_ciclico(prices, "prezzo")
            production_not_rs = shift_ciclico(production_not_rs, "Difference")
        
            all_populations = [a.pop for a in data["history"]]
            sampling = shifting_GA_individuals(all_populations[-1])
            dict[f"battery_capacity{i+1}"] = update_battery_values(data, "csv/socsga.csv", dict[f"b{i}"], dict[f"i{i}"], polynomial_batt)

            frozen_datetime.tick(delta=timedelta(hours=1))


    dict["soc_min"] = data["soc_min"]
    dict["soc_max"] = data["soc_max"]
    dict["sold"] = data["sold"]
    dict["battery_nominal_capacity"] = data["battery_nominal_capacity"]
    dict["battery_charging_efficiency"] = data["battery_charging_efficiency"]
    dict["battery_discharging_efficiency"] = data["battery_discharging_efficiency"]
    dict["polynomial_inverter"] = polynomial_inverter
    lista = dictionary_to_list(dict,"battery_capacity")

    dict["sum_algo"],dict["actual_percentage_algo"],dict["quantity_delta_battery_algo"],dict["co2_algo"] ,dict["ratio_algo"]= evaluate(data, dict,cycles,polynomial_batt)
    return dict["sum_algo"], dict["actual_percentage_algo"],  dict["co2_algo"],lista

def plot_cost_comparison(dictionary):
    # Imposta l'ora corrente e crea la colonna del tempo
    current_datetime = datetime.now() + timedelta(hours=1)- timedelta(hours=delta)
    time_column = pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H')

    # Creazione dei DataFrame con i dati
    cost_dataframe_mixed = pd.DataFrame({'datetime': time_column, 'value': dictionary["sum_mixed"]})
    cost_dataframe_mixed["value"] = cost_dataframe_mixed["value"].multiply(-1)

    cost_dataframe_ga = pd.DataFrame({'datetime': time_column, 'value': dictionary["sum_ga"]})
    cost_dataframe_ga["value"] = cost_dataframe_ga["value"].multiply(-1)

    # Creazione della figura
    plt.figure(figsize=(10, 6))

    # Tracciare tutte le curve sullo stesso grafico
    plt.plot(cost_dataframe_mixed["datetime"], cost_dataframe_mixed["value"], color=color_mixed, label="MIXED")

    plt.plot(cost_dataframe_ga["datetime"], cost_dataframe_ga["value"], color=color_ga, label="GA")

    # Impostazioni del grafico
    plt.xlabel("Datetime")
    plt.ylabel("Euro €")
    plt.legend()  # Mostra la legenda per distinguere le curve
    plt.ylim(-2, 2)  # Puoi regolare o rimuovere questi limiti
    plt.xticks(rotation=45)  # Ruota le etichette dell'asse x per una migliore leggibilità
    plt.grid(True)  # Aggiungi una griglia per facilitare la lettura
    plt.xticks(cost_dataframe_mixed["datetime"], cost_dataframe_mixed["datetime"].dt.strftime('%H'), rotation=10)
    plt.title("Cost Comparison ( Positive Earnings)")
    # Mostra il grafico
    plt.tight_layout()


def plot_co2_comparison_algo(dictionary):
    current_datetime = datetime.now() + timedelta(hours=1)- timedelta(hours=delta)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H') 

    co2_mixed_dataframe = pd.DataFrame({'datetime': time_column, 'value': dictionary["co2_mixed"]})
    co2_ga_dataframe = pd.DataFrame({'datetime': time_column, 'value': dictionary["co2_ga"]})


   # Creazione della figura
    plt.figure(figsize=(10, 6))

    # Tracciare tutte le curve sullo stesso grafico
    plt.plot(co2_mixed_dataframe["datetime"], co2_mixed_dataframe["value"], color=color_mixed, label="MIXED")
    plt.plot(co2_ga_dataframe["datetime"], co2_ga_dataframe["value"], color=color_ga, label="GA")


    # Impostazioni del grafico
    plt.xlabel("Datetime")
    plt.ylabel("Co2 Grams")
    plt.legend()  # Mostra la legenda per distinguere le curve
    plt.xticks(rotation=45)  # Ruota le etichette dell'asse x per una migliore leggibilità
    plt.grid(True)  # Aggiungi una griglia per facilitare la lettura
    plt.xticks(co2_mixed_dataframe["datetime"], co2_mixed_dataframe["datetime"].dt.strftime('%H'), rotation=10)
    plt.title("Co2 Emissions Comparison")
    # Mostra il grafico
    plt.tight_layout()

def plot_comparison_degradation(lista1,lista2):
    current_datetime = datetime.now() + timedelta(hours=1)- timedelta(hours=delta)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0), periods=24, freq='H') 

    degradation_plant_dataframe_mixed = pd.DataFrame({'datetime': time_column, 'value': lista1})

    degradation_plant_dataframe_ga = pd.DataFrame({'datetime': time_column, 'value':lista2})
    plt.figure(figsize=(10, 6))

    # Tracciare tutte le curve sullo stesso grafico
    plt.plot(degradation_plant_dataframe_mixed["datetime"], degradation_plant_dataframe_mixed["value"], color=color_mixed, label="Mixed")
    plt.plot(degradation_plant_dataframe_ga["datetime"], degradation_plant_dataframe_ga["value"], color=color_ga, label="GA")

    # Impostazioni del grafico
    plt.xlabel("Datetime")
    plt.ylabel("Wh")
    plt.legend()  # Mostra la legenda per distinguere le curve
    plt.xticks(rotation=45)  # Ruota le etichette dell'asse x per una migliore leggibilità
    plt.grid(True)  # Aggiungi una griglia per facilitare la lettura
    plt.xticks(degradation_plant_dataframe_ga["datetime"], degradation_plant_dataframe_ga["datetime"].dt.strftime('%H'), rotation=10)
    plt.title("Battery Degradation Comparison")
    # Mostra il grafico
    plt.tight_layout()


def plot_comparison_battery(dictionary,lista1,lista2):
    current_datetime = datetime.now() + timedelta(hours=1)- timedelta(hours=delta)
    time_column =pd.date_range(start=current_datetime.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1), periods=24, freq='H') 

    actual_percentage_mixed = dictionary["apercentage_mixed"]
    battery_wh_mixed = [float(0.2 * lista1[i]) + (percentage * (float(0.8 * lista1[i] ) - float(0.2 * lista1[i]))) for i,percentage in enumerate(actual_percentage_mixed[:-1])]
    battery_wh_dataframe_mixed = pd.DataFrame({'datetime': time_column, 'value': battery_wh_mixed})
 

    actual_percentage_ga = dictionary["apercentage_ga"]
    battery_wh_ga = [float(0.2 * lista2[i]) + (percentage * (float(0.8 *lista2[i] ) - float(0.2 * lista2[i]))) for i,percentage in enumerate(actual_percentage_ga[:-1])]
    battery_wh_dataframe_ga = pd.DataFrame({'datetime': time_column, 'value': battery_wh_ga})

    plt.figure(figsize=(10, 6))

    # Tracciare tutte le curve sullo stesso grafico
    plt.plot(battery_wh_dataframe_mixed["datetime"], battery_wh_dataframe_mixed["value"], color=color_mixed, label="MIXED")
    plt.plot(battery_wh_dataframe_ga["datetime"], battery_wh_dataframe_ga["value"], color=color_ga, label="GA")

    # Impostazioni del grafico
    plt.xlabel("Datetime")
    plt.ylabel("Wh")
    plt.legend()  # Mostra la legenda per distinguere le curve
    plt.xticks(rotation=45)  # Ruota le etichette dell'asse x per una migliore leggibilità
    plt.grid(True)  # Aggiungi una griglia per facilitare la lettura
    plt.xticks(battery_wh_dataframe_ga["datetime"], battery_wh_dataframe_ga["datetime"].dt.strftime('%H'), rotation=10)
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
    bar1 = ax.bar(index - bar_width*0.7, algorithm2_times_ga, bar_width, color=color_ga, label='GA')

    # Barre per Algoritmo 2 (spostate leggermente a destra)
    bar2 = ax.bar(index + bar_width*0.7, algorithm1_times_mixed, bar_width, color=color_mixed, label='MixedVariableGa')

    # Aggiunta delle etichette e del titolo
    ax.set_ylabel('Execution time (s)')
    ax.set_title('Comparison of the execution times')
    ax.set_xticks(index)
    ax.set_xticklabels(input_sizes)
    ax.set_xlim([-0.5, 0.5])

    # Aggiungere le etichette sotto le barre
    ax.text(index[0] - bar_width * 0.7, -0.55, 'GA', ha='center', va='top', fontsize=12)
    ax.text(index[0] + bar_width * 0.7, -0.55, 'Mixed', ha='center', va='top', fontsize=12)

    # Mostrare il grafico
    plt.tight_layout()

async def main():
    # Await the mixed function since it is asynchronous
    dictionary ={}
    start_time = time.time()

    dictionary["sum_mixed"],dictionary["apercentage_mixed"] , dictionary["co2_mixed"] , lista1 = await mixed()
    end_time = time.time()
    execution_time_mixed = end_time - start_time
    print(f"Execution_time MixedVariableGa: {execution_time_mixed} seconds")

    start_time = time.time()
    dictionary["sum_ga"], dictionary["apercentage_ga"],  dictionary["co2_ga"], lista2 = await ga()
    end_time = time.time()
    execution_time_ga = end_time - start_time
    print(f"Execution_time Ga: {execution_time_ga} seconds")

    plot_cost_comparison(dictionary)
    plt.show()

    plot_co2_comparison_algo(dictionary)
    plt.show()

    plot_comparison_degradation(lista1,lista2)
    plt.show()

    plot_comparison_battery(dictionary,lista1,lista2)
    plt.show()
    plot_time(execution_time_mixed,execution_time_ga)
    plt.show()


if __name__ == "__main__":
# Now we run the async main function
    asyncio.run(main())
