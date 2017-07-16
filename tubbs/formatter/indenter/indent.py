from typing import Any

from amino import List

from ribosome.record import Record, int_field, field, bool_field

from tubbs.tatsu.ast import RoseData


class Indent(Record):
    node = field(RoseData)
    indent = int_field()
    absolute = bool_field()

    @property
    def line(self) -> int:
        return self.node.line

    @property
    def _str_extra(self) -> List[Any]:
        return List(self.node.desc, self.indent)

    @property
    def sub(self) -> bool:
        return isinstance(self, IndentChildren)

    @property
    def after(self) -> bool:
        return isinstance(self, IndentAfter)

    def inc(self, i: int) -> 'Indent':
        return self.set(indent=self.indent + i)


class IndentAfter(Indent):
    pass


class IndentHere(Indent):
    pass


class IndentFromHere(Indent):
    pass


class IndentChildren(Indent):
    pass


def after(node: RoseData, amount: int) -> Indent:
    return IndentAfter(node=node, indent=amount)


def from_here(node: RoseData, amount: int) -> Indent:
    return IndentFromHere(node=node, indent=amount)


def children(node: RoseData, amount: int) -> Indent:
    return IndentChildren(node=node, indent=amount)


def keep(node: RoseData) -> Indent:
    return Indent(node=node, indent=0)

__all__ = ('Indent', 'after', 'from_here', 'children', 'keep')
