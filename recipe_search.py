from elasticsearch import Elasticsearch


def recipe_elastic_query(ingridients_norm_list, tags):
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


def ingridients_elastic_query(ingridients_raw_list):
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


def get_recipe(ingridients_raw_list, tags):
    ingridients_pre_norm_list = ingridients_elastic_query(ingridients_raw_list)

    ingridients_norm_list = [ingridients_pre_norm_list[0]]
    for i in ingridients_pre_norm_list:
        if i['ingr_name'] not \
                in [d['ingr_name'] for d in ingridients_norm_list]:
            ingridients_norm_list.append(i.copy())

    ingridients_query_list = [d['ingr_name'] for d in ingridients_norm_list]

    recipe = recipe_elastic_query(ingridients_query_list, tags)

    used_norm_ingr_list = \
        [val for val in ingridients_norm_list
            if val['ingr_name'] in recipe['ingridients']]
    needed_ingr_list = \
        [val for val in recipe['ingridients']
            if val not in [d['ingr_name'] for d in used_norm_ingr_list]]
    used_ingr_list = \
        [val for val in ingridients_raw_list
            if val['ingr_id'] in [d['ingr_id'] for d in used_norm_ingr_list]]

    recipe['needed_ingridients'] = needed_ingr_list
    recipe['used_ingridients'] = used_ingr_list

    return(recipe)


if __name__ == "__main__":
    ingridients = [
        {'ingr_id': 1, 'ingr_name': 'картофельные чипсы'},
        {'ingr_id': 2, 'ingr_name': 'соль экстра'},
        {'ingr_id': 3, 'ingr_name': 'картофелина адидас'},
        {'ingr_id': 4, 'ingr_name': 'какая-то неведомая хрень'}]

    tags = ["завтраки"]
    print(get_recipe(ingridients, tags))
