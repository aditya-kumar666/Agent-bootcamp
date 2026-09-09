"""File operations tools for agents."""

import os
from pathlib import Path
from typing import Optional


class FileToolsPlugin:
    """Plugin for file system operations with safety checks."""

    def __init__(self, workspace_root: Optional[Path] = None):
        """Initialize the file tools plugin.
        
        Args:
            workspace_root: Root directory for workspace operations. 
                          If None, uses current working directory.
        """
        self.workspace_root = workspace_root or Path.cwd()

    def _validate_path(self, path: str) -> bool:
        """Validate that a path is within the workspace root.
        
        Args:
            path: Path to validate
            
        Returns:
            True if path is within workspace, False otherwise
        """
        try:
            full_path = (self.workspace_root / path).resolve()
            workspace_resolved = self.workspace_root.resolve()
            return str(full_path).startswith(str(workspace_resolved))
        except Exception:
            return False

    def read_file(self, path: str) -> str:
        """Read file content.
        
        Args:
            path: Path to file relative to workspace
            
        Returns:
            File content or error message
        """
        try:
            if not self._validate_path(path):
                return "DENIED_OUTSIDE_WORKSPACE"
            
            file_path = self.workspace_root / path
            if not file_path.exists():
                return "FILE_NOT_FOUND"
            
            return file_path.read_text(encoding="utf-8")
        except Exception as ex:
            return f"ERROR_READING_FILE: {str(ex)}"

    def write_file(self, path: str, content: str) -> str:
        """Write content to file.
        
        Args:
            path: Path to file relative to workspace
            content: Content to write
            
        Returns:
            Status message
        """
        try:
            if not self._validate_path(path):
                return "DENIED_OUTSIDE_WORKSPACE"
            
            trimmed = content.strip()
            if not trimmed or trimmed in ("...", "None", "pass") or trimmed == "...":
                return "ERROR_REJECTED: Cannot write placeholder ellipsis (...) to file. Provide complete implementation."
            
            file_path = self.workspace_root / path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            return "WRITE_OK"
        except Exception as ex:
            return f"ERROR_WRITING_FILE: {str(ex)}"

    def search_files(self, pattern: str, limit: int = 20) -> str:
        """Search for files matching a pattern.
        
        Args:
            pattern: Pattern to search for (case-insensitive substring match)
            limit: Maximum number of results to return
            
        Returns:
            Newline-separated list of matching files
        """
        try:
            matches = []
            for file_path in self.workspace_root.rglob("*"):
                if file_path.is_file() and pattern.lower() in str(file_path).lower():
                    matches.append(str(file_path.relative_to(self.workspace_root)))
                    if len(matches) >= limit:
                        break
            
            return "\n".join(matches) if matches else "NO_MATCHES_FOUND"
        except Exception as ex:
            return f"ERROR_SEARCHING: {str(ex)}"

    def list_directory(self, path: str = ".") -> str:
        """List files in a directory.
        
        Args:
            path: Directory path relative to workspace
            
        Returns:
            Newline-separated list of files and directories
        """
        try:
            if not self._validate_path(path):
                return "DENIED_OUTSIDE_WORKSPACE"
            
            dir_path = self.workspace_root / path
            if not dir_path.exists():
                return "DIRECTORY_NOT_FOUND"
            
            items = []
            for item in sorted(dir_path.iterdir()):
                relative = str(item.relative_to(self.workspace_root))
                suffix = "/" if item.is_dir() else ""
                items.append(f"{relative}{suffix}")
            
            return "\n".join(items) if items else "EMPTY_DIRECTORY"
        except Exception as ex:
            return f"ERROR_LISTING_DIRECTORY: {str(ex)}"

    def delete_file(self, path: str) -> str:
        """Delete a file.
        
        Args:
            path: Path to file relative to workspace
            
        Returns:
            Status message
        """
        try:
            if not self._validate_path(path):
                return "DENIED_OUTSIDE_WORKSPACE"
            
            file_path = self.workspace_root / path
            if not file_path.exists():
                return "FILE_NOT_FOUND"
            
            if file_path.is_dir():
                return "TARGET_IS_DIRECTORY"
            
            file_path.unlink()
            return "DELETE_OK"
        except Exception as ex:
            return f"ERROR_DELETING_FILE: {str(ex)}"
