from bson import json_util
from fastapi import APIRouter, Body
from pydantic import BaseModel

from watchmen.auth.storage.user import create_user_storage, query_users_by_name_with_pagination
from watchmen.auth.storage.user_group import create_user_group_storage, query_user_groups_by_name_with_paginate
from watchmen.auth.user import User
from watchmen.auth.user_group import UserGroup
from watchmen.common.data_page import DataPage
from watchmen.common.pagination import Pagination
from watchmen.index import generate_suggestion_topic_service, generate_suggestion_factor
from watchmen.raw_data.model_schema import ModelSchema
from watchmen.raw_data.model_schema_set import ModelSchemaSet
from watchmen.space.service.admin import create_space, update_space_by_id
from watchmen.space.space import Space
from watchmen.space.storage.space_storage import query_space_with_pagination
from watchmen.topic.service.topic_service import create_topic_schema, update_topic_schema
from watchmen.topic.storage.topic_schema_storage import query_topic_list_with_pagination
from watchmen.topic.topic import Topic

router = APIRouter()


class TopicSuggestionIn(BaseModel):
    lake_schema_set: ModelSchemaSet = None
    master_schema: Space = None


class FactorSuggestionIn(BaseModel):
    lake_schema: ModelSchema = None
    topic: Topic = None



async def add_topic_to_space():
    pass


async def add_topic_list_to_space():
    pass


@router.post("/admin/suggestion/topic", tags=["admin"])
async def generate_suggestion_topic(topic_suggestion: TopicSuggestionIn):
    return generate_suggestion_topic_service(topic_suggestion.lake_schema, topic_suggestion.master_schema)


@router.post("/admin/suggestion/factors", tags=["admin"])
async def generate_suggestion_factor(factor_suggestion: FactorSuggestionIn):
    return generate_suggestion_factor(factor_suggestion.lake_schema, factor_suggestion.topic)


async def create_pipeline():
    pass


async def add_stage_to_pipeline():
    pass


async def save_stage():
    pass


#
# @router.post("/mapping/topic", tags=["admin"])
# async def save_topic_mapping_http(topic_mapping_rule: TopicMappingRule):
#     return save_topic_mapping(topic_mapping_rule)
#
#
# @router.get("/mapping/topic", tags=["admin"], response_model=TopicMappingRule)
# async def load_topic_mapping_http(temp_topic_name: str, topic_name: str):
#     return load_topic_mapping(temp_topic_name, topic_name)


### NEW
@router.post("/space", tags=["admin"],response_model=Space)
async def create_empty_space(space: Space):
    return create_space(space)


@router.post("/update/space", tags=["admin"],response_model=Space)
async def update_space(space_id: int, space: Space = Body(...)):
    return update_space_by_id(space_id, space)


@router.post("/space/name", tags=["admin"], response_model=DataPage)
async def query_space_list(query_name: str, pagination: Pagination = Body(...)):
    result = query_space_with_pagination(query_name, pagination)
    return await __build_data_pages(pagination, result)


@router.post("/topic", tags=["admin"],response_model=Topic)
async def create_topic(topic: Topic):
    return create_topic_schema(topic)


@router.post("/update/topic", tags=["admin"],response_model=Topic)
async def update_topic(topic_id, topic: Topic = Body(...)):
    topic = Topic.parse_obj(topic)
    return update_topic_schema(topic_id, topic)


@router.post("/topic/name", tags=["admin"],response_model=DataPage)
async def query_topic_list_by_name(query_name: str, pagination: Pagination = Body(...)):
    result = query_topic_list_with_pagination(query_name, pagination)
    return await __build_data_pages(pagination, result)


async def __build_data_pages(pagination, result):
    data_page = DataPage()
    if len(result) > 0:
        data_page.data = result
        data_page.itemCount = len(result)
        data_page.pageSize = pagination.pageSize
        data_page.pageNumber = pagination.pageNumber
        return data_page
    else:
        return data_page


@router.post("/user", tags=["admin"],response_model=User)
async def create_user(user: User):
    return create_user_storage(user)


@router.post("/user_group", tags=["admin"],response_model=UserGroup)
async def create_user_group(user_group: UserGroup):
    return create_user_group_storage(user_group)


@router.post("/user/name", tags=["admin"],response_model=DataPage)
async def query_user_list_by_name(query_name: str, pagination: Pagination = Body(...)):
    result = query_users_by_name_with_pagination(query_name, pagination)
    return await __build_data_pages(pagination, result)


@router.post("/user_group/name", tags=["admin"],response_model=DataPage)
async def query_user_groups_list_by_name(query_name: str, pagination: Pagination = Body(...)):
    result = query_user_groups_by_name_with_paginate(query_name, pagination)
    return await __build_data_pages(pagination, result)
