from flask import url_for
from markupsafe import Markup


def model_link_formatter(section, attr, view_type="details_view"):
    def wrapped(view, context, model, name):
        obj = getattr(model, attr) if attr else model
        return Markup(
            u"<a href='{}'>{}</a>".format(url_for("{}.{}".format(section, view_type), id=obj.id), obj)) if obj else u""
    return wrapped



def model_link_formatter_inisCd(section, attr, view_type="details_view"):
    def wrapped(view, context, model, name):
        obj = getattr(model, attr) if attr else model
        return Markup(
            u"<a href='{}'>{}</a>".format(url_for("{}.{}".format(section, view_type), id=obj.inisCd, baseDt=obj.baseDt), obj.inisCd)) if obj else u""

    return wrapped


def model_link_formatter_insId(section, attr, view_type="details_view"):
    def wrapped(view, context, model, name):
        obj = getattr(model, attr) if attr else model
        return Markup(
            u"<a href='{}'>{}</a>".format(url_for("{}.{}".format(section, view_type), id=obj.insId, baseDt=obj.baseDt), obj.insId)) if obj else u""

    return wrapped


def model_link_formatter_opstInisCd(section, attr, view_type="details_view"):
    def wrapped(view, context, model, name):
        obj = getattr(model, attr) if attr else model
        return Markup(
            u"<a href='{}'>{}</a>".format(url_for("{}.{}".format(section, view_type), id=obj.opstInisCd, baseDt=obj.baseDt), obj.opstInisCd)) if obj else u""

    return wrapped