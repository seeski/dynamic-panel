import asyncio
from head_services import Schedulerio, collect_globus

schedule = Schedulerio(collect_globus, '2023-04-19 18:23')

async def main():
    while True:
        await schedule.check_time()
        await asyncio.sleep(5)

if __name__ == '__main__':
    asyncio.run(main())