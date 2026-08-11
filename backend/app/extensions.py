"""Инициализация Flask extensions в одном месте."""

from flask_cors import CORS
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_migrate import Migrate


db = SQLAlchemy()
sess = Session()
cors = CORS()
csrf = CSRFProtect()
migrate = Migrate(compare_type=True)
