import logging
from typing import List

import arrow
from fastapi import APIRouter, Body, Depends
from pydantic import BaseModel

from watchmen.auth.service.user import sync_user_to_user_groups
from watchmen.auth.service.user_group import sync_user_group_to_space, sync_user_group_to_user
from watchmen.auth.storage.user import create_user_storage, query_users_by_name_with_pagination, get_user_list_by_ids, \
    get_user, load_user_list_by_name, update_user_storage, load_user_by_name
from watchmen.auth.storage.user_group import create_user_group_storage, query_user_groups_by_name_with_paginate, \
    get_user_group_list_by_ids, get_user_group, load_group_list_by_name, update_user_group_storage, \
    get_user_group_by_name
from watchmen.auth.user import User
from watchmen.auth.user_group import UserGroup
from watchmen.common import deps
from watchmen.common.data_page import DataPage
from watchmen.common.pagination import Pagination
from watchmen.common.presto.presto_utils import create_or_update_presto_schema_fields
from watchmen.common.security.pat.pat_service import createPAT, queryPAT, deletePAT
from watchmen.common.snowflake.snowflake import get_surrogate_key
from watchmen.common.utils.data_utils import check_fake_id, add_tenant_id_to_model, \
    compare_tenant, clean_password
from watchmen.console_space.storage.last_snapshot_storage import load_last_snapshot
from watchmen.dashborad.model.dashborad import ConsoleDashboard
from watchmen.dashborad.storage.dashborad_storage import load_dashboard_by_id
from watchmen.enum.model.enum import Enum
from watchmen.enum.storage.enum_storage import save_enum_to_storage, query_enum_list_with_pagination, load_enum_by_id, \
    load_enum_list
from watchmen.monitor.services.query_service import query_pipeline_monitor
from watchmen.pipeline.model.pipeline import Pipeline
from watchmen.pipeline.model.pipeline_flow import PipelineFlow
from watchmen.pipeline.model.pipeline_graph import PipelinesGraphics
from watchmen.pipeline.storage.pipeline_storage import update_pipeline, create_pipeline, load_pipeline_by_topic_id, \
    load_pipeline_list, load_pipeline_graph, create_pipeline_graph, update_pipeline_graph, update_pipeline_status, \
    update_pipeline_name, load_pipeline_by_id, remove_pipeline_graph
from watchmen.raw_data.service.generate_schema import create_raw_data_model_set, RawTopicGenerateEvent
from watchmen.report.model.report import Report
from watchmen.report.storage.report_storage import query_report_list_with_pagination, load_reports_by_ids
from watchmen.space.service.admin import create_space, update_space_by_id, sync_space_to_user_group
from watchmen.space.space import Space
from watchmen.space.storage.space_storage import query_space_with_pagination, get_space_by_id, get_space_list_by_ids, \
    load_space_list_by_name, load_space_by_name
from watchmen.topic.service.topic_service import create_topic_schema, update_topic_schema, build_topic
from watchmen.topic.storage.topic_schema_storage import query_topic_list_with_pagination, get_topic_by_id, \
    get_topic_list_by_ids, load_all_topic_list, load_topic_list_by_name, load_all_topic, load_topic_by_name
from watchmen.topic.topic import Topic

router = APIRouter()

log = logging.getLogger("app." + __name__)


class AdminDashboard(BaseModel):
    dashboard: ConsoleDashboard = None
    reports: List[Report] = []


class MonitorLogCriteria(BaseModel):
    topicId: str = None
    pipelineId: str = None
    startDate: str = None
    endDate: str = None
    status: str = None


class MonitorLogQuery(BaseModel):
    criteria: MonitorLogCriteria = None
    pagination: Pagination = None


# ADMIN
@router.post("/space", tags=["admin"], response_model=Space)
async def save_space(space: Space, current_user: User = Depends(deps.get_current_user)):
    space = add_tenant_id_to_model(space, current_user)
    if space.spaceId is None or check_fake_id(space.spaceId):
        # sync space group id
        result = create_space(space)
        sync_space_to_user_group(result, current_user)
        return result
    else:
        sync_space_to_user_group(space, current_user)
        return update_space_by_id(space.spaceId, space)


