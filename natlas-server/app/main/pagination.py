from flask_login import current_user
from flask import url_for


def build_pagination_urls(route, page, count, **kargs):
    next_url = (
        url_for(route, page=page + 1, **kargs)
        if count > page * current_user.results_per_page
        else None
    )
    prev_url = url_for(route, page=page - 1, **kargs) if page > 1 else None
    return next_url, prev_url


def results_offset(page):
    results_per_page = current_user.results_per_page
    search_offset = results_per_page * (page - 1)
    return results_per_page, search_offset
