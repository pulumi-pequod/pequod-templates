from pulumi import Config, get_organization, get_project, get_stack, StackReference

config = Config()

base_name = config.get("baseName") or f"{get_project()}-{get_stack()}"
drift_management = config.get("driftManagement") or "Correct"

# Get stack name of the base k8s infra to deploy to and get the kubeconfig for the cluster.
base_infra_stack_name = config.get("base_infra_stack_name")  or "shared-dev-eks/dev"
k8s_stack_name = f"{get_organization()}/{base_infra_stack_name}"
k8s_stack_ref = StackReference(k8s_stack_name)

kubeconfig = k8s_stack_ref.require_output("kubeconfig") 

pulumi_config = Config("pulumiservice")
pulumi_access_token = pulumi_config.get_secret("accessToken")
