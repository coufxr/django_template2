import base64
from urllib.parse import parse_qsl, urlencode

from django.db.models import Q
from rest_framework.pagination import CursorPagination, PageNumberPagination
from rest_framework.response import Response


class CursorPagination(CursorPagination):
    page_size = 20

    filtering = None
    ordering = "id"

    page_size_query_param = "page_size"

    max_page_size = None

    def paginate_queryset(self, queryset, request, view=None):
        page_size = self.get_page_size(request)
        if not page_size:
            return None

        kwargs = self.decode_cursor(request) or {}

        self.ordering = self.get_ordering(request, queryset, view)

        filtering = self.get_filtering(request, queryset, view, **kwargs)
        if filtering:
            queryset = queryset.filter(filtering)

        queryset = queryset.order_by(*self.ordering)
        results = list(queryset[: page_size + 1])
        if len(results) < page_size + 1:
            self.next = None
            self.page = results
        else:
            self.next = self.construct_next_cursor(results[-1], self.ordering)
            self.page = results[:-1]
        return self.page

    def decode_cursor(self, request):
        """
        Given a request with a cursor, return a `Cursor` instance.
        """
        # Determine if we have a cursor, and if so then decode it.
        encoded = request.query_params.get(self.cursor_query_param)
        if encoded is None:
            return None

        try:
            querystring = base64.b64decode(encoded.encode("ascii")).decode("ascii")
            return dict(parse_qsl(querystring, keep_blank_values=True))
        except (TypeError, ValueError):
            return

    @staticmethod
    def construct_next_cursor(inst, ordering):
        fields = []
        for field in ordering:
            if field.startswith("-"):
                fields.append(field[1:])
            else:
                fields.append(field)
        msg = urlencode({field: getattr(inst, field) for field in fields})
        return base64.b64encode(msg.encode("ascii")).decode("ascii")

    def get_filtering(self, request, queryset, view, **kwargs):
        """
        Return a tuple of strings, that may be used in an `order_by` method.
        """
        filter_fn = getattr(view, "get_filtering", None)

        filtering = None

        if filter_fn:
            filtering = filter_fn(request, queryset, **kwargs)
        elif self.filtering is not None:
            filtering = self.filtering
        elif not kwargs:
            return
        else:
            for item in self.ordering:
                if item.startswith("-"):
                    key = item[1:]
                    sort_key = "lt"
                else:
                    key = item
                    sort_key = "gt"

                if key not in kwargs:
                    continue

                filter_item = Q(**{f"{key}__{sort_key}": kwargs[key]})
                if filtering is None:
                    filtering = filter_item
                else:
                    filtering &= filter_item

        return filtering

    def get_ordering(self, request, queryset, view):
        """
        Return a tuple of strings, that may be used in an `order_by` method.
        """
        ordering = getattr(view, "ordering", None)
        if not ordering:
            ordering = self.ordering

        if isinstance(ordering, str):
            ordering = (ordering,)
        return ordering

    def get_paginated_response(self, data):
        resp = dict({"items": data, "next": self.next})
        return Response(resp)


class Pagination(PageNumberPagination):
    page_size = 20  # 每页显示多少条
    page_query_param = "page"  # 请求参数中的 page参数名 URL中页码的参数
    page_size_query_param = "page_size"  # 每页显示多少条
    max_page_size = 100  # 最大页码数限制，请求参数中如果超过了这个配置，不会报错，会按照此配置工作

    def get_paginated_response(self, data):
        return Response(
            {
                "total": self.page.paginator.count,
                "page": self.page.number,
                "page_size": self.page.paginator.per_page,
                "items": data,
            }
        )
