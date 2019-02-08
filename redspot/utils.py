from pathlib import Path
import shutil
from typing import List, Dict, Any, Tuple

import boto3
import click
import toml

#  Files and folders required by the project.
CONFIG_PATH = Path(".redspot.toml")
JOB_STACK = Path(".redspot_templates/job_stack.yml")
BUILD_STACK = Path(".redspot_templates/build_stack.yml")

MUST_EXIST = [CONFIG_PATH, JOB_STACK, BUILD_STACK]

CONFIG_FIELDS = ["S3PayloadPath", "S3OutputPath", "ImageTag"]

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
    root: Path, timeout: int, instance_type: str
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

    config["TimeOut"] = timeout
    config["InstanceType"] = instance_type

    missing = verify_config(config)
    return config, missing


def verify_config(config: CFG) -> List[str]:
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
    click.echo(f"Zipping {payload_directory.resolve()} for job payload.")

    shutil.make_archive("payload", "zip", payload_directory)
    payload_path = payload_directory / "payload.zip"
    return payload_path


def push_payload(payload: Path, destination: str) -> None:
    pass


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
    return client.validate_template(TemplateBody=template_body)
    #  return client.create_stack(
    #     StackName=stack_name, TemplateBody=template_body
    #  )
    #  return {}
