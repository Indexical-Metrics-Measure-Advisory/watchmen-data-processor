from sqlalchemy import MetaData, Table, Column, String, Date, DateTime, Integer, JSON

from watchmen.common.oracle.oracle_engine import engine

metadata = MetaData()

users_table = Table("users", metadata,
                    Column('userid', String(60), primary_key=True),
                    Column('name', String(45), nullable=False),
                    Column('nickname', String(45), nullable=True),
                    Column('password', String(100), nullable=True),
                    Column('is_active', String(5), nullable=True),
                    Column('groupids', JSON, nullable=True),
                    Column('role', String(45), nullable=True),
                    Column('createtime', String(50), nullable=True),
                    Column('lastmodified', Date, nullable=True)
                    )

user_groups_table = Table("user_groups", metadata,
                          Column('usergroupid', String(60), primary_key=True),
                          Column('name', String(45), nullable=False),
                          Column('description', String(45), nullable=True),
                          Column('userids', JSON, nullable=True),
                          Column('spaceids', JSON, nullable=True),
                          Column('createtime', String(50), nullable=True),
                          Column('lastmodified', Date, nullable=True)
                          )

console_space_last_snapshot_table = Table("console_space_last_snapshot", metadata,
                                          Column('userid', String(60), primary_key=True),
                                          Column('language', String(5), nullable=True),
                                          Column('lastdashboardid', String(25), nullable=True),
                                          Column('admindashboardid', String(25), nullable=True),
                                          Column('favoritepin', String(5), nullable=True),
                                          Column('createtime', String(50), nullable=True),
                                          Column('lastmodified', Date, nullable=True)
                                          )

console_dashboards_table = Table("console_dashboards", metadata,
                                 Column('dashboardid', String(60), primary_key=True),
                                 Column('name', String(25), nullable=False),
                                 Column('reports', JSON, nullable=True),
                                 Column('paragraphs', JSON, nullable=True),
                                 Column('lastvisittime', String(25), nullable=False),
                                 Column('userid', String(60), nullable=False),
                                 Column('createtime', String(50), nullable=True),
                                 Column('lastmodified', DateTime, nullable=True)
                                 )

topics_table = Table("topics", metadata,
                     Column("topicid", String(60), primary_key=True),
                     Column("name", String(25), nullable=False),
                     Column("kind", String(10), nullable=True),
                     Column("type", String(10), nullable=True),
                     Column("description", String(50), nullable=True),
                     Column("factors", JSON, nullable=True),
                     Column('createtime', String(50), nullable=True),
                     Column('last_modified', DateTime, nullable=True),
                     Column('lastmodified', DateTime, nullable=True)
                     )

enums_table = Table("enums", metadata,
                    Column("enumid", String(60), primary_key=True),
                    Column("name", String(25), nullable=False),
                    Column("description", String(25), nullable=True),
                    Column("parentenumid", String(60), nullable=True),
                    Column("items", JSON, nullable=True),
                    Column('createtime', String(50), nullable=True),
                    Column('lastmodified', DateTime, nullable=True)
                    )

spaces_table = Table("spaces", metadata,
                     Column("spaceid", String(60), primary_key=True),
                     Column("topicids", JSON, nullable=True),
                     Column("groupids", JSON, nullable=True),
                     Column("name", String(25), nullable=False),
                     Column("description", String(25), nullable=True),
                     Column('createtime', String(50), nullable=True),
                     Column('last_modified', DateTime, nullable=True),
                     Column('lastmodified', DateTime, nullable=True)
                     )

console_space_favorites_table = Table("console_space_favorites", metadata,
                                      Column("userid", String(60), primary_key=True),
                                      Column("connectedspaceids", JSON, nullable=True),
                                      Column("dashboardids", JSON, nullable=True),
                                      Column('createtime', String(50), nullable=True),
                                      Column('last_modified', DateTime, nullable=True),
                                      Column('lastmodified', DateTime, nullable=True)
                                      )

console_space_graph_table = Table("console_space_graph", metadata,
                                  Column("connectid", String(60), primary_key=True),
                                  Column("topics", JSON, nullable=True),
                                  Column("subjects", JSON, nullable=True),
                                  Column("userid", String(60), nullable=False),
                                  Column('createtime', String(50), nullable=True),
                                  Column('last_modified', DateTime, nullable=True),
                                  Column('lastmodified', DateTime, nullable=True)
                                  )

