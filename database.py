from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite 数据库文件名为 todo_v2.db
SQLALCHEMY_DATABASE_URL = "sqlite:///./todo_v2.db"

# 创建引擎（connect_args 是 SQLite 特有的多线程参数）
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 创建会话工厂（每一个请求都会用一个会话去操作数据库）
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 所有数据模型的基类
Base = declarative_base()
