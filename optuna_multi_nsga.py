import optuna
from multi_genetic_nsga import *
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





def objective(trial):
    return asyncio.run(objective_async(trial))

async def objective_async(trial):
    
    
    # Parametri che Optuna ottimizza
    pop_size = trial.suggest_int('pop_size', 10, 100)  # Pop size tra 10 e 100
    n_gen = trial.suggest_int('n_gen', 5, 30)        # Generazioni tra 50 e 300

    prob_cross = trial.suggest_float('prob_cross',0.3,0.9)          #probabilità di mutazione

    prob_mut_bit = trial.suggest_float('prob_mut_bit',0.2,0.5)          #probabilità di mutazione
    prob_mut_int = trial.suggest_float('prob_mut_int',0.3,0.9)          #probabilità di mutazione

    n_threads = 24 
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

    res,_ = start_nsga2_genetic_algorithm(data, pop_size=pop_size, n_gen=n_gen, n_threads=n_threads,prob_mut_int=prob_mut_int,prob_mut_bit=prob_mut_bit,prob_cross=prob_cross, sampling=None)

    # Restituisci i valori degli obiettivi
    return res.F[0].tolist()

# Crea uno studio Optuna per ottimizzare i parametri
study = optuna.create_study(directions=["minimize", "minimize", "minimize"])
study.optimize(objective, n_trials=50)

# Visualizza i risultati
print("Pareto solutions:", len(study.best_trials))
for trial in study.best_trials:
    print(trial.values)

