import pulumi
from pulumi_pequod_stackmgmt import StackSettings, StackSettingsArgs

from pulumi_pequod_container_services import AppImageDeploy, AppImageDeployArgs

config = pulumi.Config()
cpu = config.get_int("cpu") or 256 
memory = config.get_int("memory") or 512

# Use component abstraction to create docker image, push to ECR and deploy to ECS.
app_deployment = AppImageDeploy(f"app-deployment", AppImageDeployArgs(  
  docker_file_path="./app"
))

# Manage stack settings using the centrally managed custom component.
stackmgmt = StackSettings("stacksettings") 

# Export URL for the service
pulumi.export("service_url", pulumi.Output.concat("http://",app_deployment.loadbalancer_dns_name))
