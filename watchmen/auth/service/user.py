from fastapi import HTTPException
from starlette import status

from watchmen.auth.service.security import verify_password
from watchmen.auth.storage.user import load_user_by_name
from watchmen.auth.storage.user_group import USER_GROUPS, get_user_group_list_by_ids, update_user_group_storage
from watchmen.auth.user import User
from watchmen.auth.user_group import UserGroup
# from watchmen.common import deps
from watchmen.common.storage.storage_template import pull_update


def authenticate(username, password):
    user = load_user_by_name(username)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    else:
        user = User.parse_obj(user)
        if verify_password(password, user.password):
            return User.parse_obj(user)
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


# def __is_initialized(db=Depends(deps.get_db)):
#     pass
#     # db.get_connection
#
#
# def init_superuser():
#     pass
#
#     if __is_initialized():
#         pass


def sync_user_to_user_groups(user: User):
    '''
    update_many(collection_name=USER_GROUPS, query_dict={"userIds": {"$in": [user.userId]}},
                update_dict={"$pull": {"userIds": {"$in": [user.userId]}}})
    '''
    pull_update({"userIds": {"in": [user.userId]}}, {"userIds": {"in": [user.userId]}}, UserGroup, USER_GROUPS)

    user_groups = get_user_group_list_by_ids(user.groupIds)
    for user_group in user_groups:
        if user.userId not in user_group.userIds:
            user_group.userIds.append(user.userId)
            update_user_group_storage(user_group)
