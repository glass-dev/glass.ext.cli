# author: Nicolas Tessore <n.tessore@ucl.ac.uk>
# license: MIT
"""Module for dealing with config options."""

import click

from glass.ext.config import Config

from ._util import get_resource

DEFAULT_INI = "default.ini"

config_option = click.make_pass_decorator(Config)


def config_files():
    """Return the list of config files used."""
    ctx = click.get_current_context(silent=True)
    files = []
    while ctx is not None:
        files += ctx.params.get("config", [])
        ctx = ctx.parent
    return files


def load_config(files, *, no_defaults=False):
    from configparser import ConfigParser
    parser = ConfigParser()
    parser.optionxform = lambda obj: obj
    if not no_defaults:
        with get_resource(DEFAULT_INI).open("r") as fp:
            parser.read_file(fp)
    for file in files:
        with open(file) as fp:
            parser.read_file(fp)
    options = {f"{section}.{key}": parser[section][key]
               for section in parser for key in parser[section]}
    return Config(options)


@click.group()
def cli():
    """Show and manipulate configuration."""


@cli.command()
@config_option
def show(config):
    """Show the loaded configuration."""
    for key, value in config.items():
        click.echo(f"{key}: {value}")


@cli.command()
@click.option("-f", "--force", is_flag=True,
              help="Force writing over existing file.")
@click.argument("path", type=click.Path(writable=True))
@config_option
def write(config, path, force):
    """Write the loaded configuration to file."""
    import os.path
    from datetime import datetime
    if os.path.exists(path) and not force:
        raise click.ClickException(f"File '{path}' exists "
                                   "(use --force to overwrite")
    inputs = config_files()
    sections = {}
    for key, value in config.items():
        section, _, item = key.partition('.')
        section = sections.setdefault(section, {})
        section[item] = value
    with open(path, "w") as fp:
        fp.write(f"; glass config write {datetime.now()}\n")
        if inputs:
            fp.write(f"; inputs: {', '.join(inputs)}\n")
        for section, items in sections.items():
            fp.write(f"\n[{section}]\n")
            for key, value in items.items():
                fp.write(f"{key} = {value}\n")


if __name__ == "__main__":
    cli()