@router.post("/update/space", tags=["admin"], response_model=Space)
async def update_space(space_id, space: Space = Body(...), current_user: User = Depends(deps.get_current_user)):
    space = add_tenant_id_to_model(space, current_user)
    sync_space_to_user_group(space, current_user)
    return update_space_by_id(space_id, space)


@router.get("/space", tags=["admin"], response_model=Space)
async def load_space(space_id: str, current_user: User = Depends(deps.get_current_user)):
    return get_space_by_id(space_id, current_user)


@router.post("/space/name", tags=["admin"], response_model=DataPage)
async def query_space_list(query_name: str, pagination: Pagination = Body(...),
                           current_user: User = Depends(deps.get_current_user)):
    result = query_space_with_pagination(query_name, pagination, current_user)
    return result


@router.post("/space/ids", tags=["admin"], response_model=List[Space])
async def query_space_list_by_ids(space_ids: List[str], current_user: User = Depends(deps.get_current_user)):
    return get_space_list_by_ids(space_ids, current_user)


@router.get("/query/space/group", tags=["admin"], response_model=List[Space])
async def query_space_list_for_user_group(query_name: str, current_user: User = Depends(deps.get_current_user)):
    return load_space_list_by_name(query_name, current_user)


@router.post("/space/list/name", tags=["admin"], response_model=List[Space])
async def load_space_list_by_name_list(name_list: List[str], current_user: User = Depends(deps.get_current_user)) -> \
        List[Space]:
    results = []
    for name in name_list:
        results.append(load_space_by_name(name, current_user))
    return results


# Topic

@router.get("/topic", tags=["admin"], response_model=Topic)
async def load_topic(topic_id, current_user: User = Depends(deps.get_current_user)):
    return get_topic_by_id(topic_id, current_user)


@router.post("/topic", tags=["admin"], response_model=Topic)
async def create_topic(topic: Topic, current_user: User = Depends(deps.get_current_user)):
    topic = add_tenant_id_to_model(topic, current_user)
    return create_topic_schema(topic)


@router.post("/save/topic", tags=["admin"], response_model=Topic)
async def save_topic(topic: Topic, current_user: User = Depends(deps.get_current_user)):
    topic = add_tenant_id_to_model(topic, current_user)
    if topic.topicId is None or check_fake_id(topic.topicId):
        result = create_topic_schema(topic)
        create_or_update_presto_schema_fields(result)
        return result
    else:
        topic = Topic.parse_obj(topic)
        data = update_topic_schema(topic.topicId, topic)
        create_or_update_presto_schema_fields(data)
        return data


@router.post("/update/topic", tags=["admin"], response_model=Topic)
async def update_topic(topic_id, topic: Topic = Body(...), current_user: User = Depends(deps.get_current_user)):
    topic = Topic.parse_obj(topic)
    topic = add_tenant_id_to_model(topic, current_user)
    data = update_topic_schema(topic_id, topic)
    create_or_update_presto_schema_fields(data)
    return data


@router.post("/topic/name", tags=["admin"], response_model=DataPage)
async def query_topic_list_by_name(query_name: str, pagination: Pagination = Body(...),
                                   current_user: User = Depends(deps.get_current_user)):
    result = query_topic_list_with_pagination(query_name, pagination, current_user)
    return result


@router.get("/topic/query", tags=["admin"], response_model=List[Topic])
async def load_topic_list_by_name_without_page(query_name, current_user: User = Depends(deps.get_current_user)):
    return load_topic_list_by_name(query_name, current_user)


@router.post("/topic/list/name", tags=["admin"], response_model=List[Topic])
async def load_topic_list_by_name_list(name_list: List[str], current_user: User = Depends(deps.get_current_user)) -> \
        List[Topic]:
    results = []
    for name in name_list:
        results.append(load_topic_by_name(name, current_user))
    return results


@router.post("/report/name", tags=["admin"], response_model=DataPage)
async def query_topic_list_by_name(query_name: str, pagination: Pagination = Body(...),
                                   current_user: User = Depends(deps.get_current_user)):
    return query_report_list_with_pagination(query_name, pagination, current_user)


