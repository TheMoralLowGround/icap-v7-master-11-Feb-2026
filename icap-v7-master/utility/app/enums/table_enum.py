from enum import Enum


class RowDirectionRule(Enum):
    NON_EMPTY_ROWS = "non-empty-rows"
    FIRST = "first"
    LAST = "last"
    ALL = "all"
