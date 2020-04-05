# coding=UTF-8

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import pymysql
from app.config import MYSQLHOST
from app.config import MONGODBHOST
from flask_pymongo import PyMongo


pymysql.install_as_MySQLdb()
db = SQLAlchemy()

app = Flask(__name__)
# 配置启动模式为调试模式
app.config["DEBUG"] = False
# 配置数据库连接
app.config['SQLALCHEMY_DATABASE_URI'] = MYSQLHOST
# 配置数据库自动提交
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
# session配置key
app.config["SECRET_KEY"] = "mysite2"
# 数据库初始化
db.init_app(app)
mongo = PyMongo(app, uri=MONGODBHOST)
