# RedSpot facilitates using Docker and Jupyter with AWS EC2

[![Build Status](https://travis-ci.org/tomcatling/redspot.svg?branch=master)](https://travis-ci.org/tomcatling/redspot)

# Philosophy

* Local is development is cheap
* Sometimes more power is required
* Environmental consistency is important

Containerisation allows us to recreate the same environment (from `redspot build`) locally and on a powerful, temporary EC2 instance.

# Usage

`redspot build <dockerfile>`

`redspot run <jupyter notebook>`

Parameters can be supplied via the CLI or a `.redspot.toml` file in the same file tree as the target Dockerfile or Jupyter notebook. The `run` and `build` jobs must be supplied with the name of an instance profile, an image tag (ECR), S3 buckets and paths for outputs and job payloads, and other parameters such as job timeout and instance type. More documentation needed!