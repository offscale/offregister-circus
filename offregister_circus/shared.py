from functools import partial
from os import path
from sys import modules

from fabric.context_managers import shell_env
from fabric.contrib.files import upload_template, exists
from fabric.operations import sudo, run
from offregister_python.ubuntu import install_venv0
from pkg_resources import resource_filename

configs_dir = partial(path.join,
                      path.join(path.dirname(
                          resource_filename(modules[__name__].__package__, '__init__.py'))
                      ), 'data')


def setup_circus(circus_virtual_env, home, log_dir, name,
                 remote_user, app_virtual_env, working_dir,
                 uname, cmd='gunicorn', shell='/bin/bash'):
    conf_dir = '/etc/circus/conf.d'
    remote_circus_ini = '{conf_dir}/circus.ini'.format(conf_dir=conf_dir)
    circus_ini_context = {
        'CMD': cmd,
        'HOME': home,
        'LOG_DIR': log_dir,
        'NAME': name,
        'SHELL': shell,
        'USER': remote_user,
        'VENV': app_virtual_env,
        'WORKING_DIR': working_dir
    }

    if remote_circus_ini:
        raise NotImplementedError('TODO: Append file')

    paths = '{circus_virtual_env} {log_dir} {working_dir}'.format(
        circus_virtual_env=circus_virtual_env, log_dir=log_dir, working_dir=working_dir
    )
    sudo('mkdir -p {paths}'.format(paths=paths))
    group_user = run('''printf '%s:%s' "{user}" $(id -gn)'''.format(user=remote_user),
                     shell_escape=False, quiet=True)
    sudo('chown -R {group_user} {paths}'.format(group_user=group_user, paths=paths))

    venvs = (venv for venv in (circus_virtual_env, app_virtual_env)
             if not exists('{}/bin'.format(circus_virtual_env)))
    for virtual_env in venvs:
        if 'Ubuntu' in uname:
            install_venv0(python3=True, virtual_env=virtual_env)
        else:
            run('python3 -m venv "{virtual_env}"'.format(virtual_env=virtual_env))

    with shell_env(VIRTUAL_ENV=circus_virtual_env,
                   PATH="{}/bin:$PATH".format(circus_virtual_env)):
        run('pip install circus')

    sudo('mkdir -p {conf_dir}'.format(conf_dir=conf_dir))
    py_ver = run('{virtual_env}/bin/python --version'.format(
        virtual_env=app_virtual_env
    )).partition(' ')[2][:3]
    circus_ini_context['PYTHON_VERSION'] = py_ver
    upload_template(configs_dir('circus.ini'), remote_circus_ini,
                    context=circus_ini_context,
                    use_sudo=True)
    circusd_context = {
        'CONF_DIR': conf_dir,
        'CIRCUS_VENV': circus_virtual_env
    }
    if uname.startswith('Darwin'):
        upload_template(
            configs_dir('circusd.launchd.xml'),
            '{home}/Library/LaunchAgents/io.readthedocs.circus.plist'.format(home=home),
            context=circusd_context)
    elif exists('/etc/systemd/system'):
        upload_template(configs_dir('circusd.service'), '/etc/systemd/system/',
                        context=circusd_context, use_sudo=True)
    else:
        upload_template(configs_dir('circusd.conf'), '/etc/init/',
                        context=circusd_context, use_sudo=True)
    return circus_virtual_env
