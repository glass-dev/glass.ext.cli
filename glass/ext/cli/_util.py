# author: Nicolas Tessore <n.tessore@ucl.ac.uk>
# license: MIT
"""Internal module for utilities."""

import importlib.resources


def get_resource(resource):
    return importlib.resources.files(__package__).joinpath(resource)
