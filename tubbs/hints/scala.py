from tubbs.hints.base import HintsBase, Hint, RegexHint

from amino import Map, List
from amino.regex import Regex


class DefHint(RegexHint):

    @property
    def regex(self) -> Regex:
        return Regex(r'.*\b(def)\b')

    @property
    def rules(self) -> List[str]:
        return List('templateStatDef')


class Hints(HintsBase):

    @property
    def hints(self) -> Map[str, List[Hint]]:
        return Map({'def': List(DefHint())})

__all__ = ('Hints',)
