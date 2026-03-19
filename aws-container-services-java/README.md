# AWS Elastic Container Service (ECS) Java

Deploys:
- Docker Image to AWS ECR
- Fargate ECS app

## Setup

After creating a project from this template, run:
```bash
pulumi install
```
This generates the Java SDKs for the private registry components. Follow the printed instructions to copy the generated SDK sources into `src/` and then build with Maven.

## Demonstrated Capabilities
- Remote Pulumi component(s) (`AppImageDeploy`, `StackSettings`)

## Related Template(s)
- "aws-container-services-ts" can be used to compare this Java example with a TypeScript example
- "aws-container-services-py" can be used to compare this Java example with a Python example
- "aws-container-services-yaml" can be used to compare this Java example with a YAML example
