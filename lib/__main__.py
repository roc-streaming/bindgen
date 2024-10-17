from .base_generator import *
from .doxygen_parser import *
from .go_generator import *
from .java_generator import *
from .log_formatter import *

import argparse
import colorama
import logging
import os
import sys


_LOG = logging.getLogger(__name__)

_DEFAULT_DOXYGEN_DIR = "build/docs/public_api/xml"
_ROC_TOOLKIT_BASE_PATH = "../roc-toolkit"
_ROC_JAVA_BASE_PATH = "../roc-java"
_ROC_GO_BASE_PATH = "../roc-go"


def _run_generator(generator_class, output_dir, api_root):
    _LOG.info(f"Running {generator_class.__name__} for {output_dir}")

    if not os.path.isdir(output_dir):
        _LOG.error(f"Output directory doesn't exist: {output_dir}")
        exit(1)

    generator = generator_class(output_dir, api_root)
    generator.generate_files()


def _run_all_generators(args):
    api_root = parse_doxygen(args.toolkit_dir, args.doxygen_dir)

    if args.type in ['all', 'java']:
        _run_generator(JavaGenerator, args.java_output_dir, api_root)

    if args.type in ['all', 'go']:
        _run_generator(GoGenerator, args.go_output_dir, api_root)


def main():
    os.chdir(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

    parser = argparse.ArgumentParser(description='Generate bindings')

    parser.add_argument('-t', '--type', choices=['all', 'java', 'go'],
                        help='Type of enum generation', required=True)
    parser.add_argument('--toolkit_dir',
                        default=_ROC_TOOLKIT_BASE_PATH,
                        help=f"Roc Toolkit directory (default: {_ROC_TOOLKIT_BASE_PATH})")
    parser.add_argument('--doxygen_dir',
                        default=None,
                        help=f"Doxygen XML directory (default: <toolkit_dir>/{_DEFAULT_DOXYGEN_DIR})")
    parser.add_argument('--go_output_dir',
                        default=_ROC_GO_BASE_PATH,
                        help=f"Go output directory (default: {_ROC_GO_BASE_PATH})")
    parser.add_argument('--java_output_dir',
                        default=_ROC_JAVA_BASE_PATH,
                        help=f"Java output directory (default: {_ROC_JAVA_BASE_PATH})")

    args = parser.parse_args()

    colorama.init()

    logHandler = logging.StreamHandler(sys.stderr)
    logHandler.setFormatter(LogFormatter())
    logging.basicConfig(level=logging.DEBUG, handlers=[logHandler])

    if not args.doxygen_dir:
        args.doxygen_dir = os.path.join(args.toolkit_dir, _DEFAULT_DOXYGEN_DIR)

    _run_all_generators(args)
