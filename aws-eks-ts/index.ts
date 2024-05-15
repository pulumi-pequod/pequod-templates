import * as pulumi from "@pulumi/pulumi";
import * as awsx from "@pulumi/awsx";
import * as eks from "@pulumi/eks";
import { K8sMonitor } from "@pequod/k8sdatadog";
import { StackSettings } from "@pequod/stackmgmt";

// Grab some values from the Pulumi configuration (or use default values)
const config = new pulumi.Config();
const minClusterSize = config.getNumber("minClusterSize") || 3;
const maxClusterSize = config.getNumber("maxClusterSize") || 6;
const desiredClusterSize = config.getNumber("desiredClusterSize") || 3;
const eksNodeInstanceType = config.get("eksNodeInstanceType") || "t3.medium";
const vpcNetworkCidr = config.get("vpcNetworkCidr") || "10.0.0.0/16";
const apiKey = config.requireSecret("datadogApiKey")

const baseName = `${pulumi.getProject()}-${pulumi.getOrganization()}`

// Create a new VPC
const eksVpc = new awsx.ec2.Vpc(`${baseName}-vpc`, {
    enableDnsHostnames: true,
    cidrBlock: vpcNetworkCidr,
    natGateways: {
        strategy: awsx.ec2.NatGatewayStrategy.Single
    }
});

// Create the EKS cluster
const eksCluster = new eks.Cluster(`${baseName}-eks`, {
    // Put the cluster in the new VPC created earlier
    vpcId: eksVpc.vpcId,
    // Public subnets will be used for load balancers
    publicSubnetIds: eksVpc.publicSubnetIds,
    // Private subnets will be used for cluster nodes
    privateSubnetIds: eksVpc.privateSubnetIds,
    // Change configuration values to change any of the following settings
    instanceType: eksNodeInstanceType,
    desiredCapacity: desiredClusterSize,
    minSize: minClusterSize,
    maxSize: maxClusterSize,
    // Do not give the worker nodes public IP addresses
    nodeAssociatePublicIpAddress: false,
    // Change these values for a private cluster (VPN access required)
    endpointPrivateAccess: false,
    endpointPublicAccess: true,
});

const datadogK8sAgent = new K8sMonitor(baseName, {
    apiKey: apiKey,
}, {provider: eksCluster.provider})

const stackmgmt = new StackSettings(baseName, {driftManagement: config.get("driftManagement")})

// Export some values 
export const kubeconfig = pulumi.secret(eksCluster.kubeconfig);
export const datadogDashboard = eksCluster.eksCluster.name.apply(name => `https://app.datadoghq.com/dash/integration/86/kubernetes---overview?refresh_mode=sliding&tpl_var_cluster%5B0%5D=${name}&live=true`.toLowerCase())