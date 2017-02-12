from integration._support.base import TubbsPluginIntegrationSpec

from amino.test.path import fixture_path

from kallikrein.expectation import Expectation
from amino import List, Path, Map


class ScalaSpec(TubbsPluginIntegrationSpec):
    ''' scala text objects

    select a def $select_def
    delete a def $delete_def
    '''

    @property
    def scala_file(self) -> Path:
        return fixture_path('scala', 'file1.scala')

    def select_def(self) -> Expectation:
        self.vim.vars.set_p('parser', 'scala')
        self.vim.edit(self.scala_file).run_sync()
        self.vim.window.set_cursor(22)
        self.vim.cmd_sync('call TubA(\'def\')')
        self._wait(.1)
        self.vim.normal('x')
        return self._buffer_length(22)

    def delete_def(self) -> Expectation:
        self.vim.cmd_sync('onoremap ad :call TubA(\'def\')<cr>')
        self.vim.edit(self.scala_file).run_sync()
        self.vim.buffer.options.set('filetype', 'scala')
        self.vim.window.set_cursor(22)
        lines_pre = self.vim.buffer.line_count
        self.vim.cmd_sync('normal dad')
        return self._buffer_length(lines_pre - 4)


format_range_def_target = '''package pack

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

format_at_def_target = '''package pack

object Ob2 {
  def fun1[TPar1 <: UB1: TC1]
  (par1a: Tpe1, par1b: Tpe1)
  (par2a: Tpe2, par2b: Tpe2)
  (implicit par3: Tpe3, par4: Tpe4) = {
    val a = par1a match {
      case _: Tpe1 => {
        println("Tpe1")
      }
      case Tpe2(f) => par1b map f
      case _ => {
        val v1 = fun2(par1);
        fun3(v1)
      }
    }
  }
}'''

format_dict_def_target = '''package pack

object Ob2 {
  def fun1[TPar1 <: UB1: TC1](par1a: Tpe1, par1b: Tpe1)
  (par2a: Tpe2, par2b: Tpe2)
  (implicit par3: Tpe3, par4: Tpe4) = {
    val a = par1a match {
      case _: Tpe1 => {
        println("Tpe1")
        }
        case Tpe2(f) => par1b map f
        case _ => {
          val v1 = fun2(par1);
          fun3(v1)
          }
          }
          }
}'''


class ScalaFormatSpec(TubbsPluginIntegrationSpec):
    '''formatting scala code

    format a function def via range $format_range_def
    format a line $format_line
    format via gqq and 'formatexpr' $formatexpr
    format via 'formatexpr' with multiple line range $formatexpr_multi
    format via custom dict $dict
    '''

    def edit_file(self, fpath: Path) -> None:
        self.vim.edit(fpath).run_sync()
        self.vim.buffer.options.set('filetype', 'scala')
        self.vim.buffer.options.set('textwidth', 40)

    @property
    def scala_file1(self) -> Path:
        return fixture_path('scala', 'format', 'file1.scala')

    @property
    def scala_file2(self) -> Path:
        return fixture_path('scala', 'format', 'file2.scala')

    def format_range_def(self) -> Expectation:
        self.edit_file(self.scala_file1)
        self.json_cmd_sync('TubFormatRange', start=5, end=5)
        return self._buffer_content(List.lines(format_range_def_target))

    def format_line(self) -> Expectation:
        self.edit_file(self.scala_file2)
        self.json_cmd_sync('TubFormatAt 8')
        return self._buffer_content(List.lines(format_at_def_target))

    def setup_formatexpr(self) -> None:
        self.edit_file(self.scala_file2)
        self.vim.buffer.options.set('formatexpr', 'TubFormat(v:lnum, v:count)')

    def formatexpr(self) -> Expectation:
        self.setup_formatexpr()
        self.vim.window.set_cursor(9)
        self.vim.cmd_sync('normal gqq')
        return self._buffer_content(List.lines(format_at_def_target))

    def formatexpr_multi(self) -> Expectation:
        self.setup_formatexpr()
        self.vim.window.set_cursor(9)
        self.vim.cmd_sync('normal gqj')
        return self._buffer_content(List.lines(format_at_def_target))

    def dict(self) -> Expectation:
        breaks = Map(
            map_case_clause=('casekw', 1.0, 0.0),
            map_block_body=('head', 0.9, 0.0),
            list_block_rest_stat=('stat', 0.9, 0.0),
            token_seminl_semi=('semi', 0.0, 1.1),
            token_lbrace=('lbrace', 0.0, 1.0),
            token_rbrace=('rbrace', 1.0, 0.0),
            map_implicit_param_clause=('lpar', 0.9, 0.1),
        )
        indents = Map(
            case_clauses=1,
            block_body=1,
        )
        self.vim.vars.set_p('scala_breaks', breaks)
        self.vim.vars.set_p('scala_indents', indents)
        self.setup_formatexpr()
        self.vim.window.set_cursor(9)
        self.vim.cmd_sync('normal gqq')
        return self._buffer_content(List.lines(format_dict_def_target))

__all__ = ('ScalaSpec', 'ScalaFormatSpec')
