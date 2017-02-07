import abc
from typing import Callable, Sized, Tuple, Any, Union

from hues import huestr

from amino import Either, List, L, Boolean, _, __, Left, Right, Maybe, Map
from amino.util.string import snake_case
from amino.func import dispatch
from amino.regex import Regex

from ribosome.record import Record, int_field, float_field, field
from ribosome.nvim import NvimFacade
from ribosome.util.callback import VimCallback

from tubbs.logging import Logging
from tubbs.formatter.tree import Tree, MapNode, ListNode, TokenNode, Node


def hl(data: str) -> str:
    return huestr(data).bg_yellow.black.colorized


ws_re = Regex(r'^\s*$')


def only_ws(data: str) -> Boolean:
    return ws_re.match(data).present


class Formatter(Logging, abc.ABC):

    @abc.abstractmethod
    def format(self, tree: Tree) -> Either[str, List[str]]:
        ...

    def __call__(self, tree: Tree) -> Either:
        return self.format(tree)


class VimFormatterMeta(abc.ABCMeta):

    def convert_data(self, data: Map) -> Map:
        return data


class Break(Record):
    position = int_field()
    prio = float_field()

    @property
    def _str_extra(self) -> List[Any]:
        return List(self.position, self.prio)


SingleBreakData = Tuple[str, float, float]
BreakData = Union[List[SingleBreakData], SingleBreakData]


class BreakRules:

    def default(self, node: Node) -> BreakData:
        return List()


class BreakerBase(Formatter):

    def __init__(self, textwidth: int) -> None:
        self.textwidth = textwidth
        self.breaks = dispatch(self, List(MapNode, ListNode, TokenNode),
                               'break_')

    @abc.abstractmethod
    def handler(self, node: Node, tmpl: str) -> Callable[[Node], BreakData]:
        ...

    @abc.abstractproperty
    def default_handler(self) -> Callable[[Node], BreakData]:
        ...

    def format(self, tree: Tree) -> Either:
        return self.breaks(tree.root) / L(self.apply_breaks)(tree, _)

    def apply_breaks(self, tree: Tree, breaks: List[Break]) -> List[str]:
        self.log.debug('applying breaks: {}'.format(breaks))
        return (
            tree.lines
            .zip(tree.bols)
            .flat_map2(L(self.break_line)(_, breaks, _))
            .map(__.rstrip())
        )

    def break_line(self, cur: str, brks: List[Break], start: int) -> List[str]:
        end = start + len(cur)
        qualified = brks.filter(lambda a: start < a.position < end)
        def rec2(data: str, pos: int) -> List[str]:
            return (
                List()
                if only_ws(data) else
                self.break_line(data, qualified, pos)
            )
        def rec1(pos: int) -> List[str]:
            local_pos = pos - start
            self.log.ddebug('breaking at {}, {}'.format(pos, local_pos))
            left = cur[:local_pos]
            right = cur[local_pos:]
            self.log.ddebug(
                lambda:
                'broke line into\n{}\n{}'.format(hl(left), hl(right))
            )
            return rec2(left, start) + rec2(right, pos)
        def rec0(brk: Break) -> Either[str, List[str]]:
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

    def lookup_handler(self, node: Node, tmpl: str
                       ) -> Callable[[Node], BreakData]:
        def handler(suf: str, or_else: Callable=lambda: None) -> Callable:
            attr = tmpl.format(suf)
            self.log.ddebug('trying break handler {}'.format(attr))
            h = self.handler(node, attr)
            if h is not None:
                self.log.ddebug('success')
            return h or or_else() or self.default_handler
        rule = snake_case(node.rule)
        return handler(
            '{}_{}'.format(rule, node.key),
            L(handler)(rule, L(handler)(node.key))
        )

    def handle(self, node: Node, tmpl: str) -> Either:
        result = self.lookup_handler(node, tmpl)(node)
        def is_break(a: Any) -> bool:
            return isinstance(a, Sized) and len(a) == 3
        def mkbreak(position: int, prio: float) -> Maybe:
            return Boolean(prio > 0).m(Break(position=position,
                                             prio=float(prio)))
        def mkbreaks(name: str, before: int, after: int) -> Either[str, List]:
            return node.sub_range(name).map2(
                lambda start, end:
                List((start, before), (end, after))
                .flat_map2(mkbreak)
            )
        def mkbreakss(a: Tuple) -> Either[str, List[Break]]:
            return mkbreaks(*a) if is_break(a) else Right(List())
        return (
            result  # type: ignore
            .map(mkbreakss)
            .filter(_.present)
            .sequence(Either) /
            _.join
            if isinstance(result, List) else
            mkbreakss(result)
        )

    def break_map_node(self, node: MapNode) -> Either:
        sub = node.sub.traverse(self.breaks, Either) / _.join
        return (self.handle(node, 'map_{}') & sub).map2(lambda a, b: a + b)

    def break_list_node(self, node: ListNode) -> Either:
        sub = node.sub.traverse(self.breaks, Either) / _.join
        return (self.handle(node, 'list_{}') & sub).map2(lambda a, b: a + b)

    def break_token_node(self, node: TokenNode) -> Either:
        return self.handle(node, 'token_{}')


