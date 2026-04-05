#!/usr/bin/env python3
"""
Speckit Worktree Manager

Manages git worktrees for speckit projects with template integration.
Provides isolated development environments for different work types.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


class WorktreeManager:
    """Manages git worktrees for speckit development workflows."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.speckit_dir = project_root / ".speckit"
        self.specs_dir = self.speckit_dir / "specs"
        self.templates_dir = self.specs_dir / ".templates"

    def create_worktree(
        self,
        project_id: str,
        work_type: str,
        feature_name: str,
        base_branch: str = "main",
    ) -> dict[str, str]:
        """
        Create a new git worktree for a speckit project.

        Args:
            project_id: TSK-ID for the project
            work_type: Type of work (feature-development, bug-fix, rca, etc.)
            feature_name: Descriptive name for the work
            base_branch: Base branch to create worktree from

        Returns:
            Dictionary with worktree information
        """
        # Validate work type has templates
        work_type_path = self.templates_dir / work_type
        if not work_type_path.exists():
            raise ValueError(
                f"Work type '{work_type}' not found. Available: {self._list_work_types()}"
            )

        # Create worktree name
        worktree_name = (
            f"{work_type}-{project_id}-{feature_name.lower().replace(' ', '-')}"
        )
        worktree_path = self.project_root.parent / worktree_name

        # Check if worktree already exists
        if worktree_path.exists():
            raise ValueError(f"Worktree already exists at {worktree_path}")

        try:
            # Create git worktree
            subprocess.run(
                ["git", "worktree", "add", str(worktree_path), base_branch],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )

            # Create project spec directory
            project_spec_dir = (
                self.specs_dir
                / f"{project_id}-{feature_name.lower().replace(' ', '-')}"
            )
            project_spec_dir.mkdir(exist_ok=True)

            # Copy templates to project spec directory
            self._copy_templates(work_type, project_spec_dir, project_id, feature_name)

            # Create worktree configuration
            worktree_config = {
                "project_id": project_id,
                "work_type": work_type,
                "feature_name": feature_name,
                "worktree_name": worktree_name,
                "worktree_path": str(worktree_path),
                "base_branch": base_branch,
                "created_at": subprocess.run(
                    ["git", "log", "-1", "--format=%ct"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                ).stdout.strip(),
                "session_id": self._generate_session_id(),
            }

            # Save worktree configuration
            config_file = project_spec_dir / "worktree_config.json"
            with open(config_file, "w") as f:
                json.dump(worktree_config, f, indent=2)

            # Create .speckit directory in worktree
            worktree_speckit_dir = worktree_path / ".speckit"
            worktree_speckit_dir.mkdir(exist_ok=True)

            # Link to project spec
            (worktree_speckit_dir / "current_project").symlink_to(project_spec_dir)

            # Setup development environment script in worktree
            self._create_setup_script(worktree_path, worktree_config)

            return {
                "status": "success",
                "worktree_name": worktree_name,
                "worktree_path": str(worktree_path),
                "project_spec_dir": str(project_spec_dir),
                "session_id": worktree_config["session_id"],
            }

        except subprocess.CalledProcessError as e:
            # Cleanup on failure
            if worktree_path.exists():
                import shutil

                shutil.rmtree(worktree_path)
            raise RuntimeError(f"Failed to create worktree: {e.stderr}")

    def list_worktrees(self) -> list[dict[str, str]]:
        """List all speckit worktrees."""
        try:
            result = subprocess.run(
                ["git", "worktree", "list"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )

            worktrees = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split()
                    path = parts[0]
                    commit = parts[1]
                    branch = parts[2].strip("[]") if len(parts) > 2 else "detached"

                    # Check if this is a speckit worktree
                    if self._is_speckit_worktree(Path(path)):
                        worktrees.append(
                            {
                                "path": path,
                                "commit": commit,
                                "branch": branch,
                                "is_speckit": True,
                                "config": self._get_worktree_config(Path(path)),
                            }
                        )

            return worktrees

        except subprocess.CalledProcessError:
            return []

    def remove_worktree(
        self, worktree_name: str, force: bool = False
    ) -> dict[str, str]:
        """
        Remove a git worktree.

        Args:
            worktree_name: Name of the worktree to remove
            force: Force removal even if there are uncommitted changes

        Returns:
            Dictionary with removal status
        """
        worktree_path = self.project_root.parent / worktree_name

        if not worktree_path.exists():
            raise ValueError(f"Worktree {worktree_name} not found")

        try:
            # Remove git worktree
            cmd = ["git", "worktree", "remove"]
            if force:
                cmd.append("--force")
            cmd.append(str(worktree_path))

            subprocess.run(
                cmd, cwd=self.project_root, capture_output=True, text=True, check=True
            )

            # Clean up project spec if it exists
            config = self._get_worktree_config(worktree_path)
            if config and "project_id" in config:
                project_spec_dir = (
                    self.specs_dir
                    / f"{config['project_id']}-{config['feature_name'].lower().replace(' ', '-')}"
                )
                if project_spec_dir.exists():
                    import shutil

                    shutil.rmtree(project_spec_dir)

            return {
                "status": "success",
                "message": f"Worktree {worktree_name} removed successfully",
            }

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to remove worktree: {e.stderr}")

    def sync_worktree(self, worktree_name: str) -> dict[str, str]:
        """
        Sync worktree with latest changes from base branch.

        Args:
            worktree_name: Name of the worktree to sync

        Returns:
            Dictionary with sync status
        """
        worktree_path = self.project_root.parent / worktree_name

        if not worktree_path.exists():
            raise ValueError(f"Worktree {worktree_name} not found")

        try:
            # Stash any local changes
            subprocess.run(
                [
                    "git",
                    "stash",
                    "push",
                    "-m",
                    f"Auto-stash before sync {worktree_name}",
                ],
                cwd=worktree_path,
                capture_output=True,
                text=True,
            )

            # Pull latest changes
            subprocess.run(
                ["git", "pull", "origin", "main"],
                cwd=worktree_path,
                capture_output=True,
                text=True,
                check=True,
            )

            # Try to reapply stashed changes
            result = subprocess.run(
                ["git", "stash", "pop"],
                cwd=worktree_path,
                capture_output=True,
                text=True,
            )

            has_conflicts = result.returncode != 0

            return {
                "status": "success",
                "has_conflicts": has_conflicts,
                "message": (
                    "Worktree synced successfully"
                    if not has_conflicts
                    else "Worktree synced with merge conflicts"
                ),
            }

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to sync worktree: {e.stderr}")

    def _list_work_types(self) -> list[str]:
        """List available work types with templates."""
        if not self.templates_dir.exists():
            return []

        return [d.name for d in self.templates_dir.iterdir() if d.is_dir()]

    def _copy_templates(
        self, work_type: str, project_spec_dir: Path, project_id: str, feature_name: str
    ):
        """Copy template files to project spec directory."""
        template_dir = self.templates_dir / work_type

        for template_file in template_dir.glob("*.md"):
            # Read template content
            with open(template_file) as f:
                content = f.read()

            # Replace placeholders
            content = content.replace("TSK-XXX", project_id)
            content = content.replace("[Feature Name]", feature_name)
            content = content.replace(
                "[Date]",
                subprocess.run(["date"], capture_output=True, text=True).stdout.strip(),
            )
            content = content.replace("[UUID]", self._generate_session_id())

            # Write to project spec directory
            output_file = project_spec_dir / template_file.name
            with open(output_file, "w") as f:
                f.write(content)

    def _is_speckit_worktree(self, worktree_path: Path) -> bool:
        """Check if a worktree is a speckit worktree."""
        speckit_dir = worktree_path / ".speckit"
        if not speckit_dir.exists():
            return False

        current_project_link = speckit_dir / "current_project"
        return current_project_link.exists() and current_project_link.is_symlink()

    def _get_worktree_config(self, worktree_path: Path) -> dict | None:
        """Get worktree configuration."""
        if not self._is_speckit_worktree(worktree_path):
            return None

        try:
            current_project_link = worktree_path / ".speckit" / "current_project"
            project_spec_dir = current_project_link.resolve()
            config_file = project_spec_dir / "worktree_config.json"

            if config_file.exists():
                with open(config_file) as f:
                    return json.load(f)
        except Exception:
            pass

        return None

    def _create_setup_script(self, worktree_path: Path, config: dict[str, str]):
        """Create development environment setup script."""
        script_content = f"""#!/bin/bash
# Speckit Worktree Setup Script
# Project: {config["project_id"]} - {config["feature_name"]}
# Work Type: {config["work_type"]}

echo "Setting up development environment for {config["project_id"]}"

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install development dependencies
if [ -f "requirements-dev.txt" ]; then
    pip install -r requirements-dev.txt
fi

# Install pre-commit hooks
pre-commit install

# Create development branch
git checkout -b {config["project_id"]}-{config["feature_name"].lower().replace(" ", "-")}

echo "Development environment ready!"
echo "Project spec directory: $(pwd)/.speckit/current_project"
echo "Session ID: {config["session_id"]}"
"""

        script_path = worktree_path / "setup_dev_env.sh"
        with open(script_path, "w") as f:
            f.write(script_content)

        # Make script executable
        os.chmod(script_path, 0o755)

    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        import uuid

        return str(uuid.uuid4())


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="Speckit Worktree Manager")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory (default: current directory)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Create worktree command
    create_parser = subparsers.add_parser("create", help="Create a new worktree")
    create_parser.add_argument("project_id", help="Project ID (e.g., TSK-001)")
    create_parser.add_argument("work_type", help="Type of work")
    create_parser.add_argument("feature_name", help="Feature/bug description")
    create_parser.add_argument(
        "--base-branch", default="main", help="Base branch to create from"
    )

    # List worktrees command
    subparsers.add_parser("list", help="List all worktrees")

    # Remove worktree command
    remove_parser = subparsers.add_parser("remove", help="Remove a worktree")
    remove_parser.add_argument("worktree_name", help="Name of worktree to remove")
    remove_parser.add_argument("--force", action="store_true", help="Force removal")

    # Sync worktree command
    sync_parser = subparsers.add_parser(
        "sync", help="Sync worktree with latest changes"
    )
    sync_parser.add_argument("worktree_name", help="Name of worktree to sync")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    manager = WorktreeManager(args.project_root)

    try:
        if args.command == "create":
            result = manager.create_worktree(
                args.project_id, args.work_type, args.feature_name, args.base_branch
            )
            print(json.dumps(result, indent=2))

        elif args.command == "list":
            worktrees = manager.list_worktrees()
            print(json.dumps(worktrees, indent=2))

        elif args.command == "remove":
            result = manager.remove_worktree(args.worktree_name, args.force)
            print(json.dumps(result, indent=2))

        elif args.command == "sync":
            result = manager.sync_worktree(args.worktree_name)
            print(json.dumps(result, indent=2))

    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
