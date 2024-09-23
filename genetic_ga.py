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
from pymoo.core.sampling import Sampling
from pymoo.algorithms.soo.nonconvex.ga import GA


def start_GA_genetic_algorithm(data, pop_size, n_gen, n_threads, sampling=None,verbose=False):
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

    termination= DefaultMultiObjectiveTermination(xtol=0.001, n_max_gen=n_gen, n_skip=1, period=20)
    
    if sampling is None:
        algorithm = GA(pop_size=pop_size)
    else:
        algorithm = GA(pop_size=pop_size, sampling=MySampling())
        #algorithm = Optuna(sampling = MySampling())
        
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