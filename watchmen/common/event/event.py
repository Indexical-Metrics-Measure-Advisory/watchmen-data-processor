from watchmen.common.mongo_model import MongoModel


class Event(MongoModel):
    type: str = None
    description: str = None
    # time: datetime = None


def before(func):
    def run_before():
        print("run_before")
        return func()

    return run_before


def after(func):
    def run_after(request):
        result = func(request)
        print("run  event ", request)
        ## base on request type switch
        return result

    return run_after
