
from datetime import timedelta;
import os;

#databaseURL=os.environ["DATABASE_URL"]

class Configuration():
    #SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:root@{databaseURL}/baza";
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:root@localhost/elections";
    REDIS_HOST = "localhost";
    REDIS_THREADS_LIST = "threads"
    JWT_SECRET_KEY="Slike Kusadasi";
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=60);
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30);
