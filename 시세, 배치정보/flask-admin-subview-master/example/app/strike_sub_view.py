from flask import request, abort, redirect
from flask_admin.helpers import get_redirect_target, flash_errors
from .formatters import *
import flask_admin_subview as subview
from DAO import OptionDAO
from .option_view import OptionView


class StrikeSubview(subview.View, OptionView):
    can_set_page_size = True
    can_view_details = False
    column_display_actions = False

    list_template = "deals_sub_view.html"

    column_exclude_list = ("inisType", 'insIdHref', "posType")

    def get_query(self):
        return self._extend_query(super(StrikeSubview, self).get_query())

    def get_count_query(self):  # list(총 개수)
        return self._extend_query(super(StrikeSubview, self).get_count_query())

    def _apply_query_filter(self, query, param):
        insId = param.get('insId')
        baseDt = param.get('baseDt')
        posType = param.get('posType')
        matDt = param.get('matDt')  # 만기의 값은 같은 상황에서

        if posType is None or matDt is None:
            return query.filter(OptionDAO.insId == insId,
                                OptionDAO.baseDt == baseDt,
                                OptionDAO.matDt >= baseDt
                                )

        return query.filter(OptionDAO.insId == insId,
                            OptionDAO.baseDt == baseDt,
                            OptionDAO.posType == posType,
                            OptionDAO.matDt == matDt)\
               .order_by(OptionDAO.strike)


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
