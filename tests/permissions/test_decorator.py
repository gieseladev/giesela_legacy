from discord.ext.commands import Cog, command

from giesela.permission import perm_tree
from giesela.permission.decorators import get_decorated_permissions, has_global_permission, has_permission


def test_decorators():
    @has_global_permission(perm_tree.admin.control.execute)
    @has_permission(perm_tree.admin.control.shutdown)
    def func():
        pass

    assert get_decorated_permissions(func, global_only=False) == [perm_tree.admin.control.shutdown]
    assert get_decorated_permissions(func, global_only=True) == [perm_tree.admin.control.execute]


def test_command_decorators():
    @has_permission(perm_tree.admin.control.shutdown)
    @command()
    async def test():
        pass

    assert get_decorated_permissions(test, global_only=False) == [perm_tree.admin.control.shutdown]
    assert get_decorated_permissions(test, global_only=True) == []


def test_command_decorators_before_command():
    @command()
    @has_permission(perm_tree.admin.control.shutdown)
    async def test():
        pass

    assert get_decorated_permissions(test, global_only=False) == [perm_tree.admin.control.shutdown]
    assert get_decorated_permissions(test, global_only=True) == []


def test_cog_command_decorator():
    class TestCog(Cog):
        @has_global_permission(perm_tree.admin.control.shutdown)
        @command()
        async def test_after(self):
            pass

        @command()
        @has_permission(perm_tree.admin.control.shutdown)
        async def test_before(self):
            pass

    assert get_decorated_permissions(TestCog.test_after, global_only=True) == [perm_tree.admin.control.shutdown]
    assert get_decorated_permissions(TestCog.test_before, global_only=False) == [perm_tree.admin.control.shutdown]
