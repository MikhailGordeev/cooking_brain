import requests, bs4
from time import sleep
from elasticsearch import Elasticsearch
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError



pg = 1

es = Elasticsearch()

client = MongoClient('localhost', 27017)

db = client.recipes
#collection = db.recipes


def get_page(url):
    s = requests.Session()
    s.get(url.rsplit('/',maxsplit=1)[0])
    r = s.get(url)
    return r.text

r_url = 'https://eda.ru/recepty/zavtraki?page=' + str(pg)

while get_page:
    print('ITER ' + r_url)
    soup = bs4.BeautifulSoup(get_page(r_url), "html.parser")
    all = soup.findAll("div", {"class": "tile-list__horizontal-tile horizontal-tile js-portions-count-parent js-bookmark__obj"})
    for i in all:
        try:
            recipe_id = i.find('div', {'class': 'bookmark js-tooltip js-bookmark__label '}).attrs['data-id']
            title = i.find('div', {'class': 'lazy-load-container js-lazy-loading'}).attrs['data-title']
            data_href = i.find('div', {'class': 'horizontal-tile__item-link js-click-link '}).attrs['data-href']
            image_href = i.find('div', {'class': 'lazy-load-container js-lazy-loading'}).attrs['data-src']

            tags = i.find('ul', {'class': 'breadcrumbs'})
            tags = ((tags.text).strip()).split('\n')

            ingridients_p = i.findAll('p', {'class': 'ingredients-list__content-item content-item js-cart-ingredients'})
            ingridients = []
            for p in ingridients_p:
                ingridient = p.find('span', {'class': 'js-tooltip js-tooltip-ingredient'})
                ingridient = ((ingridient.text).strip()).split('\n')
                ingridients += ingridient

            print('{} {} {} {} {} {}'.format(recipe_id, title, data_href, image_href, tags, ingridients))

 #           es.index( index='recipes', id=recipe_id, doc_type='recipe', body={ 'recipe_name': title, 'data_href': data_href, \
 #            'image_href': image_href, 'tags': tags, 'ingridients': ingridients })

            db.recipes.insert({ '_id': recipe_id, 'recipe_name': title, 'data_href': data_href, 'image_href': image_href, \
                'tags': tags, 'ingridients': ingridients })


        except (AttributeError, DuplicateKeyError):
            pass

    sleep(3)

    pg += 1


    r_url = 'https://eda.ru/recepty/zavtraki?page=' + str(pg)