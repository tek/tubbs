import abc
from typing import Tuple

from amino import Either, Left, Right, List
from amino.util.string import ToStr


class Range:

    def __init__(self, desc: str) -> None:
        self.desc = desc

    def __str__(self) -> str:
        return self.desc

    def __repr__(self) -> str:
        return str(self)

Here = Range('Here')
After = Range('After')
FromHere = Range('FromHere')
Children = Range('Children')
Skip = Range('Skip')


class Amount(ToStr):

    def __init__(self, value: int) -> None:
        self.value = value

    @property
    def _arg_desc(self) -> List[str]:
        return List(self.value)


class IndentInfo(ToStr):

    @abc.abstractmethod
    def amount(self, amount: int) -> 'IndentInfo':
        ...

    @abc.abstractproperty
    def info(self) -> Either[str, Tuple[int, Range]]:
        ...

    def __nonzero__(self) -> bool:
        return not isinstance(self, Invalid)

    def __bool__(self) -> bool:
        return self.__nonzero__()


class Incomplete(IndentInfo):

    @abc.abstractproperty
    def _error(self) -> str:
        ...

    @property
    def info(self) -> Either[str, Tuple[int, Range]]:
        return Left(self._error)

    @property
    def _arg_desc(self) -> List[str]:
        return List(self._error)


class Empty(Incomplete):

    @property
    def _error(self) -> str:
        return 'neither amount nor range was set'

    def range(self, range: Range) -> IndentInfo:
        return IndentRange(range)

    def amount(self, amount: int) -> IndentInfo:
        return IndentAmount(amount)


class Invalid(Incomplete):

    def __init__(self, error: str) -> None:
        self.error = error

    @property
    def _error(self) -> str:
        return self.error

    def range(self, range: Range) -> IndentInfo:
        return self

    def amount(self, amount: int) -> IndentInfo:
        return self


class HasAmount:

    def amount(self, amount: int) -> IndentInfo:
        return Invalid('more than one break amount')


class IndentAmount(HasAmount, Incomplete):

    def __init__(self, amount: int) -> None:
        self._amount = amount

    @property
    def _error(self) -> str:
        return 'range was not set'

    def range(self, range: Range) -> IndentInfo:
        return IndentAmountRange(self._amount, range)

    @property
    def _arg_desc(self) -> List[str]:
        return List(self._amount)


class HasRange:

    def range(self, range: Range) -> IndentInfo:
        return Invalid('more than one break position')


class IndentRange(HasRange, Incomplete):

    def __init__(self, range: Range) -> None:
        self._range = range

    @property
    def _error(self) -> str:
        return 'amount was not set'

    def amount(self, amount: int) -> IndentInfo:
        return IndentAmountRange(amount, self._range)

    @property
    def _arg_desc(self) -> List[str]:
        return List(self._range)


class IndentAmountRange(HasRange, HasAmount, IndentInfo):

    def __init__(self, amount: int, range: Range) -> None:
        self._amount = amount
        self._range = range

    @property
    def info(self) -> Either[str, Tuple[int, Range]]:
        return Right((self._amount, self._range))

    @property
    def _arg_desc(self) -> List[str]:
        return List(self._range, self._amount)


class SkipRange(IndentAmountRange):

    def __init__(self) -> None:
        super().__init__(0, Here)

__all__ = ('Range', 'Here', 'After', 'FromHere', 'Children', 'Skip', 'Amount', 'IndentInfo', 'Incomplete', 'Empty',
           'Invalid', 'IndentAmount', 'IndentRange', 'IndentAmountRange', 'SkipRange')
