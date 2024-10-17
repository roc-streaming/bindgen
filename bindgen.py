#! /usr/bin/env python3

import typeguard
typeguard.install_import_hook('lib')

from lib import __main__
if __name__ == '__main__':
    __main__.main()
