from tubbs.hints.base import HintsBase, Hint, RegexHint, EOLEnd

from amino import Map, List
from amino.regex import Regex


class DefHint(RegexHint, EOLEnd):

    @property
    def regex(self) -> Regex:
        return Regex(r'^\s*\b(def)\b')

    @property
    def rules(self) -> List[str]:
        return List('templateStatDef')


class ValHint(RegexHint, EOLEnd):

    @property
    def regex(self) -> Regex:
        return Regex(r'^\s*\b(val)\b')

    @property
    def rules(self) -> List[str]:
        return List('templateStatDef')


class Hints(HintsBase):

    @property
    def hints(self) -> Map[str, List[Hint]]:
        return Map(
            {
                'def': List(DefHint()),
                'val': List(ValHint()),
            }
        )

__all__ = ('Hints',)
