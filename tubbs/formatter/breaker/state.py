from typing import Callable, Sized, Any

from amino import List, L, Boolean, _, __
from amino.lazy import lazy
from amino.tree import SubTree

from tubbs.tatsu.ast import RoseData, RoseAstTree
from tubbs.formatter.breaker.strict import StrictBreak


class BreakState:

    def __init__(self, node: RoseAstTree, breaks: List[StrictBreak]) -> None:
        self.node = node
        self.breaks = breaks

    @property
    def data(self) -> RoseData:
        return self.node.data

    @property
    def is_token(self) -> Boolean:
        return self.data.is_token

    @lazy
    def parent_inode(self) -> RoseData:
        p = self.node.parent
        return p.parent if self.is_token else p

    @lazy
    def after_breaks(self) -> List[StrictBreak]:
        return (
            self.breaks
            .filter(_.line == self.data.line)
            .filter(_.position > self.data.pos)
        )

    def after(self, name: str) -> Boolean:
        return self.after_breaks.exists(__.match_name(name))

    @lazy
    def before_breaks(self) -> List[StrictBreak]:
        return (
            self.breaks
            .filter(_.line == self.data.line)
            .filter(_.position < self.data.pos)
        )

    def before(self, name: str) -> Boolean:
        return self.before_breaks.exists(__.match_name(name))

    @property
    def parent(self) -> RoseAstTree:
        return self.data.parent

    @lazy
    def parent_breaks(self) -> List[StrictBreak]:
        siblings = self.parent_inode.sub
        def match(node: RoseAstTree, break_node: RoseData) -> bool:
            return node.data == break_node or node.data.ast.contains(break_node.ast)
        return (
            self.breaks
            .filter(lambda a: siblings.exists(L(match)(_, a.node)))
        )

    def sibling(self, f: Callable[[SubTree], SubTree]) -> Boolean:
        target = f(self.parent.s).e
        return self.parent_breaks.exists(lambda a: target.contains(a.ast))

    @property
    def rule(self) -> str:
        return self.node.rule

    def __str__(self) -> str:
        return f'BreakState({self.node}, {self.breaks})'


def is_break_tuple(a: Any) -> bool:
    return isinstance(a, Sized) and len(a) == 2

__all__ = ('BreakState', 'is_break_tuple')
