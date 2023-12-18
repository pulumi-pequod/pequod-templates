# Pulumi SDKs
from pulumi import ResourceOptions, Output, export, get_organization, get_project, get_stack
from pulumi_azure_native import resources
import pulumi_kubernetes as k8s

# Pequod SDKs
from pequod_k8sdatadog import K8sMonitor
from pequod_stackmgmt import StackSettings 
from pequod_kafkacluster import ConfluentCluster 

# Components
from azure_aks import AksCluster, AksClusterArgs

# Local modules
import config

base_name = config.base_name

# Create an Azure Resource Group
resource_group = resources.ResourceGroup(f"{base_name}-rg")

cluster = AksCluster(base_name, AksClusterArgs(
    rg_name=resource_group.name,
    cluster_node_count=config.node_count,
    cluster_node_size=config.node_size,
    admin_username=config.admin_username,
    ssh_public_key=config.ssh_public_key
), opts=ResourceOptions())

k8s_provider = k8s.Provider('k8s-provider', kubeconfig=cluster.kubeconfig, delete_unreachable=True)

kafka = ConfluentCluster(f"{base_name}-kafka", 
    kafka_cluster_name=config.kafkaClusterName,
    kafka_topics=config.kafkaTopics
)

datadog_k8s_agent = K8sMonitor(f"{base_name}-mon", 
    api_key=config.require_secret("datadogApiKey"),
    opts=ResourceOptions(provider=k8s_provider))

stackmgmt = StackSettings(f"{base_name}-stacksettings", 
                          drift_management=config.get("driftManagement"))

export("resource_group", resource_group.name)
export("kubeconfig", Output.secret(cluster.kubeconfig))
export("kafkaUrl", kafka.kafkaUrl)
export("kafkaEnvironmentName", kafka.envId)
export("datadogDashboard", cluster.name.apply(lambda name: f"https://app.datadoghq.com/dash/integration/86/kubernetes---overview?refresh_mode=sliding&tpl_var_cluster%5B0%5D={name}&live=true".lower()))

