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
from pymoo.core.sampling import Sampling
from pymoo.operators.selection.tournament import TournamentSelection
from pymoo.core.crossover import Crossover
from pymoo.algorithms.soo.nonconvex.ga import FitnessSurvival, comp_by_cv_and_fitness
from pymoo.operators.mutation.bitflip import BFM
from pymoo.operators.repair.rounding import RoundingRepair
from pymoo.operators.mutation.pm import PM
from pymoo.core.selection import Selection
from pymoo.util.misc import random_permuations
import math


def evaluate(data, variables_values,cycles,polynomial_batt):
    sum = []
    sum.append(0)
    sold = data["sold"]
    
    actual_percentage = []
    actual_percentage.append(variables_values["first_battery_value"])
    co2_emissions = []
    co2_emissions.append(0)
    battery_capacity = round(polynomial_batt(cycles) * variables_values["battery_nominal_capacity"], 4)

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
            #aggiungo eff di 0.9 in carica e scarica ma comunque lo pago!   
            posso_caricare_di = upper_limit - effettivo_in_batteria 

            
            quantity_charging_battery = ((posso_caricare_di* percentage) / 100)/data["battery_charging_efficiency"]
            
            if quantity_charging_battery - variables_values[f"difference_of_production{j}"] < 0:
                ratio = min((variables_values[f"load{j}"] + quantity_charging_battery - (quantity_charging_battery - variables_values[f"difference_of_production{j}"])) / data["inverter_nominal_power"],1)
            else:
                ratio = min((variables_values[f"load{j}"] + quantity_charging_battery) / data["inverter_nominal_power"], 1)

            variables_values[f"difference_of_production{j}"] = variables_values[f"production{j}"] * data["polynomial_inverter"](ratio) - variables_values[f"load{j}"]
            if quantity_charging_battery - variables_values[f"difference_of_production{j}"] < 0:
                # devo vendere
                co2_emissions.append(co2_emissions[j])

                sum.append(
                    sum[j] + ((quantity_charging_battery - variables_values[f"difference_of_production{j}"]) * sold))  # sum = sum - rimborso
            else:
                co2_emissions.append(co2_emissions[j] + co2_quantity_emission(data, variables_values, -((quantity_charging_battery - variables_values[f"difference_of_production{j}"])/data["polynomial_inverter"](ratio)), j))
                
                sum.append(
                    sum[j] + ((quantity_charging_battery - variables_values[f"difference_of_production{j}"])) * variables_values[f"prices{j}"])
            
            actual_percentage.append((effettivo_in_batteria + (quantity_charging_battery*data["battery_charging_efficiency"]) - lower_limit) / ( upper_limit - lower_limit))
            
        else:
            #aggiungo eff di 0.9 in carica e scarica ma comunque lo pago!    
            posso_scaricare_di=(effettivo_in_batteria-lower_limit)
            quantity_discharging_battery=((posso_scaricare_di*percentage)/100)*data["battery_discharging_efficiency"]
           
            if variables_values[f"difference_of_production{j}"] + quantity_discharging_battery > 0:
                ratio = min((variables_values[f"load{j}"] + (variables_values[f"difference_of_production{j}"] + quantity_discharging_battery)) / data["inverter_nominal_power"], 1)
            else:
                ratio = min(variables_values[f"load{j}"] / data["inverter_nominal_power"], 1)

            quantity_discharging_battery = quantity_discharging_battery * data["polynomial_inverter"](ratio)

            variables_values[f"difference_of_production{j}"] = variables_values[f"production{j}"] * data["polynomial_inverter"](ratio) - variables_values[f"load{j}"]
            if variables_values[f"difference_of_production{j}"] + quantity_discharging_battery > 0:
                
                co2_emissions.append(co2_emissions[j])             
                sum.append(sum[j] - ((variables_values[f"difference_of_production{j}"] + quantity_discharging_battery) * sold))

            else:
                co2_emissions.append(co2_emissions[j] + co2_quantity_emission(data, variables_values, (variables_values[f"difference_of_production{j}"] + quantity_discharging_battery/data["battery_discharging_efficiency"])/data["polynomial_inverter"](ratio), j))

                sum.append(sum[j] + (
                        - ((variables_values[f"difference_of_production{j}"] + quantity_discharging_battery/data["battery_discharging_efficiency"])) * variables_values[f"prices{j}"]))
            
            
            scarico=(posso_scaricare_di*percentage)/100
            cycles = round(cycles+(scarico/battery_capacity), 5)
            battery_capacity = round(polynomial_batt(cycles) * variables_values["battery_nominal_capacity"], 4)
            actual_percentage.append((effettivo_in_batteria - (quantity_discharging_battery/data["battery_discharging_efficiency"]) - lower_limit) / ( upper_limit - lower_limit))


        ratio_list.append(ratio)

        if quantity_charging_battery != None:
            quantity_delta_battery.append(+quantity_charging_battery)
        else:
            quantity_delta_battery.append(-quantity_discharging_battery)

    return sum[1:], actual_percentage, quantity_delta_battery, co2_emissions[1:],ratio_list


