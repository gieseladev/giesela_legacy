from typing import Awaitable, Callable, Dict, Iterable, List, Optional, Tuple, Union, cast

from discord import Colour, Embed, Message
from discord.abc import Messageable
from discord.ext.commands import Cog, Command, Group, HelpCommand

from giesela.ui import EmbedPaginator

__all__ = ["GieselaHelpFormatter", "GIESELA_HELP_FORMATTER", "GieselaHelpCommand"]

CommandFilter = Callable[[Iterable[Command]], Union[bool, Awaitable[bool]]]


class GieselaHelpFormatter:
    """Help formatter for generating help embeds."""
    signature_language: str

    default_cog_description: str
    default_group_description: str
    default_command_description: str

    max_description_length_for_inline: int

    def __init__(self, *,
                 signature_language: str = "css",
                 default_cog_description: str = "No description",
                 default_group_description: str = "No description",
                 default_command_description: str = "No description",
                 max_description_length_for_inline: int = 35
                 ) -> None:
        self.signature_language = signature_language

        self.default_cog_description = default_cog_description
        self.default_group_description = default_group_description
        self.default_command_description = default_command_description

        self.max_description_length_for_inline = max_description_length_for_inline

    @classmethod
    def get_paginator(cls, first_embed: Embed = None) -> EmbedPaginator:
        """Create a help themed embed paginator.

        Args:
            first_embed: Template for the first embed.
                If the embed doesn't already specify the values
                set by the template, they are written to it.
                This means that the first embed will look like
                the other embeds by default unless you explicitly
                change it.
        """

        def _prepare_embed(embed: Embed) -> None:
            if not embed.colour:
                embed.colour = Colour.blue()
            if not embed.author:
                embed.set_author(name="Giesela Help")

        template = Embed()

        _prepare_embed(template)
        if first_embed is not None:
            add_embed = True
            _prepare_embed(first_embed)
        else:
            add_embed = False

        paginator = EmbedPaginator(template=template, special_template=first_embed)

        if add_embed:
            # noinspection PyProtectedMember
            paginator._add_embed()

        return paginator

    @classmethod
    def get_ending_note(cls, *, help_command_name: str, prefix: Optional[str]) -> str:
        """Ending note added to the last embed's footer.

        Args:
            help_command_name: Name of the help command.
            prefix: Command prefix.
                If this is `None`, no prefix is shown.
        """
        command = help_command_name
        if prefix is not None:
            command = prefix + command

        return f"Type {command} command/category for more info on the command/category."

    @classmethod
    def finalise_paginator(cls, paginator: EmbedPaginator, *, help_command_name: str, prefix: Optional[str]) -> None:
        """Add final footer to the last embed.

        Args:
            paginator: Embed paginator to apply the footer to
            help_command_name: Name of the help command.
            prefix: Command prefix.
                If this is `None`, no prefix is shown.
        """
        try:
            last_embed = paginator[-1]
        except IndexError:
            return

        last_embed.set_footer(text=cls.get_ending_note(help_command_name=help_command_name, prefix=prefix))

    def get_styled_signature(self, signature: str) -> str:
        """Decorate a signature with some code markup.

        Uses `signature_language` for the language.

        Args:
            signature: Signature from `get_command_signature` to decorate.
        """
        return f"```{self.signature_language}\n{signature}```"

    def get_description(self, obj: Union[Cog, Group, Command], *, short: bool = False) -> str:
        """Extract the description from the given instance.

        Returns the default for the type if no description is set.

        Args:
            obj: Object to get description from.
            short: Whether or not a short version of the
                description should be used.
        """
        if isinstance(obj, Cog):
            description = obj.description
            if description and short:
                description = description.split("\n", 1)[0]

            if description is None:
                description = self.default_cog_description
        else:
            if short:
                description = obj.short_doc
            else:
                description = obj.help

            if not description:
                if isinstance(obj, Group):
                    description = self.default_group_description
                elif isinstance(obj, Command):
                    description = self.default_command_description
                else:
                    raise TypeError(f"No default description for type {type(obj).__name__}: {obj}")

        return description

    @classmethod
    def get_command_signature(cls, command: Command, *, prefix: Optional[str], name_padding: int = None) -> str:
        """Get the full command signature.

        Args:
            command: Command to build signature for
            prefix: Command prefix to use for the signature.
                If `None` no command prefix is shown.
            name_padding: Padded length of name. Padding is done
                with spaces. Padding is only performed if this is
                not `None`. If the padding is set, aliases won't be
                displayed as they would possibly alter the length.
        """
        if name_padding is not None and len(command.aliases) > 0:
            aliases = "|".join(command.aliases)
            fmt = f"[{command.name}|{aliases}]"

            parent = command.full_parent_name
            if parent:
                fmt = parent + " " + fmt

            alias = fmt
        else:
            alias = command.qualified_name

        if name_padding is not None:
            alias = alias.ljust(name_padding)

        signature = f"{alias} {command.signature}"
        if prefix is None:
            return signature
        else:
            return prefix + signature

    @classmethod
    async def filter_commands(cls, commands: Iterable[Command], command_filter: Optional[CommandFilter]) -> List[Command]:
        """Perform filtering.

        Args:
            commands: Commands to be checked
            command_filter: Command filter to use.
                If this is `None`, all passed commands
                are accepted.

        Returns:
            Commands that passed the command filter. If no filter was passed
            all commands are accepted.
        """
        if command_filter is None:
            return list(commands)
        else:
            return await command_filter(commands)

    def _check_description_inline(self, next_no_inline: bool, description_len: int) -> Tuple[bool, bool]:
        """Check whether a description should be displayed in an inline field.

        Args:
            next_no_inline: Whether or not this field must not be
                inline. This should be `False` for the first call
                and the first return value of this method for all
                subsequent calls.
            description_len: Length of the description

        Returns:
            next_no_inline, inline.
            The first return value should be passed to the next call of this method.
        """
        if description_len > self.max_description_length_for_inline:
            inline = False
            next_no_inline = True
        elif next_no_inline:
            inline = False
            next_no_inline = False
        else:
            inline = True

        return next_no_inline, inline

    def _add_command_fields(self, paginator: EmbedPaginator, commands: Iterable[Command], *, prefix: Optional[str]) -> None:
        """Generate command fields for the embed paginator.

        Args:
            paginator: embed paginator to add fields to
            commands: Commands to add
            prefix: Command prefix.
                If this is `None`, no command prefix
                is shown.
        """
        next_no_inline: bool = False

        for command in commands:
            command = cast(Command, command)
            signature = self.get_command_signature(command, prefix=prefix)
            description = self.get_description(command, short=True)

            next_no_inline, inline = self._check_description_inline(next_no_inline, len(description))

            paginator.add_field(signature, description, inline=inline)

    async def get_bot_help(self, mapping: Dict[Optional[Cog], List[Command]], *,
                           prefix: Optional[str],
                           help_command_name: Optional[str],
                           command_filter: Optional[CommandFilter]) -> EmbedPaginator:
        """Generate help for the bot.

        Args:
            mapping: cog -> List[Command] mapping.
                Use key `None` for commands that aren't
                from a cog.
            prefix: Command prefix.
                If this is `None`, no prefix is shown.
            help_command_name: Name of the help command
            command_filter: Callback to filter out invalid commands.
        """
        paginator = self.get_paginator()

        general_commands = mapping.pop(None, None)

        next_no_inline: bool = False

        for cog, commands in mapping.items():
            filtered_commands = await self.filter_commands(commands, command_filter)
            if not filtered_commands:
                continue

            description = self.get_description(cog)
            next_no_inline, inline = self._check_description_inline(next_no_inline, len(description))
            paginator.add_field(cog.qualified_name, description, inline=inline)

        if general_commands:
            max_name_len: int = max((len(command.name) for command in general_commands))

            text = "\n".join(self.get_command_signature(command, prefix=prefix, name_padding=max_name_len) for command in general_commands)
            paginator.add_field("General Commands", self.get_styled_signature(text))

        if help_command_name is not None:
            self.finalise_paginator(paginator, help_command_name=help_command_name, prefix=prefix)

        return paginator

    async def get_cog_help(self, cog: Cog, *,
                           prefix: Optional[str],
                           help_command_name: Optional[str],
                           command_filter: Optional[CommandFilter]) -> EmbedPaginator:
        """Generate help for a cog.

        Args:
            cog: Cog to generate help for.
            prefix: Command prefix.
                If this is `None`, no prefix is shown.
            help_command_name: Name of the help command
            command_filter: Callback to filter out invalid commands.
        """
        embed = Embed(title=cog.qualified_name, description=self.get_description(cog))
        paginator = self.get_paginator(embed)

        commands = await self.filter_commands(cog.get_commands(), command_filter)
        self._add_command_fields(paginator, commands, prefix=prefix)

        if help_command_name is not None:
            self.finalise_paginator(paginator, help_command_name=help_command_name, prefix=prefix)

        return paginator

    async def get_group_help(self, group: Group, *,
                             prefix: Optional[str],
                             help_command_name: Optional[str],
                             command_filter: Optional[CommandFilter]) -> EmbedPaginator:
        """Generate help for a command group.

        Args:
            group: Group to generate help for.
            prefix: Command prefix.
                If this is `None`, no prefix is shown.
            help_command_name: Name of the help command
            command_filter: Callback to filter out invalid commands.
        """
        embed = Embed(title=self.get_command_signature(group, prefix=prefix), description=self.get_description(group))
        paginator = self.get_paginator(embed)

        commands = await self.filter_commands(group.commands, command_filter)
        self._add_command_fields(paginator, commands, prefix=prefix)

        if help_command_name is not None:
            self.finalise_paginator(paginator, help_command_name=help_command_name, prefix=prefix)

        return paginator

    async def get_command_help(self, command: Command, *,
                               prefix: Optional[str],
                               help_command_name: Optional[str]) -> EmbedPaginator:
        """Generate help for a command.

        Args:
            command: Command to generate help for.
            prefix: Command prefix.
                If this is `None`, no prefix is shown.
            help_command_name: Name of the help command
        """
        embed = Embed(title=self.get_command_signature(command, prefix=prefix), description=self.get_description(command))
        paginator = self.get_paginator(embed)

        if help_command_name is not None:
            self.finalise_paginator(paginator, help_command_name=help_command_name, prefix=prefix)

        return paginator

    async def get_help_for(self, obj: Union[Cog, Group, Command], *,
                           prefix: Optional[str],
                           help_command_name: Optional[str],
                           command_filter: Optional[CommandFilter]) -> EmbedPaginator:
        """Pick the correct help generator based on the object type.

        Args:
            obj: Object to get help for.
            prefix: Command prefix.
                If this is `None`, no prefix is shown.
            help_command_name: Name of the help command
            command_filter: Callback to filter out invalid commands.

        Raises:
            TypeError: Invalid type with no help is passed.
        """
        if isinstance(obj, Cog):
            return await self.get_cog_help(obj, prefix=prefix, help_command_name=help_command_name, command_filter=command_filter)
        elif isinstance(obj, Group):
            return await self.get_group_help(obj, prefix=prefix, help_command_name=help_command_name, command_filter=command_filter)
        elif isinstance(obj, Command):
            return await self.get_command_help(obj, prefix=prefix, help_command_name=help_command_name)
        else:
            raise TypeError(f"Cannot generate help for type {type(obj).__name__}: {obj}")


