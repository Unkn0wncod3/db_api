from typing import List, Optional, Sequence, Tuple
from typing import Literal

VisibilityLevel = Literal["admin", "user"]
VISIBILITY_ADMIN: VisibilityLevel = "admin"
VISIBILITY_USER: VisibilityLevel = "user"


def is_admin_role(role: str) -> bool:
    return role == VISIBILITY_ADMIN


def allowed_visibility_levels(role: str) -> Sequence[VisibilityLevel]:
    return (VISIBILITY_ADMIN, VISIBILITY_USER) if is_admin_role(role) else (VISIBILITY_USER,)


def visibility_clause_for_role(
    role: str,
    alias: Optional[str] = None,
    column: Optional[str] = None,
) -> Tuple[Optional[str], List[VisibilityLevel]]:
    """
    Returns a SQL condition snippet (without WHERE/AND) plus the parameters to enforce
    the requested visibility level. Admins receive None so callers can skip filtering.
    """
    if is_admin_role(role):
        return None, []

    if column:
        column_expr = column
    else:
        column_expr = f"{alias}.visibility_level" if alias else "visibility_level"
    return f"{column_expr} = %s", [VISIBILITY_USER]


def cache_role_key(role: str) -> str:
    return role if role in (VISIBILITY_ADMIN, VISIBILITY_USER) else VISIBILITY_USER
