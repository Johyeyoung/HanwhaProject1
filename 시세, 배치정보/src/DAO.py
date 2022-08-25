from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select, func, and_

# DB에 접근하기 위한 객체입니다.

db = SQLAlchemy()
app = Flask(__name__)

app.config['SECRET_KEY'] = '123456790'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost:3306/MM'
app.config['SQLALCHEMY_ECHO'] = True
db.init_app(app)




class OptionDAO(db.Model):
    __tablename__ = "OPTION_TABLE"
    __table_args__ = {'extend_existing': True}
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

    def __init__(self, dto):
        self.inisCd = dto.inisCd
        self.inisNm = dto.inisNm
        self.inisType = dto.inisType
        self.insId = dto.insId
        self.matDt = dto.matDt
        self.baseDt = dto.baseDt
        self.atmCd = dto.atmCd
        self.strike = dto.strike
        self.price = dto.price
        self.upPrice1 = dto.upPrice1
        self.upPrice2 = dto.upPrice2
        self.upPrice3 = dto.upPrice3
        self.lowPrice1 = dto.lowPrice1
        self.lowPrice2 = dto.lowPrice2
        self.lowPrice3 = dto.lowPrice3
        self.prevTransAmt = int(dto.prevTransAmt)
        self.prevTransPrc = int(dto.prevTransPrc)
        self.posType = dto.posType

    def __repr__(self):
        return self.inisCd

    @property
    def status(self):
        from _datetime import datetime
        today = datetime.today().strftime("%Y-%m-%d")
        #return "Live" if str(self.matDt) >= today else "Terminated"
        return "Live" if self.matDt >= self.baseDt else "Terminated"

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

        matDtList = sorted(list(set([x[0] for x in matDtList])))
        return f'{matDtList.index(self.matDt)+1}' if len(matDtList) != 0  and self.matDt in matDtList else ''


class FutureDAO(db.Model):
    __tablename__ = "FUTURE_TABLE"
    __table_args__ = {'extend_existing': True}
    inisCd = db.Column(db.String(45), primary_key=True)
    inisNm = db.Column(db.String(45), nullable=False)
    inisType = db.Column(db.String(45), nullable=False, unique=True)
    insId = db.Column(db.String(80), db.ForeignKey("UNDERLYING_TABLE.insId", ondelete="CASCADE"), nullable=False)
    matDt = db.Column(db.String(45))
    baseDt = db.Column(db.String(45), primary_key=True)
    strike = db.Column(db.String(45))
    price = db.Column(db.String(45))
    upPrice1 = db.Column(db.String(45))
    upPrice2 = db.Column(db.String(45))
    upPrice3 = db.Column(db.String(45))
    lowPrice1 = db.Column(db.String(45))
    lowPrice2 = db.Column(db.String(45))
    lowPrice3 = db.Column(db.String(45))
    prevTransAmt = db.Column(db.String(45))
    prevTransPrc = db.Column(db.String(45))

    def __init__(self, dto):
        self.inisCd = dto.inisCd
        self.inisNm = dto.inisNm
        self.inisType = dto.inisType
        self.insId = dto.insId
        self.matDt = dto.matDt
        self.baseDt = dto.baseDt
        self.strike = dto.strike
        self.price = dto.price
        self.upPrice1 = dto.upPrice1
        self.upPrice2 = dto.upPrice2
        self.upPrice3 = dto.upPrice3
        self.lowPrice1 = dto.lowPrice1
        self.lowPrice2 = dto.lowPrice2
        self.lowPrice3 = dto.lowPrice3
        self.prevTransAmt = int(dto.prevTransAmt)
        self.prevTransPrc = int(dto.prevTransPrc)

    @property
    def status(self):
        from _datetime import datetime
        today = datetime.today().strftime("%Y-%m-%d")
        #return "Live" if str(self.matDt) >= today else "Terminated"
        return "Live" if self.matDt >= self.baseDt else "Terminated"


    def sameOtherInfoButMatDt(self):
        return

    @property
    def matdtIdx(self):
        matDtList = db.session.query(FutureDAO.matDt) \
                    .filter(FutureDAO.baseDt == self.baseDt,
                            FutureDAO.matDt >= self.baseDt,
                            FutureDAO.insId == self.insId) \
                    .order_by(FutureDAO.matDt).all()

        matDtList = sorted(list(set([x[0] for x in matDtList])))
        return f'{matDtList.index(self.matDt)+1}' if len(matDtList) != 0 else ''


class EquityDAO(db.Model):
    __tablename__ = "EQUITY_TABLE"
    __table_args__ = {'extend_existing': True}
    inisType = db.Column(db.String(45), nullable=False, unique=True)
    inisCd = db.Column(db.String(45), primary_key=True)
    inisNm = db.Column(db.String(45))
    matDt = db.Column(db.String(45))
    baseDt = db.Column(db.String(45), primary_key=True)
    price = db.Column(db.String(45))
    upPrice = db.Column(db.String(45))
    lowPrice = db.Column(db.String(45))
    groupId = db.Column(db.String(45))  # 증권그룹ID

    def __init__(self, dto):
        self.inisType = dto.inisType
        self.inisCd = dto.inisCd
        self.inisNm = dto.inisNm
        self.matDt = dto.matDt
        self.baseDt = dto.baseDt
        self.price = dto.price
        self.upPrice = dto.upPrice
        self.lowPrice = dto.lowPrice
        self.groupId = dto.groupId

    @property
    def status(self):
        from _datetime import datetime
        today = datetime.today().strftime("%Y-%m-%d")
        #return "Live" if str(self.matDt) >= today else "Terminated"
        return "Live" if self.matDt >= self.baseDt else "Terminated"


class UnderlyingDAO(db.Model):
    __tablename__ = "UNDERLYING_TABLE"
    __table_args__ = {'extend_existing': True}
    insId = db.Column(db.String(45), primary_key=True)
    insNm = db.Column(db.String(45), nullable=False)
    insPrice = db.Column(db.String(45), nullable=False)
    baseDt = db.Column(db.String(45), primary_key=True)
    # backref : Deal에서 Underlying 모델을 참조할 이름(Deal.xxx) 설정
    inisCd_OPref = db.relationship("FutureDAO", cascade="all,delete", foreign_keys=FutureDAO.insId, backref="underlying", lazy=True)
    inisCd_FUref = db.relationship("OptionDAO", cascade="all,delete", foreign_keys=OptionDAO.insId, backref="underlying", lazy=True)

    def __init__(self, dto):
        self.insId = dto.insId
        self.insNm = dto.insNm
        self.insPrice = dto.insPrice
        self.baseDt = dto.baseDt

    def __repr__(self):
        return self.insId



