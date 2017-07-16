import abc
from typing import Callable, Any

from amino import List, Either

from tubbs.tatsu.ast import RoseAstTree
from tubbs.formatter.breaker.strict import StrictBreak
from tubbs.formatter.breaker.state import BreakState
from tubbs.formatter.breaker.info import BreakInfo, before, after, BreakSide, Before
from tubbs.formatter.breaker import info


def mk_break(prio: float, node: RoseAstTree, pos: int) -> StrictBreak:
    return StrictBreak(node=node.data, prio=prio, position=pos)


class BreakCond(abc.ABC):

    @abc.abstractmethod
    def info(self, state: BreakState) -> BreakInfo:
        ...

    @abc.abstractproperty
    def _desc(self) -> str:
        ...

    def __or__(self, other: 'BreakCond') -> 'BreakCond':
        return BreakCondOr(self, other)

    def __and__(self, other: 'BreakCond') -> 'BreakCond':
        return BreakCondAnd(self, other)

    @property
    def before(self) -> 'BreakCondPos':
        return BreakCondPos(self, before)

    @property
    def after(self) -> 'BreakCondPos':
        return BreakCondPos(self, after)

    def prio(self, prio: float) -> 'BreakCondPrio':
        return BreakCondPrio(self, prio)

    def __str__(self) -> str:
        return f'{self.__class__.__name__}({self._desc})'

    def __repr__(self) -> str:
        return str(self)


class BreakCondNest(BreakCond):

    def __init__(self, cond: BreakCond) -> None:
        self.cond = cond

    def info(self, state: BreakState) -> BreakInfo:
        return self.cond.info(state)


class BreakCondAlg(BreakCond):

    def __init__(self, left: BreakCond, right: BreakCond) -> None:
        self.left = left
        self.right = right


class BreakCondOr(BreakCondAlg):

    @property
    def _desc(self) -> str:
        return f'{self.left} | {self.right}'

    def info(self, state: BreakState) -> BreakInfo:
        return self.left.info(state) or self.right.info(state)


class BreakCondAnd(BreakCondAlg):

    @property
    def _desc(self) -> str:
        return f'{self.left} & {self.right}'

    def info(self, state: BreakState) -> BreakInfo:
        return self.left.info(state) and self.right.info(state)


class BreakCondPrio(BreakCondNest):

    def __init__(self, cond: BreakCond, prio: float) -> None:
        super().__init__(cond)
        self._prio = prio

    def info(self, state: BreakState) -> BreakInfo:
        return self.cond.info(state).prio(self._prio)

    @property
    def _desc(self) -> str:
        return f'{self.cond._desc}, {self._prio}'


class BreakCondPos(BreakCondNest):

    def __init__(self, cond: BreakCond, side: BreakSide) -> None:
        self.cond = cond
        self.side = side

    def __str__(self) -> str:
        return f'BreakCondPos({str(self.cond)}, {self.side})'

    def info(self, state: BreakState) -> BreakInfo:
        return self.cond.info(state).pos(self.side)

    @property
    def _desc(self) -> str:
        return f'{self.cond._desc}, {self.side}'


class Invariant(BreakCond):

    @property
    def _desc(self) -> str:
        return 'inv'

    def info(self, state: BreakState) -> BreakInfo:
        return info.Empty()

    def __str__(self) -> str:
        return self._desc


class NoBreak(BreakCond):

    @property
    def _desc(self) -> str:
        return 'no break'

    def info(self, state: BreakState) -> BreakInfo:
        return info.Invalid(self._desc)

PC = Callable[[BreakState], bool]


class PredCond(BreakCond):

    def __init__(self, desc: str, f: PC) -> None:
        self.f = f
        self.desc = desc

    @property
    def _desc(self) -> str:
        return self.desc

    def info(self, state: BreakState) -> BreakInfo:
        return info.Empty() if self.f(state) else info.Invalid(f'{self._desc} failed')


def pred_cond(desc: str) -> Callable[[PC], BreakCond]:
    def dec(f: PC) -> BreakCond:
        return PredCond(desc, f)
    return dec

PCF = Callable[..., bool]


def pred_cond_f(desc: str) -> Callable[[PCF], Callable[..., BreakCond]]:
    def dec(f: PCF) -> Callable[..., BreakCond]:
        def args(*a: Any, **kw: Any) -> BreakCond:
            def wrap(state: BreakState) -> bool:
                return f(state, *a, **kw)
            return PredCond(desc, wrap)
        return args
    return dec


class CondBreak:

    def __init__(self, node: RoseAstTree, cond: BreakCond) -> None:
        self.node = node
        self.cond = cond

    @property
    def startpos(self) -> int:
        return self.node.pos

    @property
    def endpos(self) -> int:
        return self.node.endpos

    def pos(self, side: BreakSide) -> int:
        return self.node.startpos if isinstance(side, Before) else self.node.endpos

    def brk(self, breaks: List[StrictBreak]) -> Either[str, List[StrictBreak]]:
        def cons(prio: float, side: BreakSide) -> StrictBreak:
            return mk_break(prio, self.node, self.pos(side))
        state = BreakState(self.node, breaks)
        return (self.cond.info(state).info.map2(cons)).lmap(lambda a: f'{self.cond} did not match: {a}')

    def __str__(self) -> str:
        return f'CondBreak({self.node.rule}, {self.cond})'

    def __repr__(self) -> str:
        return str(self)

__all__ = ('BreakCond', 'Invariant', 'NoBreak', 'pred_cond', 'pred_cond_f', 'CondBreak')
