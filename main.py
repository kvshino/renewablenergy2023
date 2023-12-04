from functions import *
import asyncio


async def main():
    data = setup()
    #energy_request(data)

    meteo_df = filter_meteo_between_ss_and_sr(data)
    delta_production = difference_of_production(data)

    meteo_df["expected_power_production"] = get_expected_power_production_from_pv(data, meteo_df["direct_radiation"], meteo_df["diffuse_radiation"], meteo_df["temperature_2m"])
    print(delta_production)

if __name__ == "__main__":
    asyncio.run(main())
