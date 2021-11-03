
from datetime import timedelta;
import os;

databaseURL=os.environ["DATABASE_URL_AUTHENTIFICATION"]
asd=os.environ["REDIS_URL"];
class Configuration():
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:root@{databaseURL}/elections";
    #SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:root@localhost/elections";
    REDIS_HOST = asd;
    REDIS_VOTES_LIST = "votes"
    JWT_SECRET_KEY="Slike Kusadasi";
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=60);
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30);
