# K8s Container App Go

 Deploys:
 - AWS Elastic Container Registry (ECR)
 - Docker image
 - K8s application that consumes ESC data onto shared K8s infrastructure

## Demonstrated Capabilities
- Pulumi AWSx package
- Remote Pulumi component(s) (`ServiceDeployment`, `StackSettings`)

## Related Template(s)
By default, the shared k8s infrastructure is used
However, one can deploy the following templates and deploy onto that infrastructure:
- "aws-eks-*"
- "azure-aks-*"
- "gcp-gke-*"