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
import os

import toml
from redspot import utils

CONFIG_FIELDS = [
    "ImageTag",
    "InstanceType",
    "S3PayloadBucket",
    "S3PayloadKey",
    "InboundIP",
    "InstanceProfile",
    "TimeOut",
    "KeyPair",
]


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option(
    "--timeout", type=int, help="Timeout for the job.", show_default=True
)
@click.option(
    "--instance-type", type=str, help="EC2 instance type for the job."
)
@click.option(
    "--stack-name",
    type=str,
    default="ephemeral-stack",
    help="Name of the CloudFormation stack which will be created.",
    show_default=False,
)
@click.option("--payload-bucket", type=str, help="A bucket for job payloads.")
@click.option("--payload-path", type=str, help="A key for job payloads in S3.")
@click.option(
    "--instance-profile",
    type=str,
    help="Name of the instance profile to use for the job instance.",
)
@click.option(
    "--inbound-ip",
    type=str,
    help="IP address from which inbound connections will be allowed.",
)
@click.argument(
    "src",
    nargs=1,
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        allow_dash=True,
    ),
    is_eager=False,
)
@click.pass_context
def cli(
    ctx: click.Context,
    timeout: int,
    instance_type: str,
    stack_name: str,
    payload_bucket: str,
    payload_path: str,
    instance_profile: str,
    inbound_ip: str,
    src: str,
) -> None:
    """
    Build a dockerfile in EC2 and push the image to ECR.
    """

    arg_config = {
        "InboundIP": inbound_ip,
        "S3PayloadBucket": payload_bucket,
        "S3PayloadKey": payload_path,
        "TimeOut": timeout,
        "InstanceType": instance_type,
        "InstanceProfile": instance_profile,
    }

    config, missing = utils.load_config(src, arg_config, CONFIG_FIELDS)
    target = Path(src)

    click.secho(toml.dumps(config).rstrip(), fg="green", bold=True)
    if missing:
        click.secho(str(missing), fg="red")
        ctx.exit(1)

    #  Create a stack with the appropriate template
    #  and loaded config.
    try:
        start_build_job(target, stack_name, config)
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "InvalidClientTokenId":
            click.secho("Bad AWS credentials.", fg="red")
            ctx.exit(1)
        else:
            click.secho(str(e), fg="red")
            ctx.exit(1)
    except boto3.exceptions.S3UploadFailedError:
        click.secho("Failed to upload payload to S3.", fg="red")
        ctx.exit(1)
    else:
        click.secho("Done", fg="green")
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
    build_template = Path(__file__).parent / "build_stack.yml"

    payload_directory = dockerfile.parent
    payload_path = utils.create_payload(payload_directory)

    utils.push_payload(
        config["S3PayloadBucket"], payload_path, config["S3PayloadKey"]
    )
    os.remove(payload_path)
    utils.create_stack(stack_name, build_template, config)
