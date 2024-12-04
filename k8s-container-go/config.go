package main

import (
	"fmt"
	"github.com/pulumi/pulumi/sdk/v3/go/pulumi"
	"github.com/pulumi/pulumi/sdk/v3/go/pulumi/config"
)

type Configs struct {
	BaseName          string
	DriftManagement   string
	EscEnvName        string
	Kubeconfig        pulumi.StringOutput
	PulumiAccessToken pulumi.StringOutput
}

func GetConfig(ctx *pulumi.Context) Configs {
	programConfig := config.New(ctx, "")

	baseName, err := programConfig.Try("baseName")
	if err != nil {
		baseName = fmt.Sprint(ctx.Project(), "-", ctx.Stack())
	}
	driftManagement, err := programConfig.Try("driftManagement")
	if err != nil {
		driftManagement = "Correct"
	}

	// The default set up for this template is to leverage the shared-k8s-cluster ESC environment for the kubeconfig.
	// However, if the kubeconfig is not found, then use the stack reference to get the kubeconfig.
	// It's not necessarily a real-world use-case, but provides a way to contrast ESC-based stack references and in-code stack references.
	// The big talking point here is using ESC means this project does not need to be aware of the k8s cluster's stack.
	// It just gets it as config.
	// This also enable testing use-cases since one can initialize a test stack and hand-copy a kubeconfig to use in the stack config file
	kubeconfig, err := programConfig.TrySecret("kubeconfig")
	// If no kubeconfig found in config (via ESC or otherwise), then use the stack reference to get the kubeconfig.
	if err != nil {
		// Get stack name of the base k8s infra to deploy to and get the kubeconfig for the cluster.
		baseInfraStackName, err := programConfig.Try("baseInfraStackName")
		if err != nil {
			baseInfraStackName = "shared-dev-eks/dev"
		}
		k8sStackName := fmt.Sprint(ctx.Organization(), "-", baseInfraStackName)
		k8sStackRef, err := pulumi.NewStackReference(ctx, k8sStackName, nil)
		if err != nil {
			panic(fmt.Sprint("failed stack reference from [", k8sStackName, "]"))
		}
		kubeconfigDetail, err := k8sStackRef.GetOutputDetails("kubeconfig")
		if err != nil {
			panic(fmt.Sprint("failed stack reference from [", k8sStackName, "]"))
		}
		kubeconfig = kubeconfigDetail.SecretValue.(pulumi.StringOutput)
	}

	pulumiServiceConfig := config.New(ctx, "pulumiservice")

	return Configs{
		BaseName:          baseName,
		DriftManagement:   driftManagement,
		EscEnvName:        programConfig.Get("escEnvName"),
		Kubeconfig:        kubeconfig,
		PulumiAccessToken: pulumiServiceConfig.GetSecret("accessToken"),
	}
}
