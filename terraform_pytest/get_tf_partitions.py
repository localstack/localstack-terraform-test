# Prints a JSON dict mapping the different partitions in the terraform-tests.yaml to their service
import json

import yaml


def get_partitions(services: list[str]):
    with open("terraform_pytest/service-partitions.yml") as f:
        service_partitions = yaml.load(f, Loader=yaml.FullLoader)
        mapping = []
        for service in services:
            if service in service_partitions.keys():
                partition_keys = service_partitions[service].keys()
                for partition in partition_keys:
                    mapping.append({"service": service, "partition": partition})
            else:
                mapping.append({"service": service, "partition": "All"})
        return mapping


def get_tests_for_partition(service: str, partition: str):
    with open("terraform_pytest/service-partitions.yml") as f:
        service_partitions = yaml.load(f, Loader=yaml.FullLoader)
        if service in service_partitions.keys():
            return json.dumps(service_partitions[service][partition])
