from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# DB에 접근하기 위한 객체입니다.

db = SQLAlchemy()
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost:3306/MM'
app.config['SQLALCHEMY_ECHO'] = True
db.init_app(app)


class OptionDAO(db.Model):
    __tablename__ = "DEAL_TABLE"
    __table_args__ = {'extend_existing': True}
    inisCd = db.Column(db.String(45), primary_key=True)
    inisNm = db.Column(db.String(45), nullable=False)
    inisType = db.Column(db.String(45), nullable=False, unique=True)
    insCd = db.Column(db.String(45), nullable=False)
    posType = db.Column(db.String(1), nullable=False)
    matDt = db.Column(db.String(45))
    atmCd = db.Column(db.String(45))
    strike = db.Column(db.Integer)
    status = db.Column(db.Integer)
    baseDt = db.Column(db.String(45))

    def __init__(self, dto):
        self.inisCd  = dto.inisCd
        self.inisNm  = dto.inisNm
        self.inisType= dto.inisType
        self.insCd   = dto.insCd
        self.matDt   = dto.matDt
        self.atmCd   = dto.atmCd
        self.strike  = dto.strike
        self.posType = dto.posType
        self.status  = dto.status
        self.baseDt   = dto.baseDt


class FutureDAO(db.Model):
    __tablename__ = "DEAL_TABLE"
    __table_args__ = {'extend_existing': True}
    inisCd = db.Column(db.String(45), primary_key=True)
    inisNm = db.Column(db.String(45), nullable=False)
    inisType = db.Column(db.String(45), nullable=False, unique=True)
    insCd = db.Column(db.String(45), nullable=False)
    matDt = db.Column(db.String(45))
    baseDt = db.Column(db.String(45))

    def __init__(self, dto):
        self.inisCd  = dto.inisCd
        self.inisNm  = dto.inisNm
        self.inisType= dto.inisType
        self.insCd   = dto.insCd
        self.matDt   = dto.matDt
        self.baseDt   = dto.baseDt


class EquityDAO(db.Model):
    __tablename__ = "DEAL_TABLE"
    __table_args__ = {'extend_existing': True}
    inisCd = db.Column(db.String(45), primary_key=True)
    inisNm = db.Column(db.String(45), nullable=False)
    inisType = db.Column(db.String(45), nullable=False, unique=True)
    baseDt = db.Column(db.String(45))

    def __init__(self, dto):
        self.inisType= dto.inisType
        self.inisCd  = dto.inisCd
        self.inisNm  = dto.inisNm
        self.baseDt   = dto.baseDt
