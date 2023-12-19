from pulumi import ComponentResource, ResourceOptions, Output
from pulumi_azure_native import containerservice, managedidentity, authorization
import pulumi_kubernetes as k8s
import pulumi_tls as tls
import base64
import time

class AksClusterArgs:

    def __init__(self,
                 rg_name=None,
                 rg_id=None,
                 cluster_node_count=None,
                 cluster_node_size=None,
                 admin_username=None,
                 ssh_public_key=None,
                 ):

        self.rg_name = rg_name 
        self.rg_id = rg_id
        self.cluster_node_count = cluster_node_count
        self.cluster_node_size = cluster_node_size
        self.admin_username = admin_username
        self.ssh_public_key = ssh_public_key


class AksCluster(ComponentResource):

    def __init__(self,
                 name: str,
                 args: AksClusterArgs,
                 opts: ResourceOptions = None):

        super().__init__('custom:kubernetes:AksCluster', name, {}, opts)
        opts.parent=self

        rg_name = args.rg_name
        rg_id = args.rg_id
        cluster_node_count = args.cluster_node_count
        cluster_node_size = args.cluster_node_size
        admin_username = args.admin_username
        ssh_public_key = args.ssh_public_key

        privateKey = tls.PrivateKey(f"{name}-privateKey", 
            algorithm="RSA",
            rsa_bits=4096,
            opts=opts)
        
        identity = managedidentity.UserAssignedIdentity(f"{name}-identity", 
            resource_group_name=rg_name,
            opts=opts)
        
        # K8s cluster
        cluster_name = f"{name}-k8s"
        k8s_cluster = containerservice.ManagedCluster(cluster_name,
            resource_group_name=rg_name,
            identity=containerservice.ManagedClusterIdentityArgs(
                type=containerservice.ResourceIdentityType.USER_ASSIGNED,
                user_assigned_identities=[identity.id],
            ),
            dns_prefix=f"{name}-dns-pre",
            enable_rbac=True,
            agent_pool_profiles=[{
                'count': cluster_node_count,
                'max_pods': 110,
                'mode': 'System',
                'name': 'agentpool',
                'node_labels': {},
                'os_disk_size_gb': 30,
                'os_type': 'Linux',
                'type': 'VirtualMachineScaleSets',
                'vm_size': cluster_node_size,
            }],
            linux_profile={
                'admin_username': admin_username,
                'ssh': {
                    'publicKeys': [{
                        'keyData': ssh_public_key,
                    }],
                },
            },
            opts=opts)

        creds = containerservice.list_managed_cluster_user_credentials_output(
            resource_group_name=rg_name,
            resource_name=k8s_cluster.name)

        # grant the 'contributor' role to the identity on the resource group
        assignment = authorization.RoleAssignment(f"{name}-roleAssignment", 
            principal_id=identity.principal_id,
            principal_type="ServicePrincipal",
            role_definition_id="/providers/Microsoft.Authorization/roleDefinitions/b24988ac-6180-42a0-ab88-20f7382dd24c",
            scope=rg_id,
            opts=opts,
        )

        self.cluster_name = k8s_cluster.name

        self.kubeconfig = creds.kubeconfigs[0].value.apply(
            lambda enc: base64.b64decode(enc).decode())

        self.k8s_provider = k8s.Provider('k8s-provider', kubeconfig=self.kubeconfig, delete_unreachable=True)

        self.register_outputs({})


def sp_profile(args):
    # Azure AD will sometimes return service principal info, 
    # but the SP hasn't propagated and so Azure throws an error 
    # about not finding the SP when creating the AKS cluster. 
    # So take a small nap to give time for the propagation.
    time.sleep(30) 
    return({'client_id': args["app_id"],'secret': args["pwd"]})