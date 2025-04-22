from pulumi import export, Output

# Component that sets up schedules and other stack-related settings.
from pulumi_pequod_stackmgmt import StackSettings, StackSettingsArgs

# Locally defined component resources.
# Would likely be versioned and distributed as a package.
import instance
import network

# Local module for config data
from config import project, owner, subnet_cidr_blocks, webserver_startup_script

base_metadata = {
    "Project": project,
    "Owner": owner,
}

network = network.Vpc(project,
                      network.VpcArgs(
                          subnet_cidr_blocks=subnet_cidr_blocks,
                      ))

service_name = "webserver"
webserver = instance.Server(f"{project}-{service_name}",
                                 instance.ServerArgs(
                                     service_name=service_name,
                                     metadata_startup_script=webserver_startup_script,
                                     ports=["80"],
                                     subnet=network.subnets[0],
                                     metadata=base_metadata,
                                 ))
                                
stackmgmt = StackSettings(f"{project}-stacksettings")

export('network', network.network.name)
export('webserver_url', Output.format("http://{0}",
       webserver.instance.network_interfaces.apply(lambda ws: ws[0].access_configs[0].nat_ip)))
