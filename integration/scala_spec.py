from integration._support.base import TubbsPluginIntegrationSpec

from amino.test.path import fixture_path
from amino.test import later
from amino import List


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


format_def_target = '''package pack

object Ob1
{
  def fun1[TPar1 <: UB1: TC1]
  (par1a: Tpe1, par1b: Tpe1)
  (par2a: Tpe2, par2b: Tpe2)
  (implicit par3: Tpe3, par4: Tpe4) = {
    val v1 = fun2(par1);
    fun3(v1)
  }
}'''


class ScalaFormatSpec(TubbsPluginIntegrationSpec):

    @property
    def _scala_file(self):
        return fixture_path('scala', 'format', 'file1.scala')

    def format_def(self):
        self.vim.edit(self._scala_file).run_sync()
        self.vim.buffer.options.set('filetype', 'scala')
        self.vim.buffer.options.set('textwidth', 40)
        self.json_cmd_sync('TubFormatRange', start=5)
        self._buffer_content(List.lines(format_def_target))

__all__ = ('ScalaSpec',)
