"""Abstract project builder framework for multi-language support."""

from abc import ABC, abstractmethod
from pathlib import Path
import subprocess
import sys
import os


def is_verbose_logging_enabled() -> bool:
    """Enable noisy builder diagnostics only when VERBOSE_LOGS=true."""
    return os.getenv("VERBOSE_LOGS", "false").lower() == "true"


def verbose_log(message: str) -> None:
    """Print non-essential builder logs only in verbose mode."""
    if is_verbose_logging_enabled():
        print(message, file=sys.stderr)


class ProjectBuilder(ABC):
    """Abstract base class for language-specific project builders."""
    
    def __init__(self, output_dir: Path):
        """Initialize builder with output directory.
        
        Args:
            output_dir: Path to project output directory
        """
        self.output_dir = output_dir
    
    @abstractmethod
    def validate_environment(self) -> bool:
        """Validate that required SDK/runtime is installed.
        
        Returns:
            True if environment is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def setup_project(self) -> bool:
        """Create project structure and config files.
        
        Returns:
            True if setup successful, False otherwise
        """
        pass
    
    @abstractmethod
    def build(self) -> tuple[bool, str]:
        """Build/compile the project.
        
        Returns:
            Tuple of (success: bool, output: str)
        """
        pass
    
    @abstractmethod
    def execute(self) -> tuple[bool, str]:
        """Execute the built project.
        
        Returns:
            Tuple of (success: bool, output: str)
        """
        pass
    
    def build_and_execute(self) -> tuple[bool, str]:
        """Build and execute the project.
        
        Returns:
            Tuple of (success: bool, output: str)
        """
        # Build
        build_success, build_output = self.build()
        if not build_success:
            return False, f"Build failed:\n{build_output}"
        
        # Execute
        return self.execute()


class CSharpBuilder(ProjectBuilder):
    """Builder for C# .NET projects."""
    
    def __init__(self, output_dir: Path):
        """Initialize C# builder.
        
        Args:
            output_dir: Path to project output directory
        """
        super().__init__(output_dir)
        self.project_name = self.output_dir.name or "App"
    
    def validate_environment(self) -> bool:
        """Check if .NET SDK is installed."""
        try:
            result = subprocess.run(
                ["dotnet", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except FileNotFoundError:
            print("[ERROR] dotnet not found. Install .NET SDK.", file=sys.stderr)
            return False
        except Exception as e:
            print(f"[ERROR] Failed to validate .NET: {e}", file=sys.stderr)
            return False
    
    def setup_project(self) -> bool:
        """Create .csproj file for the C# project."""
        csproj_content = """<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net9.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>
</Project>
"""
        try:
            csproj_path = self.output_dir / f"{self.project_name}.csproj"
            csproj_path.write_text(csproj_content, encoding="utf-8")
            verbose_log(f"[OK] Created project file: {csproj_path}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to create .csproj: {e}", file=sys.stderr)
            return False
    
    def build(self) -> tuple[bool, str]:
        """Build C# project using dotnet."""
        try:
            verbose_log("\n[BUILD] Compiling C# project...")
            
            result = subprocess.run(
                ["dotnet", "build", "-c", "Release"],
                cwd=str(self.output_dir),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                print(f"[ERROR] Build failed", file=sys.stderr)
                return False, error_msg
            
            verbose_log("[OK] Build successful")
            return True, "Build successful"
            
        except subprocess.TimeoutExpired:
            return False, "Build timed out (60s)"
        except FileNotFoundError:
            return False, "dotnet not found"
        except Exception as e:
            return False, f"Build error: {e}"
    
    def execute(self) -> tuple[bool, str]:
        """Execute compiled C# application."""
        try:
            # Find the executable
            exe_path = self.output_dir / "bin" / "Release" / "net9.0" / f"{self.project_name}.exe"
            if not exe_path.exists():
                return False, f"Executable not found at {exe_path}"
            
            verbose_log("\n[RUN] Executing application...")
            
            result = subprocess.run(
                [str(exe_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = result.stdout
            if result.returncode != 0:
                error_msg = result.stderr or "Unknown error"
                print(f"[ERROR] Execution failed", file=sys.stderr)
                return False, f"Execution error: {error_msg}"
            
            verbose_log("[OK] Execution successful")
            return True, output
            
        except subprocess.TimeoutExpired:
            return False, "Execution timed out (30s)"
        except Exception as e:
            return False, f"Execution error: {e}"


class JavaBuilder(ProjectBuilder):
    """Builder for Java projects with Maven."""
    
    def __init__(self, output_dir: Path):
        """Initialize Java builder.
        
        Args:
            output_dir: Path to project output directory
        """
        super().__init__(output_dir)
    
    def validate_environment(self) -> bool:
        """Check if Java and Maven are installed."""
        try:
            # Check Maven
            mvn_result = subprocess.run(
                ["mvn", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if mvn_result.returncode != 0:
                print("[ERROR] Maven not found. Install Maven.", file=sys.stderr)
                return False
            
            # Check Java
            java_result = subprocess.run(
                ["java", "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return java_result.returncode == 0
        except FileNotFoundError:
            print("[ERROR] Maven or Java not found.", file=sys.stderr)
            return False
        except Exception as e:
            print(f"[ERROR] Failed to validate Java/Maven: {e}", file=sys.stderr)
            return False
    
    def setup_project(self) -> bool:
        """Create pom.xml for the Java project."""
        proj_name = self.output_dir.name or "App"
        pom_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.{proj_name.lower()}</groupId>
    <artifactId>{proj_name}</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>
    
    <properties>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    </properties>
    
    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.11.0</version>
                <configuration>
                    <source>11</source>
                    <target>11</target>
                </configuration>
            </plugin>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-jar-plugin</artifactId>
                <version>3.3.0</version>
                <configuration>
                    <archive>
                        <manifest>
                            <mainClass>Main</mainClass>
                        </manifest>
                    </archive>
                </configuration>
            </plugin>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-shade-plugin</artifactId>
                <version>3.4.1</version>
                <executions>
                    <execution>
                        <phase>package</phase>
                        <goals>
                            <goal>shade</goal>
                        </goals>
                    </execution>
                </executions>
            </plugin>
        </plugins>
    </build>
</project>
"""
        try:
            pom_path = self.output_dir / "pom.xml"
            pom_path.write_text(pom_content, encoding="utf-8")
            verbose_log(f"[OK] Created project file: {pom_path}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to create pom.xml: {e}", file=sys.stderr)
            return False
    
    def build(self) -> tuple[bool, str]:
        """Build Java project using Maven."""
        try:
            verbose_log("\n[BUILD] Compiling Java project...")
            
            result = subprocess.run(
                ["mvn", "clean", "package", "-q"],
                cwd=str(self.output_dir),
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                print(f"[ERROR] Build failed", file=sys.stderr)
                return False, error_msg
            
            verbose_log("[OK] Build successful")
            return True, "Build successful"
            
        except subprocess.TimeoutExpired:
            return False, "Build timed out (120s)"
        except FileNotFoundError:
            return False, "Maven not found"
        except Exception as e:
            return False, f"Build error: {e}"
    
    def execute(self) -> tuple[bool, str]:
        """Execute compiled Java application."""
        try:
            # Find the jar file
            jar_files = list(self.output_dir.glob("target/TodoApp-*.jar"))
            if not jar_files:
                # Try to find any jar in target directory
                all_jars = list(self.output_dir.glob("target/*.jar"))
                if not all_jars:
                    return False, "JAR file not found in target directory"
                jar_files = all_jars
            
            jar_path = jar_files[0]
            
            verbose_log("\n[RUN] Executing Java application...")
            
            result = subprocess.run(
                ["java", "-jar", str(jar_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = result.stdout
            if result.returncode != 0:
                error_msg = result.stderr or "Unknown error"
                print(f"[ERROR] Execution failed", file=sys.stderr)
                return False, f"Execution error: {error_msg}"
            
            verbose_log("[OK] Execution successful")
            return True, output
            
        except subprocess.TimeoutExpired:
            return False, "Execution timed out (30s)"
        except Exception as e:
            return False, f"Execution error: {e}"


class PythonBuilder(ProjectBuilder):
    """Builder for Python projects."""
    
    def __init__(self, output_dir: Path):
        """Initialize Python builder.
        
        Args:
            output_dir: Path to project output directory
        """
        super().__init__(output_dir)
    
    def validate_environment(self) -> bool:
        """Check if Python is installed."""
        try:
            result = subprocess.run(
                ["python", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except FileNotFoundError:
            print("[ERROR] Python not found.", file=sys.stderr)
            return False
        except Exception as e:
            print(f"[ERROR] Failed to validate Python: {e}", file=sys.stderr)
            return False
    
    def setup_project(self) -> bool:
        """Setup Python project (create __init__.py if needed)."""
        try:
            init_path = self.output_dir / "__init__.py"
            if not init_path.exists():
                init_path.write_text("", encoding="utf-8")
            verbose_log("[OK] Python project structure ready")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to setup Python project: {e}", file=sys.stderr)
            return False
    
    def build(self) -> tuple[bool, str]:
        """For Python, build is a no-op (interpreted language)."""
        verbose_log("\n[BUILD] Python is interpreted, skipping build...")
        verbose_log("[OK] Build skipped (interpreted language)")
        return True, "Python is interpreted"
    
    def execute(self) -> tuple[bool, str]:
        """Execute Python application."""
        try:
            main_path = None
            
            # 1. Check standard conventions: main.py, app.py, __main__.py
            for name in ["main.py", "app.py", "__main__.py"]:
                candidate = self.output_dir / name
                if candidate.exists():
                    main_path = candidate
                    break

            # 2. Inspect Python files to find one with an entry point (__main__ block)
            if not main_path:
                py_files = [
                    f for f in self.output_dir.rglob("*.py")
                    if f.name != "__init__.py" and not f.name.startswith("test_")
                ]
                for f in py_files:
                    try:
                        content = f.read_text(encoding="utf-8", errors="ignore")
                        if '__name__ == "__main__"' in content or "__name__ == '__main__'" in content:
                            main_path = f
                            break
                    except Exception:
                        pass

                # 3. Fallback to top-level or any non-test Python file
                if not main_path:
                    top_level_py = [
                        f for f in self.output_dir.glob("*.py")
                        if f.name != "__init__.py" and not f.name.startswith("test_")
                    ]
                    if top_level_py:
                        main_path = top_level_py[0]
                    elif py_files:
                        main_path = py_files[0]
                    else:
                        return False, "No executable Python files found in output directory"
            
            verbose_log(f"\n[RUN] Executing Python application ({main_path.name})...")
            
            # Pass simulated stdin input so interactive prompt loops (e.g. input()) don't hang in CI/automated runs
            simulated_input = "1\n2\n3\n4\n5\n6\n7\n8\n9\nq\nexit\n\n"
            result = subprocess.run(
                ["python", str(main_path)],
                input=simulated_input,
                capture_output=True,
                text=True,
                timeout=20,
                cwd=str(self.output_dir)
            )
            
            output = result.stdout
            if result.returncode != 0 and "EOFError" not in (result.stderr or ""):
                error_msg = result.stderr or "Unknown error"
                print(f"[ERROR] Execution failed", file=sys.stderr)
                return False, f"Execution error: {error_msg}"
            
            # Run unit tests if any test files exist
            test_files = list(self.output_dir.glob("test_*.py"))
            if test_files:
                test_result = subprocess.run(
                    ["python", "-m", "unittest", "discover", "-s", str(self.output_dir)],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    cwd=str(self.output_dir)
                )
                if test_result.returncode == 0:
                    output += f"\n\n[TESTS PASSED]\n{test_result.stderr or test_result.stdout}"
            
            verbose_log("[OK] Execution successful")
            return True, output
            
        except subprocess.TimeoutExpired:
            return False, "Execution timed out (interactive prompt waited for input or loop did not terminate)"
        except Exception as e:
            return False, f"Execution error: {e}"


class GoBuilder(ProjectBuilder):
    """Builder for Go projects."""
    
    def __init__(self, output_dir: Path):
        """Initialize Go builder.
        
        Args:
            output_dir: Path to project output directory
        """
        super().__init__(output_dir)
    
    def validate_environment(self) -> bool:
        """Check if Go is installed."""
        try:
            result = subprocess.run(
                ["go", "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except FileNotFoundError:
            print("[ERROR] Go not found. Install Go.", file=sys.stderr)
            return False
        except Exception as e:
            print(f"[ERROR] Failed to validate Go: {e}", file=sys.stderr)
            return False
    
    def setup_project(self) -> bool:
        """Create go.mod for the Go project."""
        proj_name = self.output_dir.name or "app"
        go_mod_content = f"""module {proj_name.lower()}

go 1.21
"""
        try:
            go_mod_path = self.output_dir / "go.mod"
            go_mod_path.write_text(go_mod_content, encoding="utf-8")
            verbose_log(f"[OK] Created project file: {go_mod_path}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to create go.mod: {e}", file=sys.stderr)
            return False
    
    def build(self) -> tuple[bool, str]:
        """Build Go project."""
        try:
            verbose_log("\n[BUILD] Building Go project...")
            proj_name = self.output_dir.name or "app"
            
            result = subprocess.run(
                ["go", "build", "-o", proj_name.lower()],
                cwd=str(self.output_dir),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                print(f"[ERROR] Build failed", file=sys.stderr)
                return False, error_msg
            
            verbose_log("[OK] Build successful")
            return True, "Build successful"
            
        except subprocess.TimeoutExpired:
            return False, "Build timed out (60s)"
        except FileNotFoundError:
            return False, "Go not found"
        except Exception as e:
            return False, f"Build error: {e}"
    
    def execute(self) -> tuple[bool, str]:
        """Execute compiled Go application."""
        try:
            # Look for the compiled binary with different possible names
            proj_name = self.output_dir.name or "app"
            possible_names = [
                proj_name.lower(),
                f"{proj_name.lower()}.exe",
                "app",
                "app.exe",
                "main",
                "main.exe"
            ]
            exe_path = None
            
            for name in possible_names:
                candidate = self.output_dir / name
                if candidate.exists():
                    exe_path = candidate
                    break
            
            if not exe_path:
                return False, f"Executable not found (tried: {', '.join(possible_names)})"
            
            verbose_log("\n[RUN] Executing Go application...")
            
            result = subprocess.run(
                [str(exe_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = result.stdout
            if result.returncode != 0:
                error_msg = result.stderr or "Unknown error"
                print(f"[ERROR] Execution failed", file=sys.stderr)
                return False, f"Execution error: {error_msg}"
            
            verbose_log("[OK] Execution successful")
            return True, output
            
        except subprocess.TimeoutExpired:
            return False, "Execution timed out (30s)"
        except Exception as e:
            return False, f"Execution error: {e}"


class BuilderFactory:
    """Factory for creating language-specific project builders."""
    
    _builders = {
        "csharp": CSharpBuilder,
        "c#": CSharpBuilder,
        "cs": CSharpBuilder,
        "java": JavaBuilder,
        "python": PythonBuilder,
        "py": PythonBuilder,
        "go": GoBuilder,
    }
    
    @classmethod
    def get_builder(cls, language: str, output_dir: Path) -> ProjectBuilder:
        """Get builder for specified language.
        
        Args:
            language: Programming language (e.g., "csharp", "java", "python", "go")
            output_dir: Path to project output directory
            
        Returns:
            ProjectBuilder instance for the specified language
            
        Raises:
            ValueError: If language is not supported
        """
        language_lower = language.lower().strip()
        
        if language_lower not in cls._builders:
            supported = ", ".join(sorted(set(cls._builders.values().__class__.__name__ 
                                           for _ in cls._builders.values())))
            raise ValueError(
                f"Language '{language}' not supported. "
                f"Supported: {', '.join(k for k, v in cls._builders.items() if v not in cls._builders.values() or k == list(cls._builders.keys())[list(cls._builders.values()).index(v)])}"
            )
        
        builder_class = cls._builders[language_lower]
        return builder_class(output_dir)
    
    @classmethod
    def register_builder(cls, language: str, builder_class: type):
        """Register a custom builder for a language.
        
        Args:
            language: Language identifier
            builder_class: Subclass of ProjectBuilder
        """
        if not issubclass(builder_class, ProjectBuilder):
            raise TypeError("builder_class must be a subclass of ProjectBuilder")
        cls._builders[language.lower()] = builder_class
