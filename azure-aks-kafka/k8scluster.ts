import * as containerservice from "@pulumi/azure-native/containerservice";
import * as managedidentity from "@pulumi/azure-native/managedidentity";
import * as authorization from "@pulumi/azure-native/authorization";
import * as pulumi from "@pulumi/pulumi";
import * as tls from "@pulumi/tls";

export interface K8sClusterArgs {
    adminUserName: pulumi.Input<string>;
    k8sVersion: pulumi.Input<string>;
    nodeCount: number;
    nodeSize: string
    resourceGroupName: pulumi.Input<string>;
    resourceGroupId: pulumi.Input<string>;
}

export class K8sCluster extends pulumi.ComponentResource {
    public readonly clusterName: pulumi.Output<string>;
    public readonly kubeconfig: pulumi.Output<string>;

    constructor(name: string, args: K8sClusterArgs, opts?: pulumi.ComponentResourceOptions) {

        super("custom:resource:AzureCluster", name, args, opts);
    
        // create a private key to use for the cluster's ssh key
        const privateKey = new tls.PrivateKey(`${name}-privateKey`, {
            algorithm: "RSA",
            rsaBits: 4096,
        }, { parent: this });

        // create a user assigned identity to use for the cluster
        const identity = new managedidentity.UserAssignedIdentity(`${name}-identity`, { resourceGroupName: args.resourceGroupName }, { parent: this });

        // create the cluster
        const clusterName = `${name}-k8s`
        const cluster = new containerservice.ManagedCluster(clusterName, {
            resourceName: clusterName,
            resourceGroupName: args.resourceGroupName,
            identity: {
                type: containerservice.ResourceIdentityType.UserAssigned,
                userAssignedIdentities: [identity.id],
            },
            kubernetesVersion: args.k8sVersion,
            dnsPrefix: "dns-prefix",
            enableRBAC: true,
            agentPoolProfiles: [{
                name: "agentpool",
                mode: "System",
                count: args.nodeCount,
                vmSize: args.nodeSize,
                osType: "Linux",
                osDiskSizeGB: 30,
                type: "VirtualMachineScaleSets",
            }],
            linuxProfile: {
                adminUsername: args.adminUserName,
                ssh: {
                    publicKeys: [{
                        keyData: privateKey.publicKeyOpenssh,
                    }],
                },
            },
        }, { parent: this });

        // retrieve the admin credentials which contain the kubeconfig
        const adminCredentials = containerservice.listManagedClusterAdminCredentialsOutput({
            resourceGroupName: args.resourceGroupName,
            resourceName: cluster.name,
        }, { parent: this });

        // grant the 'contributor' role to the identity on the resource group
        const assignment = new authorization.RoleAssignment(`${name}-roleAssignment`, {
            principalId: identity.principalId,
            principalType: "ServicePrincipal",
            roleDefinitionId: "/providers/Microsoft.Authorization/roleDefinitions/b24988ac-6180-42a0-ab88-20f7382dd24c",
            scope: args.resourceGroupId,
        }, { parent: this });

        // kubeconfig
        this.kubeconfig = pulumi.secret(adminCredentials.apply(adminCredentials => Buffer.from(adminCredentials.kubeconfigs?.[0]?.value, "base64").toString("utf8")));
        this.clusterName = cluster.name
    }
};
