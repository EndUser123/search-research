# TSK-DUF6-RAW-OUTPUT-FIX: Data Model Specification

## Core Data Structures

### DUF6OutputMode
```python
from enum import Enum

class DUF6OutputMode(Enum):
    """Output mode enumeration for DUF6 validation"""

    SUMMARY = "summary"      # Default: processed summaries with metrics
    RAW = "raw"             # Raw tool output without processing
    JSON = "json"           # Structured JSON format for integration

    def get_description(self) -> str:
        """Get human-readable description of output mode"""
        descriptions = {
            self.SUMMARY: "Processed summaries with issue counts and timing",
            self.RAW: "Raw tool output (ruff JSON, mypy errors, bandit findings)",
            self.JSON: "Structured JSON format for CI/CD integration"
        }
        return descriptions[self]
```

### RawOutputConfig
```python
@dataclass
class RawOutputConfig:
    """Configuration for raw output mode behavior"""

    output_mode: DUF6OutputMode = DUF6OutputMode.SUMMARY
    preserve_encoding: bool = True
    buffer_size: int = 8192
    stream_output: bool = False

    def should_process_output(self) -> bool:
        """Check if output should be processed or passed through raw"""
        return self.output_mode != DUF6OutputMode.RAW

    def get_encoding(self) -> str:
        """Get encoding for output streams"""
        return 'utf-8' if self.preserve_encoding else 'charmap'
```

### ToolRawResult
```python
@dataclass
class ToolRawResult:
    """Raw result from individual validation tools without processing"""

    tool_name: str                      # "ruff", "mypy", "bandit"
    exit_code: int                     # Process exit code
    stdout: str                        # Raw standard output
    stderr: str                        # Raw standard error
    execution_time: float              # Tool execution time in seconds
    target_files: List[str]            # Files validated by this tool
    encoding_issues: List[str] = None   # Any encoding warnings encountered

    def get_output_format(self) -> str:
        """Get the expected output format for this tool"""
        formats = {
            "ruff": "json",
            "mypy": "text",
            "bandit": "json",
            "radon": "text",
            "vulture": "text"
        }
        return formats.get(self.tool_name.lower(), "text")

    def is_json_output(self) -> bool:
        """Check if this tool produces JSON output"""
        return self.get_output_format() == "json"

    def has_encoding_issues(self) -> bool:
        """Check if there were any encoding issues"""
        return bool(self.encoding_issues)
```

### ProcessedValidationResult
```python
@dataclass
class ProcessedValidationResult:
    """Processed validation result (current default behavior)"""

    tool_name: str
    success: bool
    issues_found: int
    execution_time: float
    error_message: Optional[str] = None
    issues_data: Optional[List[Dict[str, Any]]] = None

    def to_summary_dict(self) -> Dict[str, Any]:
        """Convert to summary dictionary for output"""
        return {
            "tool": self.tool_name,
            "status": "SUCCESS" if self.success else "FAILED",
            "issues": self.issues_found,
            "time": f"{self.execution_time:.2f}s",
            "error": self.error_message
        }
```

### ValidationSessionConfig
```python
@dataclass
class ValidationSessionConfig:
    """Configuration for validation session execution"""

    scope: str                          # "L1", "L2", "L3"
    output_config: RawOutputConfig
    timeout_seconds: int = 300
    parallel_execution: bool = True
    target_files: Optional[List[str]] = None

    def is_raw_mode(self) -> bool:
        """Check if session is in raw output mode"""
        return self.output_config.output_mode == DUF6OutputMode.RAW

    def get_output_handler(self) -> 'OutputHandler':
        """Get appropriate output handler for this configuration"""
        if self.is_raw_mode():
            return RawOutputHandler(self.output_config)
        else:
            return ProcessedOutputHandler(self.output_config)
```

## Output Handlers

### OutputHandler (Base)
```python
from abc import ABC, abstractmethod

class OutputHandler(ABC):
    """Base class for different output handling strategies"""

    def __init__(self, config: RawOutputConfig):
        self.config = config

    @abstractmethod
    def handle_tool_result(self, result: ToolRawResult) -> None:
        """Handle output from a single tool execution"""
        pass

    @abstractmethod
    def finalize_session(self) -> None:
        """Finalize and output session summary"""
        pass

    def get_encoding(self) -> str:
        """Get output encoding for this handler"""
        return self.config.get_encoding()
```

### RawOutputHandler
```python
class RawOutputHandler(OutputHandler):
    """Handler for raw tool output without processing"""

    def handle_tool_result(self, result: ToolRawResult) -> None:
        """Output raw tool result directly to stdout/stderr"""
        encoding = self.get_encoding()

        # Output raw stdout
        if result.stdout:
            try:
                print(result.stdout, encoding=encoding)
            except UnicodeEncodeError as e:
                # Handle encoding issues gracefully
                self._handle_encoding_error(result.stdout, e)

        # Output raw stderr if it exists
        if result.stderr:
            print(f"[{result.tool_name} STDERR]:", file=sys.stderr)
            try:
                print(result.stderr, file=sys.stderr, encoding=encoding)
            except UnicodeEncodeError as e:
                self._handle_encoding_error(result.stderr, e)

    def finalize_session(self) -> None:
        """No final summary for raw mode - tools output directly"""
        pass

    def _handle_encoding_error(self, content: str, error: UnicodeEncodeError) -> None:
        """Handle encoding errors by logging and attempting fallback"""
        print(f"[ENCODING WARNING] {str(error)}", file=sys.stderr)
        try:
            # Fallback: replace problematic characters
            safe_content = content.encode('ascii', errors='replace').decode('ascii')
            print(safe_content, encoding=self.get_encoding())
        except Exception as fallback_error:
            print(f"[ENCODING ERROR] Could not display content: {fallback_error}", file=sys.stderr)
```

