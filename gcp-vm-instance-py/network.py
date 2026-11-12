from pulumi import ComponentResource, ResourceOptions
from pulumi_gcp import compute

from naming import gcp_resource_name


class VpcArgs:

    def __init__(self,
                 subnet_cidr_blocks=None,
                 ):
        self.subnet_cidr_blocks = subnet_cidr_blocks


class Vpc(ComponentResource):

    def __init__(self,
                 name: str,
                 args: VpcArgs,
                 opts: ResourceOptions = None):

        super().__init__("pequod:local:Vpc", name, {}, opts)

        # Guard against names that GCP rejects (uppercase, too long, etc.).
        base_name = gcp_resource_name(name)

        child_opts = ResourceOptions(parent=self)

        self.network = compute.Network(base_name,
                                       auto_create_subnetworks=False,
                                       opts=ResourceOptions(parent=self)
                                       )

        self.subnets = []
        for i, ip_cidr_range in enumerate(args.subnet_cidr_blocks):
            subnet = compute.Subnetwork(gcp_resource_name(f"{base_name}-{i}"),
                                        network=self.network.self_link,
                                        ip_cidr_range=ip_cidr_range,
                                        opts=ResourceOptions(
                                            parent=self.network)
                                        )
            self.subnets.append(subnet)

        self.router = compute.Router(base_name,
                                     network=self.network.self_link,
                                     opts=ResourceOptions(parent=self.network)
                                     )

        self.nat = compute.RouterNat(base_name,
                                     router=self.router.name,
                                     nat_ip_allocate_option="AUTO_ONLY",
                                     source_subnetwork_ip_ranges_to_nat="ALL_SUBNETWORKS_ALL_IP_RANGES",
                                     opts=ResourceOptions(parent=self.network)
                                     )

        self.register_outputs({})
