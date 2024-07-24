import os
import pulumi

config = pulumi.Config()

project = config.get('project')
if project is None:
    project = f"{pulumi.get_project()}-{pulumi.get_stack()}"

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
