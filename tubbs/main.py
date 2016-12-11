from amino import List

from ribosome import NvimFacade

from tubbs.env import Env
from tubbs.state import TubbsState


class Tubbs(TubbsState):

    def __init__(self, vim: NvimFacade, plugins: List[str]) -> None:
        core = 'tubbs.plugins.core'
        TubbsState.__init__(self, vim, plugins.cons(core))

    def init(self):
        return Env(  # type: ignore
        )

__all__ = ('Tubbs',)
