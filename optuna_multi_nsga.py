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



async def obtaining_data():
    polynomial_batt = battery_function()
    polynomial_inverter = inverter_function()
    data = setup(polynomial_inverter)
    prices = await get_future_day_italian_market(data)  # Funzione asincrona
    production_not_rs = forecast_percentage_production_from_not_renewable_sources(api_key=data["api_key"], zona=data["entsoe_timezone"])
    data = setup(polynomial_inverter)
    data["prices"] = prices 
    data["production_not_rs"] = production_not_rs  
    data["polynomial"] = polynomial_batt

    return data



def objective(trial):
    
    pop_size = trial.suggest_int('pop_size', 100, 700)  
    n_gen = trial.suggest_int('n_gen', 70, 300)        

    prob_cross = trial.suggest_float('prob_cross',0.3,0.9)         
    prob_mut_bit = trial.suggest_float('prob_mut_bit',0.2,0.5)          
    prob_mut_int = trial.suggest_float('prob_mut_int',0.3,0.9)  

    n_threads = 12 
    global data    

    res,_ = start_nsga2_genetic_algorithm(data, pop_size=pop_size, n_gen=n_gen, n_threads=n_threads, prob_mut_int=prob_mut_int, prob_mut_bit=prob_mut_bit, prob_cross=prob_cross, sampling=None)

    F=res.F
    F_min = np.min(F, axis=0)
    F_max = np.max(F, axis=0)
    F_norm = (F - F_min) / (F_max - F_min)
    distances = np.linalg.norm(F_norm, axis=1)
    best_index = np.argmin(distances)

    return res.F[best_index].tolist()


data= asyncio.run(obtaining_data())


# Crea uno studio Optuna per ottimizzare i parametri
study = optuna.create_study(storage="sqlite:///nsga.db", directions=["minimize", "minimize", "minimize"])
study.optimize(objective, n_trials=150)

# Visualizza i risultati
print("Pareto solutions:", len(study.best_trials))
for trial in study.best_trials:
    print(trial.values)

