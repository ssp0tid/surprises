"""Encrypted vault storage and management."""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from dotenv import dotenv_values

from envsync.core import encryption, interpolator

ENV_SYNC_DIR = ".envsync"
CONFIG_FILE = "config.json"
VAULT_FILE = "vault.enc"


@dataclass
class Project:
    name: str
    path: str
    group: str | None = None
    variables: dict[str, str] = field(default_factory=dict)


@dataclass
class Group:
    name: str
    projects: list[str] = field(default_factory=list)


@dataclass
class Vault:
    projects: dict[str, Project] = field(default_factory=dict)
    groups: dict[str, Group] = field(default_factory=dict)
    global_vars: dict[str, str] = field(default_factory=dict)


def get_config_dir() -> Path:
    home = Path.home()
    return home / ".envsync"


def get_project_dir() -> Path | None:
    cwd = Path.cwd()
    envsync_dir = cwd / ENV_SYNC_DIR
    if envsync_dir.exists():
        return envsync_dir
    return get_config_dir()


class VaultManager:
    def __init__(self, password: str | None = None):
        self.password = password
        self.vault = Vault()
        self.config_dir = get_project_dir() or get_config_dir()
        self.vault_path = self.config_dir / VAULT_FILE

    def load(self) -> bool:
        if not self.vault_path.exists():
            return False
        try:
            encrypted = self.vault_path.read_bytes()
            if self.password is None:
                return False
            data = encryption.decrypt_data(self.password, encrypted)
            if data is None:
                return False
            vault_dict = json.loads(data)
            self.vault = Vault(
                projects={k: Project(**v) for k, v in vault_dict.get("projects", {}).items()},
                groups={k: Group(**v) for k, v in vault_dict.get("groups", {}).items()},
                global_vars=vault_dict.get("global_vars", {}),
            )
            return True
        except Exception:
            return False

    def save(self) -> bool:
        if self.password is None:
            return False
        try:
            vault_dict = {
                "projects": {k: asdict(v) for k, v in self.vault.projects.items()},
                "groups": {k: asdict(v) for k, v in self.vault.groups.items()},
                "global_vars": self.vault.global_vars,
            }
            data = json.dumps(vault_dict, indent=2).encode("utf-8")
            encrypted = encryption.encrypt_data(self.password, data)
            self.config_dir.mkdir(parents=True, exist_ok=True)
            self.vault_path.write_bytes(encrypted)
            self._add_to_gitignore()
            return True
        except Exception:
            return False

    def _add_to_gitignore(self) -> None:
        gitignore = Path(".gitignore")
        if gitignore.exists():
            content = gitignore.read_text()
            if ENV_SYNC_DIR not in content:
                content += f"\n{ENV_SYNC_DIR}/\n"
                gitignore.write_text(content)
        else:
            gitignore.write_text(f"{ENV_SYNC_DIR}/\n")

    def add_project(self, name: str, path: str, group: str | None = None) -> Project:
        project = Project(name=name, path=path, group=group)
        self.vault.projects[name] = project
        if group and group in self.vault.groups:
            if name not in self.vault.groups[group].projects:
                self.vault.groups[group].projects.append(name)
        self.save()
        return project

    def remove_project(self, name: str) -> bool:
        if name in self.vault.projects:
            project = self.vault.projects[name]
            if project.group and project.group in self.vault.groups:
                group = self.vault.groups[project.group]
                if name in group.projects:
                    group.projects.remove(name)
            del self.vault.projects[name]
            self.save()
            return True
        return False

    def add_variable(
        self,
        name: str,
        value: str,
        project: str | None = None,
        interpolate: bool = True,
    ) -> None:
        if interpolate:
            all_vars = {**self.vault.global_vars}
            if project and project in self.vault.projects:
                all_vars = {**all_vars, **self.vault.projects[project].variables}
            value = interpolator.interpolate(value, all_vars)

        if project and project in self.vault.projects:
            self.vault.projects[project].variables[name] = value
        else:
            self.vault.global_vars[name] = value
        self.save()

    def remove_variable(self, name: str, project: str | None = None) -> bool:
        if project and project in self.vault.projects:
            if name in self.vault.projects[project].variables:
                del self.vault.projects[project].variables[name]
                self.save()
                return True
        if name in self.vault.global_vars:
            del self.vault.global_vars[name]
            self.save()
            return True
        return False

    def list_variables(self, project: str | None = None) -> dict[str, str]:
        if project and project in self.vault.projects:
            return {**self.vault.global_vars, **self.vault.projects[project].variables}
        return dict(self.vault.global_vars)

    def create_group(self, name: str) -> Group:
        group = Group(name=name)
        self.vault.groups[name] = group
        self.save()
        return group

    def delete_group(self, name: str) -> bool:
        if name in self.vault.groups:
            for project in self.vault.groups[name].projects:
                if project in self.vault.projects:
                    self.vault.projects[project].group = None
            del self.vault.groups[name]
            self.save()
            return True
        return False

    def add_project_to_group(self, project: str, group: str) -> bool:
        if project not in self.vault.projects:
            return False
        if group not in self.vault.groups:
            self.create_group(group)

        old_group = self.vault.projects[project].group
        if old_group and old_group in self.vault.groups:
            if project in self.vault.groups[old_group].projects:
                self.vault.groups[old_group].projects.remove(project)

        self.vault.projects[project].group = group
        if project not in self.vault.groups[group].projects:
            self.vault.groups[group].projects.append(project)
        self.save()
        return True

    def remove_project_from_group(self, project: str) -> bool:
        if project in self.vault.projects:
            old_group = self.vault.projects[project].group
            if old_group and old_group in self.vault.groups:
                if project in self.vault.groups[old_group].projects:
                    self.vault.groups[old_group].projects.remove(project)
            self.vault.projects[project].group = None
            self.save()
            return True
        return False

    def list_groups(self) -> dict[str, Group]:
        return self.vault.groups

    def import_from_file(self, path: str, project: str | None = None) -> int:
        env_vars = dotenv_values(path)
        count = 0
        for key, value in env_vars.items():
            if value is not None:
                self.add_variable(key, value, project=project)
                count += 1
        return count

    def export_to_file(self, path: str, project: str | None = None) -> int:
        variables = self.list_variables(project)
        lines = [f"{k}={v!r}\n" for k, v in variables.items()]
        content = "".join(lines)
        Path(path).write_text(content)
        return len(variables)

    def sync_group(self, group: str) -> dict[str, int]:
        if group not in self.vault.groups:
            return {}
        results = {}
        for project_name in self.vault.groups[group].projects:
            project = self.vault.projects.get(project_name)
            if project:
                project_path = Path(project.path)
                if project_path.exists():
                    lines = []
                    all_vars = {
                        **self.vault.global_vars,
                        **project.variables,
                    }
                    for key, value in all_vars.items():
                        lines.append(f"{key}={value!r}\n")
                    (project_path / ".env").write_text("".join(lines))
                    results[project_name] = len(all_vars)
        return results
