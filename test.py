# from meteo import *
# import pandas as pd
# import asyncio

# import sys

# from costi import *

# async def main():
#     result = await get_intra_days_market()
#     print(result)
    

# if __name__ == "__main__":
#     asyncio.run(main())


import random
import pandas as pd
from datetime import datetime, timedelta
 
# Il tuo DataFrame esistente
df = pd.read_csv("csv/loadnew.csv")
 
# Calcola il minimo e il massimo consumo per ogni ora
limiti_consumo = df.groupby('ora')['consumo'].agg(['min', 'max']).to_dict('index')
 
# Data di inizio (1 Marzo)
start_date = datetime(2024, 3, 1)
 
# Data di fine (oggi)
end_date = datetime.now()
 
# Inizializza una lista vuota per i tuoi nuovi dati
nuovi_dati = []
 
# Genera dati per ogni giorno tra la data di inizio e la data di fine
current_date = start_date
while current_date <= end_date:
    for hour in range(24):  # Per ogni ora del giorno
        # Ottieni i limiti di consumo per questa ora
        min_consumo, max_consumo = limiti_consumo.get(hour, (900, 3400))
        # Genera un consumo casuale all'interno dei limiti
        consumo = random.randint(int(min_consumo), int(max_consumo))
        # Aggiungi i nuovi dati alla lista
        # Nota: stiamo convertendo la data in una stringa nel formato desiderato
        nuovi_dati.append((current_date.strftime('%Y%m%d'), hour, consumo))
    # Passa al giorno successivo
    current_date += timedelta(days=1)
 
# Crea un nuovo DataFrame con i dati generati
nuovi_dati_df = pd.DataFrame(nuovi_dati, columns=['data', 'ora', 'consumo'])
 
# Ora 'nuovi_dati_df' contiene i tuoi dati generati casualmente
print(nuovi_dati_df)