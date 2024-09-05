import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
import numpy as np
from plot import *

def init_gui(data, sum, actual_percentage, quantity_delta_battery):

    def on_graph_select(event):
        selected_graph_1 = combo1.get()
        selected_graph_2 = combo2.get()
        selected_graph_3 = combo3.get()

        # Mostra solo il grafico selezionato nell'ultimo menu a tendina modificato
        if event.widget == combo1:
            match selected_graph_1:
                case "Grafico 1: Simulazione Completa":
                    simulation_plot(data, sum, actual_percentage, quantity_delta_battery)
                    plt.show()

                case "Grafico 2: Prezzi dell'energia":
                    plot_GME_prices(data)
                    plt.show()

                case "Grafico 3: Consumi":
                    plot_load(data)
                    plt.show()

                case "Grafico 4: Produzione":
                    plot_production(data)
                    plt.show()

                case "Grafico 5: Costo":
                    plot_costi_plant(data,sum)
                    plt.show()

                case "Grafico 6: Scambio con la Rete":
                    plot_scambio_rete(data,quantity_delta_battery)
                    plt.show()
                
                case "Grafico 7: Energia in Batteria":
                    plot_energia_batteria(data,actual_percentage)
                    plt.show()

                case "Grafico 8: Percentuale Energia in Batteria":
                    plot_percentage_battery(data,actual_percentage)
                    plt.show()

                case "Grafico 9: Scambio Energia in Batteria":
                    plot_battery_status(data,quantity_delta_battery)
                    plt.show()

                case "Grafico 10: Co2 immessa con Impianto":
                    plot_co2_plant(data,quantity_delta_battery)   
                    plt.show()
            
                case "Grafico 11: Confronto costi":
                    plot_cost_comparison(data,sum)
                    plt.show()
                case "Grafico 12: Confronto Co2":
                    plot_co2_comparison(data,quantity_delta_battery)
                    plt.show()

        elif event.widget == combo2:
            match selected_graph_2:
                case "Grafico 1: Simulazione Completa":
                    simulation_plant_nobattery(data)
                    plt.show()

                case "Grafico 2: Prezzi dell'energia":
                    plot_GME_prices(data)
                    plt.show()

                case "Grafico 3: Consumi":
                    plot_load(data)
                    plt.show()

                case "Grafico 4: Produzione":
                    plot_production(data)
                    plt.show()

                case "Grafico 5: Costo":
                    plot_costi_plant_nobattery(data)
                    plt.show()
               
                    
        elif event.widget == combo3:
            match selected_graph_3:
                case "Grafico 1: Simulazione Completa":
                    simulation_noplant(data)
                    plt.show()

                case "Grafico 2: Prezzi dell'energia":
                    plot_GME_prices(data)
                    plt.show()

                case "Grafico 3: Consumi":
                    plot_load(data)
                    plt.show()
                    
                case "Grafico 4: Costo":
                    plot_costi_plant_nobattery(data)
                    plt.show()

                case "Grafico 5: Co2 senza impianto":
                    plot_co2_noplant(data)
                    plt.show()

    # Creazione della finestra principale
    root = tk.Tk()
    root.title("Selezione del Grafico")
    root.geometry("700x500")  # Imposta la larghezza a 600px e l'altezza a 300px

    icon_path = "sole.png"  # Specifica il percorso al file .ico
    icon = tk.PhotoImage(file=icon_path)
    root.iconphoto(True, icon)

    bg_image = tk.PhotoImage(file='meme3.png')
    

    # Crea un Label con l'immagine di sfondo
    background_label = tk.Label(root, image=bg_image)

    # Posiziona il Label in modo che copra l'intera finestra
    background_label.place(relwidth=1, relheight=1)

    # Porta il frame principale in primo piano (se usato)
    # Creazione di un frame per centrare tutto
    frame = ttk.Frame(root)
    frame.place(relx=0.5, rely=0.5, anchor="center")
    frame.lift()

    # Creazione delle etichette
    label1 = ttk.Label(frame, text="Simulazioni con Impianto Completo:")
    label2 = ttk.Label(frame, text="Simulazioni con Impianto senza Batteria:")
    label3 = ttk.Label(frame, text="Simulazioni senza Impianto:")

    # Creazione dei menu a tendina
    combo1 = ttk.Combobox(frame, values=["Grafico 1: Simulazione Completa", "Grafico 2: Prezzi dell'energia", "Grafico 3: Consumi",
                                        "Grafico 4: Produzione","Grafico 5: Costo", "Grafico 6: Scambio con la Rete",
                                        "Grafico 7: Energia in Batteria","Grafico 8: Percentuale Energia in Batteria",
                                        "Grafico 9: Scambio Energia in Batteria","Grafico 10: Co2 immessa con Impianto",
                                        "Grafico 11: Confronto costi","Grafico 12: Confronto Co2"
                                        ])
    combo1.current(0)  # Imposta il primo valore come selezionato di default

    combo2 = ttk.Combobox(frame, values=["Grafico 1: Simulazione Completa", "Grafico 2: Prezzi dell'energia", "Grafico 3: Consumi",
                                        "Grafico 4: Produzione","Grafico 5: Costo"])
    combo2.current(0)

    combo3 = ttk.Combobox(frame, values=["Grafico 1: Simulazione Completa", "Grafico 2: Prezzi dell'energia", "Grafico 3: Consumi",
                                        "Grafico 4: Costo","Grafico 5: Co2 senza impianto"])
    combo3.current(0)

    # Posizionamento delle etichette e dei menu a tendina sulla griglia con adattamento
    label1.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
    label2.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
    label3.grid(row=0, column=2, padx=10, pady=10, sticky="ew")

    combo1.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
    combo2.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
    combo3.grid(row=1, column=2, padx=10, pady=10, sticky="ew")

    # Binding della selezione a una funzione
    combo1.bind("<<ComboboxSelected>>", on_graph_select)
    combo2.bind("<<ComboboxSelected>>", on_graph_select)
    combo3.bind("<<ComboboxSelected>>", on_graph_select)

    # Creazione e posizionamento del pulsante di uscita
    exit_button = ttk.Button(frame, text="Esci", command=root.quit)
    exit_button.grid(row=2, column=1, pady=20, sticky="ew")  # Posizionato al centro sotto i menu

    # Espandi le colonne per riempire il frame
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_columnconfigure(1, weight=1)
    frame.grid_columnconfigure(2, weight=1)

    # Avviare il loop dell'interfaccia grafica
    root.mainloop()







