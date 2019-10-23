import argparse
from .config import configure


class CommandLine(object):
    """Sets up command line parser and invokes main functions"""

    def __init__(self):
        parser = argparse.ArgumentParser(
            description='Complex file based memoization - configuration')
        subparsers = parser.add_subparsers()

        self.setup_configure_parser(subparsers)
        self.parser = parser

    def main(self):
        args = self.parser.parse_args()
        args.func(args)

    def setup_configure_parser(self, subparsers):
        parser_configure = subparsers.add_parser('configure')
        parser_configure.set_defaults(func=self.configure)
        parser_configure.add_argument(
            '--package', required=False,
            help='can optionally specify a specific package to configure')

    def configure(self, args):
        print(args)
        configure()


def main():
    command_line = CommandLine()
    command_line.main()


if __name__ == '__main__':
    main()
