from tubbs.logging import Logging
from tubbs.formatter.breaker.cond import BreakCond, NoBreak


class BreakRules(Logging):

    def default(self) -> BreakCond:
        return NoBreak()

__all__ = ('BreakRules',)
