"""Example script showing how to use the multi-language task executor."""

from main_with_tools import main

if __name__ == "__main__":
    import sys
    
    # Default to C# if no language specified
    language = sys.argv[1] if len(sys.argv) > 1 else "csharp"
    
    print(f"\n{'='*60}")
    print(f"Multi-Language Task Executor - {language.upper()}")
    print(f"{'='*60}\n")
    
    # Supported languages
    supported = ["csharp", "java", "python", "go"]
    
    if language not in supported:
        print(f"❌ Unsupported language: {language}")
        print(f"✅ Supported languages: {', '.join(supported)}")
        sys.exit(1)
    
    print(f"🚀 Generating {language} Todo application...")
    print(f"📦 Language builder: {language}")
    print()
    
    # Run with specified language
    main(language=language)
    
    print(f"\n✅ {language.upper()} generation complete!")
