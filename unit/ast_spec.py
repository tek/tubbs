from amino.test import temp_dir
from amino.test.path import fixture_path

from kallikrein import Expectation, k, unsafe_k
from kallikrein.matchers.either import be_right
from kallikrein.matchers import contain
from kallikrein.expectable import Expectable
from amino import _, Either, Path

from tubbs.grako.base import BuiltinParser
from tubbs.formatter.tree import Tree
from tubbs.grako.ast import AstElem


class Parser(BuiltinParser):

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


class AstSpec:
    ''' AST
    positions of tokens $token_position
    range of a list $list_range
    positive closure $positive_closure
    pre-token whitespace $whitespace
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
        tok1 = ast.l._data
        tok2 = ast.r._data
        return (k(tok1.pos) == 4) & (k(tok2.pos) == 8) & (k(tok2.endpos) == 11)

    def list_range(self) -> Expectation:
        clos = ', bar, zam'
        data = 'tok(foo{})'.format(clos)
        ast = self.ast(data, 'call')
        start, end = ast.rest._data.range
        tree = Tree(ast)
        return (
            (k(start) == 7) &
            (k(end) == 17) &
            (k(tree.root.sub[3].text) == clos)
        )

    def positive_closure(self) -> Expectation:
        data = 'tok: foo bar baz'
        ast = self.ast(data, 'poswrap')
        return k(ast.clos.id.last.raw).must(contain('baz'))

    def whitespace(self) -> Expectation:
        i = 4
        ws = ' ' * i
        data = '{}tok: foo,  bar,baz'.format(ws)
        ast = self.ast(data, 'ws')
        tree = Tree(ast)
        root = tree.root
        args = (root.sub.last / _.sub).x
        def indent(i: int) -> Expectable:
            return k(args.lift(i) / _.indent)
        return (
            (k(root.indent) == i) &
            (indent(0).must(contain(1))) &
            (indent(1).must(contain(0))) &
            (indent(2).must(contain(2))) &
            (indent(3).must(contain(0))) &
            (indent(4).must(contain(0))) &
            (k(root.with_ws) == data)
        )

__all__ = ('AstSpec',)
