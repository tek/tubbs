import abc
from typing import Callable, Sized, Tuple, Any, Union, cast

from hues import huestr

from amino import Either, List, L, Boolean, _, __, Right, Maybe, Map, Empty, Task
from amino.util.string import snake_case
from amino.func import dispatch
from amino.lazy import lazy
from amino.tree import MapNode, ListNode, LeafNode
from amino.regex import Regex

from ribosome.record import Record, int_field, float_field, field, str_field, any_field
from ribosome.nvim import NvimFacade
from ribosome.util.callback import VimCallback

from tubbs.formatter.tree import Tree, BiNode, BiInode
from tubbs.formatter.base import Formatter, VimFormatterMeta


def hl(data: str) -> str:
    return huestr(data).bg_yellow.black.colorized


ws_re = Regex(r'^\s*$')


def only_ws(data: str) -> Boolean:
    return ws_re.match(data).present


class BreakHandler(Record):
    handler = any_field()
    rule = str_field()


SingleBreakData = Tuple[str, float, float]
StrictBreakData = Union[List[SingleBreakData], SingleBreakData]


def is_break(a: Any) -> bool:
    return isinstance(a, Sized) and len(a) == 3


class StrictBreak(Record):
    position = int_field()
    prio = float_field()
    rule = str_field()
    node = field(BiNode)

    @property
    def _str_extra(self) -> List[Any]:
        return List(self.line, self.position, self.prio, self.rule)

    def match_name(self, name: str) -> bool:
        return name == self.rule

    @property
    def line(self) -> int:
        return self.node.line


class LazyBreakData:

    def __init__(self, node: BiNode, rule: str, f: Callable[[List['Break']], StrictBreakData]) -> None:
        self.node = node
        self.rule = rule
        self.f = f

    def invoke(self, breaks: List[StrictBreak]) -> StrictBreakData:
        return self.f(BreakState(self.node, breaks))

    def brk(self, breaks: List[StrictBreak]) -> Either[str, List[StrictBreak]]:
        return cons_breaks(self.node, self.rule, self.invoke(breaks))


BreakData = Union[StrictBreakData, LazyBreakData]


Break = Union[StrictBreak, LazyBreakData]


LazyBreakCallback = Callable[[List[Break]], StrictBreakData]


BreakResult = Union[LazyBreakCallback, StrictBreakData]


def cons_breaks(node: BiNode, rule: str, result: BreakResult) -> Either[str, List[Break]]:
    def mkbreak(position: int, prio: float) -> Either[str, StrictBreak]:
        return Boolean(prio > 0).m(StrictBreak(position=position, prio=float(prio), rule=rule, node=node))
    def mkbreaks(name: str, before: int, after: int) -> Either[str, List]:
        return (
            node
            .sub_range(name)
            .map2(lambda start, end: List((start, before), (end, after)).flat_map2(mkbreak))
        )
    def mkbreakss(a: Tuple) -> Either[str, List[Break]]:
        return mkbreaks(*a) if is_break(a) else Right(List())
    return (
        cast(List[SingleBreakData], result)
        .map(mkbreakss)
        .filter(_.present)
        .sequence(Either) /
        _.join
        if isinstance(result, List) else
        Right(List(LazyBreakData(node, rule, result)))
        if callable(result) else
        mkbreakss(result)
    )


class BreakState:

    def __init__(self, node: BiNode, breaks: List[Break]) -> None:
        self.node = node
        self.breaks = breaks

    @property
    def is_token(self) -> Boolean:
        return Boolean(isinstance(self.node, LeafNode))

    @lazy
    def parent_inode(self) -> BiInode:
        p = self.node.parent
        return p.parent if self.is_token else p

    @lazy
    def after_breaks(self) -> List[Break]:
        return (
            self.breaks
            .filter(_.line == self.node.line)
            .filter(_.position > self.node.pos)
        )

    def after(self, name: str) -> Boolean:
        return self.after_breaks.exists(__.match_name(name))

    @lazy
    def before_breaks(self) -> List[Break]:
        return (
            self.breaks
            .filter(_.line == self.node.line)
            .filter(_.position < self.node.pos)
        )

    def before(self, name: str) -> Boolean:
        return self.before_breaks.exists(__.match_name(name))

    @lazy
    def parent_breaks(self) -> List[Break]:
        siblings = self.parent_inode.sub
        def match(node: BiNode, break_node: BiNode) -> bool:
            return node == break_node or node.contains(break_node)
        return (
            self.breaks
            .filter(lambda a: siblings.exists(L(match)(_, a.node)))
        )

    @property
    def rule(self) -> str:
        return self.node.rule

    def __str__(self) -> str:
        return f'BreakState({self.node}, {self.breaks})'


