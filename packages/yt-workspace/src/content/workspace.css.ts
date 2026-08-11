/**
 * Workspace CSS — dark theme matching YouTube's dark mode.
 * Injected as a <style> element by the content script.
 *
 * Font sizing: child elements use `em` units (relative to the workspace
 * root font-size). The settings slider changes the root font-size, and
 * all children scale proportionally.
 */

export const WORKSPACE_CSS = `
#__yt_workspace {
  padding: 12px;
  margin-bottom: 8px;
  background: #0f0f0f;
  color: #f1f1f1;
  border-radius: 8px;
  font-family: 'YouTube Sans', Roboto, Arial, sans-serif;
  font-size: 14px;
}

#__yt_workspace .ytws-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  justify-content: space-between;
}

#__yt_workspace .ytws-title {
  font-size: 1.15em;
  font-weight: 600;
  color: #f1f1f1;
}

#__yt_workspace .ytws-info {
  opacity: 0.7;
  margin-bottom: 6px;
  font-size: 0.86em;
  font-family: monospace;
}

#__yt_workspace .ytws-provenance {
  opacity: 0.6;
  margin-bottom: 8px;
  font-size: 0.79em;
  font-family: monospace;
}

#__yt_workspace .ytws-tabs {
  display: flex;
  gap: 0;
  margin-bottom: 8px;
  border-bottom: 1px solid #272727;
}

#__yt_workspace .ytws-tab {
  padding: 6px 12px;
  font-size: 0.93em;
  font-weight: 500;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: border-color 0.15s, background 0.15s;
}

#__yt_workspace .ytws-tab:hover {
  background: #1f1f1f;
}

#__yt_workspace .ytws-tab-active {
  color: #f1f1f1;
  border-bottom-color: #3ea6ff;
  cursor: pointer;
}

#__yt_workspace .ytws-tab-disabled {
  color: #717171;
  cursor: not-allowed;
}

#__yt_workspace .ytws-tab-disabled:hover {
  background: transparent;
}

#__yt_workspace .ytws-chapters {
  min-height: 40px;
  max-height: 400px;
  overflow-y: auto;
}

#__yt_workspace .ytws-chapter-row {
  display: flex;
  align-items: flex-start;
  padding: 6px 4px;
  cursor: pointer;
  border-bottom: 1px solid #1a1a1a;
  transition: background 0.1s;
}

#__yt_workspace .ytws-chapter-row:hover {
  background: #1f1f1f;
}

#__yt_workspace .ytws-chapter-time {
  color: #3ea6ff;
  margin-right: 12px;
  min-width: 60px;
  font-size: 0.86em;
  font-family: monospace;
  flex-shrink: 0;
}

#__yt_workspace .ytws-chapter-title {
  color: #f1f1f1;
  font-size: 0.93em;
  line-height: 1.3;
}

#__yt_workspace .ytws-empty {
  padding: 12px 4px;
  color: #717171;
  font-size: 0.93em;
}

#__yt_workspace .ytws-header-gear {
  margin-left: auto;
}

#__yt_workspace .ytws-settings-container {
  position: relative;
}

#__yt_workspace .ytws-gear {
  background: none;
  border: none;
  color: #aaaaaa;
  font-size: 1.29em;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
  line-height: 1;
}

#__yt_workspace .ytws-gear:hover {
  background: #272727;
  color: #f1f1f1;
}

#__yt_workspace .ytws-settings-panel {
  display: none;
  position: absolute;
  top: 100%;
  right: 0;
  background: #1f1f1f;
  border: 1px solid #303030;
  border-radius: 6px;
  padding: 10px 12px;
  z-index: 10000;
  white-space: nowrap;
  box-shadow: 0 4px 12px rgba(0,0,0,0.4);
}

#__yt_workspace .ytws-settings-panel-open {
  display: flex;
  align-items: center;
  gap: 8px;
}

#__yt_workspace .ytws-settings-label {
  font-size: 0.86em;
  color: #aaaaaa;
}

#__yt_workspace .ytws-settings-slider {
  width: 100px;
  accent-color: #3ea6ff;
  cursor: pointer;
}

#__yt_workspace .ytws-settings-value {
  font-size: 0.86em;
  color: #f1f1f1;
  font-family: monospace;
  min-width: 36px;
  text-align: right;
}

#__yt_workspace_resizer {
  width: 4px;
  cursor: col-resize;
  background: transparent;
  flex-shrink: 0;
  align-self: stretch;
  margin-right: -4px;
  position: relative;
  z-index: 9999;
}

#__yt_workspace_resizer:hover {
  background: #3ea6ff40;
}

#__yt_workspace_resizer:active {
  background: #3ea6ff80;
}
`;
