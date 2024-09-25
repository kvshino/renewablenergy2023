import optuna
from genetic_optuna import *
import asyncio
from functions import *
import warnings
from update_costs import *
from consumptions import *
from plot import *
from update_battery import *
from test_inv import *
from gui import *
from freezegun import freeze_time

warnings.filterwarnings("ignore", category=FutureWarning)

# Wrapper per eseguire codice asincrono in modo sincrono
def objective(trial):
    return asyncio.run(objective_async(trial))

# La tua funzione obiettivo asincrona con ottimizzazione di crossover e mutazione
async def objective_async(trial):
    # Parametri che Optuna ottimizza
    pop_size = trial.suggest_int('pop_size', 10, 500)  # Pop size tra 10 e 500
    n_gen = trial.suggest_int('n_gen', 50, 300)        # Generazioni tra 50 e 300
    block_size = trial.suggest_int('block_size', 2, 10)  # Dimensione del blocco per il crossover
    bitflip_prob = trial.suggest_float('bitflip_prob', 0.01, 0.5)  # Probabilità di mutazione bit-flip
    int_mut_prob = trial.suggest_float('int_mut_prob', 0.01, 0.5)  # Probabilità di mutazione sugli interi
    int_step = trial.suggest_int('int_step', 1, 20)      # Step massimo per la mutazione sugli interi
    n_threads = 24  # o un altro valore

    dict = {}
    polynomial_batt = battery_function()
    polynomial_inverter = inverter_function()
    data = setup(polynomial_inverter)
    prices = await get_future_day_italian_market(data)  # Funzione asincrona
    production_not_rs = forecast_percentage_production_from_not_renewable_sources(api_key=data["api_key"], zona=data["entsoe_timezone"])
    data = setup(polynomial_inverter)
    data["prices"] = prices 
    data["production_not_rs"] = production_not_rs  
    data["polynomial"] = polynomial_batt

    dict["first_battery_value"] = data["socs"]
    dict[f"battery_capacity{0}"] = data["battery_capacity"]

    # Modifica la chiamata per includere i parametri di crossover e mutazione ottimizzati
    res, _ = start_genetic_algorithm(data, pop_size, n_gen, n_threads, 
                                     block_size=block_size, 
                                     bitflip_prob=bitflip_prob, 
                                     int_mut_prob=int_mut_prob, 
                                     int_step=int_step, 
                                     verbose=False)

    # Valutazione finale da minimizzare o massimizzare
    return -np.min(res.pop.get("F"))  # Supponiamo di voler massimizzare "F"

# Crea uno studio Optuna
study = optuna.create_study(direction="maximize")  # Modifica 'maximize' o 'minimize' a seconda del tuo obiettivo
study.optimize(objective, n_trials=50)  # Esegui 50 prove di ottimizzazione

# Stampa il risultato migliore
best_trial = study.best_trial
print(f"Best pop_size: {best_trial.params['pop_size']}")
print(f"Best n_gen: {best_trial.params['n_gen']}")
print(f"Best block_size: {best_trial.params['block_size']}")
print(f"Best bitflip_prob: {best_trial.params['bitflip_prob']}")
print(f"Best int_mut_prob: {best_trial.params['int_mut_prob']}")
print(f"Best int_step: {best_trial.params['int_step']}")
