package main

import (
	"fmt"
	"github.com/pulumi-pequod/pequod-mlc-stackmgmt"
	"github.com/pulumi/pulumi-awsx/sdk/v2/go/awsx/ecr"
	"github.com/pulumi/pulumi-kubernetes/sdk/v4/go/kubernetes"
	corev1 "github.com/pulumi/pulumi-kubernetes/sdk/v4/go/kubernetes/core/v1"
	metav1 "github.com/pulumi/pulumi-kubernetes/sdk/v4/go/kubernetes/meta/v1"
	"github.com/pulumi/pulumi/sdk/v3/go/pulumi"
)

//import { StackSettings } from "@pequod/stackmgmt";

func main() {
	pulumi.Run(func(ctx *pulumi.Context) error {
		config := GetConfig(ctx)

		imageRepository, err := ecr.NewRepository(ctx, "imageRepository", &ecr.RepositoryArgs{
			ForceDelete: pulumi.Bool(true),
		})
		if err != nil {
			return err
		}

		image, err := ecr.NewImage(ctx, "image", &ecr.ImageArgs{
			RepositoryUrl: imageRepository.Url,
			Context:       pulumi.StringPtr("./app"),
			Platform:      pulumi.StringPtr("linux/amd64"),
		})
		if err != nil {
			return err
		}

		k8sProvider, err := kubernetes.NewProvider(ctx, "k8s-provider", &kubernetes.ProviderArgs{
			Kubeconfig:        config.Kubeconfig,
			DeleteUnreachable: pulumi.Bool(true),
		})
		if err != nil {
			return err
		}

		containerNamespace, err := corev1.NewNamespace(ctx, config.BaseName, nil, pulumi.Provider(k8sProvider))
		if err != nil {
			return err
		}

		containerNsName := containerNamespace.Metadata.ApplyT(func(output metav1.ObjectMeta) *string {
			return output.Name
		}).(pulumi.StringPtrOutput)

		frontend, err := NewServiceDeployment(ctx, "frontend", &ServiceDeploymentArgs{
			Replicas:          pulumi.Int(2),
			Image:             image.ImageUri,
			Namespace:         containerNsName,
			ContainerPort:     pulumi.Int(8080),
			HostPort:          pulumi.Int(80),
			AllocateIpAddress: true,
			EnvVars: corev1.EnvVarArray{
				corev1.EnvVarArgs{
					Name:  pulumi.String("ESC_ENV_NAME"),
					Value: pulumi.String(config.EscEnvName),
				},
				corev1.EnvVarArgs{
					Name:  pulumi.String("PULUMI_ACCESS_TOKEN"),
					Value: config.PulumiAccessToken,
				},
			},
		}, pulumi.Provider(k8sProvider))
		if err != nil {
			return err
		}

		//const stackmgmt = new StackSettings(baseName, {driftManagement: driftManagement, pulumiAccessToken: pulumiAccessToken})

		url := frontend.IpAddress.ApplyT(func(ipAddr *string) string {
			return fmt.Sprint("http://", *ipAddr)
		}).(pulumi.StringOutput)
		ctx.Export("frontendIP", url)

		return nil
	})
}
