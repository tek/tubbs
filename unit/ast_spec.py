from amino.test import temp_dir
from amino.test.path import fixture_path

from kallikrein import Expectation, k, unsafe_k
from kallikrein.matchers.either import be_right
from kallikrein.matchers import contain
from kallikrein.expectable import Expectable
from amino import _, Either, Path, __

from tubbs.tatsu.base import LangParser
from tubbs.tatsu.ast import AstElem, ast_rose_tree

from unit._support.ast import be_token


class Parser(LangParser):

    @property
    def module_base(self) -> str:
        return 'unit._temp.parser'

    @property
    def parsers_path(self) -> Path:
        return temp_dir('parser')

    @property
    def grammar_path(self) -> Path:
        return fixture_path('parser')

    @property
    def name(self) -> str:
        return 'spec1'

    @property
    def left_recursion(self) -> bool:
        return False


class AstSpec:
    ''' AST
    positions of tokens $token_position
    range of a list $list_range
    positive closure $positive_closure
    pre-token whitespace $whitespace
    line number attribute $lines
    '''

    def setup(self) -> None:
        self._parser = Parser()
        self._parser.gen()

    def parse(self, text: str, rule: str) -> Either[str, AstElem]:
        return self._parser.parse(text, rule)

    def ast(self, text: str, rule: str) -> AstElem:
        res = self.parse(text, rule)
        unsafe_k(res).must(be_right)
        return res.value

    def token_position(self) -> Expectation:
        data = 'tok foo bar'
        ast = self.ast(data, 'ids')
        tok1 = ast.s.l.data
        tok2 = ast.s.r.data
        return (k(tok1.pos) == 4) & (k(tok2.pos) == 8) & (k(tok2.endpos) == 11)

    def list_range(self) -> Expectation:
        clos = ', bar, zam'
        data = 'tok(foo{})'.format(clos)
        ast = self.ast(data, 'call')
        start, end = ast.s.rest.data.range
        tree = ast_rose_tree(ast)
        return (
            (k(start) == 7) &
            (k(end) == 17) &
            (k(tree.sub[3].data.ast.text) == clos)
        )

    def positive_closure(self) -> Expectation:
        data = 'tok: foo bar baz'
        ast = self.ast(data, 'poswrap')
        return k(ast.s.clos.id.last).must(be_token('baz'))

    def whitespace(self) -> Expectation:
        i = 4
        ws = ' ' * i
        data = '{}tok: foo,  bar,baz'.format(ws)
        ast = self.ast(data, 'ws')
        tree = ast_rose_tree(ast)
        args = tree.sub.last / _.sub
        def ws_count(i: int) -> Expectable:
            return k(args.flat_map(__.lift(i)) / _.data.ws_count)
        return (
            (k(tree.data.ws_count) == i) &
            (ws_count(0).must(contain(1))) &
            (ws_count(1).must(contain(0))) &
            (k(tree.data.with_ws) == data)
        )

    def lines(self) -> Expectation:
        data = '{tok(a)\ntok(b)}'
        ast = self.ast(data, 'stats')
        return (
            k(ast.s.head.e.map(_.lnum)).must(contain(0)) &
            k(ast.s.tail.head.e.map(_.lnum)).must(contain(0)) &
            k(ast.s.tail[1].first.e.map(_.lnum)).must(contain(1))
        )

__all__ = ('AstSpec',)
