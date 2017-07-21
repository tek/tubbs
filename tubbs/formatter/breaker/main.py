import abc
import math
from typing import Callable, Tuple, Any

from hues import huestr

from amino import Either, List, L, Boolean, _, __, Maybe, Map, Eval, Right
from amino.regex import Regex
from amino.lazy import lazy

from ribosome.nvim import NvimFacade
from ribosome.util.callback import VimCallback

from tubbs.tatsu.ast import AstElem, RoseData, ast_rose_tree, RoseAstTree
from tubbs.formatter.base import Formatter, VimFormatterMeta
from tubbs.formatter.breaker.strict import StrictBreak
from tubbs.formatter.breaker.breaks import Breaks
from tubbs.formatter.breaker.rules import BreakRules
from tubbs.formatter.breaker.cond import BreakCond, CondBreak, NoBreak
from tubbs.tatsu.breaker_dsl import Parser
from tubbs.formatter.breaker.dsl import parse_break_expr


def hl(data: str) -> str:
    return huestr(data).bg_yellow.black.colorized


ws_re = Regex(r'^\s*$')


def only_ws(data: str) -> Boolean:
    return ws_re.match(data).present

Handler = Callable[[], BreakCond]
Z = Tuple[Breaks, List[str]]


class BreakerBase(Formatter[BreakCond]):

    def __init__(self, textwidth: int, split_weight_variance: float=0.25) -> None:
        self.textwidth = textwidth
        self.split_weight_variance = split_weight_variance

    @abc.abstractproperty
    def default_handler(self) -> Handler:
        ...

    def format(self, ast: AstElem) -> Eval[Either[str, List[str]]]:
        rt = ast_rose_tree(ast)
        return (self.breaks(rt).eff() / L(self.apply_breaks)(ast, _)).value

    def breaks(self, ast: RoseAstTree) -> Eval[Either[str, List[CondBreak]]]:
        return (self.brk(ast, List()).eff() / Breaks.from_attr('conds')).value

    def apply_breaks(self, ast: AstElem, breaks: Breaks) -> List[str]:
        def folder(z: Tuple[Breaks, List[str]], a: Tuple[str, int]) -> Tuple[Breaks, List[str]]:
            state0, lines0 = z
            line, start = a
            state1, lines1 = self.analyze_line(state0, line, start)
            return state1.reset(state0), lines0 + lines1
        def trim(lines: List[str]) -> List[str]:
            return lines.detach_head.map2(lambda h, t: t.map(__.strip()).cons(h.rstrip())) | lines
        return trim(
            ast.lines
            .zip(ast.bols)
            .fold_left((breaks, List()))(folder)[1]
        )

    def analyze_line(self, breaks: Breaks, line: str, start: int) -> Z:
        def log_error(err: str) -> None:
            self.log.error(f'error in break conditions: {err}')
        end = start + len(line)
        sub_breaks, qualified = breaks.range(start, end).leffect(log_error) | (breaks, List())
        return (
            self
            .best_break(qualified, line, start)
            .flat_map(L(self.break_line)(sub_breaks, _, line, start))
            .leffect(self.log.ddebug)
            .get_or_else((breaks, List(line)))
        )

    def best_break(self, breaks: List[StrictBreak], line: str, start: int) -> Either[str, StrictBreak]:
        '''select the break with the highest prio.
        if any forced breaks (>= 1.0) exist, use the highest one unconditionally.
        otherwise, weight the prios with the evenness of the ratio by which they split the line, scoring highest for
        0.5 split, using a gaussian with configurable variance.
        '''
        length = len(line)
        def weighted_prio(b: StrictBreak) -> float:
            return self._split_weight((b.position - start) / length)
        return (
            breaks
            .filter(_.prio >= 1)
            .max_by(_.prio)
            .o(lambda: breaks.max_by(weighted_prio))
            .to_either('no breaks for {}'.format(line))
        )

    def _split_weight(self, ratio: int) -> float:
        val = ratio - 0.5
        return math.exp(-(val * val) / self._split_coeff)

    @lazy
    def _split_coeff(self) -> float:
        return 2 * self.split_weight_variance

    def break_line(self, breaks: Breaks, brk: StrictBreak, line: str, start: int) -> Either[str, Z]:
        def rec2(sub: Breaks, data: str, pos: int) -> Z:
            return (
                (sub, List(data))
                if only_ws(data) else
                self.analyze_line(sub, data, pos)
            )
        def rec1(brk: StrictBreak) -> List[str]:
            pos = brk.position
            local_pos = pos - start
            self.log.ddebug('breaking at {}, {}'.format(pos, local_pos))
            left = line[:local_pos]
            right = line[local_pos:]
            self.log.ddebug(lambda: 'broke line into\n{}\n{}'.format(hl(left), hl(right)))
            breaks1 = breaks.apply(brk)
            breaks_l, lines_l = rec2(breaks1, left, start)
            breaks_r, lines_r = rec2(breaks1.update(breaks_l), right, pos)
            return breaks_r, (lines_l + lines_r)
        msg = 'line did not exceed tw: {}'
        return (
            Boolean(len(line) > self.textwidth or brk.prio >= 1.0)
            .e(msg.format(line), brk) /
            rec1
        )

    def handle(self, node: RoseAstTree, breaks: List[StrictBreak]) -> Either[str, List[CondBreak]]:
        handler = self.lookup_handler(node.data)
        result = handler()
        return Right(List(CondBreak(node, result)))

    def _handler_names(self, node: RoseData, names: List[str]) -> List[str]:
        return names

    def brk(self, node: RoseAstTree, breaks: List[StrictBreak]) -> Eval[Either[str, List[CondBreak]]]:
        handler = self.break_node if node.data.is_token else self.break_inode
        return handler(node, breaks)

    def sub_breaks(self, node: RoseAstTree, breaks: List[StrictBreak]) -> Eval[Either[str, List[CondBreak]]]:
        return (
            node.sub.drain.traverse(L(self.brk)(_, breaks), Eval) /
            __.flat_sequence(Either).map(breaks.add)
        )

    def break_inode(self, node: RoseAstTree, breaks: List[StrictBreak]) -> Eval[Either[str, List[CondBreak]]]:
        return (
            self.break_node(node, breaks) //
            __.flat_traverse(L(self.sub_breaks)(node, _), Eval)
        )

    def break_node(self, node: RoseAstTree, breaks: List[StrictBreak]) -> Eval[Either[str, List[CondBreak]]]:
        return Eval.later(self.handle, node, breaks)


