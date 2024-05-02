from everest_models.jobs.fm_ops_remover.parser import build_argument_parser
from everest_models.jobs.fm_ops_remover.tasks import remove_operations


def main_entry_point(args=None):
    args_parser = build_argument_parser()
    options = args_parser.parse_args(args)

    remove_operations(options.input, options.wells)
    options.input.json_dump(options.output)
