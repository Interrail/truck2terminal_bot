"""Import all routers and add them to routers_list."""

from .profile import profile_router
from .route import route_router
from .support import support_router
from .terminals import terminals_router
from .user import user_router

routers_list = [
    # admin_router,
    terminals_router,
    support_router,
    profile_router,
    user_router,
    route_router,
]

__all__ = [
    "routers_list",
]
