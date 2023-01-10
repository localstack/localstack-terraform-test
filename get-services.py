import json
import os

blacklist_services = ["controltower"]
whitelist_service = ["s3"]

services = []
for service in os.listdir('terraform-provider-aws/internal/service'):
    if service in whitelist_service:
        services.append(service)
    # if service not in blacklist_services:
    #     services.append(service)
print(json.dumps(services))


# with open("tests/terraform/terraform-tests.yaml") as f:
#     service_mapping = yaml.load(f, Loader=yaml.FullLoader)
#     mapping = []
#     for service, partition_or_tests in service_mapping.items():
#         if isinstance(partition_or_tests, dict):
#             partitions = list(partition_or_tests.keys())
#             for partition in partitions:
#                 mapping.append({"service": service, "partition": str(partition)})
#         else:
#             mapping.append({"service": service, "partition": None})
#     print(json.dumps(mapping))
