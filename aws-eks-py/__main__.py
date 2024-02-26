# Pulumi SDKs
import pulumi
from pulumi_aws import eks
import pulumi_kubernetes as k8s

# components
from pequod_stackmgmt import StackSettings, StackSettingsArgs
from pequod_k8sdatadog import K8sMonitor, K8sMonitorArgs
from aws_network import Vpc, VpcArgs 

# local python modules
import iam
import utils

# Get stack-specific config
config = pulumi.Config()
service_name = config.get("service_name") or pulumi.get_project()
desired_size = config.get_int("desiredClusterSize") or 2
max_size = config.get_int("maxClusterSize") or 2
min_size = config.get_int("minClusterSize") or 1

## VPC and related resources
vpc = Vpc(f'{service_name}-net', VpcArgs()) 

## EKS Cluster
eks_cluster = eks.Cluster(
    f'{service_name}-cluster',
    role_arn=iam.eks_role.arn,
    tags={
        'Name': 'pulumi-eks-cluster',
    },
    vpc_config=eks.ClusterVpcConfigArgs(
        public_access_cidrs=['0.0.0.0/0'],
        security_group_ids=[vpc.fe_security_group.id],
        subnet_ids=vpc.subnet_ids,
    ),
    opts=pulumi.ResourceOptions(depends_on=[iam.eks_service_pol_attach, iam.eks_cluster_pol_attach])
)

eks_node_group = eks.NodeGroup(
    f'{service_name}-nodegroup',
    cluster_name=eks_cluster.name,
    node_group_name='pulumi-eks-nodegroup',
    node_role_arn=iam.ec2_role.arn,
    subnet_ids=vpc.subnet_ids,
    tags={
        'Name': 'pulumi-cluster-nodeGroup',
    },
    scaling_config=eks.NodeGroupScalingConfigArgs(
        desired_size=desired_size,
        max_size=max_size,
        min_size=min_size,
    ),
)

kubeconfig = pulumi.Output.secret(utils.generate_kube_config(eks_cluster))

k8s_provider = k8s.Provider('k8s-provider', kubeconfig=kubeconfig, delete_unreachable=True)

datadog_k8s_agent = K8sMonitor(f"{service_name}-mon", 
    api_key=config.require_secret("datadogApiKey"),
    opts=pulumi.ResourceOptions(provider=k8s_provider))

stackmgmt = StackSettings(f"{service_name}-stacksettings", 
                          drift_management=config.get("driftManagement"))

pulumi.export('kubeconfig', kubeconfig)
pulumi.export('datadogDashboard', eks_cluster.name.apply(lambda name: f"https://app.datadoghq.com/dash/integration/86/kubernetes---overview?refresh_mode=sliding&tpl_var_cluster%5B0%5D={name}&live=true".lower()))
