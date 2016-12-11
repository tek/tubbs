import neovim
import os
import logging
from pathlib import Path

from tubbs.nvim_plugin import TubbsNvimPlugin

import amino

amino.development = True

import tryp.logging

logfile = Path(os.environ['TRYPNV_LOG_FILE'])
tryp.logging.tryp_file_logging(level=logging.DEBUG,
                               handler_level=logging.DEBUG,
                               logfile=logfile)


@neovim.plugin
class Plugin(TubbsNvimPlugin):
    pass
