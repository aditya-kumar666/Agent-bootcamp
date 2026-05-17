"""Test tool calling integration."""
print('🧪 Testing Tool Calling Integration\n')

# Test 1: Verify BaseAgent has invoke_with_tools
print('Test 1: BaseAgent.invoke_with_tools() method')
from agents.base_agent import BaseAgent
assert hasattr(BaseAgent, 'invoke_with_tools'), 'Method not found!'
print('✅ Method exists\n')

# Test 2: Verify agents use tool registry
print('Test 2: Agents receive tool registry')
from agents import CodingAgent, ReviewAgent
from main_with_tools import setup_tool_registry
from pathlib import Path
registry = setup_tool_registry()
agent = CodingAgent(Path('.') / 'prompts', tool_registry=registry)
assert agent.tool_registry is not None, 'Tool registry not set!'
print('✅ Tool registry configured\n')

# Test 3: Verify tool parsing
print('Test 3: Tool call parsing')
from plugins import ToolExecutor
executor = ToolExecutor(registry)

# Test ReAct format
text = 'Action: file_tools.read_file(path=models/user.py)'
parsed = executor.parse_tool_call(text)
assert parsed is not None, 'Parse failed!'
assert parsed['tool'] == 'file_tools.read_file', 'Wrong tool name!'
assert parsed['args']['path'] == 'models/user.py', 'Wrong args!'
print('✅ ReAct format parsing works')

# Test JSON format
import json
text_json = json.dumps({"tool": "test_tools.check_syntax", "args": {"file_path": "test.py"}})
parsed_json = executor.parse_tool_call(text_json)
assert parsed_json is not None, 'JSON parse failed!'
print('✅ JSON format parsing works')

# Test Markdown format
text_md = '```tool\n' + text_json + '\n```'
parsed_md = executor.parse_tool_call(text_md)
assert parsed_md is not None, 'Markdown parse failed!'
print('✅ Markdown format parsing works\n')

# Test 4: Verify tool execution
print('Test 4: Tool execution')
result = executor.execute_tool('file_tools.list_directory', path='.')
assert result is not None, 'Execution failed!'
result_preview = result.split('\n')[0] if result else 'no output'
print(f'✅ Tool executed successfully')
print(f'   Result sample: {result_preview}...\n')

# Test 5: Verify registry has 9 tools
print('Test 5: Tool registry')
tools = registry.list_tools()
assert len(tools) == 9, f'Expected 9 tools, got {len(tools)}'
print(f'✅ {len(tools)} tools registered:')
for tool in tools:
    print(f'   - {tool.name}')

print('\n' + '='*60)
print('✅ ALL TESTS PASSED - Tool Calling Ready!')
print('='*60)
print('\nTo see tools in action, run:')
print('  python demo_tool_calling.py')
print('\nOr use the full system:')
print('  python main_with_tools.py')
