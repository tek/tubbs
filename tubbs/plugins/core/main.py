from ribosome.machine import may_handle
from ribosome.machine.base import io

from amino import __

from tubbs.state import TubbsComponent, TubbsTransitions

from tubbs.plugins.core.message import StageI, AObj


class CoreTransitions(TubbsTransitions):

    @may_handle(StageI)
    def stage_i(self):
        return io(__.vars.set_p('started', True))

    @may_handle(AObj)
    def a_obj(self):
        pass


class Plugin(TubbsComponent):
    Transitions = CoreTransitions

__all__ = ('Plugin',)
