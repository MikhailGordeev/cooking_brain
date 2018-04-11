from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError
from pymongo import MongoClient


def create_indices():
    es = Elasticsearch()
    try:
        es.indices.delete('recipes')
    except NotFoundError:
        pass

    es.indices.create(
        index='recipes',
        body={
            "mappings": {
                "recipe": {
                    "properties": {
                        "ingridients": {
                            "type": "keyword"
                        }
                    }
                }
            }
        }
    )

    try:
        es.indices.delete('ingridients')
    except NotFoundError:
        pass

    es.indices.create(
        index='ingridients',
        body={
            "settings": {
                "analysis": {
                    "analyzer": {
                        "ngram_analyzer": {
                            "tokenizer": "ngram_tokenizer"
                        }
                    },
                    "tokenizer": {
                        "ngram_tokenizer": {
                            "type": "nGram",
                            "min_gram": "3",
                            "max_gram": "8"
                        }
                    }
                }
            },
            "mappings": {
                "ingridient": {
                    "properties": {
                        "ingridient": {
                            "type": "text",
                            "analyzer": "ngram_analyzer"
                        }
                    }
                }
            }
        }
    )


def insert_recipes():
    es = Elasticsearch()
    client = MongoClient('localhost', 27017)
    db = client.recipes

    cursor = db.recipes.find()
    for line in cursor:
        recipe_id = line['_id']
        title = line['recipe_name']
        data_href = line['data_href']
        image_href = line['image_href']
        tags = line['tags']
        ingridients = line['ingridients']

        es.index(
            index='recipes',
            id=recipe_id,
            doc_type='recipe',
            body={
                'recipe_name': title,
                'data_href': data_href,
                'image_href': image_href,
                'tags': tags,
                'ingridients': ingridients
            }
        )


def insert_ingridients():
    es = Elasticsearch()
    res = es.search(
        index='recipes',
        body={
            "size": 0,
            "aggs": {
                "ingridients": {
                    "terms": {
                        "min_doc_count": 2,
                        "field": "ingridients",
                        "size": 50000
                    }
                }
            }
        }
    )

    for aggr in res['aggregations']['ingridients']['buckets']:
        es.index(
            index='ingridients',
            doc_type='ingridient',
            body={
                'ingridient': aggr['key']
            }
        )


if __name__ == "__main__":
    create_indices()
    insert_recipes()
    insert_ingridients()
