from datetime import datetime, timedelta

import pandas as pd
from mercati_energetici import MercatiElettrici
import random
#import sys
#from aiohttp.client_exceptions import ClientConnectorError



async def get_future_day_market(mercato="MI-A1", zona= 'CSUD') -> pd.core.frame.DataFrame:
    """
        Fetches future price datas from mercatoelettrico.com.

        Returns:
            final: a dataframe containing future prices data with the following order:
            the first row is the next hour from the simulation hour
            the last row is the last hour from the simulation hour
    """
    iva=0.34

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
            final['prezzo'] = final['prezzo'] * iva
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


async def get_future_day_italian_market(data, zona = 'CSUD') -> pd.core.frame.DataFrame:

    async with MercatiElettrici() as mercati_elettrici:
        await mercati_elettrici.get_general_conditions()
        await mercati_elettrici.get_disclaimer()
        await mercati_elettrici.get_markets()

        market_a3=1
        tomorrow=1
        try:
            price = await mercati_elettrici.get_prices("MI-A3", (datetime.now()).strftime("%Y%m%d"))
            price_a2 = await mercati_elettrici.get_prices("MI-A2", (datetime.now()).strftime("%Y%m%d"))
        except:
            market_a3=0
            try:
                price_a2 = await mercati_elettrici.get_prices("MI-A2", (datetime.now()).strftime("%Y%m%d"))
            except:
                market_a3 = 1
                tomorrow = 0
                try:
                    price = await mercati_elettrici.get_prices("MI-A3", (datetime.now() - timedelta(days=1)).strftime("%Y%m%d"))
                    price_a2 = await mercati_elettrici.get_prices("MI-A2", (datetime.now() - timedelta(days=1)).strftime("%Y%m%d"))
                except:
                    market_a3 = 0
                    price_a2 = await mercati_elettrici.get_prices("MI-A2", (datetime.now() - timedelta(days=1)).strftime("%Y%m%d"))

        if(market_a3):
            # MERCATO A3 e A2 ODIERNO DISPONIBILE
            price_df = pd.DataFrame(price)
            price_df_2 = pd.DataFrame(price_a2)
            price_filtered = price_df[price_df["zona"] == zona]
            price_filtered_2 = price_df_2[price_df_2["zona"] == zona]
            price_filtered = pd.concat([price_filtered_2[price_filtered_2["ora"] < 13],price_filtered[price_filtered["ora"] >= 13]], axis=0)
        else:
            # MERCATO SOLO A2 ODIERNO DISPONIBILE
            price_df = pd.DataFrame(price_a2)
            price_filtered = price_df[price_df["zona"] == zona]
        

        if tomorrow:
            market_a3_tomorrow=1
            flag = 1
            try:
                price_tomorrow = await mercati_elettrici.get_prices("MI-A3", (datetime.now() + timedelta(days=1)).strftime("%Y%m%d"))
                price_tomorrow_a2 = await mercati_elettrici.get_prices("MI-A2", (datetime.now() + timedelta(days=1)).strftime("%Y%m%d"))
            except:
                try:
                    market_a3_tomorrow = 0
                    price_tomorrow = await mercati_elettrici.get_prices("MI-A2", (datetime.now() + timedelta(days=1)).strftime("%Y%m%d"))
                except:
                    try:
                        price_tomorrow = await mercati_elettrici.get_prices("MI-A1", (datetime.now() + timedelta(days=1)).strftime("%Y%m%d"))
                    except:
                        flag = 0
        else:
            flag = 0



        if flag == 0:
            #NESSUN MERCATO DI DOMANI DISPONIBILE
            price_filtered = price_filtered.reset_index(drop=True)

            price_filtered.loc[price_filtered["ora"] < (datetime.now().hour+1)%25, 'prezzo'] = price_filtered['prezzo'] + price_filtered['prezzo'] * random.uniform(-0.10, 0.10)
            final= pd.concat([price_filtered[price_filtered["ora"] >= (datetime.now().hour+1)%25],price_filtered[price_filtered["ora"] < (datetime.now().hour+1)%25]], axis=0)
        else:
            price_tomorrow_df = pd.DataFrame(price_tomorrow)
            price_tomorrow_filtered = price_tomorrow_df[price_tomorrow_df["zona"] == zona]
            if market_a3_tomorrow:
                # MERCATO A3 e A2 DI DOMANI DISPONIBILE
                price_tomorrow_a2_df = pd.DataFrame(price_tomorrow_a2)
                price_tomorrow_a2_filtered = price_tomorrow_a2_df[price_tomorrow_a2_df["zona"] == zona]

                final=pd.DataFrame(price_filtered[price_filtered["ora"] >=(datetime.now().hour+1)%25])
                final= pd.concat([final, price_tomorrow_a2_filtered[(price_tomorrow_a2_filtered["ora"] < 13) & (price_tomorrow_a2_filtered["ora"] < (datetime.now().hour+1)%25)], price_tomorrow_filtered[(price_tomorrow_filtered["ora"] >= 13) & (price_tomorrow_filtered["ora"] < (datetime.now().hour+1)%25)]], axis=0)
            else:
                # MERCATO A2 o A1 DI DOMANI DISPONIBILE
                final=pd.DataFrame(price_filtered[price_filtered["ora"] >=(datetime.now().hour+1)%25])
                final= pd.concat([final,price_tomorrow_filtered[price_tomorrow_filtered["ora"] < (datetime.now().hour+1)%25]], axis=0)
        
        final = pd.DataFrame(final).drop(["mercato", "zona"], axis=1)
        final["prezzo"] = final["prezzo"]/1000/1000
        final["prezzo"] = final["prezzo"] + (final["prezzo"] * data["iva"])
        final=final.reset_index(drop=True)


    return final