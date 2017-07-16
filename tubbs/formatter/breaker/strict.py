from typing import Any

from amino import List

from ribosome.record import Record, int_field, float_field, field

from tubbs.tatsu.ast import AstElem, RoseData, Line


class StrictBreak(Record):
    position = int_field()
    prio = float_field()
    node = field(RoseData)

    @property
    def _str_extra(self) -> List[Any]:
        index = self.position - self.line.start
        return List(self.line.text[index - 1:index + 1], self.position, self.prio, self.rule, self.key)

    @property
    def rule(self) -> str:
        return self.node.rule

    @property
    def key(self) -> str:
        return self.node.key

    def match_name(self, name: str) -> bool:
        return name == self.rule

    @property
    def line(self) -> Line:
        return self.node.line

    @property
    def ast(self) -> AstElem:
        return self.node.ast

__all__ = ('StrictBreak',)
