import argparse

from .config import configure, configure_package


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
        parser_configure.add_argument(
            '--save', required=False,
            help='can optionally specify a path to save to')

    def configure(self, args):
        if not args.package and not args.save:
            configure()
        elif not args.package and args.save:
            configure(path=args.save)
        else:
            configure_package(args.package)


def main():
    command_line = CommandLine()
    command_line.main()


if __name__ == '__main__':
    main()
