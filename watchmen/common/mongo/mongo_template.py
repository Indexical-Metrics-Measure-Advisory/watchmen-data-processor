from watchmen.common.storage.engine.storage_engine import get_client
from watchmen.common.utils.data_utils import build_data_pages

client = get_client()


def create(collection_name, instance, base_model):
    collections = client.get_collection(collection_name)
    collections.insert_one(__convert_to_dict(instance))
    return base_model.parse_obj(instance)


def update_one(collection_name, query_dict, instance, base_model):
    collections = client.get_collection(collection_name)
    collections.update_one(query_dict, {"$set": __convert_to_dict(instance)})
    return base_model.parse_obj(instance)


def remove(collection_name,query_dict):
    collections = client.get_collection(collection_name)
    collections.remove(query_dict)


def find_one(collection_name, query_dict, base_model):
    collections = client.get_collection(collection_name)
    result = collections.find_one(query_dict)
    if result is None:
        return
    else:
        return base_model.parse_obj(result)


def find_all(collection_name, base_model):
    collections = client.get_collection(collection_name)
    cursor = collections.find()
    result_list = list(cursor)
    return [base_model.parse_obj(result) for result in result_list]


def find(collection_name, query_dict, base_model, sort_dict=None):
    collections = client.get_collection(collection_name)
    cursor = collections.find(query_dict)
    result_list = list(cursor)
    return [base_model.parse_obj(result) for result in result_list]


def delete_one(collection_name, query_dict):
    collections = client.get_collection(collection_name)
    return collections.delete_one(query_dict)


def __find_with_count(collections, query_dict):
    if query_dict is None:
        return collections.find().count()
    else:
        return collections.find(query_dict).count()


def __find_with_page(collections, query_dict, pagination, skips):
    if query_dict is None:
        return collections.find().skip(skips).limit(pagination.pageSize)
    else:
        return collections.find(query_dict).skip(skips).limit(pagination.pageSize)


def __sort(cursor, sort_dict):
    if sort_dict is None:
        return cursor
    else:
        return cursor.sort(*sort_dict)


def query_with_pagination(collection_name, pagination, base_model, query_dict=None, sort_dict=None):
    collections = client.get_collection(collection_name)
    items_count = __find_with_count(collections, query_dict)
    skips = pagination.pageSize * (pagination.pageNumber - 1)
    cursor = __sort(__find_with_page(collections, query_dict, pagination, skips), sort_dict)
    return build_data_pages(pagination, [base_model.parse_obj(result) for result in list(cursor)], items_count)


def __convert_to_dict(instance):
    if type(instance) is not dict:
        return instance.dict()
    else:
        return instance