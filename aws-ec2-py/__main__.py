import pulumi
import pulumi_aws as aws
from pequod_stackmgmt import StackSettings, StackSettingsArgs

# Get some configuration values or set default values.
config = pulumi.Config()
instance_type = config.get("instanceType")
if instance_type is None:
    instance_type = "t3.micro"
vpc_network_cidr = config.get("vpcNetworkCidr")
if vpc_network_cidr is None:
    vpc_network_cidr = "10.0.0.0/16"
num_instances = config.get_int("numInstances") or 1
base_name = config.get("baseName") or f"{pulumi.get_project()}-{pulumi.get_stack()}"



# Create VPC.
vpc = aws.ec2.Vpc(f"{base_name}-vpc",
    cidr_block=vpc_network_cidr,
    enable_dns_hostnames=True,
    enable_dns_support=True)

# Create an internet gateway.
gateway = aws.ec2.InternetGateway(f"{base_name}-gw", vpc_id=vpc.id)

# Create a subnet that automatically assigns new instances a public IP address.
subnet = aws.ec2.Subnet(f"{base_name}-subnet",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    map_public_ip_on_launch=True)

# Create a route table.
route_table = aws.ec2.RouteTable(f"{base_name}-rt",
    vpc_id=vpc.id,
    routes=[aws.ec2.RouteTableRouteArgs(
        cidr_block="0.0.0.0/0",
        gateway_id=gateway.id,
    )])

# Associate the route table with the public subnet.
route_table_association = aws.ec2.RouteTableAssociation(f"{base_name}-rta",
    subnet_id=subnet.id,
    route_table_id=route_table.id)

# Create a security group allowing inbound access over port 80 and outbound
# access to anywhere.
sec_group = aws.ec2.SecurityGroup(f"{base_name}-sg",
    description="Enable HTTP access",
    vpc_id=vpc.id,
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

# Loop and create instance(s).
for i in range(num_instances):
    server_name = f"{base_name}-{i}"
    server = aws.ec2.Instance(server_name,
        instance_type=instance_type,
        subnet_id=subnet.id,
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


stackmgmt = StackSettings(f"{base_name}-stacksettings", 
                          drift_management=config.get("driftManagement"))


