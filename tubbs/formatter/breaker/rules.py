from tubbs.logging import Logging
from tubbs.formatter.breaker.state import BreakState
from tubbs.formatter.breaker.cond import BreakCond, NoBreak


class BreakRules(Logging):

    def default(self, state: BreakState) -> BreakCond:
        return NoBreak()

__all__ = ('BreakRules',)
