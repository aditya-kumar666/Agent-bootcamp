"""Clear entrypoint: run workflow WITH tool-calling support."""

import sys
from main_with_tools import main


if __name__ == "__main__":
    # Parse command-line arguments
    language = "csharp"  # default
    if len(sys.argv) > 1:
        language = sys.argv[1]
    
    # Show usage info
    if language in ["-h", "--help", "help"]:
        print("\nMulti-Language Task Executor (WITH tools)")
        print("="*60)
        print("\nUsage:")
        print("  python run_with_tools.py [language]")
        print("\nSupported languages:")
        print("  csharp (default)  - Generate C#/.NET Todo app")
        print("  java              - Generate Java Todo app (requires Maven)")
        print("  python            - Generate Python Todo app")
        print("  go                - Generate Go Todo app (requires Go SDK)")
        print("\nExamples:")
        print("  python run_with_tools.py              # Default C#")
        print("  python run_with_tools.py java         # Java app")
        print("  python run_with_tools.py python       # Python app")
        print("  python run_with_tools.py go           # Go app")
        print()
        sys.exit(0)
    
    main(language=language)