def start_genetic_algorithm(data, pop_size, n_gen, n_threads,prob_mut_bit =0.2,prob_mut_pm=0.8, sampling=None,verbose=False):
    class MixedVariableProblem(ElementwiseProblem):

        def __init__(self, n_couples=24, **kwargs):
            variables = {}
            for j in range(n_couples):
                variables[f"b{j}"] = Binary()
                variables[f"i{j}"] = Integer(bounds=(0, 100))
            super().__init__(vars=variables, n_obj=1, **kwargs)

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
            penality_sum = 1
            penality_batt = 1
            cycles = data["cycles"]
            battery_capacity = round(data["polynomial"](cycles) * data["battery_nominal_capacity"], 4)

            co2_emissions=0
            percentage_production_not_renewable = data["production_not_rs"]

            for j in range(24):                                             #Viene eseguita una predizione per le successive 24 ore         
                charge = X[f"b{j}"]
                percentage = X[f"i{j}"]
                
                upper_limit = (data["soc_max"] * battery_capacity)      #una batteria ha una certa capacità, dai parametri di configurazione si capisce fino a quando l'utente vuole che si carichi
                lower_limit = (data["soc_min"] * battery_capacity)      #una batteria ha una certa capacità, dai parametri di configurazione si capisce fino a quando l'utente vuole che si scarichi

                effettivo_in_batteria=lower_limit+(actual_percentage[j]*(upper_limit-lower_limit))

                #Caso in cui si sceglie di caricare la batteria
                if charge:                                                  

                    #Viene calcolato di quanto caricare la batteria
                    posso_caricare_di = upper_limit - effettivo_in_batteria 
                    #potrei sforare e caricare di più
                    quantity_charging_battery = ((posso_caricare_di * percentage) / 100)/data["battery_charging_efficiency"]
                    
                    if quantity_charging_battery - delta_production.iloc[j] < 0:
                        ratio = min((data["estimate"]["consumo"].values[j] + quantity_charging_battery - (quantity_charging_battery - delta_production.iloc[j])) / data["inverter_nominal_power"],1)
                    else:
                        ratio = min((data["estimate"]["consumo"].values[j] + quantity_charging_battery) / data["inverter_nominal_power"], 1)



                    #Si controlla che la carica della batteria non sia maggiore di quella fisicamente ottenibile
                    if(quantity_charging_battery > data["maximum_power_battery_exchange"]):
                        penality_batt = penality_batt + (2 -  data["maximum_power_battery_exchange"] / quantity_charging_battery)

                    if(quantity_charging_battery > data["maximum_power_absorption"]):
                        #più+ grave di sopra ma in teoria scattano entrambi
                        penality_sum = penality_sum + (2 -  data["maximum_power_absorption"] / quantity_charging_battery)

                    delta_production.iloc[j] = data["expected_production"]["production"][j] * data["polynomial_inverter"](ratio) - data["estimate"]["consumo"].values[j]

                    #Viene controllata se la produzione dei pannelli è maggiore del consumo domestico unito al consumo della carica della batteria
                    if quantity_charging_battery - delta_production.iloc[j] < 0:
                        
                        if data["estimate"]["consumo"].values[j] + quantity_charging_battery + (quantity_charging_battery - delta_production.iloc[j]) > data["inverter_nominal_power"]:
                            penality_batt = penality_batt + (2 - data["inverter_nominal_power"]/(data["estimate"]["consumo"].values[j] + quantity_charging_battery + (quantity_charging_battery - delta_production.iloc[j])))
                        
                        #Il surplus di energia viene venduto
                        sum =  sum + ((quantity_charging_battery - delta_production.iloc[j]) * sold)/penality_sum  # sum = sum - rimborso


                    #Caso in cui viene prodotto meno di quanto si consuma, di conseguenza è necessario acquistare dalla rete
                    else:

                        if data["estimate"]["consumo"].values[j] + quantity_charging_battery > data["inverter_nominal_power"]:
                            penality_batt = penality_batt + (2 - data["inverter_nominal_power"]/(data["estimate"]["consumo"].values[j] + quantity_charging_battery))
                       
                        #Viene fatto un controllo che NON permette di acquistare più energia di quanto il contratto stipulato dall'utente permetta
                        if( quantity_charging_battery > data["maximum_power_absorption"] + delta_production.iloc[j]):
                            penality_sum = penality_sum + (2 -  data["maximum_power_absorption"] / quantity_charging_battery)
                        #Viene acquistata energia

                        co2_emissions = co2_emissions + co2_quantity_emission_algo(data,percentage_production_not_renewable["Difference"][j] ,-(quantity_charging_battery - delta_production.iloc[j]))

                        sum = sum + (quantity_charging_battery - delta_production.iloc[j]) * data["prices"]["prezzo"].iloc[j] * penality_sum

                
                    #Viene aggiornato il valore di carica della batteria, essendo stata caricata
                    quantity_battery-=abs(quantity_charging_battery*0.3)
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
                        penality_batt = penality_batt + (2 -  data["maximum_power_battery_exchange"] / quantity_discharging_battery)

                    if(quantity_discharging_battery > data["maximum_power_absorption"]):
                        penality_sum = penality_sum + (2 -  data["maximum_power_absorption"] / quantity_discharging_battery)
                    
                    delta_production.iloc[j] = data["expected_production"]["production"][j] * data["polynomial_inverter"](ratio) - data["estimate"]["consumo"].values[j]

                    #Si controlla se si produce di più di quanto si consuma. Prendere energia dalla batteria viene considerata produzione
                    if delta_production.iloc[j] + quantity_discharging_battery > 0:
                      
                        if data["estimate"]["consumo"].values[j] + (delta_production.iloc[j] + quantity_discharging_battery) > data["inverter_nominal_power"]:
                            penality_batt = penality_batt + (2 - data["inverter_nominal_power"]/(data["estimate"]["consumo"].values[j] + (delta_production.iloc[j] + quantity_discharging_battery)))
                            penality_sum = penality_sum + (2 - data["inverter_nominal_power"]/(data["estimate"]["consumo"].values[j] + (delta_production.iloc[j] + quantity_discharging_battery)))                        
                        
                        #Si controlla di non prendere più energia dalla batteria di quanto il contatore sia in grado di gestire
                        if(quantity_discharging_battery + delta_production.iloc[j] > data["maximum_power_absorption"]):
                            penality_sum = penality_sum + (2 -  data["maximum_power_absorption"] / quantity_discharging_battery)

                        #Produco di più di quanto consumo, vendo il resto
                        sum = sum - ((delta_production.iloc[j] + quantity_discharging_battery) * sold) / penality_sum

                    #Produco poco e consumo di più
                    else:
                        co2_emissions = co2_emissions + + co2_quantity_emission_algo(data,percentage_production_not_renewable["Difference"][j] ,(delta_production.iloc[j] + quantity_discharging_battery/data["battery_discharging_efficiency"]))
                        
                        if data["estimate"]["consumo"].values[j] > data["inverter_nominal_power"]:
                            penality_batt = penality_batt + (2 - data["inverter_nominal_power"]/(data["estimate"]["consumo"].values[j]))
                            penality_sum = penality_sum * (2 - data["inverter_nominal_power"]/(data["estimate"]["consumo"].values[j]))                    
                                                                        
                        #Produco di meno di quanto consumo, compro il resto
                        sum = sum + (- (delta_production.iloc[j] + quantity_discharging_battery/data["battery_discharging_efficiency"]) *
                                     data["prices"]["prezzo"].iloc[j]) * penality_sum


                    scarico=(posso_scaricare_di*percentage)/100
                    cycles = round(cycles+(scarico/battery_capacity), 5)
                    battery_capacity = round(data["polynomial"](cycles) * data["battery_nominal_capacity"], 4)

                    #Viene aggiornato il valore della batteria, dopo la scarica
                    actual_percentage.append((effettivo_in_batteria - (quantity_discharging_battery/data["battery_discharging_efficiency"]) - lower_limit) / ( upper_limit - lower_limit))
                    quantity_battery+=abs(quantity_discharging_battery*0.76)


            #costo batteria divisp num cicli = 2 euro
            #coeff= 0.77
            coeff= 1.3
            cost= ((quantity_battery/data["battery_capacity"])*coeff) * penality_batt
            #Terminata la simulazione, viene attribuito un voto alla stringa in input, dato da due fattori:
            # - Il costo
            # - L'utilizzo della batteria, al quale è stato attribuito un costo
            co2_cost = co2_emissions * 0.0003
            out["F"] = sum + cost + co2_cost


    class MyOutput(Output):

        def __init__(self):
            super().__init__()
            self.f_min = Column("score", width=8)
            self.columns += [self.f_min]

        def update(self, algorithm):
            super().update(algorithm)
            self.f_min.set('{:.3F}'.format(-np.min(algorithm.pop.get("F"))))


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

    survival = FitnessSurvival() 
    selection = CustomTournamentSelection(func_comp=comp_by_cv_and_fitness)
    
    crossover = {
        Binary: CustomFourPointCrossover(),
        Integer: CustomFourPointCrossover()
    } 

    mutation = {
        Binary: BFM(prob_var=prob_mut_bit),
        Integer: PM(vtype=float, repair=RoundingRepair(), prob_var=prob_mut_pm, eta=20, at_least_once=False),
    }
    
    if sampling is None:
        algorithm = MixedVariableGA(pop_size, survival=survival, mating=MixedVariableMating(selection=selection, crossover=crossover, mutation=mutation, eliminate_duplicates=None))
    else:
        algorithm = MixedVariableGA(pop_size, sampling=MySampling(), survival=survival, mating=MixedVariableMating(selection=selection, crossover=crossover, mutation=mutation, eliminate_duplicates=None))
        
    res = minimize(problem,
                   algorithm,
                   termination= termination, 
                   seed=random.randint(0, 99999), #10
                   verbose=verbose,
                   output=MyOutput(),
                   save_history=True)
    
    pool.close()
    pool.join()

    return res, res.history


