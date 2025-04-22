#  Copyright 2016-2020, Pulumi Corporation.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import pulumi
import pulumi_kubernetes as k8s
from pulumi_pequod_stackmgmt import StackSettings, StackSettingsArgs

# Local component
from service_deployment import ServiceDeployment
# Local modules
import config

base_name = config.base_name
k8s_provider = k8s.Provider('k8s-provider', kubeconfig=config.kubeconfig, delete_unreachable=True)

guestbook_ns = k8s.core.v1.Namespace(base_name, 
    pulumi.ResourceOptions(provider=k8s_provider))
guestbook_ns_name = guestbook_ns.metadata.name

ServiceDeployment(
    "redis-leader",
    namespace=guestbook_ns_name,
    image="redis",
    ports=[6379], 
    opts=pulumi.ResourceOptions(provider=k8s_provider))

ServiceDeployment(
    "redis-replica",
    namespace=guestbook_ns_name,
    image="pulumi/guestbook-redis-replica",
    ports=[6379],
    opts=pulumi.ResourceOptions(provider=k8s_provider))

frontend = ServiceDeployment(
    "frontend",
    namespace=guestbook_ns_name,
    image="pulumi/guestbook-php-redis",
    replicas=3,
    ports=[80],
    allocate_ip_address=True,
    opts=pulumi.ResourceOptions(provider=k8s_provider))

stackmgmt = StackSettings(base_name, 
                          drift_management=config.drift_management,
                          )

pulumi.export("guestbook_url", pulumi.Output.concat("http://",frontend.ip_address))
