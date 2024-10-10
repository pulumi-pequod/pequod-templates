import pulumi

# Get configuration values or set default values.
config = pulumi.Config()
instance_type = config.get("instanceType")
if instance_type is None:
    instance_type = "t3.micro"
vpc_network_cidr = config.get("vpcNetworkCidr")
if vpc_network_cidr is None:
    vpc_network_cidr = "10.0.0.0/16"
num_instances = config.get_int("numInstances") or 1
base_name = config.get("baseName") or f"{pulumi.get_project()}-{pulumi.get_stack()}"
driftManagement = config.get("driftManagement")