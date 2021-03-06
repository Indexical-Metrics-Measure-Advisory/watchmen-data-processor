import logging
import time
import traceback
from datetime import datetime
from functools import lru_cache

import watchmen
from watchmen.common.constants import pipeline_constants
from watchmen.common.snowflake.snowflake import get_surrogate_key
from watchmen.config.config import settings, PROD
from watchmen.monitor.model.pipeline_monitor import PipelineRunStatus, StageRunStatus
from watchmen.monitor.services import pipeline_monitor_service
from watchmen.pipeline.core.context.pipeline_context import PipelineContext
from watchmen.pipeline.core.context.stage_context import StageContext
from watchmen.pipeline.core.parameter.parse_parameter import parse_parameter_joint
from watchmen.pipeline.core.worker.stage_worker import run_stage
from watchmen.pipeline.model.trigger_type import TriggerType
from watchmen.pipeline.utils.constants import PIPELINE_UID, FINISHED, ERROR
from watchmen.topic.storage.topic_schema_storage import get_topic_by_id

log = logging.getLogger("app." + __name__)


@lru_cache(maxsize=20)
def __build_merge_key(topic_name, trigger_type):
    return topic_name + "_" + trigger_type.value


def __merge_pipeline_data(pipeline_trigger_merge_list):
    merge_context = {}
    id_dict = {}
    for pipeline_data in pipeline_trigger_merge_list:
        # print("-----pipeline", pipeline_data)
        # key = __build_merge_key(pipeline_data.topicName, pipeline_data.triggerType)
        if pipeline_data.topicName in merge_context:
            data_list = merge_context[pipeline_data.topicName].get(pipeline_data.triggerType.value, [])
            data_list.append(pipeline_data.data)
            merge_context[pipeline_data.topicName][pipeline_data.triggerType.value] = data_list
        else:
            merge_context[pipeline_data.topicName] = {pipeline_data.triggerType.value: [pipeline_data.data]}
    # print(merge_context)
    return merge_context


def __build_merge_key(topic_name, trigger_type):
    return topic_name + "_" + trigger_type.value


def __get_unique_key_name() -> str:
    if settings.STORAGE_ENGINE == "mongo":
        return "_id"
    else:
        return "id_"


def __trigger_all_pipeline(pipeline_trigger_merge_list):
    after_merge_list = __merge_pipeline_data(pipeline_trigger_merge_list)

    for topic_name, item in after_merge_list.items():
        merge_data = {}
        if TriggerType.update.value in item:
            for update_data in item[TriggerType.update.value]:
                old_value = update_data[pipeline_constants.OLD]
                pk = old_value[__get_unique_key_name()]
                if pk in merge_data:
                    merge_data[pk][pipeline_constants.NEW].update(update_data[pipeline_constants.NEW])
                else:
                    merge_data[pk] = {pipeline_constants.NEW: update_data[pipeline_constants.NEW],
                                      pipeline_constants.OLD: update_data[pipeline_constants.OLD]}

                for key, data in merge_data.items():
                    watchmen.pipeline.index.trigger_pipeline(topic_name, data, TriggerType.update)
        if TriggerType.insert.value in item:
            for insert_data in item[TriggerType.insert.value]:
                watchmen.pipeline.index.trigger_pipeline(topic_name, insert_data, TriggerType.insert)


def should_run(pipeline_context: PipelineContext) -> bool:
    pipeline = pipeline_context.pipeline
    if pipeline.on is None:
        return True
    current_data = pipeline_context.currentOfTriggerData
    variables = pipeline_context.variables
    return parse_parameter_joint(pipeline.on, current_data, variables)


def run_pipeline(pipeline_context: PipelineContext):
    pipeline = pipeline_context.pipeline
    data = pipeline_context.data
    pipeline_status = PipelineRunStatus(pipelineId=pipeline.pipelineId, uid=get_surrogate_key(),
                                        startTime=datetime.now().replace(tzinfo=None), topicId=pipeline.pipelineId)
    pipeline_status.oldValue = data[pipeline_constants.OLD]
    pipeline_status.newValue = data[pipeline_constants.NEW]

    if pipeline.enabled:
        pipeline_topic = get_topic_by_id(pipeline.topicId)
        pipeline_context = PipelineContext(pipeline, data)
        pipeline_context.variables[PIPELINE_UID] = pipeline_status.uid
        pipeline_context.pipelineTopic = pipeline_topic
        pipeline_context.pipelineStatus = pipeline_status
        start = time.time()
        if should_run(pipeline_context):
            try:
                for stage in pipeline.stages:
                    stage_run_status = StageRunStatus(name=stage.name)
                    stage_context = StageContext(pipeline_context, stage, stage_run_status)
                    run_stage(stage_context)
                    pipeline_status.stages.append(stage_context.stageStatus)

                elapsed_time = time.time() - start
                pipeline_status.completeTime = elapsed_time
                pipeline_status.status = FINISHED

                log.info("run pipeline \"{0}\" spend time \"{1}\" ".format(pipeline.name, elapsed_time))
                if pipeline_topic.kind is None or pipeline_topic.kind != pipeline_constants.SYSTEM:
                    __trigger_all_pipeline(pipeline_context.pipeline_trigger_merge_list)

            except Exception as e:
                log.error(e)
                raise e
                pipeline_status.error = traceback.format_exc()
                pipeline_status.status = ERROR
            finally:
                if pipeline_topic.kind is not None and pipeline_topic.kind == pipeline_constants.SYSTEM:
                    log.debug("pipeline_status is {0}".format(pipeline_status))
                else:
                    sync_pipeline_monitor_log(pipeline_status)


def sync_pipeline_monitor_log(pipeline_status):
    if settings.ENVIRONMENT == PROD and pipeline_status.status != ERROR:
        log.debug("pipeline_status is {0}".format(pipeline_status))
    else:
        pipeline_monitor_service.sync_pipeline_monitor_data(pipeline_status)
