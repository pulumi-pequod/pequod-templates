import pulumi
import pulumi_aws as aws
import pulumi_awsx as awsx
from pulumi_pequod_container_services import AppImage, AppImageArgs
from pulumi_pequod_stackmgmt import StackSettings

config = pulumi.Config()
cpu = config.get_int("cpu") or 256
memory = config.get_int("memory") or 512

# Owner tag for all resources.
tags = {"Owner": f"{pulumi.get_project()}-{pulumi.get_stack()}"}

# Use the component abstraction to build the Docker image and push to ECR.
docker_image = AppImage("dockerImage", AppImageArgs(docker_file_path="./app"))

# Look up the default VPC for placing the service.
default_vpc = aws.ec2.get_vpc(default=True)
default_subnets = aws.ec2.get_subnets(
    filters=[aws.ec2.GetSubnetsFilterArgs(name="vpc-id", values=[default_vpc.id])]
)

# Security group for the ECS Fargate service.
# Restricts ingress to TCP port 80 only (HTTP) instead of allowing all
# protocols from 0.0.0.0/0, which resolves the database-strict-network-access
# policy issue.
service_sg = aws.ec2.SecurityGroup(
    "service-sg",
    vpc_id=default_vpc.id,
    description="ECS Fargate service - allow HTTP ingress only",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=80,
            to_port=80,
            cidr_blocks=["0.0.0.0/0"],
            description="Allow HTTP traffic",
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
            description="Allow all outbound traffic",
        ),
    ],
    tags=tags,
)

# ALB to serve the container endpoint to the internet.
loadbalancer = awsx.lb.ApplicationLoadBalancer(
    "app-lb",
    default_security_group=awsx.awsx.DefaultSecurityGroupArgs(
        security_group_id=service_sg.id,
    ),
    tags=tags,
)

# ECS cluster.
cluster = aws.ecs.Cluster("app-ecs", tags=tags)

# Deploy an ECS Service on Fargate with the restricted security group.
service = awsx.ecs.FargateService(
    "app-service",
    cluster=cluster.arn,
    assign_public_ip=True,
    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
        subnets=default_subnets.ids,
        security_groups=[service_sg.id],
        assign_public_ip=True,
    ),
    task_definition_args=awsx.ecs.FargateServiceTaskDefinitionArgs(
        container=awsx.ecs.TaskDefinitionContainerDefinitionArgs(
            name="app-container",
            image=docker_image.image_ref,
            cpu=cpu,
            memory=memory,
            essential=True,
            port_mappings=[
                awsx.ecs.TaskDefinitionPortMappingArgs(
                    container_port=80,
                    target_group=loadbalancer.default_target_group,
                ),
            ],
        ),
    ),
    tags=tags,
)

# Manage stack settings using the centrally managed custom component.
stackmgmt = StackSettings("stacksettings")

# Export URL for the service.
pulumi.export(
    "service_url",
    pulumi.Output.concat("http://", loadbalancer.load_balancer.dns_name),
)
