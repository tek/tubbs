from ribosome import Machine, NvimFacade
from ribosome.nvim import HasNvim

from ribosome.machine.state import (SubMachine, SubTransitions,
                                    UnloopedRootMachine)

from tubbs.logging import Logging
from tubbs.env import Env


class TubbsComponent(SubMachine, HasNvim, Logging):

    def __init__(self, vim: NvimFacade, parent=None, title=None) -> None:
        Machine.__init__(self, parent, title=title)
        HasNvim.__init__(self, vim)


class TubbsState(UnloopedRootMachine, Logging):
    _data_type = Env

    @property
    def title(self):
        return 'tubbs'


class TubbsTransitions(SubTransitions, HasNvim, Logging):

    def __init__(self, machine, *a, **kw):
        SubTransitions.__init__(self, machine, *a, **kw)
        HasNvim.__init__(self, machine.vim)

__all__ = ('TubbsComponent', 'TubbsState', 'TubbsTransitions')
