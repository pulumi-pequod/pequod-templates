# Pulumi SDKs
from pulumi import ResourceOptions, Output, export, get_organization, get_project, get_stack
from pulumi_azure_native import resources
import pulumi_kubernetes as k8s

# Pequod SDKs
from pequod_k8sdatadog import K8sMonitor
from pulumi_pequod_stackmgmt import StackSettings, StackSettingsArgs
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
    rg_id=resource_group.id,
    cluster_node_count=config.node_count,
    cluster_node_size=config.node_size,
    admin_username=config.admin_username,
), opts=ResourceOptions())

## Kafka temporarily removed while we wait for our Confluent Cloud account.
# kafka = ConfluentCluster(f"{base_name}-kafka", 
#     kafka_cluster_name=config.kafka_cluster_name,
#     kafka_topics=config.kafka_topics
# )
# export("kafkaUrl", kafka.kafka_url)
# export("kafkaEnvironmentName", kafka.env_id)

datadog_k8s_agent = K8sMonitor(f"{base_name}-mon", 
    api_key=config.datadog_api_key,
    opts=ResourceOptions(provider=cluster.k8s_provider))

stackmgmt = StackSettings(f"{base_name}-stacksettings", 
                          drift_management=config.drift_management)

export("resource_group", resource_group.name)
export("kubeconfig", Output.secret(cluster.kubeconfig))

export("datadogDashboard", cluster.cluster_name.apply(lambda name: f"https://app.datadoghq.com/dash/integration/86/kubernetes---overview?refresh_mode=sliding&tpl_var_cluster%5B0%5D={name}&live=true".lower()))

