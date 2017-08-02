from kallikrein import k, Expectation
from kallikrein.matchers.either import be_right
from kallikrein.matchers.lines import have_lines

from tubbs.tatsu.scala import Parser
from tubbs.formatter.scala.breaker import Breaker
from tubbs.formatter.scala.indenter import Indenter

from amino import Path, List, Either, L, _, __, Eval
from amino.lazy import lazy
from amino.test.path import load_fixture


class ScalaRulesSpec:
    '''
    break extends/with statements unconditionally $extends
    '''

    @lazy
    def parser(self) -> Parser:
        parser = Parser()
        parser.gen()
        return parser

    @lazy
    def base_path(self) -> Path:
        return Path('format/scala/rules')

    @lazy
    def breaker(self) -> Breaker:
        return Breaker(120)

    @lazy
    def indenter(self) -> Indenter:
        return Indenter(2)

    def format(self, code: str, rule: str) -> Either[str, List[str]]:
        def go(formatter, code0) -> Either[str, List[str]]:
            return self.parser.parse(code0, rule).flat_traverse(formatter.format, Eval)._value() / _.join_lines
        return go(self.breaker, code) // L(go)(self.indenter, _)

    def parse(self, name: str, rule: str) -> Expectation:
        dir = self.base_path / name
        data = load_fixture(dir / 'code.scala')
        target = load_fixture(dir / 'target.scala')
        formatted = self.format(data, rule)
        return k(formatted).must(be_right(have_lines(target)))

    def extends(self) -> Expectation:
        return self.parse('extends', 'class')

__all__ = ('ScalaRulesSpec',)