def shifting_individuals(population):
    for individuo in population:
        for i in range(23):
            individuo.X[f"b{i}"] = individuo.X[f"b{i+1}"]
            individuo.X[f"i{i}"] = individuo.X[f"i{i+1}"]

        individuo.X["b23"] =  random.choice([True, False])
        individuo.X["i23"] = random.randint(0, 100)
    
    return population


class CustomFourPointCrossover(Crossover):

    def __init__(self):
        super().__init__(2, 2)  # 2 genitori, 2 figli

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
    
class CustomTournamentSelection(Selection):
    """
      The Tournament selection is used to simulated a tournament between individuals. The pressure balances
      greedy the genetic algorithm will be.
    """

    def __init__(self, func_comp=None, pressure=2, **kwargs):
        """

        Parameters
        ----------
        func_comp: func
            The function to compare two individuals. It has the shape: comp(pop, indices) and returns the winner.
            If the function is None it is assumed the population is sorted by a criterium and only indices are compared.

        pressure: int
            The selection pressure to bie applied. Default it is a binary tournament.
        """

        super().__init__(**kwargs)

        # selection pressure to be applied
        self.pressure = pressure

        self.func_comp = func_comp
        if self.func_comp is None:
            raise Exception("Please provide the comparing function for the tournament selection!")

    def _do(self, _, pop, n_select, n_parents=1, **kwargs):
        # number of random individuals needed
        n_random = n_select * n_parents * self.pressure 


        # number of permutations needed
        n_perms = math.ceil(n_random / round(len(pop)*0.75))

        # get random permutations and reshape them
        P = random_permuations(n_perms, round(len(pop)*0.75))[:n_random]
        P = np.reshape(P, (n_select * n_parents, self.pressure))

        # compare using tournament function
        S = self.func_comp(pop, P, **kwargs)
        
        return np.reshape(S, (n_select, n_parents))