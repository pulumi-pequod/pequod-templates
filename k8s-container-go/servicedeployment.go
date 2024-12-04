package main

import (
	appsv1 "github.com/pulumi/pulumi-kubernetes/sdk/v4/go/kubernetes/apps/v1"
	corev1 "github.com/pulumi/pulumi-kubernetes/sdk/v4/go/kubernetes/core/v1"
	metav1 "github.com/pulumi/pulumi-kubernetes/sdk/v4/go/kubernetes/meta/v1"
	"github.com/pulumi/pulumi/sdk/v3/go/pulumi"
)

type ServiceDeploymentArgs struct {
	Image             pulumi.StringInput
	Namespace         pulumi.StringPtrInput
	resources         *corev1.ResourceRequirementsPtrInput
	Replicas          pulumi.IntInput
	ContainerPort     pulumi.IntInput
	HostPort          pulumi.IntInput
	AllocateIpAddress pulumi.Bool
	IsMinikube        pulumi.Bool
	EnvVars           []corev1.EnvVarInput
}

// ServiceDeployment is an example abstraction that uses a class to fold together the common pattern of a
// Kubernetes Deployment and its associated Service object.
type ServiceDeployment struct {
	pulumi.ResourceState

	Deployment *appsv1.Deployment
	Service    *corev1.Service
	IpAddress  pulumi.StringPtrOutput
}

func NewServiceDeployment(ctx *pulumi.Context, name string, serviceDeploymentArgs *ServiceDeploymentArgs, opts ...pulumi.ResourceOption) (*ServiceDeployment, error) {
	serviceDeployment := &ServiceDeployment{}
	err := ctx.RegisterComponentResource("k8sgo:service:ServiceDeployment", name, serviceDeployment, opts...)
	if err != nil {
		return nil, err
	}

	namespace := serviceDeploymentArgs.Namespace

	labels := pulumi.StringMap{"app": pulumi.String(name)}

	var resources corev1.ResourceRequirementsPtrInput
	if serviceDeploymentArgs.resources == nil {
		resources = corev1.ResourceRequirementsArgs{
			Requests: pulumi.StringMap{
				"cpu":    pulumi.String("100m"),
				"memory": pulumi.String("100Mi"),
			},
		}
	} else {
		resources = *serviceDeploymentArgs.resources
	}

	var envs corev1.EnvVarArray
	envs = corev1.EnvVarArray{
		corev1.EnvVarArgs{
			Name:  pulumi.String("GET_HOSTS_FROM"),
			Value: pulumi.String("dns"),
		},
	}
	container := corev1.ContainerArgs{
		Name:      pulumi.String(name),
		Image:     serviceDeploymentArgs.Image,
		Resources: resources,
		Env:       append(envs, serviceDeploymentArgs.EnvVars...),
		Ports: corev1.ContainerPortArray{
			corev1.ContainerPortArgs{
				ContainerPort: serviceDeploymentArgs.ContainerPort,
			},
		},
	}

	serviceDeployment.Deployment, err = appsv1.NewDeployment(ctx, name, &appsv1.DeploymentArgs{
		Metadata: &metav1.ObjectMetaArgs{
			Namespace: namespace,
		},
		Spec: appsv1.DeploymentSpecArgs{
			Selector: &metav1.LabelSelectorArgs{
				MatchLabels: labels,
			},
			Replicas: serviceDeploymentArgs.Replicas,
			Template: &corev1.PodTemplateSpecArgs{
				Metadata: &metav1.ObjectMetaArgs{
					Labels: labels,
				},
				Spec: &corev1.PodSpecArgs{
					Containers: corev1.ContainerArray{
						container,
					},
				},
			},
		},
	}, pulumi.Parent(serviceDeployment))
	if err != nil {
		return nil, err
	}

	var serviceType pulumi.String
	// Minikube does not implement services of type `LoadBalancer`; require the user to specify if we're
	// running on minikube, and if so, create only services of type ClusterIP.
	if serviceDeploymentArgs.AllocateIpAddress {
		if serviceDeploymentArgs.IsMinikube {
			serviceType = "ClusterIP"
		} else {
			serviceType = "LoadBalancer"
		}
	}
	serviceDeployment.Service, err = corev1.NewService(ctx, name, &corev1.ServiceArgs{
		Metadata: &metav1.ObjectMetaArgs{
			Labels:    labels,
			Name:      pulumi.String(name),
			Namespace: namespace,
		},
		Spec: &corev1.ServiceSpecArgs{
			Ports: &corev1.ServicePortArray{
				&corev1.ServicePortArgs{
					Port:       serviceDeploymentArgs.HostPort,
					TargetPort: serviceDeploymentArgs.ContainerPort,
				},
			},
			Selector: labels,
			Type:     serviceType,
		},
	}, pulumi.Parent(serviceDeployment))
	if err != nil {
		return nil, err
	}

	serviceDeployment.IpAddress = serviceDeployment.Service.Status.ApplyT(
		func(status *corev1.ServiceStatus) *string {
			if status.LoadBalancer.Ingress != nil {
				ingress := status.LoadBalancer.Ingress[0]
				if ingress.Hostname != nil {
					return ingress.Hostname
				}
				return ingress.Ip
			}

			return nil
		}).(pulumi.StringPtrOutput)

	err = ctx.RegisterResourceOutputs(serviceDeployment, pulumi.Map{
		"Deployment": serviceDeployment.Deployment,
		"Service":    serviceDeployment.Service,
		"IpAddress":  serviceDeployment.IpAddress,
	})
	if err != nil {
		return nil, err
	}

	return serviceDeployment, nil
}
