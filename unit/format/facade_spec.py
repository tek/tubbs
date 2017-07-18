from tubbs.tatsu.scala import Parser
from tubbs.tatsu.break_dsl import Parser as BreakParser
from tubbs.formatter.facade import FormattingFacade
from tubbs.hints.scala import Hints
from tubbs.formatter.base import Formatter
from tubbs.formatter.indenter.main import DictIndenter
from tubbs.formatter.breaker.main import DictBreaker
from tubbs.formatter.scala.breaker import Breaker
from tubbs.formatter.scala.indenter import Indenter
from tubbs.formatter.breaker.conds import default_conds

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
      .collect {
        case Extract(v1, v2) => fun2(v2, v1)
      }
      .flatMap {
        case (x, y) =>
          Option(x + y)
      }
      .zip'''

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
    break a scala def
    # with default rules $scala_def_default
    with custom rules in a dict $scala_def_dict

    break a scala val
    # with default rules $scala_val_default

    # broken apply expression with case clauses $broken_apply
    '''

    def setup(self) -> None:
        def_content = load_fixture('format', 'scala', 'file1.scala')
        val_content = load_fixture('format', 'scala', 'file2.scala')
        self.def_lines = Lists.lines(def_content)
        self.val_lines = Lists.lines(val_content)
        self.parser = Parser()
        self.parser.gen()
        self.break_parser = BreakParser()
        self.break_parser.gen()

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
        result = facade.format(lines, (9, 10))._value().lines
        return k(result) == Lists.lines(target)

    def scala_def(self, formatters: List[Formatter]) -> Expectation:
        return self.format_scala(formatters, self.def_lines, def_target)

    def scala_val(self, formatters: List[Formatter]) -> Expectation:
        return self.format_scala(formatters, self.val_lines, val_target)

    def scala_def_default(self) -> Expectation:
        return self.scala_def(self.default_formatters)

    def scala_def_dict(self) -> Expectation:
        block_rhs = '(0.3 @ (sibling_rule(_.rhs, block) & sibling_valid(_.rhs) & after(lbrace)))'
        break_rules = Map(
            case_block_body='before:(1.1 @ multi_line_block | 0.91)',
            case_clause='before:(1.0 @ multi_line_block_for(_.parent.parent.parent.parent) | 0.9)',
            block_body='before:1.1',
            block_rest_stat='before:0.8',
            seminl_semi='after:1.1',
            lbrace='after:((1.0 @ multi_line_block) | 0.31)',
            rbrace='before:((1.0 @ multi_line_block) | (1.0 @ sibling(_.body)) | (1.0 @ sibling(_.brace)) | 0.31)',
            param_clause='before:0.7',
            implicit_param_clause='before:0.75',
            assign=f'after:((0.0 @ parent_rule(param)) | {block_rhs} | 0.8)',
        )
        indents = Map(
            case_clauses=1,
            block_body=1,
            rbrace=-1,
        )
        formatters = List(DictBreaker(self.break_parser, break_rules, default_conds, 40), DictIndenter(indents, 2))
        return self.scala_def(formatters)

    def scala_val_default(self) -> Expectation:
        return self.scala_val(self.default_formatters)

    def broken_apply(self) -> Expectation:
        ast = self.parser.parse(broken_apply, 'valVarDef').get_or_raise
        ind = Indenter(2)
        r = ind.format(ast)
        return k(r.value / _.join_lines).must(contain(broken_apply))

__all__ = ('FormattingFacadeSpec',)
