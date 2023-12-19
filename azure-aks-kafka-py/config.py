from pulumi import Config, get_project
from pulumi_tls import PrivateKey

config = Config()

base_name = config.get("baseName") or "baseinfra"

k8s_version = config.get('k8sVersion') or '1.24.3'

admin_username = config.get('adminUserName') or 'testuser'

generated_key_pair = PrivateKey('ssh-key',
    algorithm='RSA', rsa_bits=4096)

ssh_public_key = config.get('sshPublicKey') or \
    generated_key_pair.public_key_openssh

node_count = config.get_int('nodeCount') or 3

node_size = config.get('nodeSize') or 'Standard_B2s'

kafka_cluster_name = config.get("kafkaClusterName") or get_project()

kafka_topics = config.get_object("kafkaTopics") or ["orders", "receipts", "returns"]; 

datadog_api_key = config.require_secret("datadogApiKey")

drift_management = config.get("driftManagement")
