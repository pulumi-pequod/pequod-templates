# Pulumi packages
import pulumi
import pulumi_eks as eks
import pulumi_awsx as awsx
import pulumi_kubernetes as k8s

# pequod packages
from pulumi_pequod_stackmgmt import StackSettings, StackSettingsArgs
from pulumi_pequod_k8sdatadog import K8sMonitor, K8sMonitorArgs 

# Get stack-specific config
config = pulumi.Config()
base_name = config.get("service_name") or pulumi.get_project()
desired_size = config.get_int("desiredClusterSize") or 2
max_size = config.get_int("maxClusterSize") or 2
min_size = config.get_int("minClusterSize") or 1
vpc_network_cidr = config.get("network_cidr") or "10.0.0.0/16"
eks_node_instance_type = config.get("node_instance_type") or "t2.medium"

# Owner tag
tags = { "Owner": pulumi.get_organization() }

# Create a new VPC
eks_vpc = awsx.ec2.Vpc(f"{base_name}-vpc",
                       enable_dns_hostnames=True,
                       cidr_block=vpc_network_cidr,
                       nat_gateways=awsx.ec2.NatGatewayConfigurationArgs(
                           strategy=awsx.ec2.NatGatewayStrategy.SINGLE
                       ),
                       tags=tags)

# Create the EKS cluster
eks_cluster = eks.Cluster(f"{base_name}-eks",
                          authentication_mode=eks.AuthenticationMode.API,
                          vpc_id=eks_vpc.vpc_id,
                          public_subnet_ids=eks_vpc.public_subnet_ids,
                          private_subnet_ids=eks_vpc.private_subnet_ids,
                          instance_type=eks_node_instance_type,
                          desired_capacity=desired_size,
                          min_size=min_size,
                          max_size=max_size,
                          node_associate_public_ip_address=False,
                          endpoint_private_access=False,
                          endpoint_public_access=True,
                          tags=tags,)


# Instantiate a Kubernetes provider
kubeconfig = pulumi.Output.secret(eks_cluster.kubeconfig)
k8sprovider = k8s.Provider(f"{base_name}-k8sprovider", kubeconfig=kubeconfig)

# Deploy the Datadog agent
datadog_k8s_agent = K8sMonitor(f"{base_name}-mon", 
    datadog_api_key=config.require_secret("datadogApiKey"),
    opts=pulumi.ResourceOptions(provider=k8sprovider))

# Manage stack settings
stackmgmt = StackSettings(f"{base_name}-stacksettings", 
                          drift_management=config.get("driftManagement"))

# Export some useful information
pulumi.export('kubeconfig', kubeconfig)
pulumi.export('datadogDashboard', eks_cluster.eks_cluster.name.apply(lambda name: f"https://app.datadoghq.com/dash/integration/86/kubernetes---overview?fromUser=false&refresh_mode=sliding&tpl_var_cluster%5B0%5D={name}&live=true".lower()))
                                                                                                                                                                # &tpl_var_cluster%5B0%5D=mitch-eks-ts-pequod-eks-ekscluster-ee942dc&from_ts=1726765011855&to_ts=1726765911855&live=true
