/**
 * Workspace CSS — dark theme matching YouTube's dark mode.
 * Injected as a <style> element by the content script (avoids needing
 * a separate CSS file in the build pipeline; WXT content scripts can
 * import CSS but this keeps it simple for the vertical slice).
 */

export const WORKSPACE_CSS = `
.__yt_workspace {
  padding: 12px;
  margin-bottom: 8px;
  background: #0f0f0f;
  color: #f1f1f1;
  border-radius: 8px;
  font-family: 'YouTube Sans', Roboto, Arial, sans-serif;
  font-size: 14px;
}

.__yt_workspace .ytws-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.__yt_workspace .ytws-title {
  font-size: 16px;
  font-weight: 600;
  color: #f1f1f1;
}

.__yt_workspace .ytws-info {
  opacity: 0.7;
  margin-bottom: 6px;
  font-size: 12px;
  font-family: monospace;
}

.__yt_workspace .ytws-provenance {
  opacity: 0.6;
  margin-bottom: 8px;
  font-size: 11px;
  font-family: monospace;
}

.__yt_workspace .ytws-tabs {
  display: flex;
  gap: 0;
  margin-bottom: 8px;
  border-bottom: 1px solid #272727;
}

.__yt_workspace .ytws-tab {
  padding: 6px 12px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: border-color 0.15s, background 0.15s;
}

.__yt_workspace .ytws-tab:hover {
  background: #1f1f1f;
}

.__yt_workspace .ytws-tab-active {
  color: #f1f1f1;
  border-bottom-color: #3ea6ff;
  cursor: pointer;
}

.__yt_workspace .ytws-tab-disabled {
  color: #717171;
  cursor: not-allowed;
}

.__yt_workspace .ytws-tab-disabled:hover {
  background: transparent;
}

.__yt_workspace .ytws-chapters {
  min-height: 40px;
  max-height: 400px;
  overflow-y: auto;
}

.__yt_workspace .ytws-chapter-row {
  display: flex;
  align-items: flex-start;
  padding: 6px 4px;
  cursor: pointer;
  border-bottom: 1px solid #1a1a1a;
  transition: background 0.1s;
}

.__yt_workspace .ytws-chapter-row:hover {
  background: #1f1f1f;
}

.__yt_workspace .ytws-chapter-time {
  color: #3ea6ff;
  margin-right: 12px;
  min-width: 60px;
  font-size: 12px;
  font-family: monospace;
  flex-shrink: 0;
}

.__yt_workspace .ytws-chapter-title {
  color: #f1f1f1;
  font-size: 13px;
  line-height: 1.3;
}

.__yt_workspace .ytws-empty {
  padding: 12px 4px;
  color: #717171;
  font-size: 13px;
}
`;
