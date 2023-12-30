from __future__ import print_function

from fabric.operations import run, sudo

from offregister_circus.shared import setup_circus


def install_circus0(c, *args, **kwargs):
    uname = run("uname -v", quiet=True)

    for key in (
        "NAME",
        "WORKING_DIR",
        "ENV",
        "LOGDIR",
        "PORT",
        "CMD",
        "CMD_ARGS",
        "SHELL",
    ):
        k = "APP_{key}".format(key=key)
        if key in kwargs and k not in kwargs:
            kwargs[k] = kwargs[key]

    kwargs.setdefault(
        "APP_VIRTUALENV", "/opt/venvs/{name}".format(name=kwargs["APP_NAME"])
    )
    kwargs.setdefault(
        "APP_WORKING_DIR", "/var/projects/{name}".format(name=kwargs["APP_NAME"])
    )
    kwargs.setdefault("APP_LOGDIR", "/var/log/{name}".format(name=kwargs["APP_NAME"]))
    kwargs.setdefault("APP_ENV", None)
    kwargs.setdefault("APP_CMD_ARGS", None)
    kwargs.setdefault("SHELL", "/bin/bash")
    kwargs.setdefault("remote_user", "ubuntu")

    setup_circus(
        circus_virtual_env=kwargs.get("CIRCUS_VIRTUALENV", "/opt/venvs/circus"),
        env=kwargs.get("APP_ENV"),
        home=sudo("echo $HOME", user=kwargs["remote_user"], quiet=True),
        log_dir=kwargs["APP_LOGDIR"],
        name=kwargs["APP_NAME"],
        port=kwargs["APP_PORT"],
        remote_user=kwargs["remote_user"],
        app_virtual_env=kwargs["APP_VIRTUALENV"],
        working_dir=kwargs["APP_WORKING_DIR"],
        uname=uname,
        cmd=kwargs.get("APP_CMD"),
        cmd_args=kwargs["APP_CMD_ARGS"],
        shell=kwargs.get("APP_SHELL"),
        wsgi_file=kwargs.get("WSGI_FILE"),
    )