class Breaker(BreakerBase):

    def __init__(self, rules: BreakRules, textwidth: int) -> None:
        super().__init__(textwidth)
        self.rules = rules

    def handler(self, attr: str) -> Maybe[Handler]:
        return Maybe.check(getattr(self.rules, attr, None))

    @property
    def default_handler(self) -> Handler:
        return self.rules.default


class DictBreaker(BreakerBase):

    def __init__(self, parser: Parser, rules: Map, conds: Map[str, Callable], textwidth: int) -> None:
        super().__init__(textwidth)
        self.parser = parser
        self.rules = rules
        self.conds = conds

    def handler(self, attr: str) -> Maybe[Handler]:
        return self.rules.lift(attr) / L(parse_break_expr)(self.parser, _, self.conds) / (lambda a: lambda: a)

    @property
    def default_handler(self) -> Handler:
        return lambda: NoBreak()


class VimDictBreaker(DictBreaker, VimCallback, metaclass=VimFormatterMeta):

    @staticmethod
    def convert_data(data: Map) -> Map:
        def convert(brk: Any) -> BreakCond:
            return (
                tuple(brk)
                if isinstance(brk, List) and not brk.exists(L(isinstance)(_, List)) else
                brk
            )
        return data.valmap(convert)

    def __init__(self, vim: NvimFacade, parser: Parser, rules: Map, conds: Map[str, Callable]) -> None:
        tw = vim.buffer.options('textwidth') | 120
        super().__init__(parser, rules, conds, tw)


__all__ = ('Breaker', 'DictBreaker', 'VimDictBreaker')
