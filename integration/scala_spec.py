from integration._support.base import TubbsPluginIntegrationSpec

from amino.test.path import fixture_path


class ScalaSpec(TubbsPluginIntegrationSpec):

    @property
    def _scala_file(self):
        return fixture_path('scala', 'file1.scala')

    def fundef(self):
        self.vim.vars.set_p('parser', 'scala')
        self.vim.edit(self._scala_file).run_sync()
        self.vim.window.set_cursor(22)
        self.vim.cmd_sync('TubbsA def')
        self._wait(.1)
        self.vim.normal('x')
        self.vim.buffer.line_count.should.equal(22)

__all__ = ('ScalaSpec',)
