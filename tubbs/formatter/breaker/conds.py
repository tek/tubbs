from typing import Callable

from amino.tree import SubTree
from amino import Boolean, Map

from tubbs.tatsu.ast import AstElem, AstList, RoseAstTree
from tubbs.formatter.breaker.state import BreakState
from tubbs.formatter.breaker.cond import pred_cond, pred_cond_f, BreakCond, Invariant


def inv(prio: float) -> BreakCond:
    return Invariant().prio(prio)


def nel(ast: AstElem) -> bool:
    return isinstance(ast, AstList) and ast.data.length > 0


def multi_line_node(n: RoseAstTree) -> Boolean:
    return n.s.body.tail.e.exists(nel) or n.sub.exists(multi_line_node)


@pred_cond('multi line block sibling')
def multi_line_block(state: BreakState) -> Boolean:
    return multi_line_node(state.parent)


@pred_cond_f('multi line block')
def multi_line_block_for(state: BreakState, attr: Callable[[RoseAstTree], RoseAstTree]) -> Boolean:
    return multi_line_node(attr(state.node))


@pred_cond_f('multi line block in parent with rule')
def multi_line_block_parent(state: BreakState, rule: str) -> Boolean:
    return state.node.parent_with_rule(rule).exists(multi_line_node)


@pred_cond_f('sibling break')
def sibling(state: BreakState, attr: Callable[[SubTree], SubTree]) -> Callable[[BreakState], Boolean]:
    return state.sibling(attr)


@pred_cond_f('parent rule')
def parent_rule(state: BreakState, rule: str) -> Callable[[BreakState], Boolean]:
    return state.parent.rule == rule


@pred_cond_f('sibling rule')
def sibling_rule(state: BreakState, attr: Callable[[SubTree], SubTree], rule: str) -> Callable[[BreakState], Boolean]:
    return attr(state.parent.s).rule.contains(rule)


@pred_cond_f('sibling valid')
def sibling_valid(state: BreakState, attr: Callable[[SubTree], SubTree]) -> Callable[[BreakState], Boolean]:
    return attr(state.parent.s).valid


@pred_cond_f('after node with rule')
def after(state: BreakState, rule: str) -> Callable[[BreakState], Boolean]:
    return state.after(rule)


default_conds = Map(
    multi_line_block_for=multi_line_block_for,
    multi_line_block_parent=multi_line_block_parent,
    multi_line_block=multi_line_block,
    sibling=sibling,
    parent_rule=parent_rule,
    sibling_rule=sibling_rule,
    sibling_valid=sibling_valid,
    after=after,
)

__all__ = ('inv', 'multi_line_block', 'sibling', 'parent_rule', 'sibling_rule', 'sibling_valid', 'after',
           'multi_line_block_for', 'default_conds')
