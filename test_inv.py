import numpy as np
from scipy.optimize import curve_fit




def inverter_function():
    # Punti di dati dalla curva
    x = np.array([0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    y = np.array([86.5, 91.5, 94.5, 96.0, 96.6, 96.8, 97.0, 97.0, 97.1, 97.1, 97.1]) / 100
    
    coeff = np.polyfit(x, y, deg=4)
    polynomial = np.poly1d(coeff)
    return polynomial


# Funzione per ottenere l'efficienza basata sul polinomio e il rapporto dato
def get_eff(polynomial, ratio):
    return polynomial(ratio)

#https://files.sma.de/downloads/WirkungDerat-TI-it-53.pdf?_ga=2.241470592.32095721.1722611712-1398327596.1718878276