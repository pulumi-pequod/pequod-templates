/* 
 * Deploys:
 * - Network: VPC, Subnets, Security Groups
 * - DB Backend: MySQL RDS
 * - Fargate ECS app
 */

// Pulumi SDKs
import * as pulumi from "@pulumi/pulumi";
import { ec2, ecs } from "@pulumi/aws";

// Platform team managed components
import { StackSettings } from "@pulumi-pequod/stackmgmt";

// Local components
import { Network } from "./local-components/aws_network";
import { Db } from "./local-components/aws_rds";
import { Frontend } from "./local-components/frontend";

// Local Modules
import { nameBase, dbName, dbUser, dbPassword, datadogApiKey, driftManagement } from "./config";

// Create an AWS VPC and subnets, etc
const network = new Network(`${nameBase}-net`, {})

// RDS acess security group.
const rdsSgName = `${nameBase}-rds-sg`
const rdsSecGroup = new ec2.SecurityGroup(rdsSgName, {
    vpcId: network.vpcId,
    description: "Allow DB client access.",
    tags: { "Name": rdsSgName },
    ingress: [{
        cidrBlocks: ["0.0.0.0/0"],
        fromPort: 3306,
        toPort: 3306,
        protocol: "tcp",
        description: "Allow RDS access."
    }],
    egress: [{
        protocol: "-1",
        fromPort: 0,
        toPort: 0,
        cidrBlocks: ["0.0.0.0/0"],
    }]
});

// Create a backend DB instance
const db = new Db(`${nameBase}-db`, {
    dbName: dbName,
    dbUser: dbUser,
    dbPassword: dbPassword,
    subnetIds: network.subnetIds,
    securityGroupIds: [rdsSecGroup.id]
});

// Create an ECS cluster onto which applications can be deployed.
const ecsCluster = new ecs.Cluster(`${nameBase}-ecs`)

export const vpcId = network.vpcId;
const ecsClusterName = ecsCluster.name;
export const ecsClusterArn = ecsCluster.arn;
export const dbHost = db.dbAddress;
export { dbName, dbUser, dbPassword};

// Create a frontend which consists of various resources like security groups, load balancers, ecs task
const frontend = new Frontend(`${nameBase}-fe`, {
    vpcId: network.vpcId,
    subnetIds: network.subnetIds,
    ecsClusterName: ecsClusterName,
    ecsClusterArn: ecsCluster.arn,
    dbHost: db.dbAddress,
    dbName: db.dbName,
    dbUser: db.dbUser,
    dbPassword: db.dbPassword,
    datadogApiKey: datadogApiKey
})

// Handle stack management settings for deployments, tags, etc.
const stackmgmt = new StackSettings(`stackmgmt`, {driftManagement: driftManagement})
  
export const frontendUrl = frontend.frontendUrl;
export const datadogAppContainerDashboard = frontend.datadogDashboardAppContainer;
export const datadogEcsDashboard = frontend.datadogDashboardEcsCluster;