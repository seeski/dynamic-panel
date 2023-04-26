import asyncio
from head_services import Schedulerio, collect_globus


# установите время в формате "%Y-%m-%d %H:%M", например '2023-04-20 12:46'
schedule = Schedulerio(collect_globus, '2023-04-26 09:56')

async def main():
    while True:
        await schedule.check_time()
        await asyncio.sleep(5)

if __name__ == '__main__':
    asyncio.run(main())
