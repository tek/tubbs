import abc

from amino import List, Map, Maybe, __, _
from amino.regex import Regex

from ribosome.record import int_field, list_field, Record, dfield

from tubbs.logging import Logging


class HintMatch(Record):
    line = int_field()
    col = dfield(0)
    rules = list_field(str)

    @property
    def _str_extra(self) -> List:
        return List(self.line, self.col, self.rules)


class Hint(Logging, abc.ABC):

    @abc.abstractproperty
    def rules(self) -> List[str]:
        ...

    @abc.abstractmethod
    def match(self, content: List[str], start: int) -> Maybe[HintMatch]:
        ...

    def _line_match(self, line: int) -> HintMatch:
        return HintMatch(line=line, rules=self.rules)


class RegexHint(Hint):

    def __init__(self, back: bool=True) -> None:
        self.back = back

    @abc.abstractproperty
    def regex(self) -> Regex:
        ...

    def match(self, content: List[str], start: int) -> Maybe[HintMatch]:
        return (
            content[:start + 1]
            .reversed
            .index_where(lambda a: self.regex.match(a).is_right) /
            (start - _) /
            self._line_match
        )


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

__all__ = ('HintsBase',)
