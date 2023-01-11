import click
from timeit import default_timer as timer

import utils


@click.group(name='pytest-golang', help='Golang Test Runner for localstack')
def cli():
    pass


@click.command(name='patch', help='Patch the golang test runner')
def patch():
    from utils import patch_repo
    patch_repo()


@click.command(name='build', help='Build binary for testing')
@click.option('--service', '-s', default=None, help='''Service to build; use "all" to build all services, example: 
--service=all; --service=ec2; --service=ec2,iam''')
def build(service):
    """Build binary for testing"""

    # skips building for the service
    if not service:
        print('No service provided')
        print('use --service or -s to specify services to build; for more help try --help to see more options')
        return
    if service == 'all':
        from utils import get_all_services
        services = get_all_services()
    else:
        if ',' in service:
            services = service.split(',')
            services = [s for s in services if s != '' and s not in utils.BLACKLISTED_SERVICES]
        else:
            services = [service]

    for service in services:
        from utils import build_test_bin
        from utils import TF_REPO_NAME
        from os.path import realpath
        print(f'Building {service}...')
        try:
            start = timer()
            build_test_bin(service=service, tf_root_path=realpath(TF_REPO_NAME))
            end = timer()
            print(f'Build {service} in {end - start} seconds')
        except KeyboardInterrupt:
            print('Interrupted')
            return
        except Exception as e:
            print(f'Failed to build binary for {service}: {e}')


cli.add_command(build)
cli.add_command(patch)
cli()
