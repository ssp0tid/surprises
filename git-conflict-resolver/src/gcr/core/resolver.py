"""Resolution engine for applying conflict resolutions."""

import os
from dataclasses import dataclass, field
from typing import Optional

from .conflict import ConflictFile, ConflictHunk, ResolutionChoice


@dataclass
class ResolutionResult:
    """Result of resolving a conflict file."""

    file: ConflictFile
    success: bool
    error_message: Optional[str] = None
    warnings: list[str] = field(default_factory=list)


class Resolver:
    """Handles conflict resolution and file writing."""

    def __init__(self, backup_enabled: bool = True):
        self.backup_enabled = backup_enabled

    def resolve(
        self,
        hunk: ConflictHunk,
        choice: ResolutionChoice,
        custom_content: Optional[str] = None,
    ) -> None:
        """Apply resolution to a conflict hunk."""
        if choice == ResolutionChoice.OURS:
            hunk.resolved_content = "".join(hunk.ours_content)
        elif choice == ResolutionChoice.THEIRS:
            hunk.resolved_content = "".join(hunk.theirs_content)
        elif choice == ResolutionChoice.MANUAL and custom_content:
            hunk.resolved_content = custom_content
        elif choice == ResolutionChoice.AUTO:
            hunk.resolved_content = "".join(hunk.ours_content)

        hunk.resolution = choice

    def apply(self, conflict_file: ConflictFile) -> ResolutionResult:
        """Apply all resolutions and write result."""
        warnings = []

        unresolved = [c for c in conflict_file.conflicts if not c.is_resolved]
        if unresolved:
            return ResolutionResult(
                file=conflict_file,
                success=False,
                error_message=f"{len(unresolved)} unresolved conflicts",
                warnings=warnings,
            )

        try:
            content = conflict_file.rebuild_content()
        except Exception as e:
            return ResolutionResult(
                file=conflict_file,
                success=False,
                error_message=str(e),
                warnings=warnings,
            )

        conflict_file.content = content

        return ResolutionResult(
            file=conflict_file,
            success=True,
            error_message=None,
            warnings=warnings,
        )

    def write_file(
        self, conflict_file: ConflictFile, output_path: Optional[str] = None
    ) -> ResolutionResult:
        """Write resolved content to file."""
        result = self.apply(conflict_file)

        if not result.success:
            return result

        path = output_path or conflict_file.path
        target_dir = os.path.dirname(path)

        if target_dir and not os.path.exists(target_dir):
            try:
                os.makedirs(target_dir)
            except OSError as e:
                return ResolutionResult(
                    file=conflict_file,
                    success=False,
                    error_message=f"Cannot create directory: {e}",
                    warnings=result.warnings,
                )

        if self.backup_enabled and os.path.exists(path):
            backup_path = f"{path}.bak"
            try:
                with open(path, "rb") as src:
                    with open(backup_path, "wb") as dst:
                        dst.write(src.read())
                warnings.append(f"Backup created: {backup_path}")
            except OSError:
                warnings.append("Warning: Could not create backup")

        try:
            with open(path, "w") as f:
                f.write(conflict_file.content)
        except OSError as e:
            return ResolutionResult(
                file=conflict_file,
                success=False,
                error_message=f"Cannot write file: {e}",
                warnings=result.warnings,
            )

        return ResolutionResult(
            file=conflict_file,
            success=True,
            error_message=None,
            warnings=result.warnings,
        )
