from watchmen.common.storage.engine.storage_engine import get_client
from watchmen.common.utils.data_utils import WATCHMEN, build_collection_name

db = get_client(WATCHMEN)


def insert_topic_data(topic_name, mapping_result):
    collection_name = build_collection_name(topic_name)
    collection = db.get_collection(collection_name)
    return collection.insert(mapping_result)


def update_topic_data(topic_name, mapping_result, target_data):
    collection_name = build_collection_name(topic_name)
    collection = db.get_collection(collection_name)
    collection.update_one({"_id": target_data["_id"]}, {"$set": mapping_result})