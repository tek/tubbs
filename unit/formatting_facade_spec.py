from tubbs.grako.scala import Parser
from tubbs.formatter.scala import Breaker, Indenter
from tubbs.formatter.facade import FormattingFacade
from tubbs.hints.scala import Hints

from kallikrein.expectation import Expectation
from kallikrein import k
from kallikrein.matchers import contain

from amino import List
from amino.test.path import load_fixture
from amino.list import Lists


target = '''  def fun1[TPar1 <: UB1: TC1]
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
  }'''


class FormattingFacadeSpec:
    ''' formatting facade

    break a scala statement $break_scala
    '''

    def break_scala(self) -> Expectation:
        content = load_fixture('format', 'scala', 'file1.scala')
        lines = Lists.lines(content)
        parser = Parser()
        parser.gen()
        formatters = List(Breaker(40), Indenter(2))
        hints = Hints()
        facade = FormattingFacade(parser, formatters, hints)
        result = facade.format(lines, (9, 10))
        return k(result).must(contain(Lists.lines(target)))

__all__ = ('FormattingFacadeSpec',)
