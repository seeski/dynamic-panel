import json, asyncio, os
from datetime import datetime, time, timedelta
from aiocfscrape import CloudflareScraper
from aiohttp.client_reqrep import ClientResponse
from aiohttp.client_exceptions import ClientOSError

# -------- Константы --------

LOCALHOST = 'http://127.0.0.1:8000'


# -------- Классы --------

# класс планировщик отправки корутин
# адекватных асинк аналогов библиотеки schedule я не нашел
# класс при инициализации получает объект корутины и указанное время вызовы
class Schedulerio:

    def __init__(self, coroutine, schedule_for):
        self.coroutine = coroutine
        self.schedule_for = schedule_for
        self.time_format = "%Y-%m-%d %H:%M"

    async def check_time(self):
        right_now = datetime.now().strftime(self.time_format)
        if self.schedule_for == right_now:
            self.schedule_for = datetime.strptime(self.schedule_for, self.time_format) + timedelta(days=1)
            await self.coroutine()



# -------- функции --------

# вспомогательная функция для проверки футуры на наличие ошибок и проч шелухи
# если с ответами от сайтами какие то проблемс, то функция возбуждает эррор со стороны клиента
# если все ок, то программа продолжает работать
def checkFuture(responses):
    for response in responses:
        if not isinstance(response, ClientResponse) or response.status != 200:
            raise ClientOSError


# -------- корутины --------

# отправляем запросы на каждую категорию к джанге
# формируем json файлик
async def collect_globus():
    attempts = 5
    while attempts:
        try:
            async with CloudflareScraper() as session:
                await session.get(LOCALHOST + '/globus/update_categories')
                with open('categories.txt') as file:
                    # запитонячил, простите
                    # распаковываем файл в список из строк, рефакторим строки от лишнего мусора
                    categories: list[str] = [category.replace('\n', '') for category in file.readlines()]

                    # асинхронно отправляем запросы на локалхост, чтобы не ждать
                    # ответа от каждой ручки, а отправляем все сразу
                    responses = await asyncio.gather(
                        *(session.get(f'{LOCALHOST}/globus/{category}', timeout=3600) for category in categories)
                    )
                    checkFuture(responses)
                    # пробегаемся по каждому json файлику, добавляем все словари в список to_globus
                    # после использования, удаляем файлик
                    to_globus = []
                    for category in categories:
                        with open(f'{category}.json', 'r', encoding='utf-8') as category_json_file:
                            json_file_data = json.load(category_json_file)
                            to_globus += json_file_data

                        os.remove(f'{category}.json')

                    # запись to_globus в мейн файл со всеми категориями
                    with open('globus.json', 'w', encoding='utf-8') as globus_json_file:
                        to_globus_data = json.dumps(to_globus)
                        to_globus_data = json.loads(str(to_globus_data))
                        json.dump(to_globus_data, globus_json_file, ensure_ascii=False, indent=4)

        except ClientOSError:
            attempts -= 1

