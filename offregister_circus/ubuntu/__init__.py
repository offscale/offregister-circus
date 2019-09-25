from fabric.operations import run, sudo

from offregister_circus.shared import setup_circus


def install_circus0(*args, **kwargs):
    uname = run('uname -v', quiet=True)
    kwargs.setdefault('remote_user', 'ubuntu')
    kwargs.setdefault('APP_NAME', 'default_app_name')

    setup_circus(
        circus_virtual_env=kwargs.get('CIRCUS_VIRTUALENV', '/opt/venvs/circus'),
        home=sudo('echo $HOME', user=kwargs['remote_user'], quiet=True),
        log_dir=kwargs.get('APP_LOGDIR', '/var/log/{name}'.format(name=kwargs['APP_NAME'])),
        name=kwargs['APP_NAME'],
        remote_user=kwargs['remote_user'],
        app_virtual_env=kwargs.get('APP_VIRTUALENV', '/opt/venvs/{name}'.format(name=kwargs['APP_NAME'])),
        working_dir=kwargs.get('APP_WORKING_DIR', '/var/projects/{name}'.format(name=kwargs['APP_NAME'])),
        uname=uname,
        cmd=kwargs.get('APP_CMD'),
        shell=kwargs.get('APP_SHELL')
    )
