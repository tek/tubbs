import abc
from typing import Callable, Sized

from amino import Either, List, L, Boolean, _, __, Left, Right
from amino.util.string import snake_case
from amino.func import dispatch

from ribosome.record import Record, int_field, float_field, field

from tubbs.logging import Logging
from tubbs.formatter.tree import Tree, MapNode, ListNode, TokenNode, Node


def eols(tree: Tree):
    def folder(z, a):
        cur, last = z
        n = last + len(a) + 1
        return cur.cat(n), n
    def fold(head, tail):
        return tail.fold_left((List(len(head)), len(head)))(folder)
    return tree.lines.detach_head.map2(fold) / _[0] | List()


def bols(tree: Tree):
    return tree.lines.fold_left(List(0))(
        lambda z, a: z.cat((z.last | 0) + 1 + len(a)))


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
        return Right(self.apply_breaks(tree, breaks))

    def __call__(self, tree: Tree):
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

    def _handler(self, node, tmpl):
        def handler(suf: str, or_else: Callable=lambda: None):
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

    def handle(self, node, tmpl):
        result = self._handler(node, tmpl)(node)
        is_break = lambda a: isinstance(a, Sized) and len(a) == 3
        def mkbreak(position, prio):
            return Boolean(prio > 0).e(
                'break prio 0',
                Break(position=position, prio=prio)
            )
        def mkbreaks(name, before, after):
            return node.sub_range(name).flat_map2(
                lambda start, end:
                List((start, before), (end, after))
                .flat_map2(mkbreak)
            )
        def mkbreakss(a):
            return mkbreaks(*a) if is_break(a) else List()
        return (result // mkbreakss
                if isinstance(result, List) else
                mkbreakss(result))

    def break_map_node(self, node):
        sub = node.sub.flat_map(self.breaks)
        return self.handle(node, 'map_{}') + sub

    def break_list_node(self, node):
        sub = node.sub.flat_map(self.breaks)
        return self.handle(node, 'list_{}') + sub

    def break_token_node(self, node):
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
        eol = eols(tree)
        def first(nodes):
            m = nodes.min_by(_.pos) / _.pos
            return nodes.filter(lambda a: m.contains(a.pos))
        line_nodes = (
            tree.line_nodes(eol)
            .map(first)
        )
        indents = (
            line_nodes /
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
