from functions import *


import numpy as np
from multiprocessing.pool import ThreadPool
from pymoo.core.problem import StarmapParallelization
from pymoo.core.mixed import MixedVariableGA
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

#Capacità della batteria
#

def evaluate(data, variables_values, cycles, polynomial):
    sum = []
    sum.append(0)
    co2_emissions = []
    co2_emissions.append(0)
    sold = data["sold"]
    
    actual_percentage = []
    actual_percentage.append(variables_values["first_battery_value"])

    
    quantity_delta_battery = []

    # valori negativi indicano consumi ,positivi guadagni
    for j in range(24):
        charge = variables_values[f"b{j}"]
        percentage = variables_values[f"i{j}"]
        quantity_charging_battery = None
        quantity_discharging_battery = None

        battery_capacity = round(polynomial(cycles) * variables_values["battery_nominal_capacity"], 4)
        upper_limit = (data["soc_max"] * battery_capacity)
        lower_limit = (data["soc_min"] * battery_capacity)
        effettivo_in_batteria=lower_limit+(actual_percentage[j]*(upper_limit-lower_limit))

        if charge:

            posso_caricare_di = upper_limit - effettivo_in_batteria

            #Viene calcolato di quanto caricare la batteria
            quantity_charging_battery = ((posso_caricare_di * percentage) / 100) / data["battery_charging_efficiency"]
            
            if quantity_charging_battery - variables_values[f"difference_of_production{j}"] < 0:
                # devo vendere
                co2_emissions.append( co2_emissions[j] )
                sum.append(
                    sum[j] + ((quantity_charging_battery - variables_values[f"difference_of_production{j}"]) * sold))  # sum = sum - rimborso
            else:
                co2_emissions.append(co2_emissions[j] + co2_quantity_emission(data, variables_values, -(quantity_charging_battery - variables_values[f"difference_of_production{j}"]), j))
                
                sum.append(
                    sum[j] + (quantity_charging_battery - variables_values[f"difference_of_production{j}"]) * variables_values[f"prices{j}"])
                
            actual_percentage.append((effettivo_in_batteria + quantity_charging_battery - lower_limit) / ( upper_limit - lower_limit))
            
        else:
            
            posso_scaricare_di=effettivo_in_batteria-lower_limit
            quantity_discharging_battery=((posso_scaricare_di*percentage)/100)*data["battery_discharging_efficiency"]

            if variables_values[f"difference_of_production{j}"] + quantity_discharging_battery > 0:
                co2_emissions.append( co2_emissions[j] )
                sum.append(sum[j] - ((variables_values[f"difference_of_production{j}"] + quantity_discharging_battery) * sold))

            else:
                
                co2_emissions.append(co2_emissions[j] + co2_quantity_emission(data, variables_values, variables_values[f"difference_of_production{j}"] + quantity_discharging_battery/data["battery_discharging_efficiency"], j))

                sum.append(sum[j] + (
                        - (variables_values[f"difference_of_production{j}"] + quantity_discharging_battery/data["battery_discharging_efficiency"]) * variables_values[f"prices{j}"]))
            
            
            scarico=(posso_scaricare_di*percentage)/100
            cycles = round(cycles+(scarico/battery_capacity), 5)
            actual_percentage.append((effettivo_in_batteria - (quantity_discharging_battery/data["battery_discharging_efficiency"]) - lower_limit) / ( upper_limit - lower_limit))

        
        if quantity_charging_battery != None:
            quantity_delta_battery.append(+quantity_charging_battery)
        else:
            quantity_delta_battery.append(-quantity_discharging_battery)

    return sum[1:], actual_percentage, quantity_delta_battery, co2_emissions[1:]


