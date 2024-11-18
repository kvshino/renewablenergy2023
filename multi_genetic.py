from functions import *
import numpy as np
from multiprocessing.pool import ThreadPool
from pymoo.core.problem import StarmapParallelization
from pymoo.core.mixed import MixedVariableGA, MixedVariableMating
from pymoo.core.problem import ElementwiseProblem
from pymoo.core.variable import Binary, Integer
from pymoo.optimize import minimize
from pymoo.termination.default import DefaultMultiObjectiveTermination
from pymoo.operators.survival.rank_and_crowding import RankAndCrowding

from pymoo.core.sampling import Sampling
from pymoo.problems import get_problem

from pymoo.core.callback import Callback
from pymoo.operators.mutation.bitflip import BFM
from pymoo.operators.repair.rounding import RoundingRepair
from pymoo.operators.mutation.pm import PM
from pymoo.operators.selection.rnd import RandomSelection
from pymoo.core.crossover import Crossover

from pymoo.core.selection import Selection
from pymoo.util.misc import random_permuations
import math


def evaluate(data, variables_values, cycles, polynomial):
    sum = []
    sum.append(0)
    co2_emissions = []
    co2_emissions.append(0)
    sold = data["sold"]
    
    actual_percentage = []
    actual_percentage.append(variables_values["first_battery_value"])
    battery_capacity = round(polynomial(cycles) * variables_values["battery_nominal_capacity"], 4)
    
    quantity_delta_battery = []
    ratio_list = []

    # valori negativi indicano consumi ,positivi guadagni
    for j in range(24):
        charge = variables_values[f"b{j}"]
        percentage = variables_values[f"i{j}"]
        quantity_charging_battery = None
        quantity_discharging_battery = None

        
        upper_limit = (data["soc_max"] * battery_capacity)
        lower_limit = (data["soc_min"] * battery_capacity)
        effettivo_in_batteria=lower_limit+(actual_percentage[j]*(upper_limit-lower_limit))

        if charge:

            posso_caricare_di = upper_limit - effettivo_in_batteria

            #Viene calcolato di quanto caricare la batteria
            quantity_charging_battery = ((posso_caricare_di * percentage) / 100) / data["battery_charging_efficiency"]


            if quantity_charging_battery - variables_values[f"difference_of_production{j}"] < 0:
                ratio = min((variables_values[f"load{j}"] + quantity_charging_battery - (quantity_charging_battery - variables_values[f"difference_of_production{j}"])) / data["inverter_nominal_power"],1)
            else:
                ratio = min((variables_values[f"load{j}"] + quantity_charging_battery) / data["inverter_nominal_power"], 1)

            variables_values[f"difference_of_production{j}"] = variables_values[f"production{j}"] * data["polynomial_inverter"](ratio) - variables_values[f"load{j}"]
            if quantity_charging_battery - variables_values[f"difference_of_production{j}"] < 0:
                # devo vendere
                co2_emissions.append( co2_emissions[j] )
                sum.append(
                    sum[j] + ((quantity_charging_battery - variables_values[f"difference_of_production{j}"]) * sold))  # sum = sum - rimborso
            else:
                co2_emissions.append(co2_emissions[j] + co2_quantity_emission(data, variables_values, -((quantity_charging_battery - variables_values[f"difference_of_production{j}"])/data["polynomial_inverter"](ratio)), j))
                
                sum.append(
                    sum[j] + ((quantity_charging_battery - variables_values[f"difference_of_production{j}"])) * variables_values[f"prices{j}"])
                
            actual_percentage.append((effettivo_in_batteria + (quantity_charging_battery*data["battery_charging_efficiency"]) - lower_limit) / ( upper_limit - lower_limit))
            
        else:
            
            posso_scaricare_di=effettivo_in_batteria-lower_limit
            quantity_discharging_battery=((posso_scaricare_di*percentage)/100)*data["battery_discharging_efficiency"]


            if variables_values[f"difference_of_production{j}"] + quantity_discharging_battery > 0:
                ratio = min((variables_values[f"load{j}"] + (variables_values[f"difference_of_production{j}"] + quantity_discharging_battery)) / data["inverter_nominal_power"], 1)
            else:
                ratio = min(variables_values[f"load{j}"] / data["inverter_nominal_power"], 1)

            quantity_discharging_battery = quantity_discharging_battery * data["polynomial_inverter"](ratio)

            variables_values[f"difference_of_production{j}"] = variables_values[f"production{j}"] * data["polynomial_inverter"](ratio) - variables_values[f"load{j}"]
            if variables_values[f"difference_of_production{j}"] + quantity_discharging_battery > 0:
                co2_emissions.append( co2_emissions[j] )
                sum.append(sum[j] - ((variables_values[f"difference_of_production{j}"] + quantity_discharging_battery) * sold))

            else:
                
                co2_emissions.append(co2_emissions[j] + co2_quantity_emission(data, variables_values, (variables_values[f"difference_of_production{j}"] + quantity_discharging_battery/data["battery_discharging_efficiency"])/data["polynomial_inverter"](ratio), j))

                sum.append(sum[j] + (
                        - ((variables_values[f"difference_of_production{j}"] + quantity_discharging_battery/data["battery_discharging_efficiency"])) * variables_values[f"prices{j}"]))
            
            
            scarico=(posso_scaricare_di*percentage)/100
            cycles = round(cycles+(scarico/battery_capacity), 5)
            battery_capacity = round(polynomial(cycles) * variables_values["battery_nominal_capacity"], 4)
            actual_percentage.append((effettivo_in_batteria - (quantity_discharging_battery/data["battery_discharging_efficiency"]) - lower_limit) / ( upper_limit - lower_limit))

        ratio_list.append(ratio)

        if quantity_charging_battery != None:
            quantity_delta_battery.append(+quantity_charging_battery)
        else:
            quantity_delta_battery.append(-quantity_discharging_battery)

    return sum[1:], actual_percentage, quantity_delta_battery, co2_emissions[1:], ratio_list