@router.get("/topic/all", tags=["admin"], response_model=List[Topic])
async def query_all_topic_list(current_user: User = Depends(deps.get_current_user)):
    result = load_all_topic(current_user)
    return result


@router.post("/topic/all/pages", tags=["admin"], response_model=DataPage)
async def query_topic_list_for_pipeline(pagination: Pagination, current_user: User = Depends(deps.get_current_user)):
    result = load_all_topic_list(pagination, current_user)
    return result


@router.get("/query/topic/space", tags=["admin"], response_model=List[Topic])
async def query_topic_list_for_space(query_name: str, current_user: User = Depends(deps.get_current_user)):
    return load_topic_list_by_name(query_name, current_user)


@router.post("/topic/ids", tags=["admin"], response_model=List[Topic])
async def query_topic_list_by_ids(topic_ids: List[str], current_user: User = Depends(deps.get_current_user)):
    return get_topic_list_by_ids(topic_ids, current_user)


# User

@router.post("/user", tags=["admin"], response_model=User)
async def save_user(user: User, current_user: User = Depends(deps.get_current_user)) -> User:
    if user.userId is None or check_fake_id(user.userId):
        if current_user.tenantId is not None:
            user.tenantId = current_user.tenantId
        result = create_user_storage(user)
        sync_user_to_user_groups(result)
        return result
    else:
        sync_user_to_user_groups(user)
        return update_user_storage(user)


@router.post("/user/name", tags=["admin"], response_model=DataPage)
async def query_user_list_by_name(query_name: str, pagination: Pagination = Body(...),
                                  current_user: User = Depends(deps.get_current_user)):
    return query_users_by_name_with_pagination(query_name, pagination, current_user)


@router.post("/user/ids", tags=["admin"], response_model=List[User])
async def query_user_list_by_ids(user_ids: List[str], current_user: User = Depends(deps.get_current_user)):
    list_user = get_user_list_by_ids(user_ids, current_user)
    # lambda user : user.password = None ,
    return clean_password(list_user)


@router.get("/user", tags=["admin"], response_model=User)
async def load_user(user_id: str, current_user: User = Depends(deps.get_current_user)):
    return get_user(user_id)


@router.get("/query/user/group", tags=["admin"], response_model=List[User])
async def query_user_list_for_user_group(query_name, current_user: User = Depends(deps.get_current_user)):
    return load_user_list_by_name(query_name, current_user)


# User Group

@router.post("/user_group", tags=["admin"], response_model=UserGroup)
async def save_user_group(user_group: UserGroup, current_user: User = Depends(deps.get_current_user)):
    user_group = add_tenant_id_to_model(user_group, current_user)
    if check_fake_id(user_group.userGroupId):
        user_group.userGroupId = None
    if user_group.userGroupId is None or check_fake_id(user_group.userGroupId):
        result = create_user_group_storage(user_group)
        sync_user_group_to_space(result, current_user)
        sync_user_group_to_user(result, current_user)
        return result
    else:
        sync_user_group_to_space(user_group, current_user)
        sync_user_group_to_user(user_group, current_user)
        return update_user_group_storage(user_group)


@router.post("/update/user_group", tags=["admin"], response_model=UserGroup)
async def update_user_group(user_group: UserGroup, current_user: User = Depends(deps.get_current_user)):
    user_group = add_tenant_id_to_model(user_group, current_user)
    sync_user_group_to_space(user_group, current_user)
    sync_user_group_to_user(user_group, current_user)
    return update_user_group_storage(user_group)


@router.get("/query/user_group/space", tags=["admin"], response_model=List[UserGroup])
async def query_group_list_for_space(query_name: str, current_user: User = Depends(deps.get_current_user)):
    return load_group_list_by_name(query_name, current_user)


@router.get("/user_group", tags=["admin"], response_model=UserGroup)
async def load_user_group(user_group_id, current_user: User = Depends(deps.get_current_user)):
    user_group = get_user_group(user_group_id, current_user)
    if compare_tenant(user_group, current_user):
        return user_group
    else:
        raise Exception("tenant is not same")


@router.post("/user_groups/ids", tags=["admin"], response_model=List[UserGroup])
async def query_user_groups_by_ids(user_group_ids: List[str], current_user: User = Depends(deps.get_current_user)):
    return get_user_group_list_by_ids(user_group_ids, current_user)


