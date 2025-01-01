from flask import url_for
from flask_login import current_user


def build_pagination_urls(route, page, count, **kargs):  # type: ignore[no-untyped-def]
    next_url = (
        url_for(route, page=page + 1, **kargs)
        if count > page * current_user.results_per_page
        else None
    )
    prev_url = url_for(route, page=page - 1, **kargs) if page > 1 else None
    return next_url, prev_url


def results_offset(page):  # type: ignore[no-untyped-def]
    results_per_page = current_user.results_per_page
    search_offset = results_per_page * (page - 1)
    return results_per_page, search_offset
