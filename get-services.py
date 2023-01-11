import json
import sys

import utils

services = []

if len(sys.argv) > 1:
    service = sys.argv[1]
    if service == 'all':
        from utils import get_all_services
        services = get_all_services()
    else:
        if ',' in service:
            services = service.split(',')
            services = [s for s in services if s != '' and s not in utils.BLACKLISTED_SERVICES]
        else:
            services = [service]
    print(json.dumps(services))
    exit(0)
else:
    print('No service provided')
    exit(1)

