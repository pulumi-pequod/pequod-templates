"""A Google Cloud Python Pulumi program"""

# Pulumi-provided packages
import pulumi
from pulumi_gcp import container
from pulumi_kubernetes.apps.v1 import Deployment, DeploymentSpecArgs
from pulumi_kubernetes.core.v1 import ContainerArgs, EnvVarArgs, PodSpecArgs, PodTemplateSpecArgs
from pulumi_kubernetes.meta.v1 import LabelSelectorArgs, ObjectMetaArgs
import pulumi_kubernetes as k8s

# MLC to create GKE cluster
from pequod_gke import Cluster, ClusterArgs
from pequod_stackmgmt import StackSettings
from pequod_k8sdatadog import K8sMonitor

# Stack Config
gcp_config = pulumi.Config("gcp")
project = gcp_config.require("project")
config = pulumi.Config()
service_name = config.get("service_name") or pulumi.get_project()
master_version = config.get("masterVersion") or container.get_engine_versions().latest_master_version
node_machine_type = config.get("nodeMachineType") or "n1-standard-1"
node_count = config.get("nodeCount") or 3 

base_name = f"gkebase-py-{pulumi.get_stack()}"

# Create a GKE cluster using the component resource 
k8s_cluster = Cluster(base_name, ClusterArgs(
    master_version=master_version,
    node_count=node_count,
    node_machine_type=node_machine_type
))
k8s_provider = k8s.Provider('k8s-provider', kubeconfig=k8s_cluster.kubeconfig, delete_unreachable=True)

# Create a canary deployment to test that the cluster works.
canary_labels = { "app": f"canary-{base_name}"}
canary = Deployment("canary", 
    spec=DeploymentSpecArgs(
      selector=LabelSelectorArgs(match_labels=canary_labels),
      replicas=1,
      template=PodTemplateSpecArgs(
        metadata=ObjectMetaArgs(labels=canary_labels),
        spec=PodSpecArgs(containers=[ContainerArgs(
          name="nginx", 
          image="nginx",
          env=[EnvVarArgs(
            name="DEPLOYMENT_SECRET",
            value=config.get_secret("deployment_secret")
          )]
        )])
      )
    ),
    opts=pulumi.ResourceOptions(provider=k8s_provider)
)

datadog_k8s_agent = K8sMonitor(f"{service_name}-mon", 
    api_key=config.require_secret("datadogApiKey"),
    opts=pulumi.ResourceOptions(provider=k8s_provider))

stackmgmt = StackSettings(f"{service_name}-stacksettings", 
                          drift_management=config.get("driftManagement"))

pulumi.export('kubeconfig', k8s_cluster.kubeconfig)
pulumi.export("cluster_name", k8s_cluster.cluster_name)
pulumi.export('datadogDashboard', k8s_cluster.cluster_name.apply(lambda name: f"https://app.datadoghq.com/dash/integration/86/kubernetes---overview?refresh_mode=sliding&tpl_var_cluster%5B0%5D={name}&live=true".lower()))
