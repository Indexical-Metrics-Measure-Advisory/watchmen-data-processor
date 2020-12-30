from watchmen.space.space import Space
from watchmen.space.storage.space_storage import insert_space_to_storage, update_space_to_storage, load_space_by_name
from watchmen.topic.storage.topic_schema_storage import save_topic


def add_topic_to_master():
    pass


def remove_from_master():
    pass


def update_topic_to_master():
    pass


def load_master_space(space_name):
    return load_space_by_name(space_name)


def add_factor_to_master_topic():
    pass


def create_space_by_domain_template(user, domain):
    master_space = Space()
    master_space.createUser = user
    master_space.name = user+"_"+domain
    # save_master_space(master_space)
    # master_space.id = inserted_id
    return master_space


def add_topic_to_master_space(topic, master_space):
    master_space.topic_list.append(topic)
    update_space_to_storage(master_space)


def add_topic_list_to_master(topic_list, master_space):

    topic_id_list =[]
    for topic in topic_list:
        insert_id =str(save_topic(topic.dict()).inserted_id)
        topic_id_list.append(insert_id)

    print(topic_id_list)
    master_space.topic_id_list = topic_id_list
    insert_space_to_storage(master_space).inserted_id
    # master_space.id = inserted_id
    return master_space


def get_summary_for_master_space(master_space):
    return master_space
