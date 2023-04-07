import json
import sys

from terraform_pytest.get_tf_partitions import get_partitions
from terraform_pytest.utils import get_services

service_partitions = []


def main():
    if len(sys.argv) > 1:
        service = sys.argv[1]
        services = get_services(service)
        partitions = get_partitions(services)
        for partition in partitions:
            service_partitions.append(partition)
        print(json.dumps(service_partitions))
    else:
        print("No service provided")
        exit(1)


if __name__ == "__main__":
    main()
