from functions import *
import numpy as np
from multiprocessing.pool import ThreadPool
from pymoo.core.problem import StarmapParallelization
from pymoo.core.problem import ElementwiseProblem
from pymoo.optimize import minimize
from pymoo.util.display.output import Output
from pymoo.util.display.column import Column
from pymoo.termination.default import DefaultSingleObjectiveTermination
from pymoo.core.sampling import Sampling
from pymoo.algorithms.soo.nonconvex.ga import GA
from pymoo.core.crossover import Crossover
from pymoo.core.variable import Real, get
from pymoo.operators.repair.bounds_repair import repair_clamp
from pymoo.algorithms.soo.nonconvex.ga import FitnessSurvival, comp_by_cv_and_fitness
from pymoo.operators.selection.tournament import  TournamentSelection
from pymoo.core.mutation import Mutation
from pymoo.core.selection import Selection
from pymoo.util.misc import random_permuations
import math



def start_GA_genetic_algorithm(data, pop_size, n_gen, n_threads,prob_cross = 0.5,prob_mut_bit = 0.5,prob_mut_int = 0.8, sampling=None,verbose=False):
    class MixedVariableProblem(ElementwiseProblem):

        def __init__(self, **kwargs):
            super().__init__(
                n_var=48,  
                n_obj=1,   
                n_constr=0, 
                xl=np.array([0 if i % 2 == 0 else 0 for i in range(48)]),  
                xu=np.array([1 if i % 2 == 0 else 100 for i in range(48)])  
            )

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
                        penality_batt = penality_batt + (1.5 -  data["maximum_power_battery_exchange"] / quantity_charging_battery)

                    if(quantity_charging_battery > data["maximum_power_absorption"]):
                        #più+ grave di sopra ma in teoria scattano entrambi
                        penality_sum = penality_sum + (1.5 -  data["maximum_power_absorption"] / quantity_charging_battery)

                    delta_production.iloc[j] = data["expected_production"]["production"][j] * data["polynomial_inverter"](ratio) - data["estimate"]["consumo"].values[j]

                    #Viene controllata se la produzione dei pannelli è maggiore del consumo domestico unito al consumo della carica della batteria
                    if quantity_charging_battery - delta_production.iloc[j] < 0:
                        
                        if data["estimate"]["consumo"].values[j] + quantity_charging_battery + (quantity_charging_battery - delta_production.iloc[j]) > data["inverter_nominal_power"]:
                            penality_batt = penality_batt + (1.5 - data["inverter_nominal_power"]/(data["estimate"]["consumo"].values[j] + quantity_charging_battery + (quantity_charging_battery - delta_production.iloc[j])))
                        
                        #Il surplus di energia viene venduto
                        sum =  sum + ((quantity_charging_battery - delta_production.iloc[j]) * sold)/penality_sum  # sum = sum - rimborso


                    #Caso in cui viene prodotto meno di quanto si consuma, di conseguenza è necessario acquistare dalla rete
                    else:

                        if data["estimate"]["consumo"].values[j] + quantity_charging_battery > data["inverter_nominal_power"]:
                            penality_batt = penality_batt + (1.5 - data["inverter_nominal_power"]/(data["estimate"]["consumo"].values[j] + quantity_charging_battery))
                       
                        #Viene fatto un controllo che NON permette di acquistare più energia di quanto il contratto stipulato dall'utente permetta
                        if( quantity_charging_battery > data["maximum_power_absorption"] + delta_production.iloc[j]):
                            penality_sum = penality_sum + (1.5 -  data["maximum_power_absorption"] / quantity_charging_battery)
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
                        penality_batt = penality_batt + (1.5 -  data["maximum_power_battery_exchange"] / quantity_discharging_battery)

                    if(quantity_discharging_battery > data["maximum_power_absorption"]):
                        penality_sum = penality_sum + (1.5 -  data["maximum_power_absorption"] / quantity_discharging_battery)
                    
                    delta_production.iloc[j] = data["expected_production"]["production"][j] * data["polynomial_inverter"](ratio) - data["estimate"]["consumo"].values[j]

                    #Si controlla se si produce di più di quanto si consuma. Prendere energia dalla batteria viene considerata produzione
                    if delta_production.iloc[j] + quantity_discharging_battery > 0:
                      
                        if data["estimate"]["consumo"].values[j] + (delta_production.iloc[j] + quantity_discharging_battery) > data["inverter_nominal_power"]:
                            penality_batt = penality_batt + (1.5 - data["inverter_nominal_power"]/(data["estimate"]["consumo"].values[j] + (delta_production.iloc[j] + quantity_discharging_battery)))
                            penality_sum = penality_sum + (1.5 - data["inverter_nominal_power"]/(data["estimate"]["consumo"].values[j] + (delta_production.iloc[j] + quantity_discharging_battery)))                        
                        
                        #Si controlla di non prendere più energia dalla batteria di quanto il contatore sia in grado di gestire
                        if(quantity_discharging_battery + delta_production.iloc[j] > data["maximum_power_absorption"]):
                            penality_sum = penality_sum + (1.5 -  data["maximum_power_absorption"] / quantity_discharging_battery)

                        #Produco di più di quanto consumo, vendo il resto
                        sum = sum - ((delta_production.iloc[j] + quantity_discharging_battery) * sold) / penality_sum

                    #Produco poco e consumo di più
                    else:
                        co2_emissions = co2_emissions + + co2_quantity_emission_algo(data,percentage_production_not_renewable["Difference"][j] ,(delta_production.iloc[j] + quantity_discharging_battery/data["battery_discharging_efficiency"]))
                        
                        if data["estimate"]["consumo"].values[j] > data["inverter_nominal_power"]:
                            penality_batt = penality_batt + (1.5 - data["inverter_nominal_power"]/(data["estimate"]["consumo"].values[j]))
                            penality_sum = penality_sum * (1.5 - data["inverter_nominal_power"]/(data["estimate"]["consumo"].values[j]))                    
                                                                        
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
                individuo = np.full(48, 1.5, dtype=float)
                for i in range(48):
                    individuo[i] = sampling[k].X[i]

                X[k] = individuo

            return X



    pool = ThreadPool(n_threads)
    runner = StarmapParallelization(pool.starmap)
    problem = MixedVariableProblem(elementwise_runner=runner)

    survival = FitnessSurvival()
    selection=CustomTournamentSelection(func_comp=comp_by_cv_and_fitness)
    crossover = SimulatedBinaryCrossoverModified(prob_var=prob_cross)
    mutation=CustomGaussianMutation(prob_mut_bit = prob_mut_bit , prob_mut_int = prob_mut_int, eta=5)

    termination= DefaultSingleObjectiveTermination(xtol=0.001, n_max_gen=n_gen, period=20)
    
    if sampling is None:
        algorithm = GA(pop_size=pop_size, survival=survival, selection=selection, crossover=crossover, mutation=mutation)
    else:
        algorithm = GA(pop_size=pop_size, sampling=MySampling(), survival=survival, selection=selection, crossover=crossover, mutation=mutation)
        
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


