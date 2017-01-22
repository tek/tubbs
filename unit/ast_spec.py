from amino.test import Spec, temp_dir
from amino.test.path import fixture_path
from amino import _, __

from tubbs.grako.base import BuiltinParser
from tubbs.formatter.tree import Tree


class Parser(BuiltinParser):

    @property
    def module_base(self):
        return 'unit._temp.parser'

    @property
    def parsers_path(self):
        return temp_dir('parser')

    @property
    def grammar_path(self):
        return fixture_path('parser')

    @property
    def name(self):
        return 'spec1'


class AstSpec(Spec):

    def setup(self):
        super().setup()
        self._parser = Parser()
        self._parser.gen()

    def _parse(self, text, rule):
        return self._parser.parse(text, rule)

    def _ast(self, text, rule):
        res = self._parse(text, rule)
        res.should.be.right
        return res.value

    def token_position(self):
        data = 'tok foo bar'
        ast = self._ast(data, 'ids')
        tok1 = ast.l._data
        tok2 = ast.r._data
        tok1.pos.should.equal(4)
        tok2.pos.should.equal(8)
        tok2.endpos.should.equal(11)

    def list_range(self):
        clos = ', bar, zam'
        data = f'tok(foo{clos})'
        ast = self._ast(data, 'call')
        start, end = ast.rest._data.range
        start.should.equal(7)
        end.should.equal(17)
        tree = Tree(ast)
        tree.root.sub[3].text.should.equal(clos)

    def positive_closure(self):
        data = 'tok: foo bar baz'
        ast = self._ast(data, 'poswrap')
        ast.clos.id

    def whitespace(self):
        i = 4
        ws = ' ' * i
        data = '{}tok: foo,  bar,baz'.format(ws)
        ast = self._ast(data, 'ws')
        tree = Tree(ast)
        root = tree.root
        root.indent.should.equal(i)
        args = (root.sub.last / _.sub).x
        indent = lambda i: (args.lift(i) / _.indent)
        indent(0).should.contain(1)
        indent(1).should.contain(0)
        indent(2).should.contain(2)
        indent(3).should.contain(0)
        indent(4).should.contain(0)
        root.with_ws.should.equal(data)

__all__ = ('AstSpec',)