def start_genetic_algorithm(data, pop_size=650, n_gen=300, n_threads=12, prob_mut_bit=0.5, prob_mut_int=0.8, sampling=None,verbose=False):
    class MixedVariableProblem(ElementwiseProblem):

        def __init__(self, n_couples=24, **kwargs):
            variables = {}
            self.gens=0
            for j in range(n_couples):
                variables[f"b{j}"] = Binary()
                variables[f"i{j}"] = Integer(bounds=(0, 100))
            super().__init__(vars=variables, n_obj=3, n_ieq_constr=0, **kwargs)


        def _evaluate(self, X, out, *args, **kwargs):
            sum = 0                                                         #variabile che viene usata come contenitore per determinare l'andamento della stringa nel corso della valutazione
            delta_production = data["difference_of_production"]             #variabile che mi dice quantitativamente se la produzione di energia supera il consumo e viceversa
            sold = data["sold"]                                             #variabile che mi dice il prezzo della vendita dell'energia
            actual_percentage = [float(data["socs"])]                          #viene memorizzato l'attuale livello della batteria
            co2_emissions=0
            percentage_production_not_renewable = data["production_not_rs"]
            penalty_costs = 0
            penalty_batt = 0
            penalty_co2=0
            cycles = data["cycles"]
            battery_capacity = round(data["polynomial"](cycles) * data["battery_nominal_capacity"], 4)


            for j in range(24):                                             #Viene eseguita una predizione per le successive 24 ore         
                charge = X[f"b{j}"]
                percentage = X[f"i{j}"]

                
                upper_limit = (data["soc_max"] * battery_capacity)      #una batteria ha una certa capacità, dai parametri di configurazione si capisce fino a quando l'utente vuole che si carichi
                lower_limit = (data["soc_min"] * battery_capacity)      #una batteria ha una certa capacità, dai parametri di configurazione si capisce fino a quando l'utente vuole che si scarichi

                effettivo_in_batteria=lower_limit+(actual_percentage[j]*(upper_limit-lower_limit))

                #Caso in cui si sceglie di caricare la batteria
                if charge:                                                  
       
                    posso_caricare_di = max(upper_limit - effettivo_in_batteria, 0)

                    #Viene calcolato di quanto caricare la batteria
                    quantity_charging_battery = ((posso_caricare_di * percentage) / 100) / data["battery_charging_efficiency"]

                    if quantity_charging_battery - delta_production.iloc[j] < 0:
                        ratio = min((data["estimate"]["consumo"].values[j] + quantity_charging_battery - (quantity_charging_battery - delta_production.iloc[j])) / data["inverter_nominal_power"],1)
                    else:
                        ratio = min((data["estimate"]["consumo"].values[j] + quantity_charging_battery) / data["inverter_nominal_power"], 1)


                    #Si controlla che la carica della batteria non sia maggiore di quella fisicamente ottenibile
                    if(quantity_charging_battery > data["maximum_power_battery_exchange"]):
                        penalty_batt = penalty_batt + data["polynomial"](cycles+(quantity_charging_battery-data["maximum_power_battery_exchange"])/battery_capacity)

                    if(quantity_charging_battery > data["maximum_power_absorption"]):
                        penalty_costs = penalty_costs + (quantity_charging_battery - data["maximum_power_absorption"])*data["prices"]["prezzo"].iloc[j]
                        penalty_co2 = penalty_co2 + (quantity_charging_battery - data["maximum_power_absorption"])* percentage_production_not_renewable["Difference"][j]
                    

                    delta_production_after_inverter = data["expected_production"]["production"][j] * data["polynomial_inverter"](ratio) - data["estimate"]["consumo"].values[j]
                    #Viene controllata se la produzione dei pannelli è maggiore del consumo domestico unito al consumo della carica della batteria
                    if quantity_charging_battery - delta_production_after_inverter < 0:

                        if data["estimate"]["consumo"].values[j] + quantity_charging_battery + (quantity_charging_battery - delta_production_after_inverter) > data["inverter_nominal_power"]:
                            penalty_batt = penalty_batt + data["polynomial"](cycles+(data["estimate"]["consumo"].values[j] + quantity_charging_battery + (quantity_charging_battery - delta_production_after_inverter)-data["inverter_nominal_power"])/battery_capacity)
                        #Il surplus di energia viene venduto
                        sum = sum + ((quantity_charging_battery - delta_production_after_inverter) * sold)  # sum = sum - rimborso


                    #Caso in cui viene prodotto meno di quanto si consuma, di conseguenza è necessario acquistare dalla rete
                    else:
                        
                        quantity_bought_from_not_renewable_sources =  ((quantity_charging_battery - delta_production_after_inverter)) * percentage_production_not_renewable["Difference"][j]

                        if data["estimate"]["consumo"].values[j] + quantity_charging_battery > data["inverter_nominal_power"]:
                            penalty_batt = penalty_batt + data["polynomial"](cycles+(data["estimate"]["consumo"].values[j] + quantity_charging_battery - data["inverter_nominal_power"])/battery_capacity)

                        #Viene fatto un controllo che NON permette di acquistare più energia di quanto il contratto stipulato dall'utente permetta
                        if( quantity_charging_battery > data["maximum_power_absorption"] + delta_production_after_inverter):
                            penalty_costs = penalty_costs + (quantity_charging_battery-(data["maximum_power_absorption"] + delta_production_after_inverter))* data["prices"]["prezzo"].iloc[j]
                            penalty_co2 = penalty_co2 + (quantity_charging_battery-(data["maximum_power_absorption"] + delta_production_after_inverter))* percentage_production_not_renewable["Difference"][j]


                        co2_emissions = co2_emissions + (quantity_bought_from_not_renewable_sources * data["coal_percentage"] * data["coal_pollution"]) + (quantity_bought_from_not_renewable_sources * data["gas_percentage"] * data["gas_pollution"]) + (quantity_bought_from_not_renewable_sources * data["oil_percentage"] * data["oil_pollution"]) 
                        #Viene acquistata energia
                        sum = sum + ((quantity_charging_battery - delta_production_after_inverter)) * data["prices"]["prezzo"].iloc[j]
                    
                    actual_percentage.append((effettivo_in_batteria + (quantity_charging_battery*data["battery_charging_efficiency"]) - lower_limit) / ( upper_limit - lower_limit))
                    
                    
                #Caso in cui si sceglie di scaricare la batteria
                else:

                    #Viene calcolato di quanto scaricare la batteria
                    posso_scaricare_di= max(effettivo_in_batteria-lower_limit, 0)
                    quantity_discharging_battery=((posso_scaricare_di*percentage)/100)*data["battery_discharging_efficiency"]

                                  
                    if delta_production.iloc[j] + quantity_discharging_battery > 0:
                        ratio = min((data["estimate"]["consumo"].values[j] + (delta_production.iloc[j] + quantity_discharging_battery)) / data["inverter_nominal_power"], 1)
                    else:
                        ratio = min(data["estimate"]["consumo"].values[j] / data["inverter_nominal_power"], 1)

                    quantity_discharging_battery = quantity_discharging_battery * data["polynomial_inverter"](ratio)


                    #Si controlla che la scarica della batteria non sia maggiore di quella fisicamente ottenibile
                    if(quantity_discharging_battery > data["maximum_power_battery_exchange"]):
                        penalty_batt = penalty_batt + data["polynomial"](cycles+(quantity_discharging_battery-data["maximum_power_battery_exchange"])/battery_capacity)
                    
                    if(quantity_discharging_battery > data["maximum_power_absorption"]):
                        penalty_costs = penalty_costs + (quantity_discharging_battery-data["maximum_power_absorption"])*sold
                        penalty_co2 = penalty_co2 + (quantity_discharging_battery-data["maximum_power_absorption"])* percentage_production_not_renewable["Difference"][j]


                    delta_production_after_inverter = data["expected_production"]["production"][j] * data["polynomial_inverter"](ratio) - data["estimate"]["consumo"].values[j]
                    #Si controlla se si produce di più di quanto si consuma. Prendere energia dalla batteria viene considerata produzione
                    if delta_production_after_inverter + quantity_discharging_battery > 0:

                        if data["estimate"]["consumo"].values[j] + (delta_production_after_inverter + quantity_discharging_battery) > data["inverter_nominal_power"]:
                            penalty_batt= penalty_batt+data["polynomial"](cycles+(data["estimate"]["consumo"].values[j] + (delta_production_after_inverter + quantity_discharging_battery)- data["inverter_nominal_power"])/battery_capacity)
                            penalty_costs=penalty_costs+(data["estimate"]["consumo"].values[j] + (delta_production_after_inverter + quantity_discharging_battery)- data["inverter_nominal_power"]) * sold
                            penalty_co2=penalty_co2+(data["estimate"]["consumo"].values[j] + (delta_production_after_inverter + quantity_discharging_battery)- data["inverter_nominal_power"])  * percentage_production_not_renewable["Difference"][j]
                           
                        #Si controlla di non prendere più energia dalla batteria di quanto il contatore sia in grado di gestire
                        if(quantity_discharging_battery + delta_production_after_inverter > data["maximum_power_absorption"]):
                            penalty_costs = penalty_costs + (quantity_discharging_battery + delta_production_after_inverter - data["maximum_power_absorption"])* sold
                            penalty_co2 = penalty_co2 + (quantity_discharging_battery + delta_production_after_inverter - data["maximum_power_absorption"])* percentage_production_not_renewable["Difference"][j]
                            
                     #Produco di più di quanto consumo, vendo il resto
                        sum = sum - ((delta_production_after_inverter + quantity_discharging_battery) * sold)

                    #Produco poco e consumo di più
                    else:
                        quantity_bought_from_not_renewable_sources = ( - (delta_production_after_inverter + quantity_discharging_battery)) * percentage_production_not_renewable["Difference"][j]

                        if data["estimate"]["consumo"].values[j] > data["inverter_nominal_power"]:
                            penalty_batt=penalty_batt+data["polynomial"](cycles+((data["estimate"]["consumo"].values[j]-data["inverter_nominal_power"])/battery_capacity)) 
                            penalty_costs=penalty_costs+(data["estimate"]["consumo"].values[j]-data["inverter_nominal_power"]) * data["prices"]["prezzo"].iloc[j]
                            penalty_co2=penalty_co2+(data["estimate"]["consumo"].values[j]-data["inverter_nominal_power"]) * percentage_production_not_renewable["Difference"][j]
                            
                        co2_emissions = co2_emissions + (quantity_bought_from_not_renewable_sources * data["coal_percentage"] * data["coal_pollution"]) + (quantity_bought_from_not_renewable_sources * data["gas_percentage"] * data["gas_pollution"]) + (quantity_bought_from_not_renewable_sources * data["oil_percentage"] * data["oil_pollution"]) 
                        #Produco di meno di quanto consumo, compro il resto
                        sum = sum + (- (delta_production_after_inverter + quantity_discharging_battery) *
                                     data["prices"]["prezzo"].iloc[j])


                    scarico=(posso_scaricare_di*percentage)/100 
                    cycles = round(cycles+(scarico/battery_capacity), 5)
                    battery_capacity = round(data["polynomial"](cycles) * data["battery_nominal_capacity"], 4)

                    #Viene aggiornato il valore della batteria, dopo la scarica
                    actual_percentage.append((effettivo_in_batteria - (quantity_discharging_battery/data["battery_discharging_efficiency"]) - lower_limit) / ( upper_limit - lower_limit))
            

            cost_objective=sum+(0.5*self.gens)*penalty_costs
            batt_objective=(-battery_capacity/data["battery_nominal_capacity"])+(0.5*self.gens)*penalty_batt
            co2_objective=(co2_emissions/1000)+(0.5*self.gens)*penalty_co2
            #Terminata la simulazione, viene attribuito un voto alla stringa in input, dato da tre fattori:
            # - Il costo
            # - L'utilizzo della batteria
            # - Emissioni CO2


            out["F"] = [cost_objective, batt_objective, co2_objective]

            



    class MySampling(Sampling):

        def _do(self, problem, n_samples=24, **kwargs):
            X = np.full(pop_size, 1, dtype=object)
            
            
            for k in range(len(sampling.X)):
                dict={}
                for i in range(24):
                    dict[f"b{i}"] = sampling.X[k][f"b{i}"]
                    dict[f"i{i}"] = sampling.X[k][f"i{i}"]

                X[k] = dict

            for j in range(k+1, pop_size):
                dict={}
                for i in range(24):
                    dict[f"b{i}"] = random.choice([True, False])
                    dict[f"i{i}"] = random.randint(0, 100)

                X[j] = dict
            
            return X
    
    class MyCallback(Callback):
        def __init__(self, problem):
            super().__init__()
            self.problem=problem

        def notify(self, algorithm):
            self.problem.gens+=1
    

    prob_mut_bit=0.1775
    prob_mut_int=0.5958

    pool = ThreadPool(n_threads)
    runner = StarmapParallelization(pool.starmap)
    problem = MixedVariableProblem(elementwise_runner=runner)

    termination= DefaultMultiObjectiveTermination(xtol=0.001, n_max_gen=n_gen, n_skip=1, period=50)

    survival = RankAndCrowding() 
    selection = CustomRandomSelection()

    
    crossover = {
        Binary: CustomFourPointCrossover(),
        Integer: CustomFourPointCrossover()
    } 

    mutation = {
        Binary: BFM(prob_var=prob_mut_bit),
        Integer: PM(vtype=float, repair=RoundingRepair(), prob_var=prob_mut_int, eta=20, at_least_once=False),
    }

    if sampling is None:
        algorithm = MixedVariableGA(pop_size=pop_size, survival=survival, mating=MixedVariableMating(selection=selection, crossover=crossover, mutation=mutation, eliminate_duplicates=None))
    else:
        algorithm = MixedVariableGA(pop_size=pop_size, sampling=MySampling(), survival=survival, mating=MixedVariableMating(selection=selection, crossover=crossover, mutation=mutation, eliminate_duplicates=None))
        
    callback = MyCallback(problem)
    res = minimize(problem,
                   algorithm,
                   termination= termination, 
                   seed= random.randint(0, 99999),
                   verbose=verbose,
                   save_history=True,
                   callback = callback
                   )
    
    pool.close()
    pool.join()  

    if res.algorithm.n_gen-1 < n_gen:
        print("Terminazione anticipata con n_gen: " + str(res.algorithm.n_gen))

    return res, res.history


