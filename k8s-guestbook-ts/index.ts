import * as pulumi from "@pulumi/pulumi";
import * as k8s from "@pulumi/kubernetes";
import { StackSettings } from "@pequod/stackmgmt";

import { ServiceDeployment } from "./servicedeployment";
import { baseName, driftManagement, kubeconfig } from "./config";

const k8sProvider = new k8s.Provider('k8s-provider', {
  kubeconfig: kubeconfig,
  deleteUnreachable: true
})

const guestbookNamespace = new k8s.core.v1.Namespace(baseName, {}, {provider: k8sProvider})
const guestbookNsName = guestbookNamespace.metadata.name

const redisLeader = new ServiceDeployment("redis-leader", {
    image: "redis",
    namespace: guestbookNsName,
    ports: [6379],
}, { provider: k8sProvider });

const redisReplica = new ServiceDeployment("redis-replica", {
    image: "pulumi/guestbook-redis-replica",
    namespace: guestbookNsName,
    ports: [6379],
}, { provider: k8sProvider });

const frontend = new ServiceDeployment("frontend", {
    replicas: 3,
    image: "pulumi/guestbook-php-redis",
    namespace: guestbookNsName,
    ports: [80],
    allocateIpAddress: true,
}, { provider: k8sProvider });

const stackmgmt = new StackSettings(baseName, {driftManagement: driftManagement})

export const frontendIp = pulumi.interpolate`http://${frontend.ipAddress}`;
