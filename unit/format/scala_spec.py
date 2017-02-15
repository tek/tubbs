from typing import Tuple

from amino.lazy import lazy

from kallikrein.matchers import contain, equal
from kallikrein import k, unsafe_k
from kallikrein.expectation import Expectation, AlgExpectation
from kallikrein.matchers.either import be_right
from kallikrein.matchers.length import have_length
from amino import _, List, __
from amino.list import Lists

from tubbs.grako.scala import Parser
from tubbs.formatter.tree import Tree, ListNode, Node
from tubbs.formatter.scala import Breaker, Indenter
from tubbs.grako.ast import AstMap

fun = '''def fun[A, B, C](p1: Type1, p2: Type2)\
(implicit p3: A :: B, p4: Type4) = {\
val a = p1 match {
case x: Type2 => 5 case _ => 3 } }'''


broken_fun = '''\
def fun[A, B, C]
(p1: Type1, p2: Type2)
(implicit p3: A :: B, p4: Type4) = {
val a = p1 match {
case x: Type2 => 5
case _ => 3
}
}'''


formatted_fun = '''def fun[A, B, C]
(p1: Type1, p2: Type2)
(implicit p3: A :: B, p4: Type4) = {
  val a = p1 match {
    case x: Type2 => 5
    case _ => 3
  }
}'''


lookbehind = 'def fun = { val b = a }'

lookbehind_target = List(
    'def fun = {',
    'val b = a',
    '}'
)


class ScalaFormatSpec:
    ''' formatting an AST
    check ast element ranges $range
    break lines of a function $break_fun
    tree bols $bols
    tree eols $eols
    range of bols and eols $bols_eols
    tree lines $tree_lines
    tree line nodes $line_nodes
    tree nodes at beginning of lines $bol_nodes
    indent broken function lines $indent_broken
    break conditionally on previous breaks $break_lookbehind
    '''

    __unsafe__ = None

    @lazy
    def parser(self) -> Parser:
        parser = Parser()
        parser.gen()
        return parser

    def parse(self, data: str) -> AstMap:
        ast = self.parser.parse(data, 'def')
        unsafe_k(ast).must(be_right)
        return ast.value

    def tree(self, code: str) -> Tree:
        return Tree(self.parse(code))

    @lazy
    def fun_tree(self) -> Tree:
        return self.tree(fun)

    @lazy
    def broken_fun_tree(self) -> Tree:
        return self.tree(broken_fun)

    def range(self) -> Expectation:
        def check_node(node: Node) -> None:
            if not isinstance(node, ListNode):
                start, end = node.range
                unsafe_k(fun[start:end]) == node.text
        tree = self.fun_tree.root
        tree.foreach(check_node)

    def tree_lines(self) -> Expectation:
        lines = self.broken_fun_tree.lines
        return k(lines.join_lines).must(equal(broken_fun))

    def bols(self) -> Expectation:
        bols = self.broken_fun_tree.bols
        return k(bols) == List(0, 17, 40, 77, 96, 115, 127, 129, 131)

    def eols(self) -> Expectation:
        eols = self.broken_fun_tree.eols
        return k(eols) == List(16, 39, 76, 95, 114, 126, 128, 130)

    def bols_eols(self) -> Expectation:
        lines = Lists.lines(broken_fun)
        tree = self.broken_fun_tree
        be = tree.bols.zip(tree.eols)
        def check(be: Tuple[List[int], List[int]], line: str) -> None:
            start, end = be
            return k(line) == broken_fun[start:end]
        exps = (be.zip(lines)).map2(check)
        return exps.fold(AlgExpectation)

    def line_nodes(self) -> Expectation:
        nodes = self.broken_fun_tree.line_nodes
        return k(nodes).must(have_length(Lists.lines(broken_fun).length))

    def bol_nodes(self) -> Expectation:
        nodes = self.broken_fun_tree.bol_nodes
        return (
            k(nodes.head // __.lift(1) / _.key).must(contain('defkw')) &
            k(nodes.lift(1) // _.head / _.key).must(contain('paramss')) &
            k(nodes.lift(2) // _.head / _.key).must(contain('lpar')) &
            k(nodes.lift(3) // _.head / _.key).must(contain('body')) &
            k(nodes.lift(4) // _.head / _.key).must(contain('cases')) &
            k(nodes.lift(5) // _.head / _.key).must(contain('case')) &
            k(nodes.lift(6) // _.head / _.key).must(contain('brace'))
        )

    def break_fun(self) -> Expectation:
        breaker = Breaker(37)
        broken = breaker.format(self.fun_tree)
        return k(broken / _.join_lines).must(contain(broken_fun))

    def indent_broken(self) -> Expectation:
        indenter = Indenter(2)
        tree = self.broken_fun_tree
        indented = indenter.format(tree)
        return k(indented / _.join_lines).must(contain(formatted_fun))

    def break_lookbehind(self) -> Expectation:
        breaker = Breaker(12)
        broken = breaker.format(self.tree(lookbehind))
        return k(broken).must(contain(lookbehind_target))

__all__ = ('ScalaFormatSpec',)
