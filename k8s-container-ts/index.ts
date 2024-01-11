import * as pulumi from "@pulumi/pulumi";
import * as k8s from "@pulumi/kubernetes";
import * as awsx from "@pulumi/awsx";
import { StackSettings } from "@pequod/stackmgmt";

import { ServiceDeployment } from "./servicedeployment";
import { baseName, driftManagement, kubeconfig } from "./config";

const imageRepository = new awsx.ecr.Repository("imageRepository", {
    forceDelete: true
});

const image = new awsx.ecr.Image("image", {
    repositoryUrl: imageRepository.url,
    context: "./app",
    platform: "linux/amd64"
});

const k8sProvider = new k8s.Provider('k8s-provider', {
  kubeconfig: kubeconfig,
  deleteUnreachable: true
})

const containerNamespace = new k8s.core.v1.Namespace(baseName, {}, {provider: k8sProvider})
const containerNsName = containerNamespace.metadata.name

const frontend = new ServiceDeployment("frontend", {
    replicas: 3,
    image: image.imageUri,
    namespace: containerNsName,
    containerPort: 8080,
    hostPort: 80,
    allocateIpAddress: true,
}, { provider: k8sProvider });

const stackmgmt = new StackSettings(baseName, {driftManagement: driftManagement})

export const frontendIp = pulumi.interpolate`http://${frontend.ipAddress}`;
