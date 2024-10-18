#! /usr/bin/env python3

import os
import sys
python = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                      "env", "bin", "python")
if not os.getenv("VIRTUAL_ENV") and sys.executable != python and os.path.exists(python):
    os.execv(python, [python] + sys.argv)

import typeguard
typeguard.install_import_hook('lib')

from lib import __main__
__main__.main()
