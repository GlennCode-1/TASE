from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LockedTestAccessPolicy:
    train_validation_dir: Path
    locked_test_dir: Path
    allow_locked_read: bool = False

    def assert_can_read(self, path: Path) -> None:
        resolved = path.resolve()
        locked = self.locked_test_dir.resolve()
        if str(resolved).startswith(str(locked)) and not self.allow_locked_read:
            raise PermissionError("locked-test path is inaccessible before final evaluation")


def write_access_report(path: Path, policy: LockedTestAccessPolicy, locked_files: list[Path]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    listing = "\n".join(f"- {file}" for file in locked_files)
    path.write_text(
        f"""# Direction A B1 Locked-Test Access Report\n\nTrain/validation directory: {policy.train_validation_dir}\n\nLocked-test directory: {policy.locked_test_dir}\n\nLocked read allowed before final evaluation: {policy.allow_locked_read}\n\nLocked artifacts written for physical separation smoke, but workflow diagnostics and selection code are not allowed to read them.\n\nLocked artifacts:\n\n{listing}\n""",
        encoding="utf-8",
    )
