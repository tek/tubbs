import abc
from typing import Callable, Sized, Tuple, Any, Union, cast, Iterable

from hues import huestr

from amino import Either, List, L, Boolean, _, __, Maybe, Map, Empty, Task
from amino.util.string import snake_case
from amino.lazy import lazy
from amino.regex import Regex

from ribosome.record import Record, int_field, float_field, field, str_field, any_field
from ribosome.nvim import NvimFacade
from ribosome.util.callback import VimCallback

from tubbs.formatter.base import Formatter, VimFormatterMeta
from tubbs.tatsu.ast import AstElem, RoseData, ast_rose_tree, RoseAstTree


def hl(data: str) -> str:
    return huestr(data).bg_yellow.black.colorized


ws_re = Regex(r'^\s*$')


def only_ws(data: str) -> Boolean:
    return ws_re.match(data).present


class BreakHandler(Record):
    handler = any_field()
    rule = str_field()


SingleBreakData = Tuple[float, float]
StrictBreakData = Union[List[SingleBreakData], SingleBreakData]


def is_break(a: Any) -> bool:
    return isinstance(a, Sized) and len(a) == 2


class StrictBreak(Record):
    position = int_field()
    prio = float_field()
    rule = str_field()
    node = field(RoseData)

    @property
    def _str_extra(self) -> List[Any]:
        return List(self.line, self.position, self.prio, self.rule)

    def match_name(self, name: str) -> bool:
        return name == self.rule

    @property
    def line(self) -> int:
        return self.node.line


class LazyBreakData:

    def __init__(self, node: RoseAstTree, rule: str, f: Callable[[List['Break']], StrictBreakData]) -> None:
        self.node = node
        self.rule = rule
        self.f = f

    def invoke(self, breaks: List[StrictBreak]) -> StrictBreakData:
        return self.f(BreakState(self.node, breaks))

    def brk(self, breaks: List[StrictBreak]) -> List[StrictBreak]:
        return cons_breaks(self.node, self.rule, self.invoke(breaks))


BreakData = Union[StrictBreakData, LazyBreakData]


Break = Union[StrictBreak, LazyBreakData]


LazyBreakCallback = Callable[[List[Break]], StrictBreakData]


BreakResult = Union[LazyBreakCallback, StrictBreakData]


def cons_breaks(node: RoseAstTree, rule: str, result: BreakResult) -> List[Break]:
    data = node.data
    def mkbreak(position: int, prio: float) -> Maybe[StrictBreak]:
        return Maybe.iff(prio > 0)(StrictBreak(position=position, prio=float(prio), rule=rule, node=data))
    def mkbreaks(before: int, after: int) -> Either[str, List]:
        start, end = node.range
        return List((start, before), (end, after)).flat_map2(mkbreak)
    def mkbreakss(a: Iterable) -> List[Break]:
        return mkbreaks(*a) if is_break(a) else List()
    return (
        cast(List[SingleBreakData], result) // mkbreakss
        if isinstance(result, List) else
        List(LazyBreakData(node, rule, result))
        if callable(result) else
        mkbreakss(result)
    )


class BreakState:

    def __init__(self, node: RoseData, breaks: List[Break]) -> None:
        self.node = node
        self.breaks = breaks

    @property
    def is_token(self) -> Boolean:
        return self.node.is_token

    @lazy
    def parent_inode(self) -> RoseData:
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
        def match(node: RoseAstTree, break_node: RoseData) -> bool:
            return node.data == break_node or node.data.ast.contains(break_node.ast)
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


def handle_lazy_breaks(breaks: List[Break]) -> Task[List[StrictBreak]]:
    lazy, strict = breaks.split_type(LazyBreakData)
    strict1 = Task.delay(lazy.flat_map, __.brk(strict))
    return strict1 / strict.add


class BreakerBase(Formatter):

    def __init__(self, textwidth: int) -> None:
        self.textwidth = textwidth

    @abc.abstractmethod
    def handler(self, node: RoseData, tmpl: str) -> Callable[[RoseData], BreakData]:
        ...

    @abc.abstractproperty
    def default_handler(self) -> Callable[[RoseData], BreakData]:
        ...

    def format(self, ast: AstElem) -> Task[List[str]]:
        rt = ast_rose_tree(ast)
        return self.breaks(rt) / L(self.apply_breaks)(ast, _)

    def breaks(self, ast: RoseAstTree) -> Task[List[StrictBreak]]:
        return self.brk(ast, List()) // handle_lazy_breaks

    def apply_breaks(self, ast: AstElem, breaks: List[Break]) -> List[str]:
        self.log.debug('applying breaks: {}'.format(breaks))
        return (
            ast.lines
            .zip(ast.bols)
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
            self.log.ddebug(lambda: 'broke line into\n{}\n{}'.format(hl(left), hl(right)))
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

    def lookup_handler(self, node: RoseData) -> BreakHandler:
        def handler(attr: str, or_else: Callable=lambda: Empty()) -> Maybe[BreakHandler]:
            self.log.ddebug('trying break handler {}'.format(attr))
            h = self.handler(node, attr) / L(BreakHandler.from_attr('handler'))(_, rule=attr)
            if h.present:
                self.log.ddebug('success')
            return h.o(or_else)
        rule = snake_case(node.rule)
        return (
            handler('{}_{}'.format(rule, node.key), L(handler)(rule, L(handler)(node.key))) |
            BreakHandler(handler=self.default_handler, rule=rule)
        )

    def handle(self, node: RoseAstTree, breaks: List[Break]) -> List[Break]:
        handler = self.lookup_handler(node.data)
        result = handler.handler(BreakState(node.data, breaks))
        return cons_breaks(node, handler.rule, result)

    def sub_breaks(self, node: RoseAstTree, breaks: List[Break]) -> Task[List[Break]]:
        return (
            node.sub.drain.flat_traverse(L(self.brk)(_, breaks), Task) /
            breaks.add
        )

    def brk(self, node: RoseAstTree, breaks: List[Break]) -> Task[List[Break]]:
        handler = self.break_node if node.data.is_token else self.break_inode
        return handler(node, breaks)

    def break_inode(self, node: RoseAstTree, breaks: List[Break]) -> Task[List[Break]]:
        return (
            self.break_node(node, breaks) //
            L(self.sub_breaks)(node, _)
        )

    def break_node(self, node: RoseAstTree, breaks: List[Break]) -> Task[List[Break]]:
        return Task.delay(self.handle, node, breaks)


class Breaker(BreakerBase):

    def __init__(self, rules: BreakRules, textwidth: int) -> None:
        super().__init__(textwidth)
        self.rules = rules

    def handler(self, node: RoseData, attr: str) -> Maybe[Callable[[RoseData], BreakData]]:
        return Maybe.check(getattr(self.rules, attr, None))

    @property
    def default_handler(self) -> Callable[[RoseData], BreakData]:
        return self.rules.default


class DictBreaker(BreakerBase):

    def __init__(self, rules: Map, textwidth: int) -> None:
        super().__init__(textwidth)
        self.rules = rules

    def handler(self, node: RoseData, attr: str) -> Maybe[Callable[[RoseData], BreakData]]:
        return self.rules.lift(attr) / (lambda a: lambda node: a)

    @property
    def default_handler(self) -> Callable[[RoseData], BreakData]:
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
