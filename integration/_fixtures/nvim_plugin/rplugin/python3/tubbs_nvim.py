import neovim
import os
import logging
from pathlib import Path

from tubbs.nvim_plugin import TubbsNvimPlugin

import amino

amino.development = True

import amino.logging

logfile = Path(os.environ['TRYPNV_LOG_FILE'])
amino.logging.tryp_file_logging(level=logging.DEBUG,
                                handler_level=logging.DEBUG,
                                logfile=logfile)


@neovim.plugin
class Plugin(TubbsNvimPlugin):
    pass
