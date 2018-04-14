from elasticsearch import Elasticsearch
from pymongo import MongoClient


def create_indices():
    es = Elasticsearch()
    if es.indices.exists('recipes'):
        print("deleting recipes index...")
        res = es.indices.delete(index='recipes')
        print(" response: {}".format(res))

    print("creating recipes index...")
    res = es.indices.create(
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
    print(" response: {}".format(res))

    if es.indices.exists('ingridients'):
        print("deleting ingridients index...")
        res = es.indices.delete(index='ingridients')
        print(" response: {}".format(res))

    print("creating ingridients index...")
    res = es.indices.create(
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
                            "min_gram": "5",
                            "max_gram": "5"
                        }
                    }
                }
            },
            "mappings": {
                "i": {
                    "properties": {
                        "ingridient": {
                            "type": "text",
                            "analyzer": "standard",
                            "fields": {
                                "ngram": {
                                    "type": "text",
                                    "analyzer": "ngram_analyzer"
                                }
                            }
                        }
                    }
                }
            }
        }
    )
    print(" response: {}".format(res))


def insert_recipes():
    es = Elasticsearch()
    client = MongoClient('localhost', 27017)
    db = client.recipes

    print("migrating data from mongodb to elastic...")
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
    print("agggregating ingridients...")
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

    print("fill ingridients index...")
    for aggr in res['aggregations']['ingridients']['buckets']:
        es.index(
            index='ingridients',
            doc_type='i',
            body={
                'ingridient': aggr['key']
            }
        )
    print("Done.")


if __name__ == "__main__":
    create_indices()
    insert_recipes()
    insert_ingridients()
