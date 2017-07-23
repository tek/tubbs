from typing import Any

from amino import List, Boolean

from ribosome.record import Record, float_field, field

from tubbs.tatsu.ast import AstElem, RoseData, Line, RoseAstTree
from tubbs.formatter.breaker.info import BreakSide, Before


class Break(Record):
    side = field(BreakSide)
    prio = float_field()
    node = field(RoseAstTree)

    @property
    def data(self) -> RoseData:
        return self.node.data

    @property
    def position(self) -> int:
        return self.node.startpos if isinstance(self.side, Before) else self.node.endpos

    @property
    def _str_extra(self) -> List[Any]:
        index = self.position - self.line.start
        return List(self.line.text[index - 1:index + 1], self.position, self.prio, self.rule, self.key, self.side)

    @property
    def rule(self) -> str:
        return self.data.rule

    @property
    def key(self) -> str:
        return self.data.key

    def match_name(self, name: str) -> bool:
        return name == self.rule

    @property
    def line(self) -> Line:
        return self.data.line

    @property
    def ast(self) -> AstElem:
        return self.data.ast

    @property
    def before(self) -> Boolean:
        return self.side.before

    @property
    def after(self) -> Boolean:
        return ~self.before

__all__ = ('Break',)
