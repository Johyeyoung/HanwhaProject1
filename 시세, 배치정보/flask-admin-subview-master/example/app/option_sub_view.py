from flask import request, abort, redirect
from flask_admin.helpers import get_redirect_target, flash_errors
from .formatters import *
import flask_admin_subview as subview
from DAO import OptionDAO
from .option_view import OptionView


class OptionSubview(subview.View, OptionView):
    can_set_page_size = False
    can_view_details = False
    column_display_actions = False

    list_template = "deals_sub_view.html"

    # 이제 받은 딜테이블을 기초자산과, baseDt, 등등으로 필터링해줘야됨
    def get_query(self):
        return self._extend_query(super(OptionSubview, self).get_query())

    def get_count_query(self):  # list(총 개수)
        return self._extend_query(super(OptionSubview, self).get_count_query())

    def _apply_query_filter(self, query, param):
        insId = param.get('insId')
        baseDt = param.get('baseDt')
        posType = param.get('posType')
        from _datetime import datetime
        today = datetime.today().strftime("%Y-%m-%d")
        if baseDt == None:
            return query.filter(OptionDAO.baseDt == today,).order_by(OptionDAO.matDt)
        return query.filter(OptionDAO.baseDt == baseDt,)

        return query.filter(OptionDAO.insId == insId,
                            OptionDAO.baseDt == baseDt,
                            OptionDAO.posType == posType,)\
               .order_by(OptionDAO.atmCd, OptionDAO.strike)


    def _extend_query(self, query):
        param = request.args
        if param is None:
            abort(400, "Client id required")
        return self._apply_query_filter(query, param=param)

    def _action_view_base(self, action, error_msg):
        return_url = get_redirect_target() or self.get_url(".index_view")
        form = self.action_form()
        if self.validate_form(form):
            action((request.form.get('id'),))
            return redirect(return_url)
        else:
            flash_errors(form, message=error_msg)
        return redirect(return_url)

    def is_sortable(self, name):
        return False
