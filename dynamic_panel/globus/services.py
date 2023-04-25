import asyncio, collections, bs4, json
import random
import aiohttp
from aiocfscrape import CloudflareScraper
from bs4 import BeautifulSoup as bs
from aiohttp import ClientTimeout
from datetime import date
from pathlib import Path
from aiohttp.client_exceptions import ClientOSError

# -------- Константы --------

BASE_DOMAIN = 'https://online.globus.ru'
TIME_OUT = ClientTimeout(total=3600)
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
PROXIES = json.load(open(f'{ROOT_DIR}/dynamic_panel/proxies.json'))

# -------- Классы --------

# именованый кортеж под объект для json файла
Product = collections.namedtuple('Product', 'date brand name pics price promo_price card_price rating desc comp url')


# класс выдергивает значение из объекта супа
# возвращает текст тега или None
class GetTagValue:
    def __init__(self, tag: bs4.Tag):
        self.tag = tag

    def value(self, tag_name: str) -> str | None:
        try:
            return self.tag.find(tag_name).text
        except:
            return None

    def scope(self, tag_name: str, scope: dict):
        try:
            tag = self.tag.find(tag_name, scope)
            return tag.text
        except:
            return None

    # рефакторинг ценника без скидок
    def oldprice(self):
        try:
            oldprice_tag = self.tag.find('span', {'class': 'item-price__old'})
            oldprice_main = oldprice_tag.text.replace('\n', '').replace(' ', '.')
            oldprice_sup = oldprice_tag.find('sup').text

            oldprice = oldprice_main[:-len(oldprice_sup)] + f'.{oldprice_sup}'
            return oldprice

        except Exception as e:
            print(e)
            return None





# выдергивает значение из словаря
# возвращает значение или None
class GetDictValue:
    def __init__(self, dict):
        self.dict = dict

    def value(self, key):
        try:
            return self.dict[key]
        except:
            return None


# -------- Функции --------

# в блоке "О товаре" теги не разделены по классам
# просто пробегаюсь по каждому тегу
# нечетные - ключи, четные - значения
def list_to_dict(arr):
    dict = {}
    for i in range(len(arr) + 1):
        try:
            if not i % 2:
                dict.update({arr[i]: arr[i + 1]})
        except IndexError:
            continue

    return dict


# функция итерирует объект Future и превращает его в список
# также отливливает ситуации, если одна из корутин не отработала и\или отаботала некорректно
# возвращает список со значениями из футуры или пустой список
def products_to_list(products):
    print('products to list working')
    products_list = []
    for arr in products:
        print(type(arr))
        if not isinstance(arr, list):
            return []
        for product in arr:
            products_list.append(product)

    return products_list


# вспомогательный алгоритм для поиска последней страницы пагинации категории
# используется в корутине scrape_category
# на вход пригимает кусок супа, отдает номер страницы
# O(n)
def find_last_page_number(soup: bs4.Tag) -> int:
    li_tags = soup.find_all('li')
    top = 0
    for tag in li_tags:
        # try/except нужен для того, чтобы программа не наебнулась
        # если в итерируемом теге нет тега a и/или аттрибута href
        try:
            href = tag.find('a').get('href')
            cur = int(href.split('=')[-1])
            top = max(top, cur)
        except:
            continue

    return top


# чистит все ненужные символы из наименования продукта
# [!] возможно в будущем будет заменено на класс для рефакторинга
# [!] а эта функция будет отдельным методом
def refactor_name(s: str) -> str:
    return s.replace('\n', '').replace(' ', '').strip()


# создаем json под определенную категорию
def create_category_json(category_name: str, products: list[Product]):
    with open(f'{ROOT_DIR}/{category_name}.json', 'w', encoding='utf-8') as file:
        arr = []
        for product in products:
            arr.append(
                {
                    'date': product.date,
                    'brand': product.brand,
                    'name': product.name,
                    'pics': product.pics,
                    'price': product.price,
                    'promo_price': product.promo_price,
                    'card_price': product.card_price,
                    'rating': product.rating,
                    'desc': product.desc,
                    'comp': product.comp,
                    'url': product.url
                }
            )
        data = json.dumps(arr)
        data = json.loads(str(data))
        json.dump(data, file, indent=4, ensure_ascii=False)


# -------- Корутины --------

# написание файла с категориями
# корутина ничего не принимает, просто отправляет запрос на сайт глобуса
# и собирает категории в один файлик
async def update_categories_file():
    async with CloudflareScraper() as session:
        response = await session.get(BASE_DOMAIN)
        soup = bs(await response.text(), 'lxml')
        categories_tags = soup.find('ul', class_='nav_main__content-list')
        categories_links = []
        for category in categories_tags:
            try:
                link = category.find('a').get('href')
                categories_links.append(link.replace('/', '%'))
            except Exception as e:
                print(e, 'during collect_categories')

    with open(fr'{ROOT_DIR}/categories.txt', 'w', encoding='utf-8') as file:
        file.write(
            '\n'.join(categories_links)
        )