class BreakRules:

    def default(self, state: BreakState) -> BreakData:
        return List()


class BreakerBase(Formatter):

    def __init__(self, textwidth: int) -> None:
        self.textwidth = textwidth
        self.brk = dispatch(self, List(MapNode, ListNode, LeafNode), 'break_')

    @abc.abstractmethod
    def handler(self, node: BiNode, tmpl: str) -> Callable[[BiNode], BreakData]:
        ...

    @abc.abstractproperty
    def default_handler(self) -> Callable[[BiNode], BreakData]:
        ...

    def format(self, tree: Tree) -> Either:
        return Right(self.apply_breaks(tree, self.breaks(tree.root).attempt.get_or_raise))

    def breaks(self, root: BiNode) -> Task[List[StrictBreak]]:
        def handle_lazy(breaks: List[Break]) -> Task[List[StrictBreak]]:
            lazy, strict = breaks.split_type(LazyBreakData)
            strict1 = lazy.traverse(__.brk(strict), Either).map(_.join).task()
            return strict1 / strict.add
        return self.brk(root, List()) // handle_lazy

    def apply_breaks(self, tree: Tree, breaks: List[Break]) -> List[str]:
        self.log.debug('applying breaks: {}'.format(breaks))
        return (
            tree.lines
            .zip(tree.bols)
            .flat_map2(L(self.break_line)(_, breaks, _))
            .map(__.rstrip())
        )

    def break_line(self, cur: str, brks: List[StrictBreak], start: int) -> List[str]:
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
        def rec0(brk: StrictBreak) -> Either[str, List[str]]:
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

    def lookup_handler(self, node: BiNode, tmpl: str) -> BreakHandler:
        def handler(suf: str, or_else: Callable=lambda: Empty()) -> Maybe[BreakHandler]:
            attr = tmpl.format(suf)
            self.log.ddebug('trying break handler {}'.format(attr))
            h = self.handler(node, attr) / L(BreakHandler.from_attr('handler'))(_, rule=suf)
            if h.present:
                self.log.ddebug('success')
            return h.o(or_else)
        rule = snake_case(node.rule)
        return handler(
            '{}_{}'.format(rule, node.key),
            L(handler)(rule, L(handler)(node.key))
        ) | BreakHandler(handler=self.default_handler, rule=rule)

    def handle(self, node: BiNode, tmpl: str, breaks: List[Break]) -> Either:
        handler = self.lookup_handler(node, tmpl)
        result = handler.handler(BreakState(node, breaks))
        return cons_breaks(node, handler.rule, result)

    def sub_breaks(self, node: BiInode, breaks: List[Break]) -> Task[List[Break]]:
        return (
            node.sub.traverse(L(self.brk)(_, breaks), Task) /
            _.join /
            breaks.add
        )

    def break_inode(self, node: BiInode, breaks: List[Break], pref: str) -> Task[List[Break]]:
        return (
            self.handle(node, '{}_{{}}'.format(pref), breaks).task() //
            L(self.sub_breaks)(node, _)
        )

    def break_map_node(self, node: MapNode, breaks: List[Break]) -> Task[List[Break]]:
        return self.break_inode(node, breaks, 'map')

    def break_list_node(self, node: ListNode, breaks: List[Break]) -> Task[List[Break]]:
        return self.break_inode(node, breaks, 'list')

    def break_leaf_node(self, node: LeafNode, breaks: List[Break]) -> Task[List[Break]]:
        return self.handle(node, 'token_{}', breaks).task()


class Breaker(BreakerBase):

    def __init__(self, rules: BreakRules, textwidth: int) -> None:
        super().__init__(textwidth)
        self.rules = rules

    def handler(self, node: BiNode, attr: str) -> Maybe[Callable[[BiNode], BreakData]]:
        return Maybe.check(getattr(self.rules, attr, None))

    @property
    def default_handler(self) -> Callable[[BiNode], BreakData]:
        return self.rules.default


class DictBreaker(BreakerBase):

    def __init__(self, rules: Map, textwidth: int) -> None:
        super().__init__(textwidth)
        self.rules = rules

    def handler(self, node: BiNode, attr: str) -> Maybe[Callable[[BiNode], BreakData]]:
        return self.rules.lift(attr) / (lambda a: lambda node: a)

    @property
    def default_handler(self) -> Callable[[BiNode], BreakData]:
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


__all__ = ('Breaker', 'DictBreaker', 'VimDictBreaker')
