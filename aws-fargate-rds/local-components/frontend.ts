import * as pulumi from "@pulumi/pulumi";
import { ComponentResource, ComponentResourceOptions, interpolate, Output } from "@pulumi/pulumi";
import { ec2, ecs, iam, lb } from "@pulumi/aws";


// Interface for Frontend
export interface FrontendArgs {
  vpcId: string | Output<any>;
  subnetIds: string[] | Output<string>[];
  ecsClusterName: string | Output<any>;
  ecsClusterArn: string | Output<any>;
  dbHost: string | Output<any>;
  dbName: string | Output<any>;
  dbUser: string | Output<any>;
  dbPassword: string | Output<any>;
  datadogApiKey: string | Output<any>;
}

// Creates Frontend elements (e.g. security group, load balancer, ecs task)
export class Frontend extends ComponentResource {
  public readonly frontendUrl: Output<string>;
  public readonly datadogDashboardAppContainer: Output<string>;
  public readonly datadogDashboardEcsCluster: Output<string>;

  constructor(name: string, args: FrontendArgs, opts?: ComponentResourceOptions) {
    super("custom:resource:Frontend", name, args, opts);

    // Gather subnet IDs from the VPC
    const vpcId = args.vpcId
    const subnetIds = args.subnetIds

    // Owner tag
    const tags = { "Owner": pulumi.getOrganization() }

    // Create security group for accessing the application.
    const feSgName = `${name}-fe-sg`
    const feSecGroup = new ec2.SecurityGroup(feSgName, {
        vpcId: vpcId,
        description: "Allow all HTTP(S) traffic.",
        tags: { "Name": feSgName, "Owner": pulumi.getOrganization() },
        ingress: [
            {
                cidrBlocks: ["0.0.0.0/0"],
                fromPort: 443,
                toPort: 443,
                protocol: "tcp",
                description: "Allow HTTPS."
            },
            {
                cidrBlocks: ["0.0.0.0/0"],
                fromPort: 80,
                toPort: 80,
                protocol: "tcp",
                description: "Allow HTTP."
            }
        ],
        egress: [{
            protocol: "-1",
            fromPort: 0,
            toPort: 0,
            cidrBlocks: ["0.0.0.0/0"],
        }]
    }, {parent: this})

    // Load balancer to front the application.
    const alb = new lb.LoadBalancer(`${name}-alb`, {
      securityGroups: [feSecGroup.id],
      subnets: subnetIds,
      tags: tags,
    }, {parent: this});

    const atg = new lb.TargetGroup(`${name}-tg`, {
      port: 80,
      protocol: "HTTP",
      targetType: "ip",
      vpcId: vpcId,
      healthCheck: {
        healthyThreshold: 2,
        interval: 5,
        timeout: 4,
        protocol: "HTTP",
        matcher: "200-399"
      },
      tags: tags,
    }, {parent: this})

    const wl = new lb.Listener(`${name}-listener`, {
      loadBalancerArn: alb.arn,
      port: 80,
      defaultActions: [{
        type: "forward",
        targetGroupArn: atg.arn
      }],
      tags: tags,
    }, {parent: this})

    // Role and ECS task and service definition.
    const role = new iam.Role(`${name}-task-role`, {
      assumeRolePolicy: JSON.stringify({
        'Version': '2008-10-17',
        'Statement': [{
          'Sid': '',
          'Effect': 'Allow',
          'Principal': {
            'Service': 'ecs-tasks.amazonaws.com'
          },
          'Action': 'sts:AssumeRole',
        }]
      }),
      tags: tags,
    }, {parent: this});

    const rpa = new iam.RolePolicyAttachment(`${name}-task-policy`, {
      role: role.name,
      policyArn: 'arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy',
    }, {parent: this})

    const taskName = `${name}-app-task`
    const appContainerName = `${name}-app-container`
    const datadogContinerName = `${name}-datadog`

    const containerDefinitions = 
      pulumi.all([args.dbHost, args.dbName, args.dbUser, args.dbPassword, args.datadogApiKey]).apply(([dbHost, dbName, dbUser, dbPassword, datadogApiKey]) => 
        JSON.stringify(
        [
          // Application container definition
          {
            'name': appContainerName,
            'image': 'wordpress',
            'portMappings': [{
                'containerPort': 80,
                'hostPort': 80,
                'protocol': 'tcp' 
            }],
            'environment': [
              {
                  'name': 'WORDPRESS_DB_HOST',
                  'value': dbHost
              },
              {
                  'name': 'WORDPRESS_DB_NAME',
                  'value': dbName
              },
              {
                  'name': 'WORDPRESS_DB_USER',
                  'value': dbUser
              },
              {
                  'name': 'WORDPRESS_DB_PASSWORD',
                  'value': dbPassword
              }
            ]
          },
          // Datadog agent
          {
            "name": datadogContinerName,
            "image": "datadog/agent:latest",
            "essential": true,
            "environment": [
                {
                    "name": "DD_API_KEY",
                    "value": `${datadogApiKey}`
                },
                {
                    "name": "ECS_FARGATE",
                    "value": "true"
                }
            ]
          }
        ])
      )

    const taskDefinition = new ecs.TaskDefinition(taskName, {
      family: "fargate-task-definition",
      cpu: "256",
      memory: "512",
      networkMode: "awsvpc",
      requiresCompatibilities: ["FARGATE"],
      executionRoleArn: role.arn,
      containerDefinitions: containerDefinitions,
      tags: tags,
    }, {parent: this})

    const service = new ecs.Service(`${name}-app-svc`, {
      cluster: args.ecsClusterArn,
      desiredCount: 1,
      launchType: "FARGATE",
      taskDefinition: taskDefinition.arn,
      networkConfiguration: {
        assignPublicIp: true,
        subnets: subnetIds,
        securityGroups: [feSecGroup.id]
      },
      loadBalancers: [{
        targetGroupArn: atg.arn,
        containerName: appContainerName,
        containerPort: 80
      }],
      tags: tags,
    }, {parent: this})

    this.frontendUrl = interpolate`http://${alb.dnsName}`
    this.datadogDashboardAppContainer = interpolate`https://app.datadoghq.com/dash/integration/30657/containers---overview?tpl_var_scope%5B0%5D=container_name%3A${appContainerName}`
    this.datadogDashboardEcsCluster = interpolate`https://app.datadoghq.com/dash/integration/30657/containers---overview?tpl_var_scope%5B0%5D=cluster_name%3A${args.ecsClusterName}`
    this.registerOutputs({});
  }
}
    