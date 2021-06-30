import logging
import time

from pydantic import BaseModel

from watchmen.database.storage.exception.exception import OptimisticLockError

log = logging.getLogger("app." + __name__)


class RetryPolicy(BaseModel):
    max_attempts: int = 3


class BackoffPolicy(BaseModel):
    sleep: int = 1


def backoff(backoffpolicy: BackoffPolicy):
    seconds_ = backoffpolicy.sleep
    time.sleep(seconds_)


def retry_or_not(count_: int, retry_policy: RetryPolicy):
    if count_ < retry_policy.max_attempts:
        return True
    else:
        return False


def retry_template(retry_callback: tuple, recovery_callback: tuple, retry_policy: RetryPolicy):
    def execute():
        need_retry = True
        count_ = 0
        while need_retry:
            try:
                retry_callback[0](*retry_callback[1])
                need_retry = False
            except OptimisticLockError as err:
                try:
                    if retry_or_not(count_, retry_policy):
                        need_retry = True
                        count_ = count_ + 1
                        log.info("this can be retried")
                        backoff(BackoffPolicy())
                    else:
                        need_retry = False
                except Exception as e:
                    raise RuntimeError("update retry failed")
        if count_ == 3:
            return recovery_callback[0](*recovery_callback[1])

    return execute
