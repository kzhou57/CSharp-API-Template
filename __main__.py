"""An Azure Python Pulumi program"""

import pulumi
from pulumi import ResourceOptions, StackReference
from pulumi_azure import core, storage, mssql
from pulumi_azure.core import ResourceGroup
from pulumi_azure.authorization import Assignment
from pulumi_azure.containerservice import KubernetesCluster, Registry
from pulumi_azure.network import VirtualNetwork, Subnet
from pulumi_kubernetes import Provider
from pulumi_kubernetes.apps.v1 import Deployment
from pulumi_kubernetes.core.v1 import Service, Namespace

config = pulumi.Config()
SA_PASSWORD = config.require('sa_password')

infra = StackReference(f"kzhou57/pulumi-azure-quickstart/dev")

# TODO read from output
ACR_NAME = 'kzhouacr'

rg = ResourceGroup.get('rg', id=infra.get_output('resource_group_id'))

custom_provider = Provider(
    "k8s", kubeconfig=infra.get_output('kubeconfig')
)

# K8s SQL server csharpexamplesql
name = 'csharpexamplesql'
sql_namespace = Namespace(name,
    metadata={},
    __opts__=ResourceOptions(provider=custom_provider)
)

appLabels = { "appClass": name }

sql_deployment = Deployment(name,
            metadata={
                "labels": appLabels
            },
            spec={
                "selector": {
                    "match_labels": appLabels
                },
                "replicas": 1,
                "template": {
                    "metadata": {
                        "labels": appLabels
                    },
                    "spec": {
                        "containers": [
                            {
                                "name": name,
                                "image": "mcr.microsoft.com/mssql/server:2017-latest-ubuntu",
                                "ports": [
                                    {
                                        "name": "sql",
                                        "containerPort": 1433
                                    }
                                ],
                                "env": [
                                    {
                                        "name": "ACCEPT_EULA",
                                        "value": "Y"
                                    },
                                    {
                                        "name": "SA_PASSWORD",
                                        "value": SA_PASSWORD
                                    },
                                    {
                                        "name": "MSSQL_PID",
                                        "value": "Developer"
                                    }

                                ]
                            }
                        ]
                    }
                }
            },
            __opts__=ResourceOptions(provider=custom_provider)
            )

sql_service = Service(name,
    metadata={
        "labels": appLabels
    },
    spec={
        "ports": [
            {
                "name": "sql",
                "port": 1433
            }
        ],
        "selector": appLabels,
        "type": "LoadBalancer",
    },
    __opts__=ResourceOptions(provider=custom_provider)
)

# K8s service csharpexample
name = 'csharpexample'
namespace = Namespace(name,
    metadata={},
    __opts__=ResourceOptions(provider=custom_provider)
)

appLabels = { "appClass": name }

deployment = Deployment(name,
            metadata={
                "labels": appLabels
            },
            spec={
                "selector": {
                    "match_labels": appLabels
                },
                "replicas": 1,
                "template": {
                    "metadata": {
                        "labels": appLabels
                    },
                    "spec": {
                        "containers": [
                            {
                                "name": name,
                                "image": ACR_NAME + ".azurecr.io/kzhoucsharpapitemplate:5",
                                "ports": [
                                    {
                                        "name": "http",
                                        "containerPort": 80
                                    }
                                ],
                                "env": [
                                    {
                                        "name": "ConnectionStrings",
                                        # read from infra module
                                        # "value": infra.get_output('sql_domain_name').apply(lambda sql_domain_name: f"TemplateAPI=Server={sql_domain_name},1433;Database=TemplateApi;User=sysadmin;Password={SA_PASSWORD};ConnectRetryCount=0")
                                        "value": sql_service.status.apply(lambda status: f"TemplateAPI=Server={status['load_balancer']['ingress'][0]['ip']},1433;Database=TemplateApi;User=sa;Password={SA_PASSWORD};ConnectRetryCount=0")
                                    },
                                    {
                                        "name": "FooBar",
                                        "value": "Foo4"
                                    }
                                ]
                            }
                        ]
                    }
                }
            },
            __opts__=ResourceOptions(provider=custom_provider)
            )

service = Service(name,
    metadata={
        "labels": appLabels
    },
    spec={
        "ports": [
            {
                "name": "http",
                "port": 80
            }
        ],
        "selector": appLabels,
        "type": "LoadBalancer",
    },
    __opts__=ResourceOptions(provider=custom_provider)
)

# Export
pulumi.export('deployment_name', deployment.metadata.apply(lambda resource: resource['name']))
pulumi.export('service_name', service.metadata.apply(lambda resource: resource['name']))
pulumi.export('service_public_endpoint', service.status.apply(lambda status: status['load_balancer']['ingress'][0]['ip']))
pulumi.export('sql_server_public_endpoint', sql_service.status.apply(lambda status: status['load_balancer']['ingress'][0]['ip']))
