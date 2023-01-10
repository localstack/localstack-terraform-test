import json
import os

blacklist_services = ["controltower"]

services = os.listdir('terraform-provider-aws/internal/service')
print(services)
