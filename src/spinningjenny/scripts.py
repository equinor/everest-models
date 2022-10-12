from os import path

import pkg_resources
import ruamel.yaml as yaml


def entry_points():
    """
    Dictionary mapping a spinning jenny job name to it's main entry point script function.
    This dictionary is used when creating the runnable python entries. The spinningjenny
    module expects there is one entry point per config file and this constraint
    will be enforced using a test.
    :return:
    """
    with open(
        pkg_resources.resource_filename("spinningjenny", "share/entry_points.yml")
    ) as fh:
        return yaml.YAML(typ="safe", pure=True).load(fh)


def fm_install_folder():
    return path.abspath(
        pkg_resources.resource_filename("spinningjenny", "share/forwardmodels")
    )


def fm_jobs():
    install_folder = fm_install_folder()
    return [
        {"name": job_name, "path": path.join(install_folder, job_name)}
        for job_name in entry_points()
    ]
