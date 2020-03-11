# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See LICENSE for more details.
#
# Copyright (c) 2020 ScyllaDB

import os
import json
import atexit
import logging

from sdcm.remote import LOCALRUNNER


LOGGER = logging.getLogger(__name__)


class SSHAgent:
    @classmethod
    def start(cls):
        if cls.is_running():
            LOGGER.warning("ssh-agent started already:\n\t\tSSH_AUTH_SOCK=%s\n\t\tSSH_AGENT_PID=%s",
                           os.environ["SSH_AUTH_SOCK"], os.environ["SSH_AGENT_PID"])
            return

        res = LOCALRUNNER.run(r"""eval $(ssh-agent -s) && """
                              r"""eval 'echo "{\"SSH_AUTH_SOCK\": \"$SSH_AUTH_SOCK\", """
                              r"""             \"SSH_AGENT_PID\": \"$SSH_AGENT_PID\"}" >&2'""")
        if not res.ok:
            raise RuntimeError()

        os.environ.update(json.loads(res.stderr))
        LOGGER.info("ssh-agent started successfully:\n\t\tSSH_AUTH_SOCK=%s\n\t\tSSH_AGENT_PID=%s",
                    os.environ["SSH_AUTH_SOCK"], os.environ["SSH_AGENT_PID"])

        atexit.register(cls.stop)

    @staticmethod
    def is_running():
        return bool(os.environ.get("SSH_AUTH_SOCK"))

    @staticmethod
    def stop():
        LOCALRUNNER.run("ssh-agent -k", ignore_status=True)
        try:
            del os.environ["SSH_AUTH_SOCK"]
            del os.environ["SSH_AGENT_PID"]
        except KeyError:
            pass

    @classmethod
    def add_key(cls, path):
        if not cls.is_running():
            cls.start()
        LOCALRUNNER.run(f"ssh-add {path}")
