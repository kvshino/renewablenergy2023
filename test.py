from meteo import *
import pandas as pd
import asyncio

import sys

from costi import *

async def main():
    result = await get_intra_days_market()
    print(result)
    

if __name__ == "__main__":
    asyncio.run(main())
