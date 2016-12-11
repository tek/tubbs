from amino import Right
from ribosome.test import PluginIntegrationSpec
from ribosome.test.integration import ExternalIntegrationSpec

from tubbs.logging import Logging
from tubbs.test import Spec
from tubbs.nvim_plugin import TubbsNvimPlugin


class IntegrationCommon(Spec):

    @property
    def _prefix(self):
        return 'tubbs'

    @property
    def plugin_class(self):
        return Right(TubbsNvimPlugin)


class TubbsIntegrationSpec(IntegrationCommon, ExternalIntegrationSpec):

    def _start_plugin(self):
        self.plugin.start_plugin()
        self._wait(.05)
        self._wait_for(lambda: self.vim.vars.p('started').present)


class TubbsPluginIntegrationSpec(IntegrationCommon, PluginIntegrationSpec,
                                 Logging):

    def _start_plugin(self):
        self._debug = True
        self.vim.cmd_sync('TubbsStart')
        self._pvar_becomes('started', True)

__all__ = ('TubbsIntegrationSpec', 'TubbsPluginIntegrationSpec')
