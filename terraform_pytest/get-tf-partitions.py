# Prints a JSON dict mapping the different partitions in the terraform-tests.yaml to their service
import json
import sys

import yaml

with open("terraform_pytest/service-partitions.yml") as f:
    service_partitions = yaml.load(f, Loader=yaml.FullLoader)
    print(sys.argv[1])
    mapping = []
    for service in json.loads(sys.argv[1]):
        if service in service_partitions.keys():
            for partitioned_service, partitions in service_partitions.items():
                print(f"Partitioned Service: {partitioned_service}")
                print(f"Partitions: {partitions}")
                partition_keys = list(partitions.keys())
                print(partitions)
                for partition in partition_keys:
                    mapping.append({"service": service, "partition": partition})
        else:
            mapping.append({"service": service, "partition": "All"})
    print(json.dumps(mapping))
