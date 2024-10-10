import pulumi
import pulumi_aws as aws

# Use centrally managed custom component for stack settings.
from pequod_stackmgmt import StackSettings, StackSettingsArgs

# Use local custom component for network.
# Could also be published to a registry and imported from there.
from local_components.network import Network, NetworkArgs

# Import the configuration values using just a simple python file import.
import config

# Create VPC using the custom component.
network = Network(f"{config.base_name}-network", NetworkArgs(
    cidr_block=config.vpc_network_cidr))

# Create a security group allowing inbound access over port 80 and outbound
# access to anywhere.
sec_group = aws.ec2.SecurityGroup(f"{config.base_name}-sg",
    description="Enable HTTP access",
    vpc_id=network.vpc_id,
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            from_port=80,
            to_port=80,
            protocol="tcp",
            cidr_blocks=["0.0.0.0/0"],
        ),
        aws.ec2.SecurityGroupIngressArgs(
            from_port=22,
            to_port=22,
            protocol="tcp",
            cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    egress=[aws.ec2.SecurityGroupEgressArgs(
        from_port=0,
        to_port=0,
        protocol="-1",
        cidr_blocks=["0.0.0.0/0"],
    )])

# Create and launch EC2 instance(s) into the public subnet.

# Look up the latest Amazon Linux 2 AMI to use for each instance.
ami = aws.ec2.get_ami(filters=[aws.ec2.GetAmiFilterArgs(
        name="name",
        # This image family supports AWS console connect.
        values=["al2023-ami-2023.*-kernel-6.1-x86_64"]
    )],
    owners=["amazon"],
    most_recent=True).id

# User data to start a HTTP server in each EC2 instance
user_data = """#!/bin/bash
echo "Hello World,  from Pulumi!" > index.html
sudo yum install -y python
nohup sudo python -m http.server 80 &
"""

# Loop and create instance(s) across the subnets created by the network component.
num_subnets = len(network.subnet_ids) 
for i in range(config.num_instances):
    # Unique name for each instance.
    server_name = f"{config.base_name}-{i}"

    # Use modulo math to distribute the instances across the subnets.
    subnet_id = network.subnet_ids[i % num_subnets]

    # Create the instance
    server = aws.ec2.Instance(server_name,
        instance_type=config.instance_type,
        subnet_id=subnet_id,
        vpc_security_group_ids=[sec_group.id],
        user_data=user_data,
        ami=ami,
        tags={
            "Name": server_name,
        }, 
        opts=pulumi.ResourceOptions(replace_on_changes=["user_data"]))

    # Export the instance's publicly accessible IP address and hostname.
    pulumi.export(f"{server_name} ip", server.public_ip)
    pulumi.export(f"{server_name} hostname", server.public_dns)
    pulumi.export(f"{server_name} url", pulumi.Output.concat("http://",server.public_dns))

# Manage stack settings using the centrally managed custom component.
stackmgmt = StackSettings(f"{config.base_name}-stacksettings", 
                          drift_management=config.driftManagement)