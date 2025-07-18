// Pulumi-published packages
import * as pulumi from "@pulumi/pulumi";
import * as resources from "@pulumi/azure-native/resources";
import * as k8s from "@pulumi/kubernetes";

import { K8sMonitor } from "@pulumi-pequod/k8sdatadog";
import { StackSettings } from "@pulumi-pequod/stackmgmt";

// Custom component resources
import { K8sCluster } from "./k8scluster"; // TODO: maybe move to central artifactory

// Typescript modules
import * as config from "./config";

const baseName = config.baseName;
const rgName = `${baseName}-rg`

const resourceGroup = new resources.ResourceGroup(rgName, { resourceGroupName: rgName } );

const cluster = new K8sCluster(baseName, {
    adminUserName: config.adminUserName,
    k8sVersion: config.k8sVersion,
    nodeCount: config.nodeCount,
    nodeSize: config.nodeSize,
    resourceGroupName: resourceGroup.name,
    resourceGroupId: resourceGroup.id,
})

const k8sProvider = new k8s.Provider("k8sprovider", {
    kubeconfig: cluster.kubeconfig
})

const datadogK8sAgent = new K8sMonitor(baseName, {
    datadogApiKey: config.apiKey,
}, {provider: k8sProvider})

const stackmgmt = new StackSettings(baseName, {driftManagement: config.driftManagement})

export const k8sClusterName = cluster.clusterName;
export const kubeconfig = cluster.kubeconfig;
export const datadogDashboard = k8sClusterName.apply(name => `https://app.datadoghq.com/dash/integration/86/kubernetes---overview?refresh_mode=sliding&tpl_var_cluster%5B0%5D=${name}&live=true`.toLowerCase())
