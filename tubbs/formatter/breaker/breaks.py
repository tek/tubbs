from typing import Any, Tuple

from ribosome.record import Record, list_field

from amino import List, Either
from amino.logging import indent

from tubbs.formatter.breaker.cond import CondBreak
from tubbs.formatter.breaker.strict import Break
from tubbs.util.string import yellow


def debug_candidates(breaks: List[Break]) -> List[str]:
    return indent(breaks, 2).map(yellow).cons('Candidates:').cons('')


class Breaks(Record):
    applied = list_field(Break)
    conds = list_field(CondBreak)

    def range(self, start: int, end: int) -> Either[str, Tuple['Breaks', List[Break]]]:
        def break_match(b: Break) -> bool:
            s = 1 if b.before else 0
            e = 1 if b.after else 0
            return (start + s) <= b.position < (end - e)
        def cond_match(b: CondBreak) -> bool:
            return (start + 1) <= b.startpos < end or start < b.endpos < (end - 1)
        def cons(all: List[Break]) -> Tuple['Breaks', List[Break]]:
            self.log.ddebug(debug_candidates, all)
            qualified = all.filter(break_match)
            sub = self.set(conds=qual_cond, applied=self.applied)
            return sub, qualified
        qual_cond = self.conds.filter(cond_match)
        return qual_cond.flat_traverse(lambda a: a.brk(self.applied, start, end), Either) / cons

    @property
    def _str_extra(self) -> List[Any]:
        return List(self.conds)

    def apply(self, applied: Break) -> 'Breaks':
        return self.append1.applied(applied)

    def reset(self, old: 'Breaks') -> 'Breaks':
        return old.set(applied=old.applied)

    def update(self, other: 'Breaks') -> 'Breaks':
        return self.append.applied(other.applied)

__all__ = ('Breaks',)
