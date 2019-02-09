"""Apply Black to Jupyter notebooks."""

# Original work Copyright © 2018 Łukasz Langa
# Modified work Copyright © 2019 Tom Catling, Liam Coatman

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.


from pathlib import Path

import boto3
import botocore
import click

import toml
from redspot import utils

CONFIG_FIELDS = [
    "ImageTag",
    "S3PayloadBucket",
    "S3PayloadPath",
    "InboundIP",
    "InstanceRole"
]


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option(
    "-t",
    "--timeout",
    type=int,
    help="Timeout for instances.",
    show_default=True,
)
@click.option(
    "-i",
    "--instance-type",
    type=str,
    help="EC2 instance type for the job.",
    show_default=True,
)
@click.option(
    "-n",
    "--stack-name",
    type=str,
    default="ephemeral-stack",
    help="A name for the CloudFormation stack.",
    show_default=False,
)
@click.option(
    "--payload-bucket",
    type=str,
    help="A bucket for job payloads.",
    show_default=False,
)
@click.option(
    "--payload-path",
    type=str,
    help="A path (key) for the job payload in S3.",
    show_default=False,
)
@click.option(
    "--instance-role",
    type=str,
    help="An ARN for the role which will be attached to the job instance.",
    show_default=False,
)
@click.option(
    "--inbound-ip",
    type=str,
    help="IP address from which to allow SSH.",
    show_default=False,
)
@click.argument(
    "src",
    nargs=1,
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        allow_dash=True
    ),
    is_eager=True,
)
@click.pass_context
def cli(
    ctx: click.Context,
    timeout: int,
    instance_type: str,
    stack_name: str,
    payload_bucket: str,
    payload_path: str,
    instance_role: str,
    inbound_ip: str,
    src: str,
) -> None:
    """
    Running notebook jobs on EC2.
    """

    arg_config = {
        "InboundIP": inbound_ip,
        "S3PayloadBucket": payload_bucket,
        "S3PayloadPath": payload_path,
        "InstanceRole": instance_role,
        "Timeout": timeout,
        "InstanceType": instance_type
    }

    config, missing = utils.load_config(
        src, arg_config, CONFIG_FIELDS
    )
    target = Path(src)

    click.secho(toml.dumps(config).rstrip(), fg="green", bold=True)
    if missing:
        ctx.exit(1)

    #  Create a stack with the appropriate template
    #  and loaded config.
    try:
        start_build_job(target, stack_name, config)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'InvalidClientTokenId':
            click.secho('Bad AWS credentials.', fg='red')
            ctx.exit(1)
    except boto3.exceptions.S3UploadFailedError:
        click.secho('Failed to upload payload to S3.', fg='red')
        ctx.exit(1)
    else:
        click.secho('Done', fg='green')
        ctx.exit(0)


def start_build_job(
    dockerfile: Path, stack_name: str, config: utils.CFG
) -> None:
    """
    Start a job to build the specified Dockerfile on an EC2
    instance.

    Arguments:
        root (Path): Project root.
        dockerfile (Path): Path to the Dockerfile we will build.
    Returns:
        None
    """
    build_template = Path(__file__).parent / 'build_stack.yml'

    utils.push_payload(
        config["S3PayloadBucket"], dockerfile, config["S3PayloadPath"]
    )

    utils.create_stack(stack_name, build_template, config)
