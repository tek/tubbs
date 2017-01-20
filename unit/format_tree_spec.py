from amino.test import Spec
from amino.lazy import lazy

from tubbs.grako.scala import Parser
from tubbs.formatter.tree import Tree, ListNode
from tubbs.formatter.scala import Breaker, Indenter

fun = '''def fun[A, B, C](p1: Type1, p2: Type2)\
(implicit p3: A :: B, p4: Type4) = {
    val a = p1 match {case x: Type2 => 5
        case _ => 3
    }
}'''

broken_fun = '''def fun[A, B, C]
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


class FormatTreeSpec(Spec):

    @lazy
    def _parser(self):
        parser = Parser()
        parser.gen()
        return parser

    def _parse(self, data):
        ast = self._parser.parse(data, 'def')
        ast.should.be.right
        return ast.value

    @lazy
    def _fun_tree(self):
        return Tree(self._parse(fun))

    @lazy
    def _broken_fun_tree(self):
        return Tree(self._parse(broken_fun))

    def range(self):
        def check_node(node):
            if not isinstance(node, ListNode):
                start, end = node.range
                fun[start:end].should.equal(node.text)  # type: ignore
        tree = self._fun_tree.root
        tree.foreach(check_node)

    def break_fun(self):
        breaker = Breaker(37)
        broken = breaker.format(self._fun_tree)
        broken.join_lines.must.equal(broken_fun)

    def indent_broken(self):
        indenter = Indenter(2)
        tree = self._broken_fun_tree
        indented = indenter.format(tree)
        indented.join_lines.should.equal(formatted_fun)

__all__ = ('FormatTreeSpec',)
