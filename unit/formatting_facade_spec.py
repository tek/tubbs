from tubbs.tatsu.scala import Parser
from tubbs.formatter.scala import Breaker, Indenter
from tubbs.formatter.facade import FormattingFacade
from tubbs.hints.scala import Hints
from tubbs.formatter.base import Formatter
from tubbs.formatter.breaker import DictBreaker
from tubbs.formatter.indenter import DictIndenter

from kallikrein.expectation import Expectation
from kallikrein import k
from kallikrein.matchers import contain
import kallikrein.matchers.either  # NOQA

from amino import List, Just, _, Map
from amino.test.path import load_fixture
from amino.list import Lists


def_target = '''  def fun1[TPar1 <: UB1: TC1]
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


val_target = '''\
  val name =
    value.attr
      .map(fun1)
      .collect { case Extract(v1, v2) => fun2(v2, v1) }
      .flatMap {
        case (x, y) =>
          Option(x + y)
      }
      .zip'''


val_target2 = '''val x = a
  .b { case aaaaaaaaaaaaaaaaaaa => b }
'''


broken_apply = '''val a =
  foo
    .map {
      case a =>
        a
    }'''

def_def = '''def foo = {
  a match {
    case b => { foo }
    case _ => 1
  }
}'''


class FormattingFacadeSpec:

    '''formatting facade

    broken apply expression with case clauses $broken_apply
    '''
    # break a scala def
    # with default rules $scala_def_default
    # with custom rules in a dict $scala_def_dict

    # break a scala val
    # with default rules $scala_val_default

    def setup(self) -> None:
        def_content = load_fixture('format', 'scala', 'file1.scala')
        val_content = load_fixture('format', 'scala', 'file2.scala')
        self.def_lines = Lists.lines(def_content)
        self.val_lines = Lists.lines(val_content)
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

    def format_scala(self, formatters: List[Formatter], lines: List[str], target: str) -> Expectation:
        facade = self.facade(formatters)
        result = facade.format(lines, (9, 10)) / _.lines
        print(result.fatal.join_lines)
        print('---')
        print(target)
        return k(result).must(contain(Lists.lines(target)))

    def scala_def(self, formatters: List[Formatter]) -> Expectation:
        return self.format_scala(formatters, self.def_lines, def_target)

    def scala_val(self, formatters: List[Formatter]) -> Expectation:
        return self.format_scala(formatters, self.val_lines, val_target)

    def scala_def_default(self) -> Expectation:
        return self.scala_def(self.default_formatters)

    def scala_def_dict(self) -> Expectation:
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
        return self.scala_def(formatters)

    def scala_val_default(self) -> Expectation:
        return self.scala_val(self.default_formatters)

    def scala_val_default2(self) -> Expectation:
        # facade = self.facade(self.default_formatters)
        # result = facade.format(List.lines(val_target2), (0, 1)) / _.lines
        return k(1) == 1

    def broken_apply(self) -> Expectation:
        ast = self.parser.parse(broken_apply, 'valVarDef').get_or_raise
        ind = Indenter(2)
        r = ind.format(ast)
        v = r.attempt / _.join_lines
        return k(v).must(contain(broken_apply))

__all__ = ('FormattingFacadeSpec',)
