from functions import *


import numpy as np
from multiprocessing.pool import ThreadPool
from pymoo.core.problem import StarmapParallelization
from pymoo.core.mixed import MixedVariableGA, MixedVariableMating
from pymoo.core.problem import ElementwiseProblem
from pymoo.core.variable import Binary, Integer
from pymoo.optimize import minimize
from pymoo.util.display.output import Output
from pymoo.util.display.column import Column

from pymoo.termination.default import DefaultMultiObjectiveTermination
from pymoo.algorithms.moo.nsga2 import RankAndCrowdingSurvival

from pymoo.core.sampling import Sampling

from pymoo.visualization.scatter import Scatter
import matplotlib.pyplot as plt
from pymoo.problems import get_problem

from pymoo.core.callback import Callback
from pymoo.algorithms.moo.nsga2 import NSGA2, binary_tournament
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.crossover.ux import UX
from pymoo.operators.mutation.bitflip import BFM
from pymoo.operators.repair.rounding import RoundingRepair
from pymoo.operators.mutation.pm import PM
from pymoo.operators.selection.rnd import RandomSelection
from pymoo.operators.selection.tournament import TournamentSelection
from pymoo.operators.survival.rank_and_crowding import RankAndCrowding




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


def start_genetic_algorithm(data, pop_size, n_gen, n_threads, sampling=None,verbose=False):
    class MixedVariableProblem(ElementwiseProblem):

        def __init__(self, n_couples=24, **kwargs):
            variables = {}
            for j in range(n_couples):
                variables[f"b{j}"] = Binary()
                variables[f"i{j}"] = Integer(bounds=(0, 100))
            super().__init__(vars=variables, n_obj=3, n_ieq_constr=0, **kwargs)


        def _evaluate(self, X, out, *args, **kwargs):
            """
            Funzione che prende in input una stringa di 24 coppie di valori (a,b) col seguente significato:
            - a: valore booleano che indica se la batteria deve essere caricata o meno. 1-> Carica Batteria, 0-> Scarica Batteria;
            - b: valore intero che indica la percentuale di carica/scarica (in base al valore di "a");
            
            Returns:
                Un valore Float che indica il risultato della stringa di input rispetto alla funzione obiettivo. 
                Valore negativo indica consumo, positivo guadagno
            """

            sum = 0                                                         #variabile che viene usata come contenitore per determinare l'andamento della stringa nel corso della valutazione
            delta_production = data["difference_of_production"]             #variabile che mi dice quantitativamente se la produzione di energia supera il consumo e viceversa
            sold = data["sold"]                                             #variabile che mi dice il prezzo della vendita dell'energia
            actual_percentage = [float(data["socs"])]                          #viene memorizzato l'attuale livello della batteria
            quantity_battery=0
            co2_emissions=0
            percentage_production_not_renewable = data["production_not_rs"]
            penality_sum = 1
            penality_batt = 1
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

                    posso_caricare_di = upper_limit - effettivo_in_batteria

                    #Viene calcolato di quanto caricare la batteria
                    quantity_charging_battery = ((posso_caricare_di * percentage) / 100) / data["battery_charging_efficiency"]

                    if quantity_charging_battery - delta_production.iloc[j] < 0:
                        ratio = min((data["estimate"]["consumo"].values[j] + quantity_charging_battery - (quantity_charging_battery - delta_production.iloc[j])) / data["inverter_nominal_power"],1)
                    else:
                        ratio = min((data["estimate"]["consumo"].values[j] + quantity_charging_battery) / data["inverter_nominal_power"], 1)


                    #Si controlla che la carica della batteria non sia maggiore di quella fisicamente ottenibile
                    if(quantity_charging_battery > data["maximum_power_battery_exchange"]):
                        penality_batt = penality_batt + (1 -  data["maximum_power_battery_exchange"] / quantity_charging_battery)

                    if(quantity_charging_battery > data["maximum_power_absorption"]):      
                        penality_sum = penality_sum + (1 -  data["maximum_power_absorption"] / quantity_charging_battery)
                    

                    delta_production.iloc[j] = data["expected_production"]["production"][j] * data["polynomial_inverter"](ratio) - data["estimate"]["consumo"].values[j]
                    #Viene controllata se la produzione dei pannelli è maggiore del consumo domestico unito al consumo della carica della batteria
                    if quantity_charging_battery - delta_production.iloc[j] < 0:

                        if data["estimate"]["consumo"].values[j] + quantity_charging_battery + (quantity_charging_battery - delta_production.iloc[j]) > data["inverter_nominal_power"]:
                            penality_batt = penality_batt + (1 - data["inverter_nominal_power"]/(data["estimate"]["consumo"].values[j] + quantity_charging_battery + (quantity_charging_battery - delta_production.iloc[j])))
                        
                        #Il surplus di energia viene venduto
                        sum = sum + ((quantity_charging_battery - delta_production.iloc[j]) * sold)/penality_sum  # sum = sum - rimborso


                    #Caso in cui viene prodotto meno di quanto si consuma, di conseguenza è necessario acquistare dalla rete
                    else:
                        
                        quantity_bought_from_not_renewable_sources =  ((quantity_charging_battery - delta_production.iloc[j])) * percentage_production_not_renewable["Difference"][j]
                        co2_emissions = co2_emissions + (quantity_bought_from_not_renewable_sources * data["coal_percentage"] * data["coal_pollution"]) + (quantity_bought_from_not_renewable_sources * data["gas_percentage"] * data["gas_pollution"]) + (quantity_bought_from_not_renewable_sources * data["oil_percentage"] * data["oil_pollution"]) * penality_sum


                        if data["estimate"]["consumo"].values[j] + quantity_charging_battery > data["inverter_nominal_power"]:
                            penality_batt = penality_batt + (1 - data["inverter_nominal_power"]/(data["estimate"]["consumo"].values[j] + quantity_charging_battery))

                        #Viene fatto un controllo che NON permette di acquistare più energia di quanto il contratto stipulato dall'utente permetta
                        if( quantity_charging_battery > data["maximum_power_absorption"] + delta_production.iloc[j]):
                            penality_sum = penality_sum + (1 -  data["maximum_power_absorption"] / quantity_charging_battery)

                        #Viene acquistata energia
                        sum = sum + ((quantity_charging_battery - delta_production.iloc[j])) * data["prices"]["prezzo"].iloc[j]*penality_sum
                    
                    actual_percentage.append((effettivo_in_batteria + (quantity_charging_battery*data["battery_charging_efficiency"]) - lower_limit) / ( upper_limit - lower_limit))
                    
                    
                #Caso in cui si sceglie di scaricare la batteria
                else:

                    #Viene calcolato di quanto scaricare la batteria
                    posso_scaricare_di=effettivo_in_batteria-lower_limit
                    quantity_discharging_battery=((posso_scaricare_di*percentage)/100)*data["battery_discharging_efficiency"]

                                  
                    if delta_production.iloc[j] + quantity_discharging_battery > 0:
                        ratio = min((data["estimate"]["consumo"].values[j] + (delta_production.iloc[j] + quantity_discharging_battery)) / data["inverter_nominal_power"], 1)
                    else:
                        ratio = min(data["estimate"]["consumo"].values[j] / data["inverter_nominal_power"], 1)

                    quantity_discharging_battery = quantity_discharging_battery * data["polynomial_inverter"](ratio)


                    #Si controlla che la scarica della batteria non sia maggiore di quella fisicamente ottenibile
                    if(quantity_discharging_battery > data["maximum_power_battery_exchange"]):
                        penality_batt = penality_batt + (1 -  data["maximum_power_battery_exchange"] / quantity_discharging_battery)
                    
                    if(quantity_discharging_battery > data["maximum_power_absorption"]):
                        penality_sum = penality_sum + (1 -  data["maximum_power_absorption"] / quantity_discharging_battery)


                    delta_production.iloc[j] = data["expected_production"]["production"][j] * data["polynomial_inverter"](ratio) - data["estimate"]["consumo"].values[j]
                    #Si controlla se si produce di più di quanto si consuma. Prendere energia dalla batteria viene considerata produzione
                    if delta_production.iloc[j] + quantity_discharging_battery > 0:

                        if data["estimate"]["consumo"].values[j] + (delta_production.iloc[j] + quantity_discharging_battery) > data["inverter_nominal_power"]:
                            penality_batt = penality_batt + (1 - data["inverter_nominal_power"]/(data["estimate"]["consumo"].values[j] + (delta_production.iloc[j] + quantity_discharging_battery)))
                            penality_sum = penality_sum + (1 - data["inverter_nominal_power"]/(data["estimate"]["consumo"].values[j] + (delta_production.iloc[j] + quantity_discharging_battery)))

                        #Si controlla di non prendere più energia dalla batteria di quanto il contatore sia in grado di gestire
                        if(quantity_discharging_battery + delta_production.iloc[j] > data["maximum_power_absorption"]):
                            penality_sum = penality_sum + (1 -  data["maximum_power_absorption"] / quantity_discharging_battery)

                     #Produco di più di quanto consumo, vendo il resto
                        sum = sum - ((delta_production.iloc[j] + quantity_discharging_battery) * sold)/penality_sum

                    #Produco poco e consumo di più
                    else:
                        quantity_bought_from_not_renewable_sources = (- (delta_production.iloc[j] + quantity_discharging_battery)) * percentage_production_not_renewable["Difference"][j]
                        co2_emissions = co2_emissions + (quantity_bought_from_not_renewable_sources * data["coal_percentage"] * data["coal_pollution"]) + (quantity_bought_from_not_renewable_sources * data["gas_percentage"] * data["gas_pollution"]) + (quantity_bought_from_not_renewable_sources * data["oil_percentage"] * data["oil_pollution"]) * penality_sum

                        if data["estimate"]["consumo"].values[j] > data["inverter_nominal_power"]:
                            penality_batt = penality_batt + (1 - data["inverter_nominal_power"]/(data["estimate"]["consumo"].values[j]))
                            penality_sum = penality_sum * (1 - data["inverter_nominal_power"]/(data["estimate"]["consumo"].values[j]))                    
                        
                        #Produco di meno di quanto consumo, compro il resto
                        sum = sum + (- (delta_production.iloc[j] + quantity_discharging_battery/data["battery_discharging_efficiency"]) *
                                     data["prices"]["prezzo"].iloc[j])*penality_sum


                    scarico=(posso_scaricare_di*percentage)/100
                    cycles = round(cycles+(scarico/battery_capacity), 5)
                    battery_capacity = round(data["polynomial"](cycles) * data["battery_nominal_capacity"], 4)

                    #Viene aggiornato il valore della batteria, dopo la scarica
                    actual_percentage.append((effettivo_in_batteria - (quantity_discharging_battery/data["battery_discharging_efficiency"]) - lower_limit) / ( upper_limit - lower_limit))
                    quantity_battery+=abs(quantity_discharging_battery) * penality_batt
            #Terminata la simulazione, viene attribuito un voto alla stringa in input, dato da tre fattori:
            # - Il costo
            # - L'utilizzo della batteria
            # - Emissioni CO2

            out["F"] = [sum, quantity_battery, co2_emissions]
            


    class MyOutput(Output):
        def __init__(self):
            super().__init__()
            # self.costi = Column("costi", width=8)
    class MyOutput(Output):
        def __init__(self):
            super().__init__()
            # self.costi = Column("costi", width=8)
            # self.batteria = Column("batteria", width=8)
            self.columns += [] #self.costi, self.batteria]

        def update(self, algorithm):
            super().update(algorithm)
            
            # Per esempio, se costi e batteria sono calcolati in base alla popolazione attuale
            # Qui si assume che costi e batteria siano memorizzati nelle colonne di F
            # Sostituisci con i calcoli corretti per il tuo caso specifico
            #print(np.min(algorithm.pop.get("F")[0, 1]))
            # self.costi.set('{:.3f}'.format(np.min(algorithm.pop.get("F")[:, 0])))  # Media della seconda colonna di F
            # self.batteria.set('{:.3f}'.format(np.min(algorithm.pop.get("F")[:, 0])))  # Media della terza colonna di F        # self.batteria = Column("batteria", width=8)
            self.columns += [] #self.costi, self.batteria]

        def update(self, algorithm):
            super().update(algorithm)
            
            # Per esempio, se costi e batteria sono calcolati in base alla popolazione attuale
            # Qui si assume che costi e batteria siano memorizzati nelle colonne di F
            # Sostituisci con i calcoli corretti per il tuo caso specifico
            #print(np.min(algorithm.pop.get("F")[0, 1]))
            # self.costi.set('{:.3f}'.format(np.min(algorithm.pop.get("F")[:, 0])))  # Media della seconda colonna di F
            # self.batteria.set('{:.3f}'.format(np.min(algorithm.pop.get("F")[:, 0])))  # Media della terza colonna di F


    class MySampling(Sampling):

        def _do(self, problem, n_samples=24, **kwargs):
            X = np.full(pop_size, 1, dtype=object)
            
            
            for k in range(pop_size):
                dict={}
                for i in range(24):
                    dict[f"b{i}"] = sampling[k].X[f"b{i}"]
                    dict[f"i{i}"] = sampling[k].X[f"i{i}"]

                X[k] = dict

            return X
    
    class MyCallback(Callback):
        def __init__(self):
            super().__init__()
            self.data["costs"] = []
            self.data["battery_degradation"] = []
            self.data["co2_emissions"] = []

        def notify(self, algorithm):
            # Prendi i migliori individui in ogni generazione (popolazione attuale)
            F = algorithm.pop.get("F")
            # Trova l'individuo con il miglior valore rispetto ai 3 obiettivi
            self.data["costs"].append(np.min(np.linalg.norm(F, axis=0)))
            self.data["battery_degradation"].append(np.min(np.linalg.norm(F, axis=0)))
            self.data["co2_emissions"].append(np.min(np.linalg.norm(F, axis=0)))


    pool = ThreadPool(n_threads)
    runner = StarmapParallelization(pool.starmap)
    problem = MixedVariableProblem(elementwise_runner=runner)

    termination= DefaultMultiObjectiveTermination(xtol=0.001, n_max_gen=n_gen, n_skip=1, period=20)

    crossover = {
        Binary: UX(),
        Integer: SBX(vtype=float, repair=RoundingRepair()),
    }

    mutation = {
        Binary: BFM(),
        Integer: PM(vtype=float, repair=RoundingRepair()),
    }
    selection=RandomSelection()

    survival = RankAndCrowdingSurvival() #Da inserire come parametro la tipologia di crowding distance

    if sampling is None:
        algorithm = MixedVariableGA(pop_size=pop_size, survival=survival, mating=MixedVariableMating(crossover=crossover, mutation=mutation, selection=selection, n_max_iterations=100, eliminate_duplicates=None))
    else:
        algorithm = MixedVariableGA(pop_size=pop_size, sampling=MySampling(), survival=survival, mating=MixedVariableMating(crossover=crossover, mutation=mutation, selection=selection, n_max_iterations=100, eliminate_duplicates=None))
        
    callback = MyCallback()
    res = minimize(problem,
                   algorithm,
                   termination= termination, 
                   seed= random.randint(0, 99999),
                   verbose=verbose,
                   output=MyOutput(),
                   save_history=True,
                   callback = callback)
    
    pool.close()
    pool.join()

    # best_cost_per_generation = np.array(callback.data["costs"])
    # best_battery_per_generation = np.array(callback.data["battery_degradation"])
    # best_co2_per_generation = np.array(callback.data["co2_emissions"])


    # generations = np.arange(1, len(best_cost_per_generation) + 1)
    # plt.figure(figsize=(10, 6))
    # plt.plot(generations, best_cost_per_generation, label="Cost")
    # plt.plot(generations, best_battery_per_generation, label="Battery Degradation")
    # plt.plot(generations, best_co2_per_generation, label="CO2 emissions")

    
    # plt.xlabel('Generazione')
    # plt.ylabel('Miglior valore (fitness)')
    # plt.title('Andamento del migliore risultato per generazione')
    # plt.legend(loc='best')
    # plt.grid(True)
    # plt.show()


    

    return res, res.history


