from ribosome import Machine, PluginStateMachine, NvimFacade
from ribosome.nvim import HasNvim
from ribosome.machine import ModularMachine, Transitions

from tubbs.logging import Logging

from amino import List


class TubbsComponent(ModularMachine, HasNvim, Logging):

    def __init__(self, name: str, vim: NvimFacade) -> None:
        Machine.__init__(self, name)
        HasNvim.__init__(self, vim)


class TubbsState(PluginStateMachine, HasNvim, Logging):

    def __init__(self, vim: NvimFacade, plugins: List[str]) -> None:
        HasNvim.__init__(self, vim)
        PluginStateMachine.__init__(self, 'tubbs', plugins)


class TubbsTransitions(Transitions, HasNvim):

    def __init__(self, machine, *a, **kw):
        Transitions.__init__(self, machine, *a, **kw)
        HasNvim.__init__(self, machine.vim)

__all__ = ('TubbsComponent', 'TubbsState', 'TubbsTransitions')
