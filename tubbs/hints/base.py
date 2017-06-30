import abc

from amino import List, Map, Maybe, __, _, Empty, L
from amino.regex import Regex

from ribosome.record import int_field, list_field, Record, dfield, maybe_field

from tubbs.logging import Logging


class HintMatch(Record):
    line = int_field()
    end_line = maybe_field(int)
    col = dfield(0)
    rules = list_field(str)

    @property
    def _str_extra(self) -> List:
        return List(self.line, self.col, self.rules) + self.end_line.to_list


class Hint(Logging, abc.ABC):

    @abc.abstractproperty
    def rules(self) -> List[str]:
        ...

    @abc.abstractmethod
    def match(self, content: List[str], cursor: int) -> Maybe[HintMatch]:
        ...

    @abc.abstractmethod
    def find_end(self, content: List[str], cursor: int, start_line: int) -> Maybe[int]:
        ...

    def _line_match(self, content: List[str], cursor: int, line: int) -> HintMatch:
        return HintMatch(line=line, rules=self.rules, end_line=self.find_end(content, cursor, line))

    def __str__(self) -> str:
        return self.__class__.__name__

    def __repr__(self) -> str:
        return str(self)


class EOLEnd(Hint):

    def find_end(self, content: List[str], cursor: int, start_line: int) -> Maybe[int]:
        return Empty()


class RegexHint(Hint):

    def __init__(self, back: bool=True) -> None:
        self.back = back

    @abc.abstractproperty
    def regex(self) -> Regex:
        ...

    def match(self, content: List[str], cursor: int) -> Maybe[HintMatch]:
        return (
            content[:cursor + 1]
            .reversed
            .index_where(lambda a: self.regex.match(a).is_right) /
            (cursor - _) /
            L(self._line_match)(content, cursor, _)
        )

    def __str__(self) -> str:
        return '{}({})'.format(self.__class__.__name__, self.regex)


class HintsBase(abc.ABC):

    @abc.abstractproperty
    def hints(self) -> Map[str, List[Hint]]:
        ...

    def find(self, content: List[str], line: int, ident: str
             ) -> Maybe[HintMatch]:
        return (
            self.hints.lift(ident) //
            __.find_map(lambda a: a.match(content, line))
        )

    def __str__(self) -> str:
        return '{}({})'.format(self.__class__.__name__, self.hints)

__all__ = ('HintsBase',)
