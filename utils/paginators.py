from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from rest_framework.pagination import PageNumberPagination

class CustomPageNumberPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'

    def get_paginated_response_data(self, data):
        """Return a paginated response with custom data."""
        return{
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'results': data,
        }
    
class PaginationMixin:
    """Mixin to add pagination to a view."""
    
    pagination_class = CustomPageNumberPagination

    def paginate_queryset(self, queryset, request, view=None):
        """Paginate the queryset."""
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        if page is not None:
            return page, paginator 
        return None, None

    def get_paginated_response(self, data, paginator):
        """Return a paginated response."""
        return paginator.get_paginated_response_data(data)