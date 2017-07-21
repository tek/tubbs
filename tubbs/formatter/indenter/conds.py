from amino import Boolean, Map

from tubbs.formatter.indenter.cond import Invariant, pred_cond
from tubbs.formatter.indenter.state import IndentState


inv = Invariant().amount(1)


@pred_cond('has indented sibling')
def sibling_indent(state: IndentState) -> Boolean:
    return state.sibling_indent

default_conds = Map(
    sibling_indent=sibling_indent,
)

__all__ = ('inv', 'sibling_indent', 'default_conds')
