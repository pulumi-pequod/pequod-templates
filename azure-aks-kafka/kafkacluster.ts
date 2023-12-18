import * as pulumi from "@pulumi/pulumi";
import * as confluent from "@pulumi/confluentcloud";

// Component resource to stand up Pequod's preferred Kafka.
// Currently, it uses Confluent.

export interface KafkaClusterArgs {
    kafkaClusterName: string;
    kafkaTopics: string[];
    region?: string;
}

export class KafkaCluster extends pulumi.ComponentResource {
    public readonly envId: pulumi.Output<string>;

    constructor(name: string, args: KafkaClusterArgs, opts?: pulumi.ComponentResourceOptions) {

        super("custom:resource:KafkaCluster", name, args, opts);

        const clusterRegion = args.region || "centralus"

        // Create a Confluent environment which is a container for the other Confluent resources
        const confluentEnvName = `${name}-environment`
        const env = new confluent.Environment(confluentEnvName, {
            displayName: confluentEnvName
        }, { parent: this });

        // Create a standard Kafka cluster with multi-zone availability and us-west-2
        const cluster = new confluent.KafkaCluster(`${name}-${args.kafkaClusterName}`, {
            displayName: args.kafkaClusterName,
            availability: "SINGLE_ZONE",
            cloud: "AZURE",
            region: clusterRegion,
            environment: {
                id: env.id,
            },
            standard: {}
        }, { parent: this });

        // Create the admin-level service account used to create Kafka topic and producer and consumer accounts. 
        // This app manager account is similar to the "DBA" account in relational databases or the root account in Linux
        const serviceAccount = new confluent.ServiceAccount(`${name}-app-manager`, {
            description: "Service account to manage 'inventory' Kafka cluster",
        }, { parent: this });

        const roleBinding = new confluent.RoleBinding(`${name}-app-manager-kafka-cluster-admin`, {
            principal: pulumi.interpolate`User:${serviceAccount.id}`,
            roleName: "CloudClusterAdmin",
            crnPattern: cluster.rbacCrn,
        }, { parent: this });

        const managerApiKey = new confluent.ApiKey(`${name}-app-manager-kafka-api-key`, {
            displayName: "app-manager-kafka-api-key",
            description: `Kafka API Key that is managed by Pulumi stack, ${pulumi.getOrganization()}/${pulumi.getProject()}/${pulumi.getStack()}`,
            owner: {
                id: serviceAccount.id,
                kind: serviceAccount.kind,
                apiVersion: serviceAccount.apiVersion,
            },
            managedResource: {
                id: cluster.id,
                apiVersion: cluster.apiVersion,
                kind: cluster.kind,
                environment: {
                    id: env.id,
                },
            }
        }, {
            dependsOn: roleBinding,
            parent: this
        });

        //  Create a consumer service account and give that account permissions to write to the topic
        const producerAccount = new confluent.ServiceAccount(`${name}-producer`, {
            description: `Service account to produce to topics of ${args.kafkaClusterName} Kafka cluster`,
        }, { parent: this });

        const producerApiKey = new confluent.ApiKey(`${name}-producer-api-key`, {
            owner: {
                id: producerAccount.id,
                kind: producerAccount.kind,
                apiVersion: producerAccount.apiVersion,
            },
            managedResource: {
                id: cluster.id,
                apiVersion: cluster.apiVersion,
                kind: cluster.kind,
                environment: {
                    id: env.id,
                },
            },
        }, { parent: this });

        // Create consumer account which will read messages from Kafka topic
        const consumerAccount = new confluent.ServiceAccount(`${name}-consumer`, {
            description: `Service account to consume from topics of ${args.kafkaClusterName} Kafka cluster`,
        }, { parent: this });

        const consumerApiKey = new confluent.ApiKey(`${name}-consumer-api-key`, {
            owner: {
                id: consumerAccount.id,
                kind: consumerAccount.kind,
                apiVersion: consumerAccount.apiVersion,
            },
            managedResource: {
                id: cluster.id,
                apiVersion: cluster.apiVersion,
                kind: cluster.kind,
                environment: {
                    id: env.id,
                },
            },
        }, { parent: this });

        new confluent.KafkaAcl(`${name}-consumer-read-group-acl`, {
            kafkaCluster: {
                id: cluster.id,
            },
            resourceType: "GROUP",
            resourceName: "confluent_cli_consumer_",
            patternType: "PREFIXED",
            principal: pulumi.interpolate`User:${consumerAccount.id}`,
            host: "*",
            operation: "READ",
            permission: "ALLOW",
            restEndpoint: cluster.restEndpoint,
            credentials: {
                key: managerApiKey.id,
                secret: managerApiKey.secret,
            }
        }, { parent: this });

        // Create topics and manage permissions.
        for (let kafkaTopic of args.kafkaTopics) {

            // Create Kafka topic using the cluster admin service account credentials created above
            const topic = new confluent.KafkaTopic(`${name}-${kafkaTopic}`, {
                kafkaCluster: {
                    id: cluster.id,
                },
                topicName: kafkaTopic,
                restEndpoint: cluster.restEndpoint,
                credentials: {
                    key: managerApiKey.id,
                    secret: managerApiKey.secret,
                },
            }, { parent: this });

            // Give produce write permissions to the topic
            new confluent.KafkaAcl(`${name}-${kafkaTopic}-app-producer-write`, {
                kafkaCluster: {
                    id: cluster.id,
                },
                resourceType: "TOPIC",
                resourceName: topic.topicName,
                patternType: "LITERAL",
                principal: pulumi.interpolate`User:${producerAccount.id}`,
                host: "*",
                operation: "WRITE",
                permission: "ALLOW",
                restEndpoint: cluster.restEndpoint,
                credentials: {
                    key: managerApiKey.id,
                    secret: managerApiKey.secret,
                }
            }, { parent: this })

            // Give consumer access to the topic
            new confluent.KafkaAcl(`${name}-${kafkaTopic}-consumer-read-topic-acl`, {
                kafkaCluster: {
                    id: cluster.id,
                },
                resourceType: "TOPIC",
                resourceName: topic.topicName,
                patternType: "LITERAL",
                principal: pulumi.interpolate`User:${consumerAccount.id}`,
                host: "*",
                operation: "READ",
                permission: "ALLOW",
                restEndpoint: cluster.restEndpoint,
                credentials: {
                    key: managerApiKey.id,
                    secret: managerApiKey.secret,
                }
            }, { parent: this });
        };

        this.envId = env.id;
        this.registerOutputs({});
    }
};
