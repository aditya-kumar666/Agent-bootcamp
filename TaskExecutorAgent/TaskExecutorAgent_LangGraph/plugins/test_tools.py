"""Test execution tools for agents."""

import subprocess
from pathlib import Path
from typing import Optional


class TestToolsPlugin:
    """Plugin for running tests."""

    def __init__(self, workspace_root: Optional[Path] = None):
        """Initialize the test tools plugin.
        
        Args:
            workspace_root: Root directory for workspace operations.
                          If None, uses current working directory.
        """
        self.workspace_root = workspace_root or Path.cwd()

    def run_tests(self, test_filter: Optional[str] = None, timeout: int = 30) -> str:
        """Run tests in the workspace.
        
        Args:
            test_filter: Optional filter for specific tests
            timeout: Timeout in seconds for test execution
            
        Returns:
            Test output or error message
        """
        try:
            # Try Python pytest first
            cmd = ["python", "-m", "pytest", "-v"]
            if test_filter:
                cmd.append(test_filter)
            
            result = subprocess.run(
                cmd,
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}\n\nReturn code: {result.returncode}"
        except subprocess.TimeoutExpired:
            return f"TESTS_TIMEOUT_AFTER_{timeout}_SECONDS"
        except FileNotFoundError:
            return "PYTEST_NOT_FOUND_TRY_UNITTEST"
        except Exception as ex:
            return f"ERROR_RUNNING_TESTS: {str(ex)}"

    def run_unittest(self, module: Optional[str] = None, timeout: int = 30) -> str:
        """Run unittest tests.
        
        Args:
            module: Optional specific test module to run
            timeout: Timeout in seconds for test execution
            
        Returns:
            Test output or error message
        """
        try:
            cmd = ["python", "-m", "unittest"]
            if module:
                cmd.append(module)
            else:
                cmd.extend(["discover", "-s", "tests"])
            
            result = subprocess.run(
                cmd,
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}\n\nReturn code: {result.returncode}"
        except subprocess.TimeoutExpired:
            return f"TESTS_TIMEOUT_AFTER_{timeout}_SECONDS"
        except Exception as ex:
            return f"ERROR_RUNNING_UNITTESTS: {str(ex)}"

    def check_syntax(self, file_path: str) -> str:
        """Check Python file syntax.
        
        Args:
            file_path: Path to Python file relative to workspace
            
        Returns:
            Syntax check result
        """
        try:
            full_path = self.workspace_root / file_path
            if not full_path.exists():
                return "FILE_NOT_FOUND"
            
            with open(full_path, "r", encoding="utf-8") as f:
                compile(f.read(), file_path, "exec")
            
            return "SYNTAX_OK"
        except SyntaxError as ex:
            return f"SYNTAX_ERROR: Line {ex.lineno}: {ex.msg}"
        except Exception as ex:
            return f"ERROR_CHECKING_SYNTAX: {str(ex)}"

    def run_linter(self, file_path: Optional[str] = None, timeout: int = 30) -> str:
        """Run pylint or flake8 linter.
        
        Args:
            file_path: Optional specific file to lint
            timeout: Timeout in seconds
            
        Returns:
            Linter output or error message
        """
        try:
            cmd = ["python", "-m", "flake8"]
            if file_path:
                cmd.append(file_path)
            else:
                cmd.append(".")
            
            result = subprocess.run(
                cmd,
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return result.stdout if result.stdout else "NO_LINTING_ISSUES_FOUND"
        except subprocess.TimeoutExpired:
            return f"LINTING_TIMEOUT_AFTER_{timeout}_SECONDS"
        except FileNotFoundError:
            return "FLAKE8_NOT_FOUND_INSTALL_WITH_PIP"
        except Exception as ex:
            return f"ERROR_RUNNING_LINTER: {str(ex)}"