def shifting_GA_individuals(population):
    for individuo in population:
        for i in range(0,46, 2):
            individuo.X[i] = individuo.X[i+2]
            individuo.X[i+1] = individuo.X[i+3]

        individuo.X[46] =  random.choice([True, False])
        individuo.X[47] = random.randint(0, 100)
        
    return population



def extract_signed_value(sign, value):
    """ Estrai il numero con il segno in base al primo valore della coppia """
    if round(sign) == 0:
        return -value  # Negativo
    else:
        return value  # Positivo

def create_signed_pair(value):
    """ Converte un numero con segno nel formato [sign, value] """
    if value < 0:
        return [0, abs(value)]  # 0 indica negativo
    else:
        return [1, value]  # 1 indica positivo

def sbx_crossover(x1, x2, eta):
    """Esegue il crossover SBX su due valori numerici."""
    if x1 == x2:
        return x1, x2

    y1, y2 = min(x1, x2), max(x1, x2)
    delta = y2 - y1
    beta = 1.0 + (2.0 * (x1 - y1) / delta)
    alpha = 2.0 - np.power(beta, -(eta[0] + 1.0))
    rand = np.random.random()

    if rand <= (1.0 / alpha):
        betaq = np.power((rand * alpha), (1.0 / (eta[0] + 1.0)))
    else:
        betaq = np.power((1.0 / (2.0 - rand * alpha)), (1.0 / (eta[0] + 1.0)))

    c1 = 0.5 * ((y1 + y2) - betaq * delta)
    c2 = 0.5 * ((y1 + y2) + betaq * delta)

    return c1, c2