def start_genetic_algorithm(data, pop_size, n_gen, n_threads, sampling=None,verbose=False):
    class MixedVariableProblem(ElementwiseProblem):

        def __init__(self, n_couples=24, **kwargs):
            variables = {}
            for j in range(n_couples):
                variables[f"b{j}"] = Binary()
                variables[f"i{j}"] = Integer(bounds=(0, 100))
            super().__init__(vars=variables, n_obj=3, n_ieq_constr=0, **kwargs)

        def lower():
            return "mixedvariableproblem"

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
            upper_limit = (data["soc_max"] * data["battery_capacity"])      #una batteria ha una certa capacità, dai parametri di configurazione si capisce fino a quando l'utente vuole che si carichi
            lower_limit = (data["soc_min"] * data["battery_capacity"])      #una batteria ha una certa capacità, dai parametri di configurazione si capisce fino a quando l'utente vuole che si scarichi
            actual_percentage = [float(data["socs"])]                          #viene memorizzato l'attuale livello della batteria
            quantity_battery=0
            co2_emissions=0
            percentage_production_not_renewable = data["production_not_rs"]
            penality_sum = 1
            penality_batt = 1
            

            for j in range(24):                                             #Viene eseguita una predizione per le successive 24 ore         
                charge = X[f"b{j}"]
                percentage = X[f"i{j}"]

                effettivo_in_batteria=lower_limit+(actual_percentage[j]*(upper_limit-lower_limit))

                #Caso in cui si sceglie di caricare la batteria
                if charge:                                                  

                    posso_caricare_di = upper_limit - effettivo_in_batteria

                    #Viene calcolato di quanto caricare la batteria
                    quantity_charging_battery = ((posso_caricare_di * percentage) / 100) / data["battery_charging_efficiency"]


                    #Si controlla che la carica della batteria non sia maggiore di quella fisicamente ottenibile
                    if(quantity_charging_battery > data["maximum_power_battery_exchange"]):
                        penality_batt = penality_batt + (1 -  data["maximum_power_battery_exchange"] / quantity_charging_battery)

                    if(quantity_charging_battery > data["maximum_power_absorption"]):
                        penality_sum = penality_sum + (1 -  data["maximum_power_absorption"] / quantity_charging_battery)
                    


                    #Viene controllata se la produzione dei pannelli è maggiore del consumo domestico unito al consumo della carica della batteria
                    if quantity_charging_battery - delta_production.iloc[j] < 0:
                        
                        #Il surplus di energia viene venduto
                        sum = sum + ((quantity_charging_battery - delta_production.iloc[j]) * sold)/penality_sum  # sum = sum - rimborso


                    #Caso in cui viene prodotto meno di quanto si consuma, di conseguenza è necessario acquistare dalla rete
                    else:
                        
                        quantity_bought_from_not_renewable_sources =  (quantity_charging_battery - delta_production.iloc[j]) * percentage_production_not_renewable["Difference"][j]
                        co2_emissions += (quantity_bought_from_not_renewable_sources * data["coal_percentage"] * data["coal_pollution"]) + (quantity_bought_from_not_renewable_sources * data["gas_percentage"] * data["gas_pollution"]) + (quantity_bought_from_not_renewable_sources * data["oil_percentage"] * data["oil_pollution"])


                        #Viene fatto un controllo che NON permette di acquistare più energia di quanto il contratto stipulato dall'utente permetta
                        if( quantity_charging_battery > data["maximum_power_absorption"] + delta_production.iloc[j]):
                            penality_sum = penality_sum + (1 -  data["maximum_power_absorption"] / quantity_charging_battery)

                        #Viene acquistata energia
                        sum = sum + (quantity_charging_battery - delta_production.iloc[j]) * data["prices"]["prezzo"].iloc[j]*penality_sum
                    
                    actual_percentage.append((effettivo_in_batteria + quantity_charging_battery - lower_limit) / ( upper_limit - lower_limit))
                    
                    
                #Caso in cui si sceglie di scaricare la batteria
                else:

                    #Viene calcolato di quanto scaricare la batteria
                    posso_scaricare_di=effettivo_in_batteria-lower_limit
                    quantity_discharging_battery=((posso_scaricare_di*percentage)/100)*data["battery_discharging_efficiency"]              


                    #Si controlla che la scarica della batteria non sia maggiore di quella fisicamente ottenibile
                    if(quantity_discharging_battery > data["maximum_power_battery_exchange"]):
                        penality_batt = penality_batt + (1 -  data["maximum_power_battery_exchange"] / quantity_discharging_battery)
                    
                    if(quantity_discharging_battery > data["maximum_power_absorption"]):
                        penality_sum = penality_sum + (1 -  data["maximum_power_absorption"] / quantity_discharging_battery)

                    #Si controlla se si produce di più di quanto si consuma. Prendere energia dalla batteria viene considerata produzione
                    if delta_production.iloc[j] + quantity_discharging_battery > 0:

                        #Si controlla di non prendere più energia dalla batteria di quanto il contatore sia in grado di gestire
                        if(quantity_discharging_battery + delta_production.iloc[j] > data["maximum_power_absorption"]):
                            penality_sum = penality_sum + (1 -  data["maximum_power_absorption"] / quantity_discharging_battery)

                     #Produco di più di quanto consumo, vendo il resto
                        sum = sum - ((delta_production.iloc[j] + quantity_discharging_battery) * sold)/penality_sum

                    #Produco poco e consumo di più
                    else:
                        quantity_bought_from_not_renewable_sources = (- (delta_production.iloc[j] + quantity_discharging_battery)) * percentage_production_not_renewable["Difference"][j]
                        co2_emissions += (quantity_bought_from_not_renewable_sources * data["coal_percentage"] * data["coal_pollution"]) + (quantity_bought_from_not_renewable_sources * data["gas_percentage"] * data["gas_pollution"]) + (quantity_bought_from_not_renewable_sources * data["oil_percentage"] * data["oil_pollution"])

                        #Produco di meno di quanto consumo, compro il resto
                        sum = sum + (- (delta_production.iloc[j] + quantity_discharging_battery/data["battery_discharging_efficiency"]) *
                                     data["prices"]["prezzo"].iloc[j])*penality_sum


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
            # self.batteria = Column("batteria", width=8)
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



    pool = ThreadPool(n_threads)
    runner = StarmapParallelization(pool.starmap)
    problem = MixedVariableProblem(elementwise_runner=runner)

    termination= DefaultMultiObjectiveTermination(xtol=0.001, n_max_gen=n_gen, n_skip=1, period=20)

    if sampling is None:
        algorithm = MixedVariableGA(pop_size, survival=RankAndCrowdingSurvival())
    else:
        algorithm = MixedVariableGA(pop_size, sampling=MySampling(), survival=RankAndCrowdingSurvival())
        

    res = minimize(problem,
                   algorithm,
                   termination= termination, 
                   seed= random.randint(0, 99999),
                   verbose=verbose,
                   output=MyOutput(),
                   save_history=True)
    
    pool.close()
    pool.join()



    # plot = Scatter()
    # plot.add(res.F, facecolor="none", edgecolor="red")
    # plot.show()

    return res, res.history


def shifting_individuals(population):
    for individuo in population:
        for i in range(23):
            individuo.X[f"b{i}"] = individuo.X[f"b{i+1}"]
            individuo.X[f"i{i}"] = individuo.X[f"i{i+1}"]

        individuo.X["b23"] =  random.choice([True, False])
        individuo.X["i23"] = random.randint(0, 100)
    
    return population