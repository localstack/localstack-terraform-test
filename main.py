import click


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
@click.option('--force', '-f', default=False, is_flag=True, help='Force build')
def build(service, force):
    """Build binary for testing"""
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
        else:
            services = [service]

    for service in services:
        from utils import build_test_bin
        from utils import BASE_PATH
        from os.path import realpath
        print(f'Building {service}...')
        try:
            build_test_bin(service=service, tf_root_path=realpath(BASE_PATH))
        except KeyboardInterrupt:
            print('Interrupted')
            return


cli.add_command(build)
cli.add_command(patch)
cli()