def cross_sbx_modified(X, xl, xu, eta, prob_var, prob_bin):
    """ SBX crossover modificato per coppie (signo, valore) """
    
    n_parents, n_matings, n_var = X.shape

    # Ensure the number of variables is even (since we deal with pairs)
    assert n_var % 2 == 0, "Number of variables must be even, since they are pairs."

    # Apply crossover on pairs of values
    n_pairs = n_var // 2

    # the probability of a crossover for each of the variables
    cross = np.random.random((n_matings, n_pairs)) < prob_var

    
    # disable crossover when lower and upper bound are identical
    cross[:] = True

    # Iterate through each pair of variables
    for i in range(n_matings):
        for j in range(n_pairs):
            if cross[i, j]:
                sign1_p1, value1_p1 = X[0, i, j * 2], X[0, i, j * 2 + 1]
                sign2_p2, value2_p2 = X[1, i, j * 2], X[1, i, j * 2 + 1]
                
                
                # Estrai i valori con il segno
                signed_value1 = extract_signed_value(sign1_p1, value1_p1)
                signed_value2 = extract_signed_value(sign2_p2, value2_p2)
                
                # Apply SBX crossover to the signed values
                c1, c2 = sbx_crossover(signed_value1, signed_value2, eta)

                # Convert the offspring back to (sign, value) format
                X[0, i, j * 2], X[0, i, j * 2 + 1] = create_signed_pair(c1)
                X[1, i, j * 2], X[1, i, j * 2 + 1] = create_signed_pair(c2)
    
    
    # Ripara i valori ai limiti specificati
    X[0] = repair_clamp(X[0], xl, xu)
    X[1] = repair_clamp(X[1], xl, xu)

    return X

# ---------------------------------------------------------------------------------------------------------
# Class
# ---------------------------------------------------------------------------------------------------------

class SimulatedBinaryCrossoverModified(Crossover):

    def __init__(self,
                 prob_var=0.5,
                 eta=20,
                 prob_exch=1.0,
                 prob_bin=0.5,
                 n_offsprings=2,
                 **kwargs):
        super().__init__(2, n_offsprings, **kwargs)

        self.prob_var = Real(prob_var, bounds=(0.1, 0.9))
        self.eta = Real(eta, bounds=(3.0, 30.0), strict=(1.0, None))
        self.prob_exch = Real(prob_exch, bounds=(0.0, 1.0), strict=(0.0, 1.0))
        self.prob_bin = Real(prob_bin, bounds=(0.0, 1.0), strict=(0.0, 1.0))

    def _do(self, problem, X, **kwargs):
        _, n_matings, _ = X.shape

        # get the parameters required by SBX
        eta, prob_var, prob_exch, prob_bin = get(self.eta, self.prob_var, self.prob_exch, self.prob_bin,
                                                 size=(n_matings, 1))

        # set the binomial probability to zero if no exchange between individuals shall happen
        rand = np.random.random((len(prob_bin), 1))
        prob_bin[rand > prob_exch] = 0.0

        # Apply the modified SBX for pairs
        Q = cross_sbx_modified(X.astype(float), problem.xl, problem.xu, eta, prob_var, prob_bin)

        if self.n_offsprings == 1:
            rand = np.random.random(size=n_matings) < 0.5
            Q[0, rand] = Q[1, rand]
            Q = Q[[0]]

        
        return Q

class SBXModified(SimulatedBinaryCrossoverModified):
    pass



class CustomGaussianMutation(Mutation):
    def __init__(self, prob_mut_int=0.8,prob_mut_bit = 0.5, eta=5):
        super().__init__()
        self.prob_int = prob_mut_int
        self.prob_bit =prob_mut_bit
        self.eta = max(min(eta, 30), 1)
    
    def _do(self, problem, X, **kwargs):
        # X ha dimensione (pop_size, n_var)
        for i in range(X.shape[0]):
            for j in range(0, X.shape[1], 2):
                if np.random.rand() < self.prob_bit:
                    X[i, j] = 1.0 if round(X[i, j]) == 0 else 0.0
                
                if np.random.rand() < self.prob_int:
                    X[i, j+1] += np.random.normal(-10*(1/self.eta), 10*(1/self.eta))
                    X[i, j+1] = max(min(X[i, j+1], problem.xu[j+1]), problem.xl[j+1])
                    # Arrotondamento se necessario
                    X[i, j+1] = np.round(X[i, j+1])
        
        return X
    
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