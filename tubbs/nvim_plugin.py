from pathlib import Path

import neovim

from amino import List

from ribosome import (command, NvimStatePlugin, msg_command, json_msg_command,
                    NvimFacade)

from tubbs.plugins.core import StageI
from tubbs.main import Tubbs
from tubbs.logging import Logging


class TubbsNvimPlugin(NvimStatePlugin, Logging):

    def __init__(self, vim: neovim.Nvim) -> None:
        super().__init__(NvimFacade(vim, 'tubbs'))
        self.tubbs = None  # type: Tubbs
        self._post_initialized = False

    def state(self):
        return self.tubbs

    @command()
    def tubbs_reload(self):
        self.tubbs_quit()
        self.tubbs_start()
        self._post_startup()

    @command()
    def tubbs_quit(self):
        if self.tubbs is not None:
            self.vim.clean()
            self.tubbs.stop()
            self.tubbs = None

    @command(sync=True)
    def tubbs_start(self):
        plugins = self.vim.pl('plugins') | List()
        self.tubbs = Tubbs(self.vim.proxy, plugins)
        self.tubbs.start()
        self.tubbs.wait_for_running()
        self.tubbs.send(StageI())

    @command()
    def tubbs_post_startup(self):
        self._post_initialized = True
        if self.tubbs is not None:
            self.vim.set_pvar('started', True)
        else:
            self.log.error('tubbs startup failed')

    @msg_command(A)
    def tubbs_a_def(self):
        pass

__all__ = ('TubbsNvimPlugin',)
