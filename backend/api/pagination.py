from rest_framework.pagination import PageNumberPagination


class LimitPagination(PageNumberPagination):
    """Кастомная пагинация."""

    page_size_query_param = 'limit'