console_spaces_table = Table("console_spaces", metadata,
                             Column("spaceid", String(60), primary_key=True),
                             Column("topics", JSON, nullable=True),
                             Column("groupids", JSON, nullable=True),
                             Column("name", String(25), nullable=False),
                             Column("connectid", String(25), nullable=False),
                             Column("type", String(10), nullable=True),
                             Column('lastvisittime', DateTime, nullable=True),
                             Column("userid", String(60), nullable=True),
                             Column("subjectids", JSON, nullable=True),
                             Column("subjects", JSON, nullable=True),
                             Column('createtime', String(50), nullable=True),
                             Column('last_modified', DateTime, nullable=True),
                             Column('lastmodified', DateTime, nullable=True)
                             )

pipelines_table = Table("pipelines", metadata,
                        Column("pipelineid", String(60), primary_key=True),
                        Column("topicid", String(60), nullable=False),
                        Column("name", String(25), nullable=False),
                        Column("type", String(10), nullable=True),
                        Column("stages", JSON, nullable=True),
                        Column("conditional", String(5), nullable=True),
                        Column("enabled", String(5), nullable=True),
                        Column("on", JSON, nullable=True),
                        Column('createtime', String(50), nullable=True),
                        Column('last_modified', DateTime, nullable=True),
                        Column('lastmodified', DateTime, nullable=True)
                        )

pipeline_graph_table = Table("pipeline_graph", metadata,
                             Column("userid", String(60), nullable=False),
                             Column("topics", JSON, nullable=True),
                             Column('lastmodified', DateTime, nullable=True),
                             Column('createtime', String(50), nullable=True)
                             )

console_space_subjects_table = Table("console_space_subjects", metadata,
                                     Column("subjectid", String(60), primary_key=True),
                                     Column("name", String(50), nullable=False),
                                     Column("topiccount", Integer, nullable=True),
                                     Column("graphicscount", Integer, nullable=True),
                                     Column("reports", JSON, nullable=True),
                                     Column("reportids", JSON, nullable=True),
                                     Column("dataset", JSON, nullable=True),
                                     Column("lastvisittime", DateTime, nullable=True),
                                     Column("createdat", String(50), nullable=True),
                                     Column('last_modified', DateTime, nullable=True),
                                     Column('lastmodifytime', DateTime, nullable=True),
                                     Column('lastmodified', DateTime, nullable=True),
                                     Column('createtime', String(50), nullable=True)
                                     )


def get_table_by_name(table_name):
    if table_name == "users":
        return users_table
    elif table_name == "console_space_last_snapshot":
        return console_space_last_snapshot_table
    elif table_name == "console_dashboards":
        return console_dashboards_table
    elif table_name == "topics":
        return topics_table
    elif table_name == "enums":
        return enums_table
    elif table_name == "spaces":
        return spaces_table
    elif table_name == "console_space_favorites":
        return console_space_favorites_table
    elif table_name == "console_space_graph":
        return console_space_graph_table
    elif table_name == "console_spaces":
        return console_spaces_table
    elif table_name == "user_groups":
        return user_groups_table
    elif table_name == "pipelines":
        return pipelines_table
    elif table_name == "pipeline_graph":
        return pipeline_graph_table
    elif table_name == "console_space_subjects":
        return console_space_subjects_table


def get_primary_key(table_name):
    if table_name == 'topics':
        return 'topicId'
    elif table_name == 'console_space_subjects':
        return 'subjectId'
    elif table_name == 'pipelines':
        return 'pipelineId'
    elif table_name == 'users':
        return 'userId'
    elif table_name == 'console_dashboards':
        return 'dashboardId'
    elif table_name == 'enums':
        return 'enumId'
    elif table_name == 'pipeline_graph':
        return 'userId'
    elif table_name == 'console_spaces':
        return 'connectId'
    elif table_name == 'console_space_favorites':
        return 'userId'
    elif table_name == 'spaces':
        return 'spaceId'
    elif table_name == 'console_space_subjects':
        return 'subjectId'
    elif table_name == 'console_reports':
        return 'reportId'
    elif table_name == 'user_groups':
        return 'userGroupId'


def get_topic_table_by_name(table_name):
    if table_name == "topic_raw_pipeline_monitor":
        return Table(table_name, metadata,
                     Column('UID', String(50), nullable=False, quote=True),
                     extend_existing=True, autoload=True, autoload_with=engine)
    else:
        return Table(table_name, metadata, extend_existing=True, autoload=True, autoload_with=engine)
