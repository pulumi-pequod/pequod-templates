import { Config, getOrganization, getProject, getStack, Output, StackReference } from "@pulumi/pulumi";

const config = new Config()

export const baseName = config.get("baseName") || `${getProject()}-${getStack()}`
export const driftManagement = config.get("driftManagement") || "Correct"
export const escEnvName = config.require("escEnvName") 

// The default set up for this template is to leverage the shared-k8s-cluster ESC environment for the kubeconfig.
// However, if the kubeconfig is not found, then use the stack reference to get the kubeconfig.
// It's not necessarily a real-world use-case, but provides a way to contrast ESC-based stack references and in-code stack references.
// The big talking point here is using ESC means this project does not need to be aware of the k8s cluster's stack.
// It just gets it as config. 
// This also enable testing use-cases since one can initialize a test stack and hand-copy a kubeconfig to use in the stack config file
export var kubeconfig: Output<string> | Output<any> | undefined
kubeconfig = config.getSecret("kubeconfig") 

// If no kubeconfig found in config (via ESC or otherwise), then use the stack reference to get the kubeconfig.
if (!kubeconfig) {
  // Get stack name of the base k8s infra to deploy to and get the kubeconfig for the cluster.
  const baseInfraStackName = config.get("baseInfraStackName") || "shared-dev-eks/dev"
  const k8sStackName = `${getOrganization()}/${baseInfraStackName}`
  const k8sStackRef = new StackReference(k8sStackName)
  kubeconfig = k8sStackRef.requireOutput("kubeconfig")
} 

const pulumiServiceConfig = new Config("pulumiservice")
export const pulumiAccessToken = pulumiServiceConfig.requireSecret("accessToken")
