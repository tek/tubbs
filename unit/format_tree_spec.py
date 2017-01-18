from amino.test import Spec
from amino.lazy import lazy
from amino import _

from tubbs.grako.scala import Parser
from tubbs.formatter.tree import Tree, ListNode
from tubbs.formatter.scala import Breaker

fun = '''def fun[A, B, C](p1: Type1, p2: Type2)\
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

    @lazy
    def _tree(self):
        ast = self._parser.parse(fun, 'def')
        ast.should.be.right
        return Tree(ast.value)

    def range(self):
        def check_node(node):
            if not isinstance(node, ListNode):
                start, end = node.range
                fun[start:end].should.equal(node.text)
        tree = self._tree.root
        tree.foreach(check_node)

    def create(self):
        breaker = Breaker(37)
        # print(t)
        broken = self._tree / breaker.format
        print(broken.join_lines)

__all__ = ('FormatTreeSpec',)
