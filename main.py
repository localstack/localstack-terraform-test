import click
from timeit import default_timer as timer
from utils import build_test_bin, TF_REPO_NAME, get_services
from os.path import realpath


@click.group(name='pytest-golang', help='Golang Test Runner for localstack')
def cli():
    pass


@click.command(name='patch', help='Patch the golang test runner')
def patch():
    from utils import patch_repo
    patch_repo()


@click.command(name='build', help='Build binary for testing')
@click.option('--service', '-s', default=None, help='''Service to build; use "ls-all", "ls-community", "ls-pro" to build all services, example: 
--service=ls-all; --service=ec2; --service=ec2,iam''')
def build(service):
    """Build binary for testing"""
    if not service:
        print('No service provided')
        print('use --service or -s to specify services to build; for more help try --help to see more options')
        return

    services = get_services(service)

    for service in services:
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
