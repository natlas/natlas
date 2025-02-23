from typing import Any

from flask import url_for
from flask_login import current_user


def build_pagination_urls(
    route: str, page: int, count: int, **kwargs: Any
) -> tuple[str | None, str | None]:
    next_url = (
        url_for(route, page=page + 1, **kwargs)
        if count > page * current_user.results_per_page
        else None
    )
    prev_url = url_for(route, page=page - 1, **kwargs) if page > 1 else None
    return next_url, prev_url


def results_offset(page: int) -> tuple[int, int]:
    results_per_page: int = current_user.results_per_page
    search_offset = results_per_page * (page - 1)
    return results_per_page, search_offset