@router.post("/user_group/name", tags=["admin"], response_model=DataPage)
async def query_user_groups_list_by_name(query_name: str, pagination: Pagination = Body(...),
                                         current_user: User = Depends(deps.get_current_user)):
    return query_user_groups_by_name_with_paginate(query_name, pagination, current_user)


@router.post("/user_group/list/name", tags=["admin"], response_model=List[UserGroup])
async def load_user_group_list_by_name_list(name_list: List[str],
                                            current_user: User = Depends(deps.get_current_user)) -> List[UserGroup]:
    results = []
    for name in name_list:
        results.append(get_user_group_by_name(name, current_user))
    return results


@router.post("/user/list/name", tags=["admin"], response_model=List[User])
async def load_user_list_by_name_list(name_list: List[str], current_user: User = Depends(deps.get_current_user)) -> \
        List[User]:
    results = []
    for name in name_list:
        results.append(load_user_by_name(name))

    return clean_password(results)


# pipeline

@router.post("/pipeline", tags=["admin"], response_model=Pipeline)
async def save_pipeline(pipeline: Pipeline, current_user: User = Depends(deps.get_current_user)):
    pipeline = add_tenant_id_to_model(pipeline, current_user)
    if check_fake_id(pipeline.pipelineId):
        return create_pipeline(pipeline)
    else:
        return update_pipeline(pipeline)


@router.get("/pipeline", tags=["admin"], response_model=PipelineFlow)
async def load_pipeline(topic_id, current_user: User = Depends(deps.get_current_user)):
    result = load_pipeline_by_topic_id(topic_id, current_user)
    pipeline_list_produce = [*result]
    for pipeline in result:
        for stage in pipeline.stages:
            for unit in stage.units:
                for action in unit.do:
                    result = load_pipeline_by_topic_id(action.topicId, current_user)
                    pipeline_list_produce = [*pipeline_list_produce, *result]

    return {"topicId": topic_id, "consume": [], "produce": pipeline_list_produce}


@router.get("/pipeline/id", tags=["admin"], response_model=Pipeline)
async def load_pipeline_by_pipeline_id(pipeline_id, current_user: User = Depends(deps.get_current_user)):
    return load_pipeline_by_id(pipeline_id, current_user)


@router.get("/pipeline/all", tags=["admin"], response_model=List[Pipeline])
async def load_all_pipelines(current_user: User = Depends(deps.get_current_user)):
    return load_pipeline_list(current_user)


@router.get("/pipeline/enabled", tags=["admin"])
async def update_pipeline_enabled(pipeline_id, enabled, current_user: User = Depends(deps.get_current_user)):
    update_pipeline_status(pipeline_id, enabled)


@router.get("/pipeline/rename", tags=["admin"])
async def rename_pipeline(pipeline_id, name, current_user: User = Depends(deps.get_current_user)):
    update_pipeline_name(pipeline_id, name)


@router.post("/pipeline/graphics", tags=["admin"], response_model=PipelinesGraphics)
async def save_pipeline_graph(pipeline_graph: PipelinesGraphics, current_user: User = Depends(deps.get_current_user)):
    pipeline_graph = add_tenant_id_to_model(pipeline_graph, current_user)
    user_id = current_user.userId
    pipeline_graph.userId = user_id
    if check_fake_id(pipeline_graph.pipelineGraphId):
        pipeline_graph.pipelineGraphId = get_surrogate_key()
        return create_pipeline_graph(pipeline_graph)
    else:
        return update_pipeline_graph(pipeline_graph)


@router.get("/pipeline/graphics/delete", tags=["admin"])
async def delete_pipeline_graph(pipeline_graph_id: str):
    remove_pipeline_graph(pipeline_graph_id)


@router.get("/pipeline/graphics/me", tags=["admin"], response_model=List[PipelinesGraphics])
async def load_pipeline_graph_by_user(current_user: User = Depends(deps.get_current_user)):
    user_id = current_user.userId
    results = load_pipeline_graph(user_id, current_user)
    return results


