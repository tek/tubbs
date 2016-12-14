from ribosome import command, NvimStatePlugin, msg_command, NvimFacade
from ribosome.request import msg_function

from tubbs.main import Tubbs

from amino import List
from tubbs.logging import Logging
from tubbs.plugins.core.message import AObj, StageI, AObjRule, IObj, IObjRule


class TubbsNvimPlugin(NvimStatePlugin, Logging):

    def __init__(self, vim) -> None:
        super().__init__(NvimFacade(vim, 'tubbs'))
        self.tubbs = None  # type: Tubbs

    @property
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

    def start_plugin(self):
        plugins = self.vim.vars.pl('plugins') | self._default_plugins
        self.tubbs = Tubbs(self.vim.proxy, plugins)
        self.tubbs.start()
        self.tubbs.wait_for_running()
        self.tubbs.send(StageI())

    @property
    def _default_plugins(self):
        return List()

    @command(sync=True)
    def tubbs_start(self):
        return self.start_plugin()

    @msg_function(AObj, sync=True)
    def tub_a(self):
        pass

    @msg_command(IObj)
    def tub_i(self):
        pass

    @msg_command(AObjRule)
    def tub_a_rule(self):
        pass

    @msg_command(IObjRule)
    def tub_i_rule(self):
        pass

__all__ = ('TubbsNvimPlugin',)
