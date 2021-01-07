from pydantic import BaseModel

from watchmen.common.mongo_model import MongoModel


class User(MongoModel):
    userId: int = None
    name: str = None
    nickName: str = None
    password: str = None
    is_active: bool = True
    groupIds: list = None

    # userId?: string;
    # name?: string;
    # nickName?: string;
