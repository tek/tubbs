import abc
from typing import Callable, Sized, Tuple

from amino import Either, List, L, Boolean, _, __, Left, Right, Maybe
from amino.util.string import snake_case
from amino.func import dispatch

from ribosome.record import Record, int_field, float_field, field

from tubbs.logging import Logging
from tubbs.formatter.tree import Tree, MapNode, ListNode, TokenNode, Node


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

    def __init__(self, rules: BreakRules, textwidth: int) -> None:
        self.rules = rules
        self.textwidth = textwidth
        self.breaks = dispatch(self, List(MapNode, ListNode, TokenNode),
                               'break_')

    def format(self, tree: Tree) -> Either:
        return self.breaks(tree.root) / L(self.apply_breaks)(tree, _)

    def __call__(self, tree: Tree) -> Either:
        return self.format(tree)

    def apply_breaks(self, tree, breaks):
        self.log.debug('applying breaks: {}'.format(breaks))
        return (tree.lines
                .zip(bols(tree))
                .flat_map2(L(self.break_line)(_, breaks, _)))

    def break_line(self, line: List[str], breaks: List[str], line_start: int
                   ) -> List[str]:
        def brk(cur, brks, start):
            end = start + len(cur)
            qualified = brks.filter(lambda a: start < a.position < end)
            def rec1(pos):
                local_pos = pos - start
                self.log.ddebug('breaking at {}, {}'.format(pos, local_pos))
                left = cur[:local_pos]
                right = cur[local_pos:]
                self.log.ddebug(
                    'broke line into\n{}\n{}'.format(left, right))
                return brk(left, qualified, start) + brk(right, qualified, pos)
            def rec0(brk):
                msg = 'line did not exceed tw: {}'
                return (
                    Boolean(len(cur) > self.textwidth or brk.prio >= 1.0)
                    .e(msg.format(cur), brk.position) /
                    rec1
                )
            broken = (
                qualified.max_by(_.prio)
                .to_either('no breaks for {}'.format(cur)) //
                rec0
            ).leffect(self.log.ddebug)
            return broken | List(cur)
        return brk(line, breaks, line_start)

    def _handler(self, node: Node, tmpl: str) -> Callable:
        def handler(suf: str, or_else: Callable=lambda: None) -> Callable:
            attr = tmpl.format(suf)
            self.log.ddebug('trying break handler {}'.format(attr))
            h = getattr(self.rules, attr, None)
            if h is not None:
                self.log.ddebug('success')
            return h or or_else() or self.rules.default
        rule = snake_case(node.rule)
        return handler(
            '{}_{}'.format(rule, node.key),
            L(handler)(rule, L(handler)(node.key))
        )

    def handle(self, node: Node, tmpl: str) -> Either:
        result = self._handler(node, tmpl)(node)
        is_break = lambda a: isinstance(a, Sized) and len(a) == 3
        def mkbreak(position: int, prio: float) -> Maybe:
            return Boolean(prio > 0).m(Break(position=position, prio=prio))
        def mkbreaks(name: str, before: int, after: int) -> Either[str, List]:
            return node.sub_range(name).map2(
                lambda start, end:
                List((start, before), (end, after))
                .flat_map2(mkbreak)
            )
        def mkbreakss(a: Tuple) -> Either[str, List[Break]]:
            return mkbreaks(*a) if is_break(a) else Right(List())
        return (result.traverse(mkbreakss, Either) / _.join
                if isinstance(result, List) else
                mkbreakss(result))

    def break_map_node(self, node: MapNode) -> Either:
        sub = node.sub.traverse(self.breaks, Either) / _.join
        return (self.handle(node, 'map_{}') & sub).map2(lambda a, b: a + b)

    def break_list_node(self, node: ListNode) -> Either:
        sub = node.sub.traverse(self.breaks, Either) / _.join
        return (self.handle(node, 'list_{}') & sub).map2(lambda a, b: a + b)

    def break_token_node(self, node: TokenNode) -> Either:
        return self.handle(node, 'token_{}')


class IndentRules:

    def default(self, node):
        return 0


class Indent(Record):
    node = field(Node)
    indent = int_field()

    @property
    def pos(self):
        return self.node.pos

    @property
    def _str_extra(self):
        return List(self.node.key, self.indent)


class Indenter(Formatter):

    def __init__(self, rules: IndentRules, shiftwidth: int) -> None:
        self.rules = rules
        self.shiftwidth = shiftwidth

    def format(self, tree: Tree):
        indents = (
            tree.bol_nodes /
            __.map(self.indents) //
            __.max_by(lambda a: abs(a.indent)) /
            _.indent
        )
        return self.indent(tree.root.indent, tree.lines, indents)

    def _handler(self, node):
        def handler(name: str, or_else: Callable=lambda: None):
            self.log.ddebug('trying ident handler {}'.format(name))
            h = getattr(self.rules, name, None)
            return h or or_else() or self.rules.default
        rule = snake_case(node.rule)
        return handler(
            '{}_{}'.format(rule, node.key),
            L(handler)(rule, L(handler)(node.key))
        )

    def indents(self, node):
        indent = self._handler(node)(node)
        return Indent(node=node, indent=indent)

    def indent(self, baseline: int, lines: List[str], indents: List[int]
               ) -> List[str]:
        if len(lines) != len(indents):
            return Left('got {} idents for {} lines'.format(len(indents),
                                                            len(lines)))
        else:
            root_indent = baseline / self.shiftwidth
            data = lines.zip(indents)
            return Right(self._indent1(data, root_indent))

    def _indent1(self, data, root_indent):
        def shift(z, a):
            current_indent, result = z
            line, indent = a
            new_indent = current_indent + indent
            line_indent = int(self.shiftwidth * new_indent)
            new_line = '{}{}'.format(' ' * line_indent, line.strip())
            return new_indent, result.cat(new_line)
        return data.fold_left((root_indent, List()))(shift)[1]

__all__ = ('Formatter', 'BuiltinFormatter', 'Breaker', 'Indenter')
