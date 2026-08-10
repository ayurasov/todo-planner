"""
Единые экземпляры расширений Flask, создаваемые вне create_app(), чтобы
избежать circular imports между blueprints и приложением (стандартный
паттерн "app factory + extensions module").
"""

from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_cors import CORS
from flask_wtf import CSRFProtect

db = SQLAlchemy()
sess = Session()
cors = CORS()
csrf = CSRFProtect()
