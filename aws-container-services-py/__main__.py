import pulumi
import pulumi_aws as aws
from pulumi_pequod_stackmgmt import StackSettings, StackSettingsArgs

from pulumi_pequod_container_services import AppImageDeploy, AppImageDeployArgs

config = pulumi.Config()
cpu = config.get_int("cpu") or 256 
memory = config.get_int("memory") or 512

# Use component abstraction to create docker image, push to ECR and deploy to ECS.
app_deployment = AppImageDeploy(f"app-deployment", AppImageDeployArgs(  
  docker_file_path="./app"
))

# Look up the ALB created by the component so we can get its ARN for WAF association.
# The ALB name is the hostname portion of the DNS name (everything before the first dot),
# with the trailing numeric load-balancer ID stripped off.
container_lb_arn = app_deployment.loadbalancer_dns_name.apply(
    lambda dns: dns.split(".")[0] if dns else ""
).apply(
    lambda host: host.rsplit("-", 1)[0] if host else ""
).apply(
    lambda name: aws.lb.get_load_balancer(name=name).arn if name else ""
)

# --- WAFv2 WebACL to protect the public-facing ALB ---
# Create a regional WAFv2 Web ACL with the AWS managed common rule set.
waf_acl = aws.wafv2.WebAcl(
    "container-lb-waf",
    scope="REGIONAL",
    description="WAF WebACL protecting the container-lb ALB",
    default_action=aws.wafv2.WebAclDefaultActionArgs(
        allow=aws.wafv2.WebAclDefaultActionAllowArgs(),
    ),
    rules=[
        aws.wafv2.WebAclRuleArgs(
            name="AWSManagedRulesCommonRuleSet",
            priority=1,
            override_action=aws.wafv2.WebAclRuleOverrideActionArgs(
                none=aws.wafv2.WebAclRuleOverrideActionNoneArgs(),
            ),
            statement=aws.wafv2.WebAclRuleStatementArgs(
                managed_rule_group_statement=aws.wafv2.WebAclRuleStatementManagedRuleGroupStatementArgs(
                    vendor_name="AWS",
                    name="AWSManagedRulesCommonRuleSet",
                ),
            ),
            visibility_config=aws.wafv2.WebAclRuleVisibilityConfigArgs(
                cloudwatch_metrics_enabled=True,
                metric_name="AWSManagedRulesCommonRuleSet",
                sampled_requests_enabled=True,
            ),
        ),
    ],
    visibility_config=aws.wafv2.WebAclVisibilityConfigArgs(
        cloudwatch_metrics_enabled=True,
        metric_name="container-lb-waf",
        sampled_requests_enabled=True,
    ),
)

# Associate the WAF WebACL with the ALB.
waf_association = aws.wafv2.WebAclAssociation(
    "container-lb-waf-association",
    resource_arn=container_lb_arn,
    web_acl_arn=waf_acl.arn,
)

# Manage stack settings using the centrally managed custom component.
stackmgmt = StackSettings("stacksettings") 

# Export URL for the service
pulumi.export("service_url", pulumi.Output.concat("http://",app_deployment.loadbalancer_dns_name))
