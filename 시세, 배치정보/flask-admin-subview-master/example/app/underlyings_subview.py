from flask import request, abort, redirect
from flask_admin.helpers import get_redirect_target, flash_errors
from .formatters import *

import flask_admin_subview as subview
from .db import Underlying
from .underlying_view import UnderlyingView


class UnderlyingSubview(subview.View, UnderlyingView):
    can_create = False
    can_delete = False
    can_edit = False

    list_template = "underlyings_sub_view.html"
    column_list = ("title", "holder",)

    def get_query(self):
        return self._extend_query(super(UnderlyingSubview, self).get_query())

    def get_count_query(self):
        return self._extend_query(super(UnderlyingSubview, self).get_count_query())

    def _apply_query_filter(self, query, client_id):
        return query.filter(Underlying.insId == client_id)

    def _extend_query(self, query):
        client_id = request.args.get('id')
        if client_id is None:
            abort(400, "Client id required")
        return self._apply_query_filter(query, client_id)

    column_formatters = {
        'title': model_link_formatter("item", ""),
    }

    def _action_view_base(self, action, error_msg):
        return_url = get_redirect_target() or self.get_url(".index_view")
        form = self.action_form()
        if self.validate_form(form):
            action((request.form.get('id'),))
            return redirect(return_url)
        else:
            flash_errors(form, message=error_msg)
        return redirect(return_url)


UnderlyingSubview.column_formatters.update(UnderlyingSubview.column_formatters)