def shifting_individuals(population):
    for individuo in population.X:
        for i in range(23):
            individuo[f"b{i}"] = individuo[f"b{i+1}"]
            individuo[f"i{i}"] = individuo[f"i{i+1}"]

        individuo["b23"] =  random.choice([True, False])
        individuo["i23"] = random.randint(0, 100)
    
    return population


class CustomFourPointCrossover(Crossover):

    def __init__(self):
        super().__init__(2, 2) 

    def _do(self, problem, X, **kwargs):

        offspring = np.full_like(X.copy(), 0)

        for j, value in enumerate(X[0]):
            for i in range(6):
                offspring[0, j, i] = value[i]
                offspring[1, j, i+6] = value[i+6]
                offspring[0, j, i+12] = value[i+12]
                offspring[1, j, i+18] = value[i+18]


        for j, value in enumerate(X[1]):
            for i in range(6):
                offspring[1, j, i] = value[i]
                offspring[0, j, i+6] = value[i+6]
                offspring[1, j, i+12] = value[i+12]
                offspring[0, j, i+18] = value[i+18]


        return offspring


class CustomRandomSelection(Selection):

    def _do(self, _, pop, n_select, n_parents, **kwargs):
        # number of random individuals needed
        n_random = n_select * n_parents

        # number of permutations needed
        n_perms = math.ceil(n_random / round(len(pop)/2))

        # get random permutations and reshape them
        P = random_permuations(n_perms, round(len(pop)/2))[:n_random]

        return np.reshape(P, (n_select, n_parents))