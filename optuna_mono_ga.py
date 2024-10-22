import optuna
from genetic_ga import *
import asyncio
from functions import *
import warnings
from update_costs import *
from consumptions import *
from plot import *
from update_battery import *
from test_inv import *
from gui import *

warnings.filterwarnings("ignore", category=FutureWarning)



async def obtaining_data():

    polynomial_batt = battery_function()
    polynomial_inverter = inverter_function()
    data = setup(polynomial_inverter,'csv/socsga.csv')
    prices = await get_future_day_italian_market(data)  # Funzione asincrona
    production_not_rs = forecast_percentage_production_from_not_renewable_sources(api_key=data["api_key"], zona=data["entsoe_timezone"])
    data = setup(polynomial_inverter,'csv/socsga.csv')
    data["prices"] = prices 
    data["production_not_rs"] = production_not_rs  
    data["polynomial"] = polynomial_batt

    return data

# Wrapper per eseguire codice asincrono in modo sincrono
def objective(trial):
    return asyncio.run(objective_async(trial))

# La tua funzione obiettivo asincrona con ottimizzazione di crossover e mutazione
async def objective_async(trial):
    # Parametri che Optuna ottimizza
    pop_size = trial.suggest_int('pop_size', 10, 20)           # Pop size tra 10 e 500
    n_gen = trial.suggest_int('n_gen', 1, 10)                 # Generazioni tra 50 e 300

    prob_cross = trial.suggest_float('prob_cross',0.3,0.8)          #probabilità di crossover
    prob_mut_bit = trial.suggest_float('prob_mut_bit',0.1,0.2)          #probabilità di mutazione
    prob_mut_int = trial.suggest_float('prob_mut_int',0.3,0.8)          #probabilità di mutazione

    n_threads=24
    global data

    # Modifica la chiamata per includere i parametri di crossover e mutazione ottimizzati
    res, _ = start_GA_genetic_algorithm(data, pop_size, n_gen, n_threads,prob_mut_bit=prob_mut_bit ,prob_mut_int=prob_mut_int,prob_cross=prob_cross,
                                     verbose=False)

    # Valutazione finale da minimizzare o massimizzare
    return np.min(res.pop.get("F"))  # Supponiamo di voler massimizzare "F"



data= asyncio.run(obtaining_data())
# Crea uno studio Optuna
study = optuna.create_study(storage ="sqlite:///ga.db",direction="minimize")  # Modifica 'maximize' o 'minimize' a seconda del tuo obiettivo
study.optimize(objective, n_trials=100)  # Esegui 50 prove di ottimizzazione

#optuna-dashboard sqlite:///ga.db

# Stampa il risultato migliore
best_trial = study.best_trial
print(f"Best pop_size: {best_trial.params['pop_size']}")
print(f"Best n_gen: {best_trial.params['n_gen']}")
print(f"Best prob_cross: {best_trial.params['prob_cross']}")
print(f"Best prob_mut_int: {best_trial.params['prob_mut_int']}")
print(f"Best prob_mut_bit: {best_trial.params['prob_mut_bit']}")

