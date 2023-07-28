# author: Nicolas Tessore <n.tessore@ucl.ac.uk>
# license: MIT
"""GLASS command line interface"""

import sys
if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points

import click

from .config import load_config, print_config


class CLI(click.MultiCommand):

    def list_commands(self, ctx):
        eps = entry_points(group="glass.cli")
        return [ep.name for ep in eps]

    def get_command(self, ctx, name):
        eps = entry_points(name=name, group="glass.cli")
        for ep in eps:
            return ep.load()


@click.command(cls=CLI)
@click.option("-C", "--config", type=click.Path(exists=True, dir_okay=False),
              multiple=True)
@click.option("-S", "--show-config", is_flag=True)
@click.option("--no-defaults", is_flag=True)
@click.pass_context
def cli(ctx, config, no_defaults, show_config):
    cfg = load_config(config, no_defaults=no_defaults)
    if show_config:
        print_config(cfg)
    ctx.obj = cfg


if __name__ == "__main__":
    cli()
