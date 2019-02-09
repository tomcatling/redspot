import click

#from redspot.build import build
#from redspot.run import run

from build import build
from run import run


@click.group()
def cli() -> None:
    pass


cli.add_command(run.cli, name="run")
cli.add_command(build.cli, name="build")

if __name__ == "__main__":
    cli()
