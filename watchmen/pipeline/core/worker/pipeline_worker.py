import json
import logging
import time
import traceback
from datetime import datetime

import watchmen
from watchmen.pipeline.core.parameter.parse_parameter import parse_parameter_joint
from watchmen.common.constants import pipeline_constants
from watchmen.common.snowflake.snowflake import get_surrogate_key
from watchmen.monitor.model.pipeline_monitor import PipelineRunStatus, StageRunStatus
from watchmen.pipeline.core.context.pipeline_context import PipelineContext
from watchmen.pipeline.core.context.stage_context import StageContext
from watchmen.pipeline.core.worker.stage_worker import run_stage
from watchmen.pipeline.single.pipeline_service import __trigger_all_pipeline
from watchmen.pipeline.single.stage.unit.utils import PIPELINE_UID, FINISHED, ERROR
from watchmen.topic.storage.topic_schema_storage import get_topic_by_id

log = logging.getLogger("app." + __name__)


def should_run(pipelineContext: PipelineContext) -> bool:
    pipeline = pipelineContext.pipeline
    if pipeline.on is None:
        return True
    current_data = pipelineContext.currentOfTriggerData
    variables = pipelineContext.variables
    return parse_parameter_joint(pipeline.on, current_data, variables)


def run_pipeline(pipelineContext: PipelineContext):
    pipeline = pipelineContext.pipeline

    # print(pipeline.json())
    data = pipelineContext.data
    pipeline_status = PipelineRunStatus(pipelineId=pipeline.pipelineId, uid=get_surrogate_key(),
                                        startTime=datetime.now().replace(tzinfo=None), topicId=pipeline.pipelineId)
    pipeline_status.oldValue = data[pipeline_constants.OLD]
    pipeline_status.newValue = data[pipeline_constants.NEW]

    if pipeline.enabled:
        pipeline_topic = get_topic_by_id(pipeline.topicId)
        # log.info("start run pipeline {0}".format(pipeline.name))
        pipelineContext = PipelineContext(pipeline, data)
        pipelineContext.variables[PIPELINE_UID] = pipeline_status.uid
        pipelineContext.pipelineTopic = pipeline_topic
        pipelineContext.pipelineStatus = pipeline_status
        start = time.time()
        if should_run(pipelineContext):
            try:
                for stage in pipeline.stages:
                    stage_run_status = StageRunStatus(name=stage.name)
                    stageContext = StageContext(pipelineContext, stage, stage_run_status)
                    run_stage(stageContext)
                    pipeline_status.stages.append(stageContext.stageStatus)

                elapsed_time = time.time() - start
                pipeline_status.completeTime = elapsed_time
                pipeline_status.status = FINISHED
                # log.debug("pipeline_status {0} time :{1}".format(pipeline.name, elapsed_time))

                log.info("run pipeline \"{0}\" spend time \"{1}\" ".format(pipeline.name, elapsed_time))
                if pipeline_topic.kind is None or pipeline_topic.kind != pipeline_constants.SYSTEM:
                    __trigger_all_pipeline(pipelineContext.pipeline_trigger_merge_list)

            except Exception as e:
                log.exception(e)
                pipeline_status.error = traceback.format_exc()
                pipeline_status.status = ERROR
            finally:
                if pipeline_topic.kind is not None and pipeline_topic.kind == pipeline_constants.SYSTEM:
                    log.debug("pipeline_status is {0}".format(pipeline_status))
                    # pass
                else:
                    watchmen.monitor.services.pipeline_monitor_service.sync_pipeline_monitor_data(pipeline_status)
                    # pass
