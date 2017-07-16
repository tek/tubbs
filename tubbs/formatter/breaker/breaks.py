from typing import Any, Tuple

from amino import List, L, _, __

from ribosome.record import Record, list_field

from tubbs.formatter.breaker.cond import BreakCond, CondBreak
from tubbs.formatter.breaker.strict import StrictBreak


class Breaks(Record):
    applied = list_field(StrictBreak)
    conds = list_field(CondBreak)

    def range(self, start: int, end: int) -> Tuple['Breaks', List[StrictBreak]]:
        def matches(pos: int) -> bool:
            return start < pos < end
        def cond_match(b: BreakCond) -> bool:
            return matches(b.startpos) or matches(b.endpos)
        matcher = __.filter(L(matches)(_.position))
        qual_cond = self.conds.filter(cond_match)
        qualified = matcher(qual_cond.flat_map(lambda a: a.brk(self.applied).to_list))
        sub = self.set(conds=qual_cond, applied=self.applied)
        return sub, qualified

    @property
    def _str_extra(self) -> List[Any]:
        return List(self.conds)

    def apply(self, applied: StrictBreak) -> 'Breaks':
        return self.append1.applied(applied)

    def reset(self, old: 'Breaks') -> 'Breaks':
        return old.set(applied=old.applied)

    def update(self, other: 'Breaks') -> 'Breaks':
        return self.append.applied(other.applied)

__all__ = ('Breaks',)
