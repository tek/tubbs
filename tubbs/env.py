from tubbs.logging import Logging
from ribosome.data import Data
from ribosome.record import dfield


class Env(Data, Logging):
    initialized = dfield(False)
    # parsers = map_file
