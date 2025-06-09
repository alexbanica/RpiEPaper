#!/usr/bin/python
# -*- coding:utf-8 -*-

from dataclasses import dataclass

@dataclass
class Context:
    default_page: int
    render_type: str
    remote_ssh_username: str = ''
    remote_ssh_key_path: str = ''
    remote_ssh_command: str = ''
    is_monitor_client: bool = False

    def __str__(self):
        return (f"Context("
            f"default_page={self.default_page},"
            f" render_type={self.render_type},"
            f" remote_ssh_username={self.remote_ssh_username},"
            f" remote_ssh_key_path={self.remote_ssh_key_path},"
            f" remote_ssh_command={self.remote_ssh_command})"
        )
