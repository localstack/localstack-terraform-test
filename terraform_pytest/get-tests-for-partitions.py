import json
import sys

import yaml

with open("terraform_pytest/service-partitions.yml") as f:
    service_partitions = yaml.load(f, Loader=yaml.FullLoader)
    mapping = []
    service = sys.argv[1]
    partition = sys.argv[2]
    if service in service_partitions.keys():
        print(json.dumps(service_partitions[service][partition]))
