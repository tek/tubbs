from typing import Any

from amino import List

from ribosome.record import Record, int_field, field, bool_field

from tubbs.tatsu.ast import RoseAstTree, RoseData
from tubbs.formatter.indenter.info import Range, Children, After


class Indent(Record):
    node = field(RoseAstTree)
    amount = int_field()
    range = field(Range)
    absolute = bool_field()

    @property
    def data(self) -> RoseData:
        return self.node.data

    @property
    def line(self) -> int:
        return self.node.line

    @property
    def _str_extra(self) -> List[Any]:
        return List(self.data.desc, self.amount)

    @property
    def sub(self) -> bool:
        return self.range is Children

    @property
    def after(self) -> bool:
        return self.range is After

    def inc(self, i: int) -> 'Indent':
        return self.set(amount=self.amount + i)

# def after(node: RoseData, amount: int) -> Indent:
#     return IndentAfter(node=node, indent=amount)


# def from_here(node: RoseData, amount: int) -> Indent:
#     return IndentFromHere(node=node, indent=amount)


# def children(node: RoseData, amount: int) -> Indent:
#     return IndentChildren(node=node, indent=amount)


# def keep(node: RoseData) -> Indent:
#     return Indent(node=node, indent=0)

__all__ = ('Indent',)
