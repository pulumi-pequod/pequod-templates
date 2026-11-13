import re
import pulumi


def gcp_name(name: str, max_len: int = 45) -> str:
    """Make name a valid GCP RFC 1035 label (lowercase, starts with a letter).

    max_len leaves room for Pulumi's 8-char autoname suffix and the "-webserver"
    suffix added in __main__.py, keeping the final name within GCP's 63 chars.
    """
    name = re.sub(r"[^a-z0-9-]+", "-", name.lower()).strip("-")
    name = re.sub(r"^[^a-z]+", "", name)
    return name[:max_len].rstrip("-") or "r"


config = pulumi.Config()

project = config.get('project')
if project is None:
    project = f"{pulumi.get_project()}-{pulumi.get_stack()}"
project = gcp_name(project)

owner = config.get('owner')
if owner is None:
    owner = pulumi.get_organization()

subnet_cidr_blocks = config.get_object('subnet_cidr_blocks')
if subnet_cidr_blocks is None:
    subnet_cidr_blocks = ['172.1.0.0/16', '172.2.0.0/16']

webserver_startup_script = f"""#!/bin/bash
    echo '<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <title>Hello, world!</title>
    </head>
    <body>
        <h1>Hello, world! 👋</h1>
        <p>Deployed with 💜 by <a href="https://pulumi.com/">Pulumi</a>.</p>
    </body>
    </html>' > index.html
    sudo python3 -m http.server 80 &
    """
