from flask_admin.contrib.sqla import ModelView
from flask_admin.helpers import get_redirect_target
from flask_admin.model.helpers import get_mdict_item_or_list
from flask_admin.babel import gettext, ngettext
from flask_admin.contrib.sqla import form, filters as sqla_filters, tools

from flask import (current_app, request, redirect, flash, abort, json,
                   Response, get_flashed_messages, stream_with_context)

from .formatters import *

from flask_admin_subview import SubviewContainerMixin, SubviewEntry

class UnderlyingView(SubviewContainerMixin, ModelView):
    details_modal = False
    can_view_details = True

    # edit, delete, create 아이콘 지우기
    can_delete, can_edit, can_create = False, False, False
    column_searchable_list = ("insId",)
    column_sortable_list = ("insId", "insNm", "insPrice", "baseDt")
    column_filters = ("insId",)
    column_list = ("insIdHref", "insNm", "insPrice", "baseDt")
    column_labels = {"insIdHref": "기초자산ID", "insNm": "기초자산명", "insPrice": "종가", "baseDt": "생성일자"}

    form_create_rules = ("insId", "insNm", "insPrice")
    form_edit_rules = ("insId",)

    column_formatters = {
        # 세부 상세 페이지 링크 생성
        "insIdHref": model_link_formatter_insId(section="underlying", attr=""),
    }


    #  기초자산 세부페이지 URL처리
    from flask_admin.base import expose
    @expose('/details/')
    def details_view(self):
        """
            Details model view
        """
        return_url = get_redirect_target() or self.get_url('.index_view')

        if not self.can_view_details:
            return redirect(return_url)
        id = get_mdict_item_or_list(request.args, 'id')
        baseDt = get_mdict_item_or_list(request.args, 'baseDt')

        model = self.session.query(self.model).filter(self.model.baseDt == baseDt, self.model.insId == id).first()
        if model is None:
            flash(gettext('Record does not exist.'), 'error')
            return redirect(return_url)

        template = "admin/model/details_with_underlyingSubview.html"

        return self.render(template,
                           model=model,
                           details_columns=self._details_columns,
                           get_value=self.get_detail_value,
                           return_url=return_url)