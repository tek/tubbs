import abc
from typing import Tuple

from amino import Either, Left, Right


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


class Amount:

    def __init__(self, value: int) -> None:
        self.value: amount = value


class IndentInfo:

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

    def __str__(self) -> str:
        return f'Invalid({self.error})'

    def __repr__(self) -> str:
        return str(self)


class HasAmount:

    def amount(self, amount: int) -> IndentInfo:
        return Invalid('more than one break amount')


class IndentAmount(HasAmount, Incomplete):

    @property
    def _error(self) -> str:
        return 'range was not set'

    def __init__(self, amount: int) -> None:
        self._prio = amount

    def range(self, range: Range) -> IndentInfo:
        return IndentAmountRange(self._prio, range)

    def __str__(self) -> str:
        return f'IndentAmount({self._prio})'


class HasRange:

    def range(self, range: Range) -> IndentInfo:
        return Invalid('more than one break position')


class IndentRange(HasRange, Incomplete):

    @property
    def _error(self) -> str:
        return 'amount was not set'

    def __init__(self, range: Range) -> None:
        self._range = range

    def amount(self, amount: int) -> IndentInfo:
        return IndentAmountRange(amount, self._range)


class IndentAmountRange(HasRange, HasAmount, IndentInfo):

    def __init__(self, amount: int, range: Range) -> None:
        self._prio = amount
        self._range = range

    @property
    def info(self) -> Either[str, Tuple[int, Range]]:
        return Right((self._prio, self._range))


class Skip(IndentAmountRange):

    def __init__(self) -> None:
        super().__init__(0, Here)

__all__ = ()
