import argparse
import sys

from aegis_maintenance.bootstrap import Bootstrap
from aegis_maintenance.reporting import render_report


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser(prog="aegis-maintenance")
    parser.add_argument("command", choices=["check", "update", "clean", "report", "doctor"], help="Commande à exécuter")
    parser.add_argument("--format", choices=["text", "json", "markdown"], default="text", help="Format de sortie")
    parser.add_argument("--verbose", action="store_true", help="Afficher plus de détails")
    args = parser.parse_args(argv)

    context = Bootstrap().initialize()
    report = context.execute(args.command)
    output = render_report(report, args.format, verbose=args.verbose)
    print(output)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
