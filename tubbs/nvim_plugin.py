import neovim

from ribosome import command, NvimStatePlugin, msg_command, NvimFacade
from ribosome.request import msg_function, json_msg_command

from amino import List

from tubbs.main import Tubbs
from tubbs.logging import Logging
from tubbs.plugins.core.message import (AObj, StageI, AObjRule, IObj, IObjRule,
                                        FormatRange, FormatAt, FormatExpr)


class TubbsNvimPlugin(Logging, NvimStatePlugin):

    def __init__(self, vim: neovim.api.Nvim) -> None:
        super().__init__(NvimFacade(vim, 'tubbs'))
        self.tubbs = None  # type: Tubbs

    @property
    def state(self) -> Tubbs:
        return self.tubbs

    @command()
    def tubbs_reload(self) -> None:
        self.tubbs_quit()
        self.tubbs_start()
        self._post_startup()

    @command()
    def tubbs_quit(self) -> None:
        if self.tubbs is not None:
            self.vim.clean()
            self.tubbs.stop()
            self.tubbs = None

    def start_plugin(self) -> None:
        plugins = self.vim.vars.pl('plugins') | self._default_plugins
        self.tubbs = Tubbs(self.vim.proxy, plugins)
        self.tubbs.start()
        self.tubbs.wait_for_running()
        self.tubbs.send(StageI())

    @property
    def _default_plugins(self) -> List[str]:
        return List()

    @command(sync=True)
    def tubbs_start(self) -> None:
        return self.start_plugin()

    @msg_function(AObj, sync=True)
    def tub_a(self) -> None:
        pass

    @msg_command(IObj, sync=True)
    def tub_i(self) -> None:
        pass

    @msg_command(AObjRule)
    def tub_a_rule(self) -> None:
        pass

    @msg_command(IObjRule)
    def tub_i_rule(self) -> None:
        pass

    @msg_function(FormatExpr, sync=True)
    def tub_format(self) -> None:
        pass

    @json_msg_command(FormatRange)
    def tub_format_range(self) -> None:
        pass

    @json_msg_command(FormatAt)
    def tub_format_at(self) -> None:
        pass

__all__ = ('TubbsNvimPlugin',)