class Breaker(BreakerBase):

    def __init__(self, rules: BreakRules, textwidth: int) -> None:
        super().__init__(textwidth)
        self.rules = rules

    def handler(self, node: Node, attr: str) -> Callable[[Node], BreakData]:
        return getattr(self.rules, attr, None)

    @property
    def default_handler(self) -> Callable[[Node], BreakData]:
        return self.rules.default


class DictBreaker(BreakerBase):

    def __init__(self, rules: Map, textwidth: int) -> None:
        super().__init__(textwidth)
        self.rules = rules

    def handler(self, node: Node, attr: str) -> Callable[[Node], BreakData]:
        return self.rules.lift(attr) / (lambda a: lambda node: a) | None

    @property
    def default_handler(self) -> Callable[[Node], BreakData]:
        return lambda node: List()


class VimDictBreaker(DictBreaker, VimCallback, metaclass=VimFormatterMeta):

    @staticmethod
    def convert_data(data: Map) -> Map:
        def convert(brk: Any) -> BreakData:
            return (
                tuple(brk)
                if isinstance(brk, List) and
                not brk.exists(L(isinstance)(_, List)) else
                brk
            )
        return data.valmap(convert)

    def __init__(self, vim: NvimFacade, rules: Map) -> None:
        tw = vim.buffer.options('textwidth') | 80
        super().__init__(rules, tw)


class IndentRules:

    def default(self, node: Node) -> int:
        return 0


class Indent(Record):
    node = field(Node)
    indent = int_field()

    @property
    def pos(self) -> int:
        return self.node.pos

    @property
    def _str_extra(self) -> List[Any]:
        return List(self.node.key, self.indent)


class IndenterBase(Formatter):

    def __init__(self, shiftwidth: int) -> None:
        self.shiftwidth = shiftwidth

    @abc.abstractmethod
    def handler(self, name: str) -> Callable[[Node], int]:
        ...

    @abc.abstractproperty
    def default_handler(self) -> Callable[[Node], int]:
        ...

    def format(self, tree: Tree) -> List[str]:
        indents = (
            tree.bol_nodes /
            __.map(self.indents) //
            __.max_by(lambda a: abs(a.indent)) /
            _.indent
        )
        return self.indent(tree.root.indent, tree.lines, indents)

    def lookup_handler(self, node: Node) -> Callable[[Node], int]:
        def handler(name: str, or_else: Callable=lambda: None
                    ) -> Callable[[Node], int]:
            self.log.ddebug('trying ident handler {}'.format(name))
            h = self.handler(name)
            return h or or_else() or self.default_handler
        rule = snake_case(node.rule)
        return handler(
            '{}_{}'.format(rule, node.key),
            L(handler)(rule, L(handler)(node.key))
        )

    def indents(self, node: Node) -> Indent:
        indent = self.lookup_handler(node)(node)
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

    def _indent1(self, data: List[Tuple[str, int]], root_indent: float
                 ) -> List[str]:
        def shift(z: Tuple[float, List[str]], a: Tuple[str, int]
                  ) -> Tuple[float, List[str]]:
            current_indent, result = z
            line, indent = a
            new_indent = current_indent + indent
            line_indent = int(self.shiftwidth * new_indent)
            new_line = '{}{}'.format(' ' * line_indent, line.strip())
            return new_indent, result.cat(new_line)
        return data.fold_left((root_indent, List()))(shift)[1]


class Indenter(IndenterBase):

    def __init__(self, rules: IndentRules, shiftwidth: int) -> None:
        super().__init__(shiftwidth)
        self.rules = rules

    def handler(self, name: str) -> Callable[[Node], int]:
        return getattr(self.rules, name, None)

    @property
    def default_handler(self) -> Callable[[Node], int]:
        return self.rules.default


class DictIndenter(IndenterBase):

    def __init__(self, rules: Map, shiftwidth: int) -> None:
        super().__init__(shiftwidth)
        self.rules = rules

    def handler(self, name: str) -> Callable[[Node], int]:
        return self.rules.lift(name) / (lambda a: lambda node: a) | None

    @property
    def default_handler(self) -> Callable[[Node], int]:
        return lambda node: 0


class VimDictIndenter(DictIndenter, VimCallback, metaclass=VimFormatterMeta):

    def __init__(self, vim: NvimFacade, rules: Map) -> None:
        sw = vim.options('shiftwidth') | 2
        super().__init__(rules, sw)

__all__ = ('Formatter', 'Breaker', 'Indenter', 'DictBreaker', 'VimDictBreaker',
           'DictIndenter', 'VimDictIndenter')
