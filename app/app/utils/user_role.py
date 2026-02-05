from fastapi import Request

from app.exceptions import InternalErrorException
from app.models.user import UserRoles
from app.utils import MessageCodes


def allowed_roles(*roles: list[UserRoles] | UserRoles) -> callable:
    def outer_wrapper(func):
        roles_tuple: tuple[UserRoles, ...] = make_flat(roles)
        func.__allowed_roles = roles_tuple
        allowed_roles_for_doc = f"Allowed roles: {[role.value for role in roles_tuple]}"
        func.__doc__ = (
            allowed_roles_for_doc
            if not func.__doc__
            else f"{func.__doc__}\n\n{allowed_roles_for_doc}"
        )
        return func

    return outer_wrapper


def make_flat(roles: tuple[list[UserRoles] | UserRoles, ...]) -> tuple[UserRoles, ...]:
    flat_roles = set()
    for role_item in roles:
        if isinstance(role_item, UserRoles):
            flat_roles.add(role_item)
        elif isinstance(role_item, list):
            # It's a group role
            for role in role_item:
                if isinstance(role, UserRoles):
                    flat_roles.add(role)

    return tuple(flat_roles)


def check_allowed_roles(request: Request, user_roles: list[UserRoles | str]) -> bool:
    if not hasattr(request.scope["endpoint"], "__allowed_roles"):
        raise InternalErrorException(
            detail="Endpoint does not have allowed_roles",
            msg_code=MessageCodes.internal_error,
        )

    roles: tuple[UserRoles] = tuple(request.scope["endpoint"].__allowed_roles)
    for user_role in user_roles:
        if user_role in roles:
            return True
    return False
