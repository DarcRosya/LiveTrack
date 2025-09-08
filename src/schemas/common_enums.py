import enum

class SortOrder(str, enum.Enum):
    """Defines the sorting order."""
    ASC = "asc"
    DESC = "desc"

class TaskSortBy(str, enum.Enum):
    """Defines the fields by which tasks can be sorted."""
    CREATED_AT = "created_at"
    STATUS = "status"
    PRIORITY = "priority"
    DEADLINE = "deadline"   