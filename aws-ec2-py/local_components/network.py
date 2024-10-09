from pulumi import ComponentResource, ResourceOptions
import pulumi_aws as aws
import netaddr # using an off-the-shelf python package for IP address manipulation

class NetworkArgs:

    def __init__(self,
                 cidr_block='10.100.0.0/16',
                 ):
        self.cidr_block = cidr_block


class Network(ComponentResource):

    def __init__(self,
                 name: str,
                 args: NetworkArgs,
                 opts: ResourceOptions = None):

        super().__init__('custom:resource:Network', name, {}, opts)



        # Create VPC.
        vpc = aws.ec2.Vpc(f"{name}-vpc",
            cidr_block=args.cidr_block,
            enable_dns_hostnames=True,
            enable_dns_support=True,
            opts=ResourceOptions(parent=self))
        self.vpc_id = vpc.id

        # Create an internet gateway.
        gateway = aws.ec2.InternetGateway(f"{name}-gw", 
            vpc_id=vpc.id,
            opts=ResourceOptions(parent=self))

        # Create a route table.
        route_table = aws.ec2.RouteTable(f"{name}-rt",
            vpc_id=vpc.id,
            routes=[aws.ec2.RouteTableRouteArgs(
                cidr_block="0.0.0.0/0",
                gateway_id=gateway.id,
            )],
            opts=ResourceOptions(parent=self))

        # Get all the zones in the region being used.
        all_zones = aws.get_availability_zones()

        # Build a list of subnets based on the CIDR block provided.
        ipNetwork = netaddr.IPNetwork(args.cidr_block)
        ipSubnets = list(ipNetwork.subnet(24))

        # Store the subnet objects and IDs in lists.
        self.subnets = []
        self.subnet_ids = []
        subnet_name_base = f'{name}-subnet'

        # Create a subnet in multiple zones.
        num_zones = 2 # limiting to 2 zones for simplicity
        for i in range(num_zones):
            zone_name = all_zones.names[i]
            subnet_cidr = str(ipSubnets[i])

            vpc_subnet = aws.ec2.Subnet(f'{subnet_name_base}-{zone_name}',
                assign_ipv6_address_on_creation=False,
                vpc_id=vpc.id,
                map_public_ip_on_launch=True,
                cidr_block=subnet_cidr,
                availability_zone=zone_name,
                tags={
                    'Name': f'{subnet_name_base}-{zone_name}',
                },
                opts=ResourceOptions(parent=self)
                )
            aws.ec2.RouteTableAssociation(
                f'vpc-route-table-assoc-{zone_name}',
                route_table_id=route_table.id,
                subnet_id=vpc_subnet.id,
                opts=ResourceOptions(parent=self)
            )
            self.subnets.append(vpc_subnet)
            self.subnet_ids.append(vpc_subnet.id)
