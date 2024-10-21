import matplotlib.pyplot as plt
import numpy as np

def plot_time(time1, time2):
    input_sizes = ['Input']  # Etichetta valida per l'asse X
    algorithm1_times_mixed = [time1]  # Tempi per Algoritmo Mixed
    algorithm2_times_ga = [time2]  # Tempi per Algoritmo GA

    # Creiamo un array per la posizione delle barre sull'asse X
    bar_width = 0.1  # Larghezza delle barre
    index = np.arange(len(input_sizes))  # Posizioni per l'asse X

    # Creazione del grafico
    fig, ax = plt.subplots()

    # Sposta leggermente le barre per l'Algoritmo GA (più a sinistra)
    bar1 = ax.bar(index - bar_width * 0.7, algorithm2_times_ga, bar_width, color="#a066cb", label='GA')

    # Sposta leggermente le barre per l'Algoritmo Mixed (più a destra)
    bar2 = ax.bar(index + bar_width * 0.7, algorithm1_times_mixed, bar_width, color="#316099", label='MixedVariableGa')

    # Aggiunta delle etichette e del titolo
    ax.set_ylabel('Execution time (s)')
    ax.set_title('Comparison of the execution times')
    ax.set_xticks(index)
    ax.set_xticklabels(input_sizes)

    # Imposta i limiti dell'asse X
    ax.set_xlim([-0.5, 0.5])

    # Aggiungere le etichette sotto le barre
    ax.text(index[0] - bar_width * 0.7, -0.05, 'GA', ha='center', va='top', fontsize=12)
    ax.text(index[0] + bar_width * 0.7, -0.05, 'Mixed', ha='center', va='top', fontsize=12)

    # Mostrare il grafico
    plt.tight_layout()
    plt.show()

# Esempio di utilizzo della funzione
plot_time(0.1, 0.5)
