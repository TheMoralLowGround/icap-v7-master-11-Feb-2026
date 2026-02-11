"""
Organization: AIDocbuilder Inc.
File: core/pagination.py
Version: 6.0

Authors:
    - Vivek - Initial implementation

Last Updated By: Vivek
Last Updated At: 2023-11-01

Description:
    This file set the pagination configurations.

Dependencies:
    - PageNumberPagination from rest_framework.pagination

Main Features:
    - Set default pagination parameters.
"""
from rest_framework.pagination import PageNumberPagination

class PaginationMeta(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100
