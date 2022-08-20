from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select, func, and_

# DB에 접근하기 위한 객체입니다.

db = SQLAlchemy()
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost:3306/MM'
app.config['SQLALCHEMY_ECHO'] = True
db.init_app(app)

# <!--EquityInfo : 종목명, 종목코드, 기준가, 상한가, 하한가, 전일거래대금, 전일거래량, 증권그룹ID, 날짜-->
# <!--FuturesInfo : 종목명, 종목코드, 기준가, 상한가 (1~3단계), 하한가 (1~3단계), 전일거래대금, 전일거래량, 기초자산ID, 월물순서, 만기일, 날짜-->
# <!--OptionsInfo : 종목명, 종목코드, 기준가, 상한가 (1~3단계), 하한가 (1~3단계), 전일거래대금, 전일거래량, 기초자산ID, 월물순서, 행사가 순서, 만기일, 날짜-->

class OptionDAO(db.Model):
    __tablename__ = "DEAL_TABLE"
    __table_args__ = {'extend_existing': True}
    inisCd = db.Column(db.String(45), primary_key=True)
    inisNm = db.Column(db.String(45), nullable=False)
    inisType = db.Column(db.String(45), nullable=False, unique=True)
    insId = db.Column(db.String(45), nullable=False)
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
        self.insId   = dto.insId
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
    insId = db.Column(db.String(45), nullable=False)
    matDt = db.Column(db.String(45))
    baseDt = db.Column(db.String(45))

    def __init__(self, dto):
        self.inisCd  = dto.inisCd
        self.inisNm  = dto.inisNm
        self.inisType= dto.inisType
        self.insId   = dto.insId
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
