from pathlib import Path
from requests import get

import shutil
from typing import List, Dict, Any, Tuple

import boto3
import toml

#  Files and folders required by the project.
CONFIG_PATH = Path(".redspot.toml")
CFG = Dict[str, Any]
DEFAULT_CONFIG: CFG = {
    "TimeOut": 60,
    "InstanceType": "c5.xlarge",
    "InboundIP": "{}/32".format(get("https://api.ipify.org").text),
}


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
    src: str, arg_config: CFG, CONFIG_FIELDS: List[str]
) -> Tuple[CFG, List[str]]:
    """
    Load cloudformation parameters and overwrite with command
    line arguments where supplied.
    """
    root = find_project_root(src)
    config_path = root / CONFIG_PATH

    # Sensible defaults exist for some parameters.
    config: CFG = DEFAULT_CONFIG
    if config_path.is_file():
        with open(config_path) as f:
            config.update(**toml.loads(f.read()))

    # CLI parameters take priority.
    for k, v in arg_config.items():
        if v is not None:
            config[k] = v

    final_config, missing = verify_config(config, CONFIG_FIELDS)

    return final_config, missing


def verify_config(
    config: CFG, CONFIG_FIELDS: List[str]
) -> Tuple[CFG, List[str]]:
    #  Report any missing entries in the config file.
    final_config = {k: v for k, v in config.items() if k in CONFIG_FIELDS}
    missing = [p for p in CONFIG_FIELDS if p not in config]
    return final_config, missing


def create_payload(payload_directory: Path) -> Path:
    """
    Create a payload by zipping a directory.

    Arguments:
        payload_directory (Path): Path to a directory
        which will be zipped.
    Returns:
        payload_path (Path): Path to the payload.
    """
    parent = payload_directory.parent
    shutil.make_archive(str(parent / "payload"), "zip", payload_directory)
    payload_path = parent / "payload.zip"
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