### ProcessedOutputHandler
```python
class ProcessedOutputHandler(OutputHandler):
    """Handler for processed output (current default behavior)"""

    def __init__(self, config: RawOutputConfig):
        super().__init__(config)
        self.results: List[ProcessedValidationResult] = []

    def handle_tool_result(self, result: ToolRawResult) -> None:
        """Process tool result and add to results list"""
        processed = self._process_result(result)
        self.results.append(processed)

    def finalize_session(self) -> None:
        """Output processed summary and session information"""
        self._output_results_summary()
        self._output_execution_summary()

    def _process_result(self, result: ToolRawResult) -> ProcessedValidationResult:
        """Process raw tool result into summary format"""
        # Parse issues from raw output based on tool type
        issues_count = self._parse_issues_count(result)

        return ProcessedValidationResult(
            tool_name=result.tool_name,
            success=result.exit_code == 0,
            issues_found=issues_count,
            execution_time=result.execution_time,
            error_message=result.stderr if result.exit_code != 0 else None
        )

    def _parse_issues_count(self, result: ToolRawResult) -> int:
        """Parse number of issues from raw tool output"""
        if result.is_json_output():
            try:
                data = json.loads(result.stdout)
                if isinstance(data, list):
                    return len(data)
                elif isinstance(data, dict):
                    return data.get('results', {}).get('issues_count', 0)
            except json.JSONDecodeError:
                pass

        # Fallback: count lines with error patterns
        lines = result.stdout.strip().split('\n')
        return len([line for line in lines if line.strip()])

    def _output_results_summary(self) -> None:
        """Output individual tool results summary"""
        print("DUF6 Validation Results:")
        print("=" * 50)

        for result in self.results:
            status = "SUCCESS" if result.success else "FAILED"
            time_str = f"{result.execution_time:.2f}s"

            print(f"{result.tool_name}: [{status}] {status}")
            print(f"    Issues found: {result.issues_found}")
            print(f"     Execution time: {time_str}")

            if result.error_message:
                print(f"   [FAIL] Error: {result.error_message}")

            print()

    def _output_execution_summary(self) -> None:
        """Output overall execution summary"""
        total_issues = sum(r.issues_found for r in self.results)
        successful_tools = sum(1 for r in self.results if r.success)
        total_tools = len(self.results)

        print(" EXECUTION SUMMARY:")
        print("-" * 25)
        print(f"Tools executed: {total_tools}")
        print(f"Tools succeeded: {successful_tools}")
        print(f"Tools failed: {total_tools - successful_tools}")
        print(f"Total issues found: {total_issues}")
        print(f"Total execution time: 0.00s")  # TODO: implement timing
```

## Data Flow Architecture

### Raw Mode Flow
```
User Input (--raw) → Tool Execution → RawOutputHandler → Direct stdout/stderr
```

### Summary Mode Flow (Default)
```
User Input (default) → Tool Execution → ProcessedOutputHandler → Summary Output
```

### Configuration Flow
```
CLI Arguments → ValidationSessionConfig → OutputHandler → Tool Results → Final Output
```

## Integration Points

### CLI Argument Integration
```python
def parse_arguments() -> ValidationSessionConfig:
    """Parse CLI arguments and create session configuration"""
    parser = argparse.ArgumentParser()
    parser.add_argument('scope', choices=['l1', 'l2', 'l3'])
    parser.add_argument('--raw', action='store_true', help='Output raw tool results')
    parser.add_argument('--output-format', choices=['text', 'json'], default='text')

    args = parser.parse_args()

    # Determine output mode
    if args.raw:
        output_mode = DUF6OutputMode.RAW
    elif args.output_format == 'json':
        output_mode = DUF6OutputMode.JSON
    else:
        output_mode = DUF6OutputMode.SUMMARY

    output_config = RawOutputConfig(
        output_mode=output_mode,
        preserve_encoding=True
    )

    return ValidationSessionConfig(
        scope=args.scope,
        output_config=output_config
    )
```

### Tool Execution Integration
```python
async def execute_tools_with_handler(config: ValidationSessionConfig) -> None:
    """Execute tools using appropriate output handler"""
    handler = config.get_output_handler()

    for tool in get_available_tools():
        result = await execute_tool(tool, config)
        handler.handle_tool_result(result)

    handler.finalize_session()
```

---

**This data model supports flexible output modes while maintaining backward compatibility and providing robust encoding handling for international character sets.**