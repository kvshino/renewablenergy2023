from entsoe import EntsoePandasClient



from openmeteo_py import OWmanager
from openmeteo_py.Hourly.HourlyForecast import HourlyForecast
from openmeteo_py.Options.ForecastOptions import ForecastOptions
from openmeteo_py.Utils.constants import *
from suntime import Sun
from datetime import datetime, timedelta
import pandas as pd
import pytz
from mercati_energetici import MercatiElettrici

import asyncio
import seaborn as sns
import yaml

from freezegun import freeze_time

from multi_genetic import *
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)



async def get_future_day_italian_market(zona = 'CSUD') -> pd.core.frame.DataFrame:

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
        final=final.reset_index(drop=True)

    return final



def forecast_percentage_production_from_not_renewable_sources(zona="IT_CSUD") -> pd.core.frame.DataFrame:

    api_key = '634ab8da-8c97-452b-b4c8-1e73462d9b7b'
    client = EntsoePandasClient(api_key=api_key)

    today = pd.Timestamp(datetime.now(), tz='Europe/Rome')
    start = pd.Timestamp(today.strftime('%Y%m%d'), tz='Europe/Rome')
    end = start + timedelta(days=1)

    try:
        ahead = client.query_wind_and_solar_forecast(zona, start=start, end=end)
        ahead["Ora"] = ahead.index.hour
        ahead["Sum"] = ahead["Solar"] + ahead["Wind Onshore"]

        total_today = client.query_generation_forecast(zona, start=start, end=end)
        total_today = total_today.to_frame(name='Generation')
        total_today["Ora"] = total_today.index.hour
    except:
        ahead = client.query_wind_and_solar_forecast(zona, start=start-timedelta(days=1), end=end)
        ahead["Ora"] = ahead.index.hour
        ahead["Sum"] = ahead["Solar"] + ahead["Wind Onshore"]

        total_today = client.query_generation_forecast(zona, start=start-timedelta(days=1), end=end)
        total_today = total_today.to_frame(name='Generation')
        total_today["Ora"] = total_today.index.hour
    

    try:
        ahead_tomorrow = client.query_wind_and_solar_forecast(zona, start=start+timedelta(days=1), end=end+timedelta(days=2))
        ahead_tomorrow["Ora"] = ahead_tomorrow.index.hour
        ahead_tomorrow["Sum"] = ahead_tomorrow["Solar"] + ahead_tomorrow["Wind Onshore"]
        final= pd.concat([ahead[ahead["Ora"] >= (datetime.now().hour+1)%25], ahead_tomorrow[ahead_tomorrow["Ora"] < (datetime.now().hour+1)%25]], axis=0)
        #print("GIORNO DOPO RENEWABLE TROVATO")
        # GIORNO DOPO RENEWABLE TROVATO
    except:
        final= pd.concat([ahead[ahead["Ora"] >= (datetime.now().hour+1)%25], ahead[ahead["Ora"] < (datetime.now().hour+1)%25]], axis=0)
        # GIORNO DOPO RENEWABLE NON TROVATO
        #print("GIORNO DOPO RENEWABLE NON TROVATO")


    try:
        total_tomorrow = client.query_generation_forecast(zona, start=start+timedelta(days=1), end=end+timedelta(days=2))
        total_tomorrow = total_tomorrow.to_frame(name='Generation')
        total_tomorrow["Ora"] = total_tomorrow.index.hour
        final_total = pd.concat([total_today[total_today["Ora"] >= (datetime.now().hour+1)%25], total_tomorrow[total_tomorrow["Ora"] < (datetime.now().hour+1)%25]], axis=0)
        # GIORNO DOPO PRODUZIONE TOTALE TROVATA 
        #print("GIORNO DOPO PRODUZIONE TOTALE TROVATA")
    except:
        final_total = pd.concat([total_today[total_today["Ora"] >= (datetime.now().hour+1)%25], total_today[total_today["Ora"] < (datetime.now().hour+1)%25]], axis=0)
        # GIORNO DOPO PRODUZIONE TOTALE NON TROVATA
        #print("GIORNO DOPO PRODUZIONE TOTALE NON TROVATA")


    final_total = final_total.reset_index(drop=True)
    final = final.reset_index(drop=True)
    result = pd.DataFrame()
    result["Difference"] = final_total["Generation"] - final["Sum"]
    result["Difference"] = result["Difference"].clip(lower=0)
    result["Difference"] = result["Difference"] / final_total["Generation"]
    
    return result



async def main():

    data = setup()
    data["prices"] = await get_future_day_italian_market()  
    data["res"], data["history"] = start_genetic_algorithm(data=data, pop_size=100, n_gen=20, n_threads=24, sampling=None, verbose=False) 
    


    print("FINE")


if __name__ == "__main__":
    asyncio.run(main())