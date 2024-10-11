import numpy as np
from scipy.optimize import curve_fit




def inverter_function():
    # Punti di dati dalla curva
    x = np.array([0.05, 0.1, 0.2, 0.25, 0.3, 0.5, 0.75, 1.0])
    y = np.array([91, 94.5, 96.3, 96.6, 96.8, 97.1, 97.1, 97.0]) / 100
    
    coeff = np.polyfit(x, y, deg=4)
    polynomial = np.poly1d(coeff)
    return polynomial


# Funzione per ottenere l'efficienza basata sul polinomio e il rapporto dato
def get_eff(polynomial, ratio):
    return polynomial(ratio)

#https://files.sma.de/downloads/WirkungDerat-TI-it-53.pdf?_ga=2.241470592.32095721.1722611712-1398327596.1718878276