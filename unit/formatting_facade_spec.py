from tubbs.tatsu.scala import Parser
from tubbs.formatter.scala import Breaker, Indenter
from tubbs.formatter.facade import FormattingFacade
from tubbs.hints.scala import Hints
from tubbs.formatter.base import DictBreaker, DictIndenter, Formatter

from kallikrein.expectation import Expectation
from kallikrein import k
from kallikrein.matchers import contain

from amino import List, Just, _, Map
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

    break a scala statement
    with default rules $scala_default
    with custom rules in a dict $scala_dict
    '''

    def setup(self) -> None:
        content = load_fixture('format', 'scala', 'file1.scala')
        self.lines = Lists.lines(content)
        self.parser = Parser()
        self.parser.gen()

    def facade(self, formatters: List[Formatter]) -> FormattingFacade:
        hints = Hints()
        return FormattingFacade(self.parser, formatters, Just(hints))

    @property
    def default_formatters(self) -> List[Formatter]:
        return List(Breaker(40), Indenter(2))

    @property
    def default_facade(self) -> FormattingFacade:
        return self.facade(self.default_formatters)

    def scala(self, formatters: List[Formatter]) -> Expectation:
        facade = self.facade(formatters)
        result = facade.format(self.lines, (9, 10)) / _.lines
        return k(result).must(contain(Lists.lines(target)))

    def scala_default(self) -> Expectation:
        return self.scala(self.default_formatters)

    def scala_dict(self) -> Expectation:
        breaks = Map(
            map_case_clause=('casekw', 1.0, 0.0),
            map_block_body=('head', 0.9, 0.0),
            list_block_rest_stat=('stat', 0.9, 0.0),
            token_seminl_semi=('semi', 0.0, 1.1),
            token_lbrace=('lbrace', 0.0, 1.0),
            token_rbrace=('rbrace', 1.0, 0.0),
            map_param_clause=('lpar', 0.89, 0.1),
            map_implicit_param_clause=('lpar', 0.9, 0.1),
        )
        indents = Map(
            case_clauses=1,
            block_body=1,
            rbrace=-1,
        )
        formatters = List(DictBreaker(breaks, 40), DictIndenter(indents, 2))
        return self.scala(formatters)

__all__ = ('FormattingFacadeSpec',)
