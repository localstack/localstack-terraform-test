import json
import sys

from utils import get_services

services = []

if len(sys.argv) > 1:
    service = sys.argv[1]
    services = get_services(service)
    print(json.dumps(services))
    exit(0)
else:
    print('No service provided')
    exit(1)

