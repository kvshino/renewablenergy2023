import optuna
from multi_genetic import *
import asyncio
from functions import *
import warnings
from update_costs import *
from consumptions import *
from plot import *
from update_battery import *
from test_inv import *
from gui import *

from pymoo.algorithms.moo.nsga2 import NSGA2, binary_tournament
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.crossover.ux import UX
from pymoo.operators.crossover.pntx import SinglePointCrossover, TwoPointCrossover

from pymoo.operators.mutation.bitflip import BFM
from pymoo.operators.repair.rounding import RoundingRepair
from pymoo.operators.mutation.pm import PM
from pymoo.operators.selection.rnd import RandomSelection
from pymoo.operators.selection.tournament import TournamentSelection
from pymoo.operators.survival.rank_and_crowding import RankAndCrowding

from pymoo.core.mixed import MixedVariableGA, MixedVariableMating
from pymoo.core.problem import ElementwiseProblem
from pymoo.core.variable import Binary, Integer
from pymoo.optimize import minimize
from pymoo.operators.mutation.bitflip import BFM

from multiprocessing.pool import ThreadPool
from pymoo.core.problem import StarmapParallelization

warnings.filterwarnings("ignore", category=FutureWarning)





def objective(trial):
    return asyncio.run(objective_async(trial))

async def objective_async(trial):
    
    
    # Parametri che Optuna ottimizza
    pop_size = trial.suggest_int('pop_size', 100, 1000)  # Pop size tra 10 e 100
    n_gen = trial.suggest_int('n_gen', 50, 300)        # Generazioni tra 50 e 300
    # crossover_prob = trial.suggest_float("crossover_prob", 0.5, 1.0)  # Probabilità di crossover
    # mutation_prob = trial.suggest_float("mutation_prob", 0.01, 0.3)   # Probabilità di mutazione
    
    
    n_threads = 12  
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
    cycles = data["cycles"]
    dict[f"battery_capacity{0}"] = data["battery_capacity"]

    res,_ = start_genetic_algorithm(data, pop_size=pop_size, n_gen=n_gen, n_threads=n_threads, sampling=None)

    # Restituisci i valori degli obiettivi
    return res.F[0].tolist()

# Crea uno studio Optuna per ottimizzare i parametri
study = optuna.create_study(directions=["minimize", "minimize", "minimize"])
study.optimize(objective, n_trials=1)

# Visualizza i risultati
print("Pareto solutions:", len(study.best_trials))
for trial in study.best_trials:
    print(trial.values)