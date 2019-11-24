from typing import Any, List

from discord.ext.commands import Command

from .tree_utils import PermissionType

__all__ = ["has_permission", "has_global_permission", "get_decorated_permissions"]


def _get_perm_attr(global_only: bool) -> str:
    """Determine the correct attribute to use for the global_only state."""
    if global_only:
        return "__required_global_permissions__"
    else:
        return "__required_permissions__"


def _get_perm_container(obj: Any) -> Any:
    """Find the appropriate container to write permissions to.

    Notes:
        This is necessary because the new cog system "copies" `Command` instances
        in a way that removes all non-default attributes.
        For `Command` instances the permissions should be written to the
        callback and that's what this function is helping with.
    """
    if isinstance(obj, Command):
        return getattr(obj, "_callback")
    else:
        return obj


def has_permission(*permissions: PermissionType, global_only: bool = False):
    """Command decorator which requires certain permissions.

    Args:
        *permissions: Permissions which are required.
        global_only: Whether or not the permissions need to be global.

    See Also:
        `has_global_permission` for a more convenient way of specifying
        `global_only`.

        `get_decorated_permissions` can be used to retrieve the permissions.

    Notes:
        Usually the decorator just overwrites previous requirements,
        but you can combine permissions with differing global only values.

        When applying to a `Command` instance the permissions are written to the callback
        to make sure they're not lost upon copying the command.

    Returns:
        A decorator which, when applied to an object, marks the given permissions
        as required.
    """
    perms = set(permissions)

    def decorator(obj: Any):
        container = _get_perm_container(obj)
        setattr(container, _get_perm_attr(global_only), perms)

        return obj

    return decorator


def has_global_permission(*permissions: PermissionType):
    """Command decorator which requires permission in a global role.

    This is a shortcut for `has_permission` with `global_only` as `True`.

    Args:
        *permissions: Permissions which are required.
    """
    return has_permission(*permissions, global_only=True)


def get_decorated_permissions(obj: Any, global_only: bool) -> List[PermissionType]:
    """Get the permissions previously added by `has_permission`.

    Args:
        obj: Command to get permissions from.
        global_only: Whether or not to retrieve only the global permissions.

    Notes:
        If the object is a `Command` the permissions are read from the command's
        callback.
    """
    attr = _get_perm_attr(global_only)
    container = _get_perm_container(obj)

    try:
        perms = getattr(container, attr)
    except AttributeError:
        return []
    else:
        return list(perms)
