import enum

class SortOrder(str, enum.Enum):
    """Defines the sorting order."""
    ASC = "asc"
    DESC = "desc"


class HabitSortBy(str, enum.Enum):
    """Defines the fields by which habits can be sorted."""
    STARTED_AT = "started_at"
    IS_ACTIVE = "is_active"
    DURATION_DAYS = "duration_days"


class TaskSortBy(str, enum.Enum):
    """Defines the fields by which tasks can be sorted."""
    CREATED_AT = "created_at"
    STATUS = "status"
    PRIORITY = "priority"
    DEADLINE = "deadline"   