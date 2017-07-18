from typing import Any

from amino import List, _, Boolean
from amino.lazy import lazy

from ribosome.record import Record, int_field, list_field, field

from tubbs.formatter.indenter.indent import Indent
from tubbs.tatsu.ast import RoseAstTree, RoseData
from tubbs.formatter.indenter.info import Children, FromHere, Here, After


class IndentState(Record):
    node = field(RoseAstTree)
    current = int_field()
    indents = list_field(Indent)
    stack = list_field(Indent)
    incs = list_field(Indent)

    def push_here(self, new: Indent) -> 'IndentState':
        add = new.inc(self.current)
        self.log.ddebug(lambda: f'indent for {add.node}: {add.amount}')
        return self.append1.indents(add)

    def update_current(self, update: Indent) -> 'IndentState':
        current = update.amount if update.absolute else self.current + update.amount
        self.log.ddebug(lambda: f'push current: {update} {current}')
        return self.set(current=current).append1.stack(update)

    def push_sub(self, new: Indent) -> 'IndentState':
        keep = Indent(node=new.node, amount=0, range=Here)
        add_stack = new if new.range in (Children, FromHere) else keep
        add_indents = new if new.range in (Here, FromHere) else keep
        s1 = self if new.amount == 0 else self.append1.incs(new)
        return s1.push_here(add_indents).update_current(add_stack)

    def push_after(self, new: Indent) -> 'IndentState':
        return self.update_current(new) if new.range in (After, FromHere) else self

    def pop(self, start: Indent) -> 'IndentState':
        index = self.stack.index_where(lambda a: a.node == start.node) | -1
        before = self.stack[:index]
        after = self.stack[index:]
        dec = sum(after.map(_.amount))
        self.log.ddebug(lambda: f'pop: {start} {dec}')
        return self.set(current=self.current - dec, stack=before)

    @property
    def _str_extra(self) -> List[Any]:
        return List(self.current, self.indents)

    @property
    def data(self) -> RoseData:
        return self.node.data

    @property
    def parent(self) -> RoseAstTree:
        return self.node.parent

    @lazy
    def sibling_indents(self) -> List[Indent]:
        return self.incs.filter(lambda a: a.node.parent is self.parent)

    @property
    def sibling_indent(self) -> Boolean:
        return not self.sibling_indents.empty

__all__ = ('IndentState',)
