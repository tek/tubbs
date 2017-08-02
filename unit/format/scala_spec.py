from typing import Tuple

from amino.lazy import lazy

from kallikrein.matchers import contain, equal
from kallikrein import k, unsafe_k
from kallikrein.expectation import Expectation, AlgExpectation
from kallikrein.matchers.either import be_right
from amino import _, List
from amino.list import Lists

from tubbs.tatsu.scala import Parser
from tubbs.tatsu.ast import AstMap, RoseAstTree, ast_rose_tree, AstList, AstElem
from tubbs.formatter.scala.breaker import Breaker
from tubbs.formatter.scala.indenter import Indenter

from unit._support.ast import be_token

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
    tree boundary nodes $boundary_nodes
    indent broken function lines $indent_broken
    break conditionally on previous breaks $break_lookbehind
    '''

    @lazy
    def parser(self) -> Parser:
        parser = Parser()
        parser.gen()
        return parser

    def parse(self, data: str) -> AstMap:
        ast = self.parser.parse(data, 'def')
        unsafe_k(ast).must(be_right)
        return ast.value

    def tree(self, code: str) -> RoseAstTree:
        return ast_rose_tree(code)

    @lazy
    def fun_ast(self) -> AstElem:
        return self.parse(fun)

    @lazy
    def fun_tree(self) -> RoseAstTree:
        return ast_rose_tree(self.fun_ast)

    @lazy
    def broken_fun_ast(self) -> AstElem:
        return self.parse(broken_fun)

    @lazy
    def broken_fun_tree(self) -> RoseAstTree:
        return ast_rose_tree(self.broken_fun_ast)

    def range(self) -> Expectation:
        def check_node(node: AstElem) -> None:
            if not isinstance(node, AstList):
                start, end = node.range
                unsafe_k(fun[start:end]) == node.text
        self.fun_ast.foreach(check_node)

    def tree_lines(self) -> Expectation:
        lines = self.broken_fun_ast.lines
        return k(lines.join_lines).must(equal(broken_fun))

    def bols(self) -> Expectation:
        bols = self.broken_fun_ast.bols
        return k(bols) == List(0, 17, 40, 77, 96, 115, 127, 129, 131)

    def eols(self) -> Expectation:
        eols = self.broken_fun_ast.eols
        return k(eols) == List(16, 39, 76, 95, 114, 126, 128, 130)

    def bols_eols(self) -> Expectation:
        lines = Lists.lines(broken_fun)
        ast = self.broken_fun_ast
        be = ast.bols.zip(ast.eols)
        def check(be: Tuple[List[int], List[int]], line: str) -> None:
            start, end = be
            return k(line) == broken_fun[start:end]
        exps = (be.zip(lines)).map2(check)
        return exps.fold(AlgExpectation)

    def boundary_nodes(self) -> Expectation:
        nodes = self.broken_fun_ast.boundary_nodes
        return (
            k(nodes.s.defkw).must(be_token('def')) &
            k(nodes.s.def_.rhs.body.head.def_.def_.rhs.block.body.head.casekw).must(be_token('case')) &
            k(nodes.s.def_.rhs.rbrace.brace).must(be_token('}'))
        )

    def break_fun(self) -> Expectation:
        breaker = Breaker(37)
        broken = breaker.format(self.fun_ast)._value()
        return k(broken / _.join_lines).must(contain(broken_fun))

    def indent_broken(self) -> Expectation:
        indenter = Indenter(2)
        indented = indenter.format(self.broken_fun_ast).value
        return k(indented / _.join_lines).must(contain(formatted_fun))

    def break_lookbehind(self) -> Expectation:
        breaker = Breaker(12)
        broken = breaker.format(self.parse(lookbehind)).value
        return k(broken).must(contain(lookbehind_target))

__all__ = ('ScalaFormatSpec',)
