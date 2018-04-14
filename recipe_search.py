from elasticsearch import Elasticsearch


def get_recipe(ingridients_norm_list, tags):
    es = Elasticsearch()
    result = {'hits': {'total': 0}}
    hits_rate = int(len(ingridients_norm_list))
    while hits_rate > 0 and result['hits']['total'] == 0:
        result = es.search(
            index="recipes",
            body={
                "size": 1,
                "query": {
                    "function_score": {
                        "random_score": {},
                        "query": {
                            "bool": {
                                "must": [
                                    {"terms_set": {
                                        "ingridients": {
                                            "terms": ingridients_norm_list,
                                            "minimum_should_match_script": {
                                                "source":
                                                    "{}".format(hits_rate)
                                            }
                                        }
                                    }
                                    },
                                    {"terms": {"tags": tags}}
                                ]
                            }
                        }
                    }
                }
            }
        )
        hits_rate -= 1
    return result['hits']['hits'][0]['_source']


def normalize_ingridients(ingridients_raw_list):
    es = Elasticsearch()
    ingridients_norm_list = []
    for ingridient in ingridients_raw_list:
        result = es.search(
            index="ingridients",
            body={
                "size": 1,
                "query": {
                    "bool": {
                        "must": [
                            {
                                "multi_match": {
                                    "query": ingridient['ingr_name'],
                                    "fields": [
                                        "ingridient^5",
                                        "ingridient.ngram"
                                    ]
                                }
                            }
                        ]
                    }
                }
            }
        )
        ingridients_norm_dict = {}

        try:
            ingridients_norm_dict['ingr_id'] = ingridient['ingr_id']
            ingridients_norm_dict['ingr_name'] = \
                result['hits']['hits'][0]['_source']['ingridient']
        except IndexError:
            ingridients_norm_dict['ingr_name'] = \
                ingridient['ingr_name'].lower()
        ingridients_norm_list.append(ingridients_norm_dict.copy())

    return(ingridients_norm_list)


ingridients_raw_list = [{'ingr_id': 1, 'ingr_name': 'картофельные чипсы'},
                        {'ingr_id': 2, 'ingr_name': 'соль экстра'},
                        {'ingr_id': 3, 'ingr_name': 'картофелина адидас'},
                        {'ingr_id': 4, 'ingr_name': 'какая-то неведомая хрень'}
                        ]
tags = ["завтраки"]

ingridients_norm_list = normalize_ingridients(ingridients_raw_list)

ingridients_query_list = [d['ingr_name'] for d in ingridients_norm_list]
recipe = get_recipe(ingridients_norm_list, tags)

print(recipe['ingridients'])
used_ingridients = \
    [val for val in ingridients_norm_list if val in recipe['ingridients']]
print(used_ingridients)
