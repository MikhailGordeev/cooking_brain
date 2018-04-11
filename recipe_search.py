from elasticsearch import Elasticsearch


def get_recipe(ingridients_norm_list, tags):
    es = Elasticsearch()
    hits_rate = int(len(ingridients_norm_list) * 0.75)
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
                                        "terms": ingridients_norm_list, "minimum_should_match_script": {
                                            "source": "{}".format(hits_rate)
                                        }
                                    }
                                }
                            },
                                {"terms": {"tags": tags}
                            }]
                        }
                    }
                }
            }
        }
    )

    return "{} {}".format(result, result['hits']['total'])


def normalize_ingridients(ingridients_raw_list):
    es = Elasticsearch()
    for ingridient in ingridients_raw_list:
        result = es.search(
            index="recipes",
            body={
                "size": 1,
                "query": {
                    "match": {"ingridients": "помидоры"}
                }
            }
        )

        return(result)


ingridients_raw_list = ["помидор", "соль", "перец", "лук"]
tags = ["завтраки"]

print(normalize_ingridients(ingridients_raw_list))
