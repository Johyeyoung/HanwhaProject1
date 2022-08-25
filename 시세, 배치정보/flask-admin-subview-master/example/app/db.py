from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select, func, and_, case
from sqlalchemy.orm import column_property
from DAO import *

db = SQLAlchemy()


class Deal(db.Model):
    __tablename__ = 'DEAL_TABLE'
    inisCd = db.Column(db.String(45), primary_key=True)
    inisNm = db.Column(db.String(45), nullable=False)
    inisType = db.Column(db.String(45), nullable=False, unique=True)
    insId = db.Column(db.String(80), db.ForeignKey("UNDERLYING_TABLE.insId", ondelete="CASCADE"), nullable=False)
    matDt = db.Column(db.String(45))
    baseDt = db.Column(db.String(45), primary_key=True)
    atmCd = db.Column(db.String(45))
    strike = db.Column(db.String(45))
    price = db.Column(db.String(45))
    upPrice1 = db.Column(db.String(45))
    upPrice2 = db.Column(db.String(45))
    upPrice3 = db.Column(db.String(45))
    lowPrice1 = db.Column(db.String(45))
    lowPrice2 = db.Column(db.String(45))
    lowPrice3 = db.Column(db.String(45))
    prevTransAmt = db.Column(db.Integer)
    prevTransPrc = db.Column(db.Integer)
    posType = db.Column(db.String(1))

    def __repr__(self):
        return self.inisCd

    @property
    def status(self):
        from _datetime import datetime
        today = datetime.today().strftime("%Y-%m-%d")
        return "Live" if str(self.matDt) >= today else "Terminated"

    @property
    def opstInisCd(self):  # 반대 포지션
        model = db.session.query(OptionDAO)\
               .filter(OptionDAO.baseDt == self.baseDt,
                       OptionDAO.insId == self.insId,
                       OptionDAO.matDt == self.matDt,
                       OptionDAO.strike == self.strike,
                       OptionDAO.posType != self.posType).first()
        return model.inisCd

    def sameOtherInfoButMatDt(self):
        return

    @property
    def matdtIdx(self):
        matDtList = db.session.query(OptionDAO.matDt) \
                    .filter(OptionDAO.baseDt == self.baseDt,
                            OptionDAO.matDt >= self.baseDt,
                            OptionDAO.insId == self.insId,
                            OptionDAO.atmCd == self.atmCd,
                            OptionDAO.posType == self.posType) \
                    .order_by(OptionDAO.matDt).all()

        matDtList = [x[0] for x in matDtList]
        return f'{matDtList.index(self.matDt)+1}번째' if len(matDtList) != 0 else ''



# 기초자산의 정보를 담고 있는 테이블 입니다.
class Underlying(db.Model):
    __tablename__ = "UNDERLYING_TABLE"
    insId = db.Column(db.String(45), primary_key=True)
    insNm = db.Column(db.String(45), nullable=False)
    insPrice = db.Column(db.String(45), nullable=False)
    baseDt = db.Column(db.String(45))
    # backref : Deal에서 Underlying 모델을 참조할 이름(Deal.xxx) 설정
    inisCd_ref = db.relationship("Deal", cascade="all,delete", foreign_keys=Deal.insId, backref="underlying", lazy=True)

    def __repr__(self):
        return self.insId



