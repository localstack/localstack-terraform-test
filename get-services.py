import json
import os

blacklist_services = ["controltower"]

services = []
for service in os.listdir('terraform-provider-aws/internal/service'):
    if service not in blacklist_services:
        services.append(service)
print(json.dumps(services))
