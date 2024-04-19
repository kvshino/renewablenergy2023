from datetime import datetime, timedelta

import pandas as pd
from mercati_energetici import MercatiElettrici

#import sys
#from aiohttp.client_exceptions import ClientConnectorError



async def get_future_day_market(mercato="MI-A2", zona= 'SUD') -> pd.core.frame.DataFrame:
    """
        Fetches future price datas from mercatoelettrico.com.

        Returns:
            final: a dataframe containing future prices data with the following order:
            the first row is the next hour from the simulation hour
            the last row is the last hour from the simulation hour
    """
    iva=0,34

    async with MercatiElettrici() as mercati_elettrici:
        await mercati_elettrici.get_general_conditions()
        await mercati_elettrici.get_disclaimer()
        await mercati_elettrici.get_markets()

        #Il blocco try-except serve per verificare se i dati di prezzo del giorno dopo sono disponibili:
        # - Se sono disponibili, li ottengo e li concateno con quelli che mi servono del giorno corrente per la simulazione
        # - Se non sono disponibili, il blocco except viene eseguito e ottengo solo i dati del giorno corrente per la simulazione 
        try:
            
            #Acquisizione dei prezzi di oggi
            price = await mercati_elettrici.get_prices(mercato, (datetime.now()).strftime("%Y%m%d"))
            price_df = pd.DataFrame(price)
            price_filtered = price_df[price_df["zona"] == zona]

            #Acquisizione dei prezzi di domani
            price_tomorrow = await mercati_elettrici.get_prices(mercato, (datetime.now() + timedelta(days=1)).strftime("%Y%m%d"))
            price_tomorrow_df = pd.DataFrame(price_tomorrow)
            price_tomorrow_filtered = price_tomorrow_df[price_tomorrow_df["zona"] == zona]

            #Concatenazione dei prezzi di oggi e domani
            final=pd.DataFrame(price_filtered[price_filtered["ora"] >=(datetime.now().hour+1)%25])
            final= pd.concat([final,price_tomorrow_filtered[price_tomorrow_filtered["ora"] < (datetime.now().hour+1)%25]], axis=0)

            #Modellazione del risultato
            final= pd.DataFrame(final).drop(["mercato", "zona"], axis=1)
            final["prezzo"] = final["prezzo"]/1000/1000
            final["prezzo"] += final["prezzo"] * iva
            final=final.reset_index(drop=True)

        
        except:
            # tipo_eccezione, valore, traccia = sys.exc_info()
            # print(f"Errore di tipo {tipo_eccezione}: {valore}")
            
            #Acquisizione dei prezzi di oggi
            price = await mercati_elettrici.get_prices(mercato, (datetime.now()).strftime("%Y%m%d"))
            price_df = pd.DataFrame(price)
            price_filtered = price_df[price_df["zona"] == zona]

            #Modellazione del risultato
            final= pd.concat([price_filtered[price_filtered["ora"] >= (datetime.now().hour+1)%25],price_filtered[price_filtered["ora"] < (datetime.now().hour+1)%25]], axis=0)
            final = pd.DataFrame(final).drop(["mercato", "zona"], axis=1)
            final["prezzo"] = final["prezzo"]/1000/1000
            final["prezzo"] += final["prezzo"] * 0.34
            final=final.reset_index(drop=True)
        

        return final

