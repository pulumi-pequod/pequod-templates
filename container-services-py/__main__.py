"""An AWS Python Pulumi program"""

import pulumi
from pulumi_aws import s3

from pulumi_container_services import AppDeploy, AppDeployArgs, AppImage, AppImageArgs 

config = pulumi.Config()
cpu = config.get_int("cpu") or 256 
memory = config.get_int("memory") or 512

app_image = AppImage(f"{pulumi.get_project()}-{pulumi.get_stack()}-image", AppImageArgs(
  docker_file_path="./app"
))

app_service = AppDeploy(f"{pulumi.get_project()}-{pulumi.get_stack()}-app", AppDeployArgs(
  image_reference=app_image.image_ref,
  cpu=cpu,
  memory=memory
))

# Export the name of the bucket
pulumi.export("image_reference", app_image.image_ref)
pulumi.export("service_url", pulumi.Output.concat("http://",app_service.loadbalancer_dns_name))
