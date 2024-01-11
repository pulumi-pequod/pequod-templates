import { Config, getOrganization, getProject, getStack, StackReference } from "@pulumi/pulumi";

const config = new Config()

export const baseName = config.get("baseName") || `${getProject()}-${getStack()}`
export const driftManagement = config.get("driftManagement") || "Correct"

// Get stack name of the base k8s infra to deploy to and get the kubeconfig for the cluster.
const baseInfraStackName = config.get("baseInfraStackName") || "shared-dev-eks/dev"
const k8sStackName = `${getOrganization()}/${baseInfraStackName}`
const k8sStackRef = new StackReference(k8sStackName)

export const kubeconfig = k8sStackRef.requireOutput("kubeconfig") 

const pulumiServiceConfig = new Config("pulumiservice")
export const pulumiAccessToken = pulumiServiceConfig.get("accessToken")
