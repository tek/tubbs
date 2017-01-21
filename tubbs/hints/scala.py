from tubbs.hints.base import HintsBase, Hint, RegexHint

from amino import Map, List
from amino.regex import Regex


class DefHint(RegexHint):

    @property
    def regex(self):
        return Regex(r'^\s+(def)\b')

    @property
    def rules(self):
        return List('funDef')


class Hints(HintsBase):

    @property
    def hints(self):
        return Map({'def': List(DefHint())})

__all__ = ('Hints',)
