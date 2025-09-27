from sqlalchemy import create_engine
from sqlmodel import SQLModel

engine=create_engine(url='mysql+pymysql://root:hoj123456@localhost:3306/PyClass')
SQLModel.metadata.create_all(engine)