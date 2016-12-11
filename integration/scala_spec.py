from integration._support.base import TubbsPluginIntegrationSpec


class ScalaSpec(TubbsPluginIntegrationSpec):

    def setup(self):
        super().setup()

    def fundef(self):
        self.vim.cmd_sync('TubbsA Def')
        self._wait(1)

__all__ = ('ScalaSpec',)
