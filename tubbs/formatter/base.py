import abc
from typing import Callable, Sized

from amino import Either, List, Left, L, Boolean, _, __
from amino.util.string import snake_case
from amino.func import dispatch

from ribosome.record import Record, int_field, float_field

from tubbs.logging import Logging
from tubbs.formatter.tree import Tree, MapNode, ListNode, TokenNode


class Formatter(Logging, abc.ABC):

    @abc.abstractmethod
    def format(self, tree: Tree) -> Either[str, List[str]]:
        ...


class BuiltinFormatter(Formatter):
    pass


class Break(Record):
    position = int_field()
    prio = float_field()

    @property
    def _str_extra(self):
        return List(self.position, self.prio)


class BreakRules:

    def default(self, node):
        return List()


class Breaker(Formatter):

    def __init__(self, rules, textwidth) -> None:
        self.rules = rules
        self.textwidth = textwidth
        self.breaks = dispatch(self, List(MapNode, ListNode, TokenNode),
                               'break_')

    def format(self, tree: Tree):
        breaks = self.breaks(tree.root)
        return self.apply_breaks(tree, breaks)

    def apply_breaks(self, tree, breaks):
        starts = tree.lines.fold_left(List(0))(
            lambda z, a: z.cat((z.last | 0) + 1 + len(a)))
        return (tree.lines
                .zip(starts)
                .flat_map2(L(self.break_line)(_, breaks, _)))

    def break_line(self, line: List[str], breaks: List[str], line_start: int
                   ) -> List[str]:
        def brk(cur, brks, start):
            end = start + len(cur)
            qual = brks.filter(lambda a: start < a.position < end)
            def rec(pos):
                local_pos = pos - start
                return (brk(cur[:local_pos], qual, start) +
                        brk(cur[local_pos:], qual, pos))
            return (
                Boolean(len(cur) > self.textwidth).maybe(qual) //
                __.max_by(_.prio) /
                _.position /
                rec |
                List(cur)
            )
        return brk(line, breaks, line_start)

    def _handler(self, node, tmpl):
        def handler(suf: str, or_else: Callable=lambda: None):
            h = getattr(self.rules, tmpl.format(suf), None)
            return h or or_else() or self.rules.default
        rule = snake_case(node.rule)
        return handler(
            '{}_{}'.format(rule, node.key),
            L(handler)(rule, L(handler)(node.key))
        )

    def handle(self, node, tmpl):
        result = self._handler(node, tmpl)(node)
        is_break = lambda a: isinstance(a, Sized) and len(a) == 3
        def mkbreak(position, prio):
            return Boolean(prio > 0).maybe(Break(position=position, prio=prio))
        def mkbreaks(name, before, after):
            start, end = node.sub_range(name)
            return List((start, before), (end, after)).flat_map2(mkbreak)
        def mkbreakss(a):
            return mkbreaks(*a) if is_break(a) else List()
        return (result // mkbreakss
                if isinstance(result, List) else
                mkbreakss(result))

    def break_node(self, node):
        sub = node.sub.flat_map(self.breaks)
        return self.handle(node, 'node_{}') + sub

    def break_list_node(self, node):
        sub = node.sub.flat_map(self.breaks)
        return self.handle(node, 'list_node_{}') + sub

    def break_leaf(self, leaf):
        return self.handle(leaf, 'leaf_{}')


class Indenter(Formatter):

    def format(self, tree, lines):
        return Left('NI')

__all__ = ('Formatter', 'BuiltinFormatter', 'Breaker', 'Indenter')
