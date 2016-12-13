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
    def _str_extra(self):
        return List(self.line, self.col, self.rules)


class Hint(Logging, abc.ABC):

    @abc.abstractproperty
    def rules(self) -> List[str]:
        ...

    @abc.abstractmethod
    def match(self, vim, start) -> Maybe[HintMatch]:
        ...

    def _line_match(self, line):
        return HintMatch(line=line, rules=self.rules)


class RegexHint(Hint):

    def __init__(self, back=True) -> None:
        self.back = back

    @abc.abstractproperty
    def regex(self) -> Regex:
        ...

    def match(self, vim, line):
        return (
            vim.buffer.content[:line + 1]
            .reversed
            .index_where(lambda a: self.regex.match(a).is_right) /
            (line - _) /
            self._line_match
        )


class HintsBase(abc.ABC):

    @abc.abstractproperty
    def hints(self) -> Map[str, List[Hint]]:
        ...

    def find(self, vim, ident):
        return (
            (self.hints.lift(ident) & vim.window.line0)
            .flat_map2(lambda a, b: a.find_map(__.match(vim, b)))
        )

__all__ = ('HintsBase',)
