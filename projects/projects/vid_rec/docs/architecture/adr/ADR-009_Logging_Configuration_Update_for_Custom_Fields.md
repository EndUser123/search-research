# ADR-009: Logging Configuration Update for Custom Fields

**Date**: 2025-06-28

**Status**: Accepted

**Authors**: Cline (AI Assistant)

## Context

In the Vid_ReC project, a persistent issue was encountered where custom fields set in log statements (such as `category` and `details`) were not appearing in the output, either in the console or in the JSON log file (`logs/vidrec.json`). This issue was critical as it prevented detailed diagnostic information from being captured and displayed as required by the logging guidelines outlined in `docs/LOGGING_GUIDE.md`. Despite multiple attempts to modify the logging configuration and code, the problem remained unresolved until a deep research analysis provided a comprehensive solution.

## Decision

To resolve the logging issue, the `structlog` configuration in `src/logger.py` was updated based on recommendations from a deep researcher. The key changes implemented are as follows:

1. **Processor Chain Update**: Changed the final processor in `structlog.configure()` from `render_to_log_kwargs` to `ProcessorFormatter.wrap_for_formatter`. This preserves the complete event dictionary structure, preventing the stripping of custom fields.
2. **Addition of ExtraAdder**: Added `structlog.stdlib.ExtraAdder()` at the beginning of the `foreign_pre_chain` for both console and JSON formatters to ensure custom fields passed via keyword arguments are captured and included in the output.
3. **Context Variables Handling**: Ensured `structlog.contextvars.merge_contextvars` is included as the first processor to handle context variables properly and prevent conflicts with explicit field assignments.

These changes were implemented in `src/logger.py` with the following code updates:

- Updated `configure_structlog()` to define shared processors and configure `structlog` with the correct processor chain.
- Modified `get_logging_config_dict()` to include `ExtraAdder` in the `foreign_pre_chain` for formatters.
- Simplified `setup_logging()` to use the updated configuration without redundant processor definitions.

## Consequences

### Positive Impacts
- **Custom Fields Displayed**: Custom fields such as `category="system"` and `details` are now correctly rendered in both console output and the JSON log file for critical events like processing interruptions and application shutdown.
- **Improved Diagnostics**: The inclusion of detailed diagnostic information in logs enhances troubleshooting and monitoring capabilities, aligning with the requirements in `docs/LOGGING_GUIDE.md`.
- **Maintainable Configuration**: The updated configuration follows `structlog` best practices, making it easier to maintain and extend logging functionality in the future.

### Negative Impacts
- **Potential Compatibility Issues**: The change in processor chain might affect any existing log parsing tools or scripts that expect a specific log format. However, since the JSON output now includes more fields, it should be backward compatible with most parsing logic.
- **Learning Curve**: Developers unfamiliar with the updated `structlog` configuration may need time to understand the new setup, though this is mitigated by documenting the decision in this ADR.

## Alternatives Considered

- **Manual Field Addition**: Manually adding custom fields to every log statement was considered but rejected due to its inefficiency and error-prone nature.
- **Custom Processor Development**: Developing a custom processor to handle field preservation was an option but was deemed unnecessary given the existing `structlog` capabilities once properly configured.
- **Switching Logging Libraries**: Moving to a different logging library like `loguru` was considered but rejected to avoid significant refactoring and potential disruptions to the existing codebase.

## Conclusion

The decision to update the `structlog` configuration as described ensures that custom logging fields are preserved and rendered correctly, addressing a critical requirement for the Vid_ReC project. This change enhances the project's logging capabilities without introducing significant negative impacts, and it is documented here to provide clarity and context for future development and maintenance efforts.
