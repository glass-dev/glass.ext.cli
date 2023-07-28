# author: Nicolas Tessore <n.tessore@ucl.ac.uk>
# license: MIT
"""Module for dealing with config options."""

from configparser import ConfigParser

import click

from glass.ext.config import Config

from ._util import get_resource


config_option = click.make_pass_decorator(Config)


def load_config(files, *, no_defaults=False):
    parser = ConfigParser()
    parser.optionxform = lambda obj: obj
    if not no_defaults:
        with get_resource("default.ini").open("r") as fp:
            parser.read_file(fp)
    for file in files:
        with open(file) as fp:
            parser.read_file(fp)
    options = {f"{section}.{key}": parser[section][key]
               for section in parser for key in parser[section]}
    return Config(options)


def print_config(config: Config) -> None:
    click.echo()
    click.echo("Configuration")
    click.echo("-------------")
    for key, value in config.items():
        click.echo(f"{key}: {value}")
    click.echo()
