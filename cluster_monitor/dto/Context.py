from dataclasses import dataclass

@dataclass
class Context:
    default_page: int
    render_type: str
    remote_ssh_username: str = ''
    remote_ssh_key_path: str = ''
    remote_ssh_command: str = ''

    def __str__(self):
        return f"Context(default_page={self.default_page}, render_type={self.render_type}, remote_ssh_username={self.remote_ssh_username}, remote_ssh_key_path={self.remote_ssh_key_path}, remote_ssh_command={self.remote_ssh_command})"