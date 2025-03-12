"""An AWS Python Pulumi program"""

import pulumi
from pulumi_aws import s3
from pequod_stackmgmt import StackSettings, StackSettingsArgs

from pulumi_container_services import AppDeploy, AppDeployArgs, AppImage, AppImageArgs 

config = pulumi.Config()
cpu = config.get_int("cpu") or 256 
memory = config.get_int("memory") or 512

app_image = AppImage(f"app-image-{pulumi.get_stack()}", AppImageArgs(  
  docker_file_path="./app"
))

app_service = AppDeploy(f"app-service-{pulumi.get_stack()}", AppDeployArgs(
  image_reference=app_image.image_ref,
  cpu=cpu,
  memory=memory
))

# Manage stack settings using the centrally managed custom component.
stackmgmt = StackSettings("stacksettings") 

# Export the name of the bucket
pulumi.export("image_reference", app_image.image_ref)
pulumi.export("service_url", pulumi.Output.concat("http://",app_service.loadbalancer_dns_name))
