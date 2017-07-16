import abc
from typing import Callable, Tuple, Any

from hues import huestr

from amino import Either, List, L, Boolean, _, __, Maybe, Map, Eval, Right
from amino.regex import Regex

from ribosome.nvim import NvimFacade
from ribosome.util.callback import VimCallback

from tubbs.tatsu.ast import AstElem, RoseData, ast_rose_tree, RoseAstTree
from tubbs.formatter.base import Formatter, VimFormatterMeta
from tubbs.formatter.breaker.state import BreakState
from tubbs.formatter.breaker.strict import StrictBreak
from tubbs.formatter.breaker.breaks import Breaks
from tubbs.formatter.breaker.rules import BreakRules
from tubbs.formatter.breaker.cond import BreakCond, CondBreak


def hl(data: str) -> str:
    return huestr(data).bg_yellow.black.colorized


ws_re = Regex(r'^\s*$')


def only_ws(data: str) -> Boolean:
    return ws_re.match(data).present

Handler = Callable[[RoseData], BreakCond]


class BreakerBase(Formatter):

    def __init__(self, textwidth: int) -> None:
        self.textwidth = textwidth

    @abc.abstractproperty
    def default_handler(self) -> Handler:
        ...

    def format(self, ast: AstElem) -> Eval[Either[str, List[str]]]:
        rt = ast_rose_tree(ast)
        return (self.breaks(rt).eff() / L(self.apply_breaks)(ast, _)).value

    def breaks(self, ast: RoseAstTree) -> Eval[Either[str, List[StrictBreak]]]:
        return (self.brk(ast, List()).eff() / Breaks.from_attr('conds')).value

    def apply_breaks(self, ast: AstElem, breaks: Breaks) -> List[str]:
        def folder(z: Tuple[Breaks, List[str]], a: Tuple[str, int]) -> Tuple[Breaks, List[str]]:
            state0, lines0 = z
            line, start = a
            state1, lines1 = self.break_line(state0, line, start)
            return state1.reset(state0), lines0 + lines1
        def trim(lines: List[str]) -> List[str]:
            return lines.detach_head.map2(lambda h, t: t.map(__.strip()).cons(h.rstrip())) | lines
        return trim(
            ast.lines
            .zip(ast.bols)
            .fold_left((breaks, List()))(folder)[1]
        )

    def break_line(self, breaks: Breaks, cur: str, start: int) -> Tuple[Breaks, List[str]]:
        end = start + len(cur)
        sub_breaks, qualified = breaks.range(start, end)
        def rec2(sub: Breaks, data: str, pos: int) -> List[str]:
            return (
                List()
                if only_ws(data) else
                self.break_line(sub, data, pos)
            )
        def rec1(brk: StrictBreak) -> List[str]:
            pos = brk.position
            local_pos = pos - start
            self.log.ddebug('breaking at {}, {}'.format(pos, local_pos))
            left = cur[:local_pos]
            right = cur[local_pos:]
            self.log.ddebug(lambda: 'broke line into\n{}\n{}'.format(hl(left), hl(right)))
            breaks1 = sub_breaks.apply(brk)
            breaks_l, lines_l = rec2(breaks1, left, start)
            breaks_r, lines_r = rec2(breaks1.update(breaks_l), right, pos)
            return breaks_r, (lines_l + lines_r)
        def rec0(brk: StrictBreak) -> Either[str, List[str]]:
            msg = 'line did not exceed tw: {}'
            return (
                Boolean(len(cur) > self.textwidth or brk.prio >= 1.0)
                .e(msg.format(cur), brk) /
                rec1
            )
        broken = (
            qualified.max_by(_.prio)
            .to_either('no breaks for {}'.format(cur)) //
            rec0
        ).leffect(self.log.ddebug)
        return broken | (breaks, List(cur))

    def handle(self, node: RoseAstTree, breaks: List[StrictBreak]) -> Either[str, List[StrictBreak]]:
        handler = self.lookup_handler(node.data)
        result = handler()
        return Right(List(CondBreak(node, result)))

    def _handler_names(self, node: RoseData, names: List[str]) -> List[str]:
        return names

    def brk(self, node: RoseAstTree, breaks: List[StrictBreak]) -> Eval[Either[str, List[StrictBreak]]]:
        handler = self.break_node if node.data.is_token else self.break_inode
        return handler(node, breaks)

    def sub_breaks(self, node: RoseAstTree, breaks: List[StrictBreak]) -> Eval[Either[str, List[StrictBreak]]]:
        return (
            node.sub.drain.traverse(L(self.brk)(_, breaks), Eval) /
            __.flat_sequence(Either).map(breaks.add)
        )

    def break_inode(self, node: RoseAstTree, breaks: List[StrictBreak]) -> Eval[Either[str, List[StrictBreak]]]:
        return (
            self.break_node(node, breaks) //
            __.flat_traverse(L(self.sub_breaks)(node, _), Eval)
        )

    def break_node(self, node: RoseAstTree, breaks: List[StrictBreak]) -> Eval[Either[str, List[StrictBreak]]]:
        return Eval.later(self.handle, node, breaks)


class Breaker(BreakerBase):

    def __init__(self, rules: BreakRules, textwidth: int) -> None:
        super().__init__(textwidth)
        self.rules = rules

    def handler(self, attr: str) -> Maybe[Callable[[RoseData], BreakCond]]:
        return Maybe.check(getattr(self.rules, attr, None))

    @property
    def default_handler(self) -> Callable[[RoseData], BreakCond]:
        return self.rules.default


class DictBreaker(BreakerBase):

    def __init__(self, rules: Map, textwidth: int) -> None:
        super().__init__(textwidth)
        self.rules = rules

    def handler(self, attr: str) -> Maybe[Callable[[RoseData], BreakCond]]:
        return self.rules.lift(attr) / (lambda a: lambda node: a)

    @property
    def default_handler(self) -> Callable[[RoseData], BreakCond]:
        return lambda node: List()


class VimDictBreaker(DictBreaker, VimCallback, metaclass=VimFormatterMeta):

    @staticmethod
    def convert_data(data: Map) -> Map:
        def convert(brk: Any) -> BreakCond:
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
