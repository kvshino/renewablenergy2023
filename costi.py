from datetime import datetime, timedelta

import pandas as pd
from mercati_energetici import MercatiElettrici


async def get_intra_days_market(days=1) -> pd.core.frame.DataFrame:
    """
    Fetches previous price datas from mercatoelettrico.com

    Args:
        days : number of days from today (days: 1 only fetches today's data)

    Returns:
        sud: a dataframe containing prices data
    """
    async with MercatiElettrici() as mercati_elettrici:
        await mercati_elettrici.get_general_conditions()
        await mercati_elettrici.get_disclaimer()
        await mercati_elettrici.get_markets()

        pandas_data = pd.DataFrame()
        today = datetime.now()
        for i in range(days):
            data = await mercati_elettrici.get_prices("MI-A2", today.strftime("%Y%m%d"))
            today = today - timedelta(days=1)
            pandas_data = pd.concat([pandas_data, pd.DataFrame(data)])

        sud = pandas_data.loc[pandas_data['zona'] == "SUD"].drop(["mercato", "zona"], axis=1)
        sud["prezzo"] = sud["prezzo"]/1000/1000
        return sud.reset_index(drop=True)

def energy_mean_price(energy_costs) -> float:
    """
        Calculate the average energy price.

        Args:
            energy_costs : Dataframe with column "prezzo"

        Returns:
            Mean of energy price
    """
    return energy_costs["prezzo"].mean()


async def get_future_day_market() -> pd.core.frame.DataFrame:
    """
        Fetches future price datas from mercatoelettrico.com

        Returns:
            price_df: a dataframe containing future prices data
    """
    async with MercatiElettrici() as mercati_elettrici:
        await mercati_elettrici.get_general_conditions()
        await mercati_elettrici.get_disclaimer()
        await mercati_elettrici.get_markets()
        try:
            price = await mercati_elettrici.get_prices("MI-A2", (datetime.now() + timedelta(days=1)).strftime("%Y%m%d"))
            price_df = pd.DataFrame(price).drop(["mercato", "zona"], axis=1)
        except:
            raise Exception("Tomorrow market data prices are not available yet")

        return price_df


async def mean_difference(days=1) -> float:
    """
        Calculate the difference between the mean of past energy prices
        and the mean of future prices

        Returns:
            Difference between the prices
    """
    past_df = await get_intra_days_market(days=days)
    past_mean = energy_mean_price(past_df)

    try:
        future_df = await get_future_day_market()
        future_mean = energy_mean_price(future_df)

        return (future_mean - past_mean), future_mean, past_mean
    except Exception as error:
        print(error)