@router.post("/enum/name", tags=["admin"], response_model=DataPage)
async def load_enum_list_by_name(query_name, pagination: Pagination = Body(...),
                                 current_user: User = Depends(deps.get_current_user)):
    return query_enum_list_with_pagination(query_name, pagination, current_user)


@router.get("/enum", tags=["admin"], response_model=Enum)
async def load_pipeline_by_pipeline_id(enum_id, current_user: User = Depends(deps.get_current_user)):
    return load_enum_by_id(enum_id, current_user)


# HOME Dashboard
@router.get("/home/dashboard", tags=["admin"], response_model=AdminDashboard)
async def load_admin_dashboard(current_user: User = Depends(deps.get_current_user)):
    result = load_last_snapshot(current_user.userId, current_user)
    if result is None:
        return None
    else:
        admin_dashboard_id = result.adminDashboardId
        dashboard = load_dashboard_by_id(admin_dashboard_id, current_user)
        if dashboard is not None:
            # report_ids = list(lambda x: return x.reportId,dashboard.reports)
            reports = load_reports_by_ids(list(map(lambda report: report.reportId, dashboard.reports)), current_user)
            return AdminDashboard(dashboard=dashboard, reports=reports)


## ENUM

@router.post("/enum", tags=["admin"], response_model=Enum)
async def save_enum(enum: Enum, current_user: User = Depends(deps.get_current_user)):
    enum = add_tenant_id_to_model(enum, current_user)
    return save_enum_to_storage(enum)


@router.get("/enum/id", tags=["admin"], response_model=dict)
async def load_enum(enum_id, current_user: User = Depends(deps.get_current_user)):
    return load_enum_by_id(enum_id, current_user)


@router.post("/enum/name", tags=["admin"], response_model=DataPage)
async def query_enum_list_by_name(query_name: str, pagination: Pagination = Body(...),
                                  current_user: User = Depends(deps.get_current_user)):
    return query_enum_list_with_pagination(query_name, pagination, current_user)


@router.get("/enum/all", tags=["admin"], response_model=List[Enum])
async def load_enum_all(current_user: User = Depends(deps.get_current_user)):
    return load_enum_list(current_user)


@router.post("/pat/create", tags=["admin"], response_model=dict)
async def pat_create(note: dict = Body(...), current_user: User = Depends(deps.get_current_user)):
    return createPAT(note['note'], current_user.userId, current_user.name, current_user.tenantId)


@router.get("/pat/list", tags=["admin"], response_model=list)
async def pat_list(current_user: User = Depends(deps.get_current_user)):
    results = []
    pats = queryPAT(current_user.tenantId)
    for pat in pats:
        results.append({"patId": pat.patId, "note": pat.note, "token": pat.tokenId})
    return results


@router.post("/pat/delete", tags=["admin"], response_model=dict)
async def pat_delete(pat_id: str, current_user: User = Depends(deps.get_current_user)):
    return deletePAT(pat_id)


@router.post("/topic/raw/generation", tags=["common"])
async def create_raw_topic_schema(event: RawTopicGenerateEvent, current_user: User = Depends(deps.get_current_user)):
    json_list = []
    for data in event.data:
        json_list.append(data)
    # print(len(json_list))
    result = create_raw_data_model_set(event.code, json_list)
    return build_topic(result, current_user)


### LOG
## TODO tenantId for log
@router.post("/pipeline/log/query", tags=["admin"])
async def query_log_by_critical(query: MonitorLogQuery):
    query_dict = {}
    query_list = []
    if query.criteria.topicId is not None:
        query_list.append({"topicId": query.criteria.topicId})
    if query.criteria.pipelineId is not None:
        query_list.append({"pipelineId": query.criteria.pipelineId})
    if query.criteria.startDate is not None and query.criteria.endDate is not None:
        query_list.append({"sys_insertTime": {
            "between": (
                arrow.get(query.criteria.startDate).datetime.replace(tzinfo=None),
                arrow.get(query.criteria.endDate).datetime.replace(tzinfo=None)
            )
        }})
    if query.criteria.status is not None:
        query_list.append({"status": query.criteria.status.upper()})
    if len(query_list) > 1:
        query_dict['and'] = query_list
    else:
        query_dict = query_list[0]
    return query_pipeline_monitor("raw_pipeline_monitor", query_dict, query.pagination)
