from flask import Flask
from flask_admin import Admin, AdminIndexView
from DAO import OptionDAO, FutureDAO, EquityDAO





from .future_view import FutureView
from .equity_view import EquityView

from .option_sub_view import *
from .future_sub_view import *
from .equity_sub_view import *

from .deal_sub_view import DealSubview
from .matdt_sub_view import MatdtSubview
from .strike_sub_view import StrikeSubview
from .underlyings_subview import UnderlyingSubview

from .underlying_view import UnderlyingView
from .db import Deal, Underlying, db
from flask_admin_subview import Subview

app = Flask(__name__)

app.config['SECRET_KEY'] = '123456790'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost:3306/MM'
app.config['SQLALCHEMY_ECHO'] = True
db.init_app(app)


admin = Admin(app, name="시세 및 배치 정보", base_template='layout.html', template_mode="bootstrap3",
              index_view=AdminIndexView(template='index.html', url='/'))  # 가장 메인 페이지
# 카테고리추가
admin.add_view(OptionView(model=OptionDAO, session=db.session, name="옵션", endpoint="option"))
admin.add_view(FutureView(model=FutureDAO, session=db.session, name="선물", endpoint="future"))
admin.add_view(EquityView(model=EquityDAO, session=db.session, name="현물", endpoint="equity"))
admin.add_view(UnderlyingView(model=Underlying, session=db.session, name="기초자산내역", endpoint="underlying"))

# 종목 세부 페이지
app.register_blueprint(OptionSubview(model=OptionDAO, session=db.session, name="Option", endpoint="option_subview").create_blueprint(admin))
app.register_blueprint(FutureSubview(model=FutureDAO, session=db.session, name="Future", endpoint="future_subview").create_blueprint(admin))
app.register_blueprint(EquitySubview(model=EquityDAO, session=db.session, name="Equity", endpoint="equity_subview").create_blueprint(admin))

# 종목 세부 - 행사가 순 나열 테이블
app.register_blueprint(StrikeSubview(model=OptionDAO, session=db.session, name="Strike", endpoint="strike_subview").create_blueprint(admin))
# 종목 세부 - 월물 정보
app.register_blueprint(MatdtSubview(model=OptionDAO, session=db.session, name="MatDt", endpoint="matdt_subview").create_blueprint(admin))

# 기초자산 페이지
app.register_blueprint(UnderlyingSubview(model=Underlying, session=db.session, name="Underlying", endpoint="underlyings_subview").create_blueprint(admin))
Subview(app)

