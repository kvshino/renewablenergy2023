from functions import *
import asyncio
import pandas as pd


async def main():
    data = setup()
    #energy_request(data)
    print(await h_parameter(data))

    meteo_df = filter_meteo_between_ss_and_sr(data)
    
    meteo_df["expected_power_production"] = get_expected_power_production_from_pv(data, meteo_df["direct_radiation"], meteo_df["diffuse_radiation"], meteo_df["temperature_2m"])
    #print(meteo_df)

if __name__ == "__main__":
    asyncio.run(main())
