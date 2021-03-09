from functools import lru_cache

import pymongo
from bson import regex

from watchmen.common.pagination import Pagination
from watchmen.common.storage.engine.storage_engine import get_client
from watchmen.common.utils.data_utils import build_data_pages
from watchmen.topic.topic import Topic

db = get_client()

topic_col = db.get_collection('topic')


def save_topic(topic):
    # print(get_topic_by_id.cache_info())
    get_topic_by_id.cache_clear()
    return topic_col.insert_one(topic)


def load_all_topic():
    result = topic_col.find()
    # .sort("last_modified", pymongo.DESCENDING)
    return list(result)


def load_all_topic_list(pagination: Pagination):
    item_count = topic_col.find().count()
    skips = pagination.pageSize * (pagination.pageNumber - 1)
    result = topic_col.find().skip(skips).limit(pagination.pageSize).sort("last_modified", pymongo.DESCENDING)
    return build_data_pages(pagination, list(result), item_count)


def get_topic_by_name(topic_name):
    return topic_col.find_one({"name": topic_name})


@lru_cache(maxsize=100)
def get_topic(topic_name) -> Topic:
    result = topic_col.find_one({"name": topic_name})
    if result is None:
        return None
    else:
        return Topic.parse_obj(result)


def load_topic_list_by_name(topic_name):
    result = topic_col.find({"name": regex.Regex(topic_name)})
    return list(result)


def check_topic_exist(topic_name, topic_type) -> bool:
    result = topic_col.find_one({"name", topic_name, "type", topic_type})
    if result is None:
        return False
    else:
        return True


# TODO clear cache
@lru_cache(maxsize=100)
def get_topic_by_id(topic_id):
    result = topic_col.find_one({"topicId": topic_id})
    return Topic.parse_obj(result)


def get_topic_list_by_ids(topic_ids):
    result = topic_col.find({"topicId": {"$in": topic_ids}})
    return list(result)


def topic_dict_to_object(topic_schema_dict):
    topic = Topic()
    return topic


def query_topic_list_with_pagination(query_name: str, pagination: Pagination):
    item_count = topic_col.find({"name": regex.Regex(query_name)}).count()
    skips = pagination.pageSize * (pagination.pageNumber - 1)
    result = topic_col.find({"name": regex.Regex(query_name)}).skip(skips).limit(pagination.pageSize).sort(
        "last_modified", pymongo.DESCENDING)
    return build_data_pages(pagination, list(result), item_count)


def update_topic(topic_id, topic: Topic):
    return topic_col.update_one({"topicId": topic_id}, {"$set": topic})
