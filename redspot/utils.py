from pathlib import Path
from requests import get

import shutil
from typing import List, Dict, Any, Tuple

import boto3
import click
import toml

#  Files and folders required by the project.
CONFIG_PATH = Path(".redspot.toml")

DEFAULT_TIMEOUT = 60
DEFAULT_INSTANCE = "c5.2xLarge"

CFG = Dict[str, Any]


def find_project_root(src: str) -> Path:
    """Return a directory containing .git, .hg, or pyproject.toml.

    If no directory in the tree contains a marker that would specify it's the
    project root, the root of the file system is returned.

    Arguments:
        src (str): String pointing to file.
    Returns:
        directory (Path): Returns the root Path of the project.
    """
    for directory in Path(src).resolve().parents:
        if (directory / CONFIG_PATH).is_file():
            return directory
    return directory


def load_config(
    root: Path, timeout: int, instance_type: str, ip: str, CONFIG_FIELDS: List[str]
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Load cloudformation parameters and overwrite with command
    line arguments where supplied.
    """
    config_path = root / CONFIG_PATH
    config: CFG = {}
    if config_path.is_file():
        with open(config_path) as f:
            config.update(**toml.loads(f.read()))

    if timeout is not None:
        config["TimeOut"] = timeout
    elif "TimeOut" not in config:
        config["TimeOut"] = 60

    if instance_type is not None:
        config["InstanceType"] = instance_type
    elif "InstanceType" not in config:
        config["InstanceType"] = "c5.2xlarge"

    if ip is not None:
        config["InBoundIP"] = ip
    elif "InBoundIP" not in config:
        config["InBoundIP"] = get("https://api.ipify.org").text

    missing = verify_config(config, CONFIG_FIELDS)
    return config, missing


def verify_config(config: CFG, CONFIG_FIELDS: List[str]) -> List[str]:
    #  Report any missing entries in the config file.
    return [p for p in CONFIG_FIELDS if p not in config]


def create_payload(payload_directory: Path) -> Path:
    """
    Create a payload by zipping a directory.

    Arguments:
        payload_directory (Path): Path to a directory
        which will be zipped.
    Returns:
        payload_path (Path): Path to the payload.
    """
    click.echo(f"Zipping {payload_directory}/* for job payload.")

    shutil.make_archive("payload", "zip", payload_directory)
    payload_path = payload_directory.parent / "payload.zip"
    return payload_path


def push_payload(bucket: str, payload: Path, destination: str) -> None:
    s3 = boto3.resource("s3")

    s3.Bucket(bucket).upload_file(str(payload), destination)


def create_stack(stack_name: str, template_path: Path, config: CFG) -> Any:
    """
    Create a CloudFormation stack called `stack_name` from
    the template at the specified `template_path`.

    Arguments:
        stack_name (str): Name of the stack to create.
        template_path (Path): Path to the cloudformation template.
    Returns:
        (dict): Response from CloudFormation.
    """

    with open(template_path) as f:
        template_body = f.read()

    client = boto3.client("cloudformation")
    # return client.validate_template(TemplateBody=template_body)

    return client.create_stack(
        StackName=stack_name,
        TemplateBody=template_body,
        Parameters=to_params(config),
    )


def to_params(config: CFG) -> List[Dict[str, Any]]:
    return [
        {"ParameterKey": k, "ParameterValue": str(v)}
        for k, v in config.items()
    ]