GIESELA_HELP_FORMATTER = GieselaHelpFormatter()


class GieselaHelpCommand(HelpCommand):
    """Giesela's help command.

    Uses `GIESELA_HELP_FORMATTER` to build messages.
    """

    async def send_bot_help(self, mapping: Dict[Optional[Cog], List[Command]]) -> None:
        paginator = await GIESELA_HELP_FORMATTER.get_bot_help(mapping, prefix=self.clean_prefix,
                                                              help_command_name=self.context.invoked_with,
                                                              command_filter=self.filter_commands)
        await self.send_paginator(paginator)

    async def send_cog_help(self, cog: Cog) -> None:
        paginator = await GIESELA_HELP_FORMATTER.get_cog_help(cog, prefix=self.clean_prefix,
                                                              help_command_name=self.context.invoked_with,
                                                              command_filter=self.filter_commands)
        await self.send_paginator(paginator)

    async def send_group_help(self, group: Group) -> None:
        paginator = await GIESELA_HELP_FORMATTER.get_group_help(group, prefix=self.clean_prefix,
                                                                help_command_name=self.context.invoked_with,
                                                                command_filter=self.filter_commands)
        await self.send_paginator(paginator)

    async def send_command_help(self, command: Command) -> None:
        paginator = await GIESELA_HELP_FORMATTER.get_command_help(command, prefix=self.clean_prefix,
                                                                  help_command_name=self.context.invoked_with)
        await self.send_paginator(paginator)

    async def send_error_message(self, error: str) -> None:
        destination: Messageable = self.get_destination()
        await destination.send(embed=Embed(description=error, colour=Colour.red()))

    async def send_paginator(self, paginator: EmbedPaginator, destination: Messageable = None) -> List[Message]:
        """Send the embeds of the embed paginator.

        Args:
            paginator: embed paginator to send
            destination: Target to send it to.
                If this is `None` it is retrieved using
                `get_destination`.

        Returns:
            List of messages that were sent.
        """
        if destination is None:
            destination = self.get_destination()

        sent: List[Message] = []

        for embed in paginator:
            msg = await destination.send(embed=embed)
            sent.append(msg)

        return sent
