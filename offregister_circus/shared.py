# -*- coding: utf-8 -*-
from __future__ import print_function

from sys import version_info

if version_info[0] == 2:
    from ConfigParser import ConfigParser
else:
    from configparser import ConfigParser

from functools import partial
from os import path
from sys import modules

from fabric.context_managers import shell_env
from fabric.contrib.files import exists, upload_template
from fabric.operations import get, put, run, sudo
from offregister_python.ubuntu import install_venv0
from pkg_resources import resource_filename
from six import StringIO, iteritems

configs_dir = partial(
    path.join,
    path.join(
        path.dirname(resource_filename(modules[__name__].__package__, "__init__.py"))
    ),
    "configs",
)


def setup_circus(
    circus_virtual_env,
    env,
    home,
    log_dir,
    name,
    port,
    remote_user,
    app_virtual_env,
    working_dir,
    wsgi_file,
    uname,
    cmd_args=None,
    cmd="gunicorn",
    shell="/bin/bash",
):
    conf_dir = "/etc/circus/conf.d"
    remote_circus_ini = "{conf_dir}/circus.ini".format(conf_dir=conf_dir)

    assert (
        cmd_args is not None or wsgi_file is not None
    ), "cmd_args or wsgi_file must be defined"

    circus_ini_context = {
        "CMD": cmd,
        "CMD_ARGS": (
            "-w 3 -t 60 -b 127.0.0.1:{port:d} {wsgi_file}".format(
                port=port, wsgi_file=wsgi_file
            )
            if cmd_args is None
            else cmd_args
        ),
        "ENV": ""
        if env is None
        else "\n".join(("{} = {}".format(k, v) for k, v in iteritems(env))),
        "HOME": home,
        "LOG_DIR": log_dir,
        "NAME": name,
        "SHELL": shell,
        "USER": remote_user,
        "VENV": app_virtual_env,
        "WORKING_DIR": working_dir,
    }

    paths = "{circus_virtual_env} {log_dir} {working_dir}".format(
        circus_virtual_env=circus_virtual_env, log_dir=log_dir, working_dir=working_dir
    )
    sudo("mkdir -p {paths} {conf_dir}".format(paths=paths, conf_dir=conf_dir))
    group_user = run(
        """printf '%s:%s' "{user}" $(id -gn)""".format(user=remote_user),
        shell_escape=False,
        quiet=True,
    )
    sudo("chown -R {group_user} {paths}".format(group_user=group_user, paths=paths))

    venvs = (
        venv
        for venv in (circus_virtual_env, app_virtual_env)
        if not exists("{}/bin".format(circus_virtual_env))
    )
    for virtual_env in venvs:
        if "Ubuntu" in uname:
            install_venv0(python3=True, virtual_env=virtual_env)
        else:
            run('python3 -m venv "{virtual_env}"'.format(virtual_env=virtual_env))

    py_ver = run(
        "{virtual_env}/bin/python --version".format(virtual_env=app_virtual_env)
    ).partition(" ")[2][:3]
    circus_ini_context["PYTHON_VERSION"] = py_ver

    with open(configs_dir("circus.ini"), "rt") as f:
        circus_ini_content = f.read()

    circus_ini_content = circus_ini_content.format(
        **circus_ini_context
    )  # Code is here because I like to error early

    if not exists(remote_circus_ini):
        with shell_env(
            VIRTUAL_ENV=circus_virtual_env,
            PATH="{}/bin:$PATH".format(circus_virtual_env),
        ):
            run("pip install circus")

        sio = StringIO()
        sio.write(
            "[circus]\n"
            "check_delay = 5\n"
            "endpoint = tcp://127.0.0.1:5555\n"
            "pubsub_endpoint = tcp://127.0.0.1:5556\n"
            "statsd = true\n\n"
        )
        sio.seek(0)

        put(sio, remote_path=remote_circus_ini, use_sudo=True)

        circusd_context = {"CONF_DIR": conf_dir, "CIRCUS_VENV": circus_virtual_env}
        if uname.startswith("Darwin"):
            upload_template(
                configs_dir("circusd.launchd.xml"),
                "{home}/Library/LaunchAgents/io.readthedocs.circus.plist".format(
                    home=home
                ),
                context=circusd_context,
            )
        elif exists("/etc/systemd/system"):
            upload_template(
                configs_dir("circusd.service"),
                "/etc/systemd/system/",
                context=circusd_context,
                use_sudo=True,
            )
        else:
            upload_template(
                configs_dir("circusd.conf"),
                "/etc/init/",
                context=circusd_context,
                use_sudo=True,
            )

    sio0 = StringIO()
    get(remote_circus_ini, sio0, use_sudo=True)
    sio0.seek(0)

    config0 = ConfigParser()
    config0.readfp(sio0)

    sio1 = StringIO()
    sio1.write(circus_ini_content)
    sio1.seek(0)

    config1 = ConfigParser()
    config1.readfp(sio1)

    for section in config1.sections():
        if config0.has_section(section):
            config0.remove_section(section)
        config0.add_section(section)
        for item, val in config1.items(section):
            config0.set(section, item, val)

    sio2 = StringIO()
    config0.write(sio2)
    sio2.seek(0)

    put(local_path=sio2, remote_path=remote_circus_ini, use_sudo=True)

    return circus_virtual_env
