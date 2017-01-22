from integration._support.base import TubbsPluginIntegrationSpec

from amino.test.path import fixture_path
from amino.test import later


class ScalaSpec(TubbsPluginIntegrationSpec):

    @property
    def _scala_file(self):
        return fixture_path('scala', 'file1.scala')

    def select_def(self):
        self.vim.vars.set_p('parser', 'scala')
        self.vim.edit(self._scala_file).run_sync()
        self.vim.window.set_cursor(22)
        self.vim.cmd_sync('call TubA(\'def\')')
        self._wait(.1)
        self.vim.normal('x')
        later(lambda: self.vim.buffer.line_count.should.equal(22))

    def delete_def(self):
        self.vim.cmd_sync('onoremap ad :call TubA(\'def\')<cr>')
        self.vim.edit(self._scala_file).run_sync()
        self.vim.buffer.options.set('filetype', 'scala')
        self.vim.window.set_cursor(22)
        lines_pre = self.vim.buffer.line_count
        self.vim.cmd_sync('normal dad')
        later(lambda: self.vim.buffer.line_count.should.equal(lines_pre - 4))


class ScalaFormatSpec(TubbsPluginIntegrationSpec):

    @property
    def _scala_file(self):
        return fixture_path('scala', 'format', 'file1.scala')

    def format_def(self):
        self.vim.edit(self._scala_file).run_sync()
        self.vim.buffer.options.set('filetype', 'scala')
        self.vim.buffer.options.set('textwidth', 10)
        self.json_cmd_sync('TubFormatRange', start=5)
        self._buffer_length(12)

__all__ = ('ScalaSpec',)
