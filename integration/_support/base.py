from amino import Right, Either
from ribosome.test.integration.spec import (ExternalIntegrationSpec,
                                            PluginIntegrationSpec)
from ribosome.test.integration.klk import VimIntegrationKlkHelpers

from tubbs.logging import Logging
from tubbs.nvim_plugin import TubbsNvimPlugin


class IntegrationCommon(VimIntegrationKlkHelpers):

    @property
    def _prefix(self) -> str:
        return 'tubbs'

    @property
    def plugin_class(self) -> Either[str, type]:
        return Right(TubbsNvimPlugin)


class TubbsIntegrationSpec(IntegrationCommon, ExternalIntegrationSpec):

    def _start_plugin(self) -> None:
        self.plugin.start_plugin()
        self._wait(.05)
        self._wait_for(lambda: self.vim.vars.p('started').present)


class TubbsPluginIntegrationSpec(IntegrationCommon, PluginIntegrationSpec,
                                 Logging):

    def _start_plugin(self) -> None:
        self._debug = True
        self.vim.cmd_sync('TubbsStart')
        self._pvar_becomes('started', True)

__all__ = ('TubbsIntegrationSpec', 'TubbsPluginIntegrationSpec')
