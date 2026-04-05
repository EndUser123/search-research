# TQDM Progress Bar Requirements for dnld_telegram

## Project Context
This document outlines the specific requirements for implementing tqdm progress bars in the dnld_telegram project for downloading media files from Telegram with proper concurrent download tracking and overall progress monitoring.

## Core Requirements

### 1. Progress Tracking Scope
- **Target**: Telegram file downloads with known file sizes
- **Overall Progress**: Track total files to download vs completed files
- **Individual Progress**: Track download progress for each active file
- **Progress Granularity**:
  - Individual bars: Per downloaded chunk/byte
  - Overall bar: Per completed file

### 2. Display Requirements
- **Overall Progress Bar**: Always visible, shows total session progress
- **Individual File Bars**: One bar per active concurrent download (1-4 max)
- **Completed Bars**: Should remain visible for user reference
- **Terminal Environment**: Windows 11 (cmd, powershell, VSCode terminal)
- **Layout Constraints**:
  - No text wrapping
  - Vertical alignment between all bars
  - Adaptive width that handles terminal resizing
  - Consistent formatting across all progress elements

### 3. Concurrency Model
- **Framework**: AsyncIO-based concurrent downloads
- **Concurrency Level**: User-configurable via `--max-concurrent` (1-4 downloads)
- **Active Bars**: Maintain relative positions during session
- **Position Management**: Automatic position allocation to prevent overlapping

### 4. Performance Considerations
- **Memory Usage**: Efficient resource usage with proper cleanup
- **Update Frequency**: Balanced refresh rate to avoid terminal flickering
- **Resource Recovery**: Proper cleanup of completed progress bars

### 5. Error Handling and Robustness
- **Failure Visibility**: Failed downloads should be clearly indicated
- **Progress Accuracy**: Bars should reflect actual download state
- **No Resume Support**: Telegram downloads don't resume, so partial progress on failure is acceptable
- **Exception Handling**: Proper cleanup of progress bars on download failures
- **Display Integrity**: Progress display should remain accurate during errors

### 6. User Experience
- **File Type Icons**: Use existing icon dictionary for different media types
- **Information Display**:
  - Overall: File count, completion percentage, elapsed time
  - Individual: Filename (truncated if needed), bytes downloaded, transfer rate, ETA
- **Logging Integration**: Use `tqdm.write()` for non-interfering log messages
- **Filename Management**: Truncate long filenames to prevent wrapping while maintaining readability
- **Vertical Alignment**: Consistent column alignment for descriptions and metrics across all bars

## Technical Requirements

### Display Configuration
- **Output Destination**: `file=sys.stdout` for consistent terminal output
- **Bar Format**: Consistent formatting with proper column alignment
- **Width Management**: Adaptive width that respects terminal boundaries
- **Refresh Control**: Appropriate `mininterval`/`maxinterval` settings

### Positioning Requirements
- **Position Strategy**: Automatic position allocation starting from position 0 (overall) + 1,2,3,4 (individual)
- **Conflict Prevention**: No overlapping or overwriting between bars
- **Active Bar Grouping**: Maintain relative positions of active download bars
- **Cleanup Protocol**: Proper bar closure and position release on completion/failure

### Integration Requirements
- **AsyncIO Support**: Use `tqdm.asyncio` module for better event loop integration
- **Task Ordering**: Preserve relative positioning of active bars
- **Logging Compatibility**: `tqdm.write()` for all log output
- **Resource Management**: Complete cleanup of bars, positions, and resources

### Progress Granularity
- **Individual Files**: Update per downloaded chunk (typically 8KB-32KB chunks)
- **Overall Progress**: Update per completed file download
- **Status Updates**: Real-time metrics (transfer rate, ETA, percentage)

## Implementation Constraints

### Concurrent Download Management
- **Maximum Active Bars**: Limited by `--max-concurrent` setting (1-4)
- **Bar Lifecycle**: Create on download start, close on completion/failure
- **Position Reuse**: Release positions for reuse by new downloads
- **Historical Visibility**: Option to keep completed bars visible

### Error State Handling
- **Failure Indication**: Clear visual indication of failed downloads
- **Progress Preservation**: Maintain accurate progress state at time of failure
- **Resource Cleanup**: Ensure failed download bars are properly closed
- **Session Integrity**: Overall progress continues accurately despite individual failures

### Display Quality
- **No Wrapping**: All text fits within terminal width
- **Consistent Alignment**: Vertical columns maintained across all progress elements
- **Adaptive Sizing**: Handle terminal resize events gracefully
- **Clean Updates**: Smooth progress updates without flickering

## Success Criteria
1. No overlapping or conflicting progress bar displays
2. Accurate progress tracking for both individual files and overall session
3. Proper handling of concurrent downloads within user-specified limits
4. Clean visual presentation with consistent alignment and formatting
5. Robust error handling with clear failure indication
6. Efficient resource usage with complete cleanup
7. Compatibility across Windows 11 terminal environments
