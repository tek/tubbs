import abc
from typing import Callable, Any

from amino.util.string import ToStr
from amino import List

from tubbs.formatter.indenter.state import IndentState
from tubbs.formatter.indenter.indent import Indent
from tubbs.formatter.indenter import info
from tubbs.formatter.indenter.info import IndentInfo, Range
from tubbs.tatsu.ast import RoseAstTree


def mk_indent(node: RoseAstTree, amount: int, range: Range) -> Indent:
    return Indent(node=node, amount=amount, range=range)


class IndentCond(ToStr):

    @abc.abstractmethod
    def info(self, state: IndentState) -> IndentInfo:
        ...

    def __or__(self, other: 'IndentCond') -> 'IndentCond':
        return IndentCondOr(self, other)

    def __and__(self, other: 'IndentCond') -> 'IndentCond':
        return IndentCondAnd(self, other)

    def range(self, range: IndentInfo) -> 'IndentCond':
        return IndentCondRange(self, range)

    def amount(self, amount: int) -> 'IndentCond':
        return IndentCondAmount(self, info.Amount(amount))

    @property
    def keep(self) -> 'IndentCond':
        return self.range(info.Here).amount(0)

    @property
    def after(self) -> 'IndentCond':
        return self.range(info.After)

    @property
    def from_here(self) -> 'IndentCond':
        return self.range(info.FromHere)

    @property
    def children(self) -> 'IndentCond':
        return self.range(info.Children)


class Invariant(IndentCond):

    def info(self, state: IndentState) -> IndentInfo:
        return info.Empty()

    @property
    def _arg_desc(self) -> List[str]:
        return List()


class IndentCondAlg(IndentCond):

    def __init__(self, left: IndentCond, right: IndentCond) -> None:
        self.left = left
        self.right = right


class IndentCondOr(IndentCondAlg):

    def info(self, state: IndentState) -> Indent:
        return self.left.info(state) or self.right.info(state)

    @property
    def _arg_desc(self) -> List[str]:
        return List(f'{self.left} | {self.right}')


class IndentCondAnd(IndentCondAlg):

    def info(self, state: IndentState) -> Indent:
        return self.left.info(state) and self.right.info(state)

    @property
    def _arg_desc(self) -> List[str]:
        return List(f'{self.left} & {self.right}')


class IndentCondNest(IndentCond):

    def __init__(self, cond: IndentCond) -> None:
        self.cond = cond


class IndentCondRange(IndentCondNest):

    def __init__(self, cond: IndentCond, range: info.Range) -> None:
        super().__init__(cond)
        self._range = range

    def info(self, state: IndentState) -> IndentInfo:
        return self.cond.info(state).range(self._range)

    @property
    def _arg_desc(self) -> List[str]:
        return List(self.cond, self._range)


class IndentCondAmount(IndentCondNest):

    def __init__(self, cond: IndentCond, amount: info.Amount) -> None:
        super().__init__(cond)
        self._amount = amount

    def info(self, state: IndentState) -> IndentInfo:
        return self.cond.info(state).amount(self._amount.value)

    @property
    def _arg_desc(self) -> List[str]:
        return List(self.cond, self._amount)


class NoIndent(IndentCond):

    def info(self, state: IndentState) -> IndentInfo:
        return info.SkipRange()

    @property
    def _arg_desc(self) -> List[str]:
        return List()

PC = Callable[[IndentState], bool]


class PredCond(IndentCond):

    def __init__(self, desc: str, f: PC) -> None:
        self.f = f
        self.desc = desc

    @property
    def _desc(self) -> str:
        return self.desc

    def info(self, state: IndentState) -> Indent:
        return info.Empty() if self.f(state) else info.Invalid(f'{self._desc} failed')

    @property
    def _arg_desc(self) -> List[str]:
        return List(self._desc)


def pred_cond(desc: str) -> Callable[[PC], IndentCond]:
    def dec(f: PC) -> IndentCond:
        return PredCond(desc, f)
    return dec

PCF = Callable[..., bool]


def pred_cond_f(desc: str) -> Callable[[PCF], Callable[..., IndentCond]]:
    def dec(f: PCF) -> Callable[..., IndentCond]:
        def args(*a: Any, **kw: Any) -> IndentCond:
            def wrap(state: IndentState) -> bool:
                return f(state, *a, **kw)
            return PredCond(desc, wrap)
        return args
    return dec

__all__ = ('IndentCond', 'Invariant')
