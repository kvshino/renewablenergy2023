import asyncio

from costi import *
from functions import *

import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

data = setup()


async def main():
    data["prices"] = await get_intra_days_market()  # Bring the prices of energy from Mercati Elettrici

    data["res"], data["history"] = start_genetic_algorithm(data, 500, 10, 24)

    sum, actual_percentage, quantity_delta_battery = evaluate(data)

    simulation_plot(data, sum, actual_percentage, quantity_delta_battery)


if __name__ == "__main__":
    asyncio.run(main())
