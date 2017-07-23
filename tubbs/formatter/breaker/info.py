import abc
from typing import Tuple

from amino import Either, Left, Right, List, Boolean
from amino.util.string import ToStr

from tubbs.tatsu.ast import RoseAstTree


class BreakSide:

    @abc.abstractmethod
    def apply(self, node: RoseAstTree) -> int:
        ...

    def __str__(self) -> str:
        return self.__class__.__name__

    @property
    def before(self) -> Boolean:
        return Boolean(isinstance(self, Before))


class Before(BreakSide):

    def apply(self, node: RoseAstTree) -> int:
        return node.startpos


class After(BreakSide):

    def apply(self, node: RoseAstTree) -> int:
        return node.endpos

before = Before()
after = After()


class BreakInfo(ToStr):

    @abc.abstractmethod
    def prio(self, prio: float) -> 'BreakInfo':
        ...

    @abc.abstractmethod
    def pos(self, pos: BreakSide) -> 'BreakInfo':
        ...

    @abc.abstractproperty
    def info(self) -> Either[str, Tuple[float, BreakSide]]:
        ...

    def __nonzero__(self) -> bool:
        return not isinstance(self, Invalid)

    def __bool__(self) -> bool:
        return self.__nonzero__()


class Incomplete(BreakInfo):

    @abc.abstractproperty
    def _error(self) -> str:
        ...

    @property
    def info(self) -> Either[str, Tuple[float, BreakSide]]:
        return Left(self._error)


class Empty(Incomplete):

    @property
    def _error(self) -> str:
        return 'neither prio nor pos was set'

    def pos(self, pos: BreakSide) -> BreakInfo:
        return BreakPos(pos)

    def prio(self, prio: float) -> BreakInfo:
        return BreakPrio(prio)

    @property
    def _arg_desc(self) -> List[str]:
        return List(self._error)


class Invalid(Incomplete):

    def __init__(self, error: str) -> None:
        self.error = error

    @property
    def _error(self) -> str:
        return self.error

    def pos(self, pos: BreakSide) -> BreakInfo:
        return self

    def prio(self, prio: float) -> BreakInfo:
        return self

    @property
    def _arg_desc(self) -> List[str]:
        return List(self.error)


class HasPrio:

    def prio(self, prio: float) -> BreakInfo:
        return Invalid('more than one break prio')


class BreakPrio(HasPrio, Incomplete):

    @property
    def _error(self) -> str:
        return 'pos was not set'

    def __init__(self, prio: float) -> None:
        self._prio = prio

    def pos(self, pos: BreakSide) -> BreakInfo:
        return BreakPrioPos(self._prio, pos)

    @property
    def _arg_desc(self) -> List[str]:
        return List(self._prio)


class HasPos:

    def pos(self, pos: BreakSide) -> BreakInfo:
        return Invalid('more than one break position')


class BreakPos(HasPos, Incomplete):

    @property
    def _error(self) -> str:
        return 'prio was not set'

    def __init__(self, pos: BreakSide) -> None:
        self._pos = pos

    def prio(self, prio: float) -> BreakInfo:
        return BreakPrioPos(prio, self._pos)


class BreakPrioPos(HasPos, HasPrio, BreakInfo):

    def __init__(self, prio: float, pos: BreakSide) -> None:
        self._prio = prio
        self._pos = pos

    @property
    def info(self) -> Either[str, Tuple[float, BreakSide]]:
        return Right((self._prio, self._pos))

    @property
    def _arg_desc(self) -> List[str]:
        return List(self._prio, self._pos)


class Skip(BreakPrioPos):

    def __init__(self, desc: str) -> None:
        super().__init__(0.0, Before())
        self.desc = desc

    @property
    def _arg_desc(self) -> List[str]:
        return List(self.desc)

__all__ = ('BreakInfo',)
