# TSK-DUF6-IMPROVEMENTS: Data Model Specification

## Core Data Structures

### ValidationScope
```python
@dataclass
class ValidationScope:
    """Represents the semantic scoping hierarchy for DUF6 validation"""

    l1_files: List[str]          # Files touched/created in current session
    l2_directories: List[str]    # Directories containing L1 files
    l3_project: Optional[str]    # Project root containing L2 directories
    scope_type: str              # "L1", "L2", "L3", or "COMBINED"
    confidence: float            # Scope detection confidence (0.0-1.0)

    def get_target_files(self, scope_filter: Optional[str] = None) -> List[str]:
        """Get target files based on scope filter"""
        pass

    def get_scope_summary(self) -> Dict[str, int]:
        """Get summary statistics for the scope"""
        pass
```

### ValidationResult
```python
@dataclass
class ValidationResult:
    """Enhanced validation result with timing and error information"""

    success: bool                    # Whether validation completed successfully
    metadata: Dict[str, Any]         # Tool results, issues found, etc.
    scope_info: ValidationScope      # Scope information used for validation
    timing_info: Optional[Dict[str, float]] = None  # Timing breakdown
    error_info: Optional[Dict[str, str]] = None     # Error details if failed

    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive validation summary"""
        pass

    def had_errors(self) -> bool:
        """Check if validation had errors"""
        return not self.success or self.error_info is not None
```

### TimingInfo
```python
@dataclass
class TimingInfo:
    """Detailed timing information for validation phases"""

    total_time: float               # Total validation time
    l1_scope_time: float            # L1 scope detection time
    l2_scope_time: float            # L2 scope detection time
    l3_scope_time: float            # L3 scope detection time
    tool_times: Dict[str, float]    # Individual tool execution times

    def get_performance_summary(self) -> str:
        """Get human-readable performance summary"""
        pass

    def identify_bottlenecks(self) -> List[str]:
        """Identify performance bottlenecks"""
        pass
```

## Configuration Models

### ValidationConfig
```python
@dataclass
class ValidationConfig:
    """Configuration for DUF6 validation behavior"""

    # Scope Configuration
    enable_l1_scope: bool = True
    enable_l2_scope: bool = True
    enable_l3_scope: bool = True
    default_scope: str = "L1"  # Default scope if no L1 files found

    # Tool Configuration
    ruff_enabled: bool = True
    mypy_enabled: bool = True
    bandit_enabled: bool = True
    tool_timeout: int = 300     # 5 minutes per tool

    # Performance Configuration
    enable_timing_logs: bool = True
    timing_precision: int = 2   # Decimal places in timing logs

    # Error Handling Configuration
    continue_on_tool_error: bool = True
    max_retries: int = 1
    enable_detailed_errors: bool = True

    # Legacy: No artificial limits
    # max_files_l1: int = 1000  # REMOVED - scope defines limits
    # max_files_l2: int = 5000  # REMOVED - scope defines limits
    # max_files_l3: int = 10000 # REMOVED - scope defines limits
```

## Tool Integration Models

### ToolResult
```python
@dataclass
class ToolResult:
    """Standardized result from individual validation tools"""

    tool_name: str                # "ruff", "mypy", "bandit"
    success: bool                 # Tool executed successfully
    exit_code: int               # Process exit code
    stdout: str                  # Tool standard output
    stderr: str                  # Tool standard error
    execution_time: float        # Tool execution time in seconds
    target_files: List[str]      # Files validated by this tool

    def parse_issues(self) -> List[Dict[str, Any]]:
        """Parse tool-specific output into standardized issues"""
        pass

    def get_issue_count(self) -> int:
        """Get total number of issues found"""
        pass
```

### ValidationError
```python
@dataclass
class ValidationError:
    """Standardized error information for validation failures"""

    error_type: str              # "TIMEOUT", "TOOL_NOT_FOUND", "PERMISSION", etc.
    tool_name: Optional[str]     # Tool that generated the error
    message: str                 # Human-readable error message
    details: Dict[str, Any]      # Additional error context
    timestamp: datetime          # When error occurred

    def get_user_friendly_message(self) -> str:
        """Get user-friendly error description"""
        pass

    def is_recoverable(self) -> bool:
        """Check if error is recoverable"""
        pass
```

## Consolidated Validation Helpers

### ValidationHelper
```python
class ValidationHelper:
    """Consolidated validation helper functions to eliminate code duplication"""

    @staticmethod
    def create_subprocess_command(tool_name: str, target_files: List[str],
                                 config: ValidationConfig) -> List[str]:
        """Create standardized subprocess command for validation tools"""
        pass

    @staticmethod
    def execute_tool_with_timeout(tool_name: str, cmd: List[str],
                                timeout: int) -> ToolResult:
        """Execute validation tool with timeout and error handling"""
        pass

    @staticmethod
    def parse_tool_output(tool_name: str, output: str) -> List[Dict[str, Any]]:
        """Parse tool-specific output into standardized format"""
        pass

    @staticmethod
    def create_validation_result(tool_results: List[ToolResult],
                               scope_info: ValidationScope,
                               timing_info: TimingInfo) -> ValidationResult:
        """Create consolidated ValidationResult from individual tool results"""
        pass
```

## State Tracking Models

### ValidationSession
```python
@dataclass
class ValidationSession:
    """Tracks validation session state and context"""

    session_id: str               # Unique session identifier
    start_time: datetime          # Session start time
    scopes_used: List[str]        # L1, L2, L3 scopes that were applied
    tools_executed: List[str]     # Tools that were run
    total_issues_found: int       # Total issues across all tools
    session_success: bool         # Overall session success

    def get_session_summary(self) -> Dict[str, Any]:
        """Get comprehensive session summary"""
        pass
```

## Performance Metrics

### PerformanceMetrics
```python
@dataclass
class PerformanceMetrics:
    """Performance metrics for validation optimization"""

    validation_sessions: List[ValidationSession]
    average_execution_time: float
    bottleneck_tools: List[str]
    scope_efficiency: Dict[str, float]  # Files per second by scope

    def get_optimization_recommendations(self) -> List[str]:
        """Get performance optimization recommendations"""
        pass

    def compare_performance(self, other_metrics: 'PerformanceMetrics') -> Dict[str, float]:
        """Compare performance with previous metrics"""
        pass
```

## Data Flow

```
User Request → Scope Detection (L1/L2/L3) → Target Files →
ValidationHelper.execute_tool_with_timeout() → ToolResult →
ValidationHelper.create_validation_result() → ValidationResult →
Performance Metrics & Session Tracking
```

## Data Persistence

### ValidationCache
```python
@dataclass
class ValidationCache:
    """Optional caching for repeated validations"""

    cache_key: str               # Based on file hashes and scope
    validation_result: ValidationResult
    cache_timestamp: datetime
    files_validated: List[str]   # Files included in this cache entry

    def is_cache_valid(self, current_files: List[str]) -> bool:
        """Check if cache is still valid for current files"""
        pass
```

---

*This data model supports the Force Multiplier Solo Dev approach with clear separation of concerns, minimal complexity, and maximum efficiency.*