# сбор даты с указанной линки
# возвращает именнованный кортеж Product
async def scrape_product(link: str, session, proxy_dict) -> Product:
    today = date.today().strftime('%d/%m/%Y')
    attemps = 5
    while attemps:
        try:
            proxy_addres = proxy_dict['proxy']
            proxy_auth = aiohttp.BasicAuth(proxy_dict['user'], proxy_dict['password'])
            resp = await session.get(url=link, proxy=proxy_addres, proxy_auth=proxy_auth)
            if resp.status == 200:
                soup = bs(await resp.text(), 'lxml')
                getTag = GetTagValue(soup)

                price_tag = soup.find('span', class_='item-price__num')
                price = price_tag.find('meta').get('content').replace(' ', '.').strip('.')

                name = refactor_name(getTag.scope('h1', {'class': 'js-with-nbsp-after-digit'}))

                tbody = soup.find('tbody')
                arr = []
                for td in tbody.find_all('td'):
                    arr.append(td.text.replace('\n', '').strip())
                brand_comp_dict = list_to_dict(arr)
                getDict = GetDictValue(brand_comp_dict)

                pics_tags = soup.find_all('img', class_='product_big_pic')
                pics = ''
                for pic in pics_tags:
                    pics += f'{BASE_DOMAIN}{pic.get("src")}, '

                desc = getTag.scope('p', {'itemprop': 'description'})

                old_price = getTag.oldprice()

                if old_price:
                    if float(old_price) > float(price):
                        return Product(
                            date=today,
                            brand=getDict.value('Бренд'),
                            name=name,
                            price=old_price,
                            promo_price=price,
                            card_price=price,
                            rating=None,
                            desc=desc,
                            comp=getDict.value('Состав'),
                            url=link,
                            pics=pics
                        )

                    return Product(
                        date=today,
                        brand=getDict.value('Бренд'),
                        name=name,
                        price=price,
                        promo_price=None,
                        card_price=None,
                        rating=None,
                        desc=desc,
                        comp=getDict.value('Состав'),
                        url=link,
                        pics=pics
                    )

                else:

                    return Product(
                        date=today,
                        brand=getDict.value('Бренд'),
                        name=name,
                        price=price,
                        promo_price=None,
                        card_price=None,
                        rating=None,
                        desc=desc,
                        comp=getDict.value('Состав'),
                        url=link,
                        pics=pics
                    )
        except Exception as e:
            attemps -= 1
            print(f'some exception at {link} -- {e}')

    return Product(
        date=today,
        brand='error',
        name='error',
        price='error',
        promo_price='error',
        card_price='error',
        rating='error',
        desc='error',
        comp='error',
        url=link,
        pics='error'
    )


# собираем данные с определенной страницы категории
# например https://online.globus.ru/catalog/molochnye-produkty-syr-yaytsa/?PAGEN_1=5
# при возникновении ошибок, отрабатывает try/except и сессия переподключается
# в противном случае корутина возвращает False и на этапе проверки
# функция products_to_list возвращает пустое значение, а вьюха 404
async def scrape_page(page: str, session) -> list[Product]:
    print(f'page {page} is scraping')
    attempts = 5
    while attempts:
        try:
            proxy = random.choice(PROXIES)
            proxy_addres = proxy['proxy']
            proxy_auth = aiohttp.BasicAuth(proxy['user'], proxy['password'])
            resp = await session.get(page, allow_redirects=True, proxy=proxy_addres, proxy_auth=proxy_auth)
            soup = bs(await resp.text(), 'lxml')
            products = soup.find_all('a',
                                     class_='catalog-section__item__link catalog-section__item__link--one-line notrans')

            return await asyncio.gather(
                *(scrape_product(f'https://online.globus.ru{link.get("href")}', session=session, proxy_dict=proxy) for
                  link in products)
            )
        except Exception as e:
            attempts -= 1
            print(f'some exception at {page} -- {e}')

    return False


# сбор данных по каждой странице категории
# например https://online.globus.ru/catalog/molochnye-produkty-syr-yaytsa/
async def scrape_category(category: str) -> list[Product]:
    print('category is scraping')
    async with CloudflareScraper(timeout=TIME_OUT, trust_env=True) as session:
        category_link = BASE_DOMAIN + category.replace('%', '/')
        resp = await session.get(category_link)
        soup = bs(await resp.text(), 'lxml')
        pagination = soup.find('ul', class_='box-content box-shadow')
        max_page = find_last_page_number(soup=pagination)
        products = await asyncio.gather(
            *(scrape_page(f'{category_link}?PAGEN_1={cur_page + 1}', session=session) for cur_page in range(max_page)),
            return_exceptions=True
        )
        return products
