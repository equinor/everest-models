import ruamel.yaml as yaml
import pkg_resources


def entry_points():
    """
    Dictionary mapping a spinning jenny job name to it's main entry point script function.
    This dictionary is used when creating the runnable python entries. The spinningjenny
    module expects there is one entry point per config file and this constraint
    will be enforced using a test.
    :return:
    """
    with open(pkg_resources.resource_filename("share", "entry_points.yml")) as fh:
        return yaml.safe_load(fh)