def shifting_individuals(population):
    for individuo in population:
        for i in range(23):
            individuo.X[f"b{i}"] = individuo.X[f"b{i+1}"]
            individuo.X[f"i{i}"] = individuo.X[f"i{i+1}"]

        individuo.X["b23"] =  random.choice([True, False])
        individuo.X["i23"] = random.randint(0, 100)
    
    return population


def start_nsga2_genetic_algorithm(data, pop_size, n_gen, n_threads, sampling=None,verbose=False):
    class MixedVariableProblem(ElementwiseProblem):

        def __init__(self, n_couples=24, **kwargs):
            super().__init__(
            n_var=48,  
            n_obj=3,   
            n_constr=0, 
            xl=np.array([0 if i % 2 == 0 else 0 for i in range(48)]),  
            xu=np.array([1 if i % 2 == 0 else 100 for i in range(48)])  
            )


        def _evaluate(self, X, out, *args, **kwargs):

            sum = 0                                                         #variabile che viene usata come contenitore per determinare l'andamento della stringa nel corso della valutazione
            delta_production = data["difference_of_production"]             #variabile che mi dice quantitativamente se la produzione di energia supera il consumo e viceversa
            sold = data["sold"]                                             #variabile che mi dice il prezzo della vendita dell'energia
            actual_percentage = [float(data["socs"])]                          #viene memorizzato l'attuale livello della batteria
            quantity_battery=0
            co2_emissions=0
            percentage_production_not_renewable = data["production_not_rs"]
            penality_sum = 1
            penality_batt = 1
            cycles = data["cycles"]
            battery_capacity = round(data["polynomial"](cycles) * data["battery_nominal_capacity"], 4)
            boolean_vars = [round(X[i]) for i in range(0, 48, 2)]  
            integer_vars = [round(X[i]) for i in range(1, 48, 2)]

            for j in range(24):                                             #Viene eseguita una predizione per le successive 24 ore         
                charge = boolean_vars[j]
                percentage = integer_vars[j]

                
                upper_limit = (data["soc_max"] * battery_capacity)      #una batteria ha una certa capacità, dai parametri di configurazione si capisce fino a quando l'utente vuole che si carichi
                lower_limit = (data["soc_min"] * battery_capacity)      #una batteria ha una certa capacità, dai parametri di configurazione si capisce fino a quando l'utente vuole che si scarichi

                effettivo_in_batteria=lower_limit+(actual_percentage[j]*(upper_limit-lower_limit))

                #Caso in cui si sceglie di caricare la batteria
                if charge:                                                  

                    posso_caricare_di = upper_limit - effettivo_in_batteria

                    #Viene calcolato di quanto caricare la batteria
                    quantity_charging_battery = ((posso_caricare_di * percentage) / 100) / data["battery_charging_efficiency"]

                    if quantity_charging_battery - delta_production.iloc[j] < 0:
                        ratio = min((data["estimate"]["consumo"].values[j] + quantity_charging_battery - (quantity_charging_battery - delta_production.iloc[j])) / data["inverter_nominal_power"],1)
                    else:
                        ratio = min((data["estimate"]["consumo"].values[j] + quantity_charging_battery) / data["inverter_nominal_power"], 1)


                    #Si controlla che la carica della batteria non sia maggiore di quella fisicamente ottenibile
                    if(quantity_charging_battery > data["maximum_power_battery_exchange"]):
                        penality_batt = penality_batt + (1 -  data["maximum_power_battery_exchange"] / quantity_charging_battery)

                    if(quantity_charging_battery > data["maximum_power_absorption"]):      
                        penality_sum = penality_sum + (1 -  data["maximum_power_absorption"] / quantity_charging_battery)
                    

                    delta_production.iloc[j] = data["expected_production"]["production"][j] * data["polynomial_inverter"](ratio) - data["estimate"]["consumo"].values[j]
                    #Viene controllata se la produzione dei pannelli è maggiore del consumo domestico unito al consumo della carica della batteria
                    if quantity_charging_battery - delta_production.iloc[j] < 0:

                        if data["estimate"]["consumo"].values[j] + quantity_charging_battery + (quantity_charging_battery - delta_production.iloc[j]) > data["inverter_nominal_power"]:
                            penality_batt = penality_batt + (1 - data["inverter_nominal_power"]/(data["estimate"]["consumo"].values[j] + quantity_charging_battery + (quantity_charging_battery - delta_production.iloc[j])))
                        
                        #Il surplus di energia viene venduto
                        sum = sum + ((quantity_charging_battery - delta_production.iloc[j]) * sold)/penality_sum  # sum = sum - rimborso


                    #Caso in cui viene prodotto meno di quanto si consuma, di conseguenza è necessario acquistare dalla rete
                    else:
                        
                        quantity_bought_from_not_renewable_sources =  ((quantity_charging_battery - delta_production.iloc[j])) * percentage_production_not_renewable["Difference"][j]
                        co2_emissions = co2_emissions + (quantity_bought_from_not_renewable_sources * data["coal_percentage"] * data["coal_pollution"]) + (quantity_bought_from_not_renewable_sources * data["gas_percentage"] * data["gas_pollution"]) + (quantity_bought_from_not_renewable_sources * data["oil_percentage"] * data["oil_pollution"]) * penality_sum


                        if data["estimate"]["consumo"].values[j] + quantity_charging_battery > data["inverter_nominal_power"]:
                            penality_batt = penality_batt + (1 - data["inverter_nominal_power"]/(data["estimate"]["consumo"].values[j] + quantity_charging_battery))

                        #Viene fatto un controllo che NON permette di acquistare più energia di quanto il contratto stipulato dall'utente permetta
                        if( quantity_charging_battery > data["maximum_power_absorption"] + delta_production.iloc[j]):
                            penality_sum = penality_sum + (1 -  data["maximum_power_absorption"] / quantity_charging_battery)

                        #Viene acquistata energia
                        sum = sum + ((quantity_charging_battery - delta_production.iloc[j])) * data["prices"]["prezzo"].iloc[j]*penality_sum
                    
                    actual_percentage.append((effettivo_in_batteria + (quantity_charging_battery*data["battery_charging_efficiency"]) - lower_limit) / ( upper_limit - lower_limit))
                    
                    
                #Caso in cui si sceglie di scaricare la batteria
                else:

                    #Viene calcolato di quanto scaricare la batteria
                    posso_scaricare_di=effettivo_in_batteria-lower_limit
                    quantity_discharging_battery=((posso_scaricare_di*percentage)/100)*data["battery_discharging_efficiency"]

                                  
                    if delta_production.iloc[j] + quantity_discharging_battery > 0:
                        ratio = min((data["estimate"]["consumo"].values[j] + (delta_production.iloc[j] + quantity_discharging_battery)) / data["inverter_nominal_power"], 1)
                    else:
                        ratio = min(data["estimate"]["consumo"].values[j] / data["inverter_nominal_power"], 1)

                    quantity_discharging_battery = quantity_discharging_battery * data["polynomial_inverter"](ratio)


                    #Si controlla che la scarica della batteria non sia maggiore di quella fisicamente ottenibile
                    if(quantity_discharging_battery > data["maximum_power_battery_exchange"]):
                        penality_batt = penality_batt + (1 -  data["maximum_power_battery_exchange"] / quantity_discharging_battery)
                    
                    if(quantity_discharging_battery > data["maximum_power_absorption"]):
                        penality_sum = penality_sum + (1 -  data["maximum_power_absorption"] / quantity_discharging_battery)


                    delta_production.iloc[j] = data["expected_production"]["production"][j] * data["polynomial_inverter"](ratio) - data["estimate"]["consumo"].values[j]
                    #Si controlla se si produce di più di quanto si consuma. Prendere energia dalla batteria viene considerata produzione
                    if delta_production.iloc[j] + quantity_discharging_battery > 0:

                        if data["estimate"]["consumo"].values[j] + (delta_production.iloc[j] + quantity_discharging_battery) > data["inverter_nominal_power"]:
                            penality_batt = penality_batt + (1 - data["inverter_nominal_power"]/(data["estimate"]["consumo"].values[j] + (delta_production.iloc[j] + quantity_discharging_battery)))
                            penality_sum = penality_sum + (1 - data["inverter_nominal_power"]/(data["estimate"]["consumo"].values[j] + (delta_production.iloc[j] + quantity_discharging_battery)))

                        #Si controlla di non prendere più energia dalla batteria di quanto il contatore sia in grado di gestire
                        if(quantity_discharging_battery + delta_production.iloc[j] > data["maximum_power_absorption"]):
                            penality_sum = penality_sum + (1 -  data["maximum_power_absorption"] / quantity_discharging_battery)

                     #Produco di più di quanto consumo, vendo il resto
                        sum = sum - ((delta_production.iloc[j] + quantity_discharging_battery) * sold)/penality_sum

                    #Produco poco e consumo di più
                    else:
                        quantity_bought_from_not_renewable_sources = (- (delta_production.iloc[j] + quantity_discharging_battery)) * percentage_production_not_renewable["Difference"][j]
                        co2_emissions = co2_emissions + (quantity_bought_from_not_renewable_sources * data["coal_percentage"] * data["coal_pollution"]) + (quantity_bought_from_not_renewable_sources * data["gas_percentage"] * data["gas_pollution"]) + (quantity_bought_from_not_renewable_sources * data["oil_percentage"] * data["oil_pollution"]) * penality_sum

                        if data["estimate"]["consumo"].values[j] > data["inverter_nominal_power"]:
                            penality_batt = penality_batt + (1 - data["inverter_nominal_power"]/(data["estimate"]["consumo"].values[j]))
                            penality_sum = penality_sum * (1 - data["inverter_nominal_power"]/(data["estimate"]["consumo"].values[j]))                    
                        
                        #Produco di meno di quanto consumo, compro il resto
                        sum = sum + (- (delta_production.iloc[j] + quantity_discharging_battery/data["battery_discharging_efficiency"]) *
                                     data["prices"]["prezzo"].iloc[j])*penality_sum


                    scarico=(posso_scaricare_di*percentage)/100
                    cycles = round(cycles+(scarico/battery_capacity), 5)
                    battery_capacity = round(data["polynomial"](cycles) * data["battery_nominal_capacity"], 4)

                    #Viene aggiornato il valore della batteria, dopo la scarica
                    actual_percentage.append((effettivo_in_batteria - (quantity_discharging_battery/data["battery_discharging_efficiency"]) - lower_limit) / ( upper_limit - lower_limit))
                    quantity_battery+=abs(quantity_discharging_battery) * penality_batt
            #Terminata la simulazione, viene attribuito un voto alla stringa in input, dato da tre fattori:
            # - Il costo
            # - L'utilizzo della batteria
            # - Emissioni CO2

            out["F"] = [sum, quantity_battery, co2_emissions]
            


    class MySampling(Sampling):

        def _do(self, problem, n_samples=24, **kwargs):
            X = np.full(pop_size, 1, dtype=object)
            
            
            for k in range(pop_size):
                individuo = np.full(48, 1.5, dtype=float)
                for i in range(48):
                    individuo[i] = sampling[k].X[i]

                X[k] = individuo

            return X
    
    class MyCallback(Callback):
        def __init__(self):
            super().__init__()
            self.data["costs"] = []
            self.data["battery_degradation"] = []
            self.data["co2_emissions"] = []

        def notify(self, algorithm):
            # Prendi i migliori individui in ogni generazione (popolazione attuale)
            F = algorithm.pop.get("F")
            # Trova l'individuo con il miglior valore rispetto ai 3 obiettivi
            self.data["costs"].append(np.min(np.linalg.norm(F, axis=0)))
            self.data["battery_degradation"].append(np.min(np.linalg.norm(F, axis=0)))
            self.data["co2_emissions"].append(np.min(np.linalg.norm(F, axis=0)))


    pool = ThreadPool(n_threads)
    runner = StarmapParallelization(pool.starmap)
    problem = MixedVariableProblem(elementwise_runner=runner)

    termination= DefaultMultiObjectiveTermination(xtol=0.001, n_max_gen=n_gen, n_skip=1, period=20)

    selection=TournamentSelection(func_comp=binary_tournament)
    crossover=SBX(eta=15, prob=0.9)
    mutation=PM(eta=20)
    survival=RankAndCrowding()

    if sampling is None:
        algorithm = NSGA2(pop_size, survival=survival, selection=selection, crossover=crossover, mutation=mutation)
    else:
        algorithm = NSGA2(pop_size, sampling=MySampling(), survival=survival, selection=selection, crossover=crossover, mutation=mutation)
        
    callback = MyCallback()
    res = minimize(problem,
                   algorithm,
                   termination= termination, 
                   seed= random.randint(0, 99999),
                   verbose=verbose,
                   save_history=True,
                   callback = callback)
    
    pool.close()
    pool.join()


    return res, res.history


def shifting_nsga2_individuals(population):
    for individuo in population:
        for i in range(0,46, 2):
            individuo.X[i] = individuo.X[i+2]
            individuo.X[i+1] = individuo.X[i+3]

        individuo.X[46] =  random.choice([True, False])
        individuo.X[47] = random.randint(0, 100)
        
    return population
