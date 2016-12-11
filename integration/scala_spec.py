from integration._support.base import VimIntegrationSpec


class ScalaSpec(VimIntegrationSpec):

    def setup(self):
        super().setup()

    def func(self):
        self.vim.cmd('TubbsADef')

__all__ = ('ScalaSpec',)
