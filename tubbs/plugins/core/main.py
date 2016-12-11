from trypnv.machine import may_handle

from tubbs.state import TubbsComponent, TubbsTransitions

from amino.lazy import lazy
from tryp import Map
from tubbs.plugins.core.message import StageI


class Plugin(TubbsComponent):

    class Transitions(TubbsTransitions):

        @may_handle(StageI)
        def stage_i(self):
            pass

__all__ = ('Plugin')
