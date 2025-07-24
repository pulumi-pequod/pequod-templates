import * as pulumi from "@pulumi/pulumi";
import * as azure_native from "@pulumi/azure-native";
import { StackSettings } from "stackmgmt";
import { AppBuildDeploy } from "containerapps";

const config = new pulumi.Config();
const insightsSku = config.get("insightsSku") || "PerGB2018";
const appIngressPort = config.getNumber("appIngressPort") || 80;
const platform = config.get("platform") || "linux/amd64";

// Create a Resource Group
const resourceGroup = new azure_native.resources.ResourceGroup("resourceGroup");

// Create a Container App and deploy a custom Docker image
const app = new AppBuildDeploy("app", {
    resourceGroupName: resourceGroup.name,
    appPath: "./app",
    platform: platform,
    insightsSku: insightsSku,
    appIngressPort: appIngressPort,
});

// Configure stack settings
const stackSettings = new StackSettings("stacksettings");

// Export the endpoint as an output
export const endpoint = pulumi.interpolate`https://${app.containerAppFqdn}`;
