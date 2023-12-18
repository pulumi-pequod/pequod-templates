import * as pulumi from "@pulumi/pulumi";
import * as azure from "@pulumi/azure";
import * as random from "@pulumi/random";

const config = new pulumi.Config();
const azConfig = new pulumi.Config("azure-native")

export const baseName = pulumi.getProject();

export var k8sVersion = config.get("k8sVersion") || azure.containerservice.getKubernetesServiceVersions({
        location: azConfig.require("location")
    }).then(current => current.latestVersion)

export const password = config.get("password") || new random.RandomPassword(`${baseName}-pw`, {
    length: 20,
    special: true,
}).result;

export const adminUserName = config.get("adminUserName") || "testuser";

export const nodeCount = config.getNumber("nodeCount") || 2;

export const nodeSize = config.get("nodeSize") || "Standard_D2_v2";

export const kafkaClusterName = config.get("kafkaClusterName") || pulumi.getProject()

export const kafkaTopics = config.getObject<string[]>("kafkaTopics") || ["orders", "receipts", "returns"]; 

export const apiKey = config.requireSecret("datadogApiKey")

export const driftManagement = config.get("driftManagement")
