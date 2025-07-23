// Import required libraries, update package.json if you add more.
import * as pulumi from "@pulumi/pulumi"; // Required for Config and interpolation

// Import the component abstraction for deploying a containerized application
// and the stack management component.
import { StackSettings } from "@pulumi-pequod/stackmgmt";
import { AppImageDeploy } from "@pulumi-pequod/container-services";

// Get stack config if provided, otherwise use default values.
const config = new pulumi.Config();
const cpu = config.getNumber("cpu") || 256; // Default CPU units
const memory = config.getNumber("memory") || 512; // Default memory in MiB

// Use component abstraction to create docker image, push to ECR and deploy to ECS.
const appDeployment = new AppImageDeploy("appDeployment", {
    dockerFilePath: "./app",
    cpu: cpu,
    memory: memory,
});

// Manage stack settings in Pulumi Cloud.
const stackmgmt = new StackSettings(`stackmgmt`);

// The URL at which the container's HTTP endpoint will be available.
export const appUrl = pulumi.interpolate`http://${appDeployment.loadbalancerDnsName}`;
