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

#__yt_workspace .ytws-tab-clickable {
  color: #aaaaaa;
  cursor: pointer;
}

#__yt_workspace .ytws-tab-clickable:hover {
  color: #f1f1f1;
  background: #1f1f1f;
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

#__yt_workspace .ytws-tab-content {
  min-height: 40px;
  max-height: 400px;
  overflow-y: auto;
}

#__yt_workspace .ytws-overview-title {
  font-size: 1.15em;
  font-weight: 600;
  color: #f1f1f1;
  margin-bottom: 8px;
}

#__yt_workspace .ytws-overview-section {
  font-size: 0.86em;
  font-weight: 600;
  color: #3ea6ff;
  margin-top: 12px;
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

#__yt_workspace .ytws-overview-toc-row {
  display: flex;
  align-items: flex-start;
  padding: 4px 0;
  cursor: pointer;
  border-bottom: 1px solid #1a1a1a;
}

#__yt_workspace .ytws-overview-toc-row:hover {
  background: #1f1f1f;
}

#__yt_workspace .ytws-overview-description {
  font-size: 0.93em;
  color: #cccccc;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 300px;
  overflow-y: auto;
  padding: 4px;
}

#__yt_workspace .ytws-transcript-header,
#__yt_workspace .ytws-links-header {
  font-size: 0.86em;
  font-weight: 600;
  color: #3ea6ff;
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

#__yt_workspace .ytws-transcript-row {
  display: flex;
  align-items: flex-start;
  padding: 4px 0;
  border-bottom: 1px solid #1a1a1a;
}

#__yt_workspace .ytws-transcript-time {
  color: #3ea6ff;
  margin-right: 12px;
  min-width: 50px;
  font-size: 0.79em;
  font-family: monospace;
  flex-shrink: 0;
  padding-top: 1px;
}

#__yt_workspace .ytws-transcript-text {
  color: #cccccc;
  font-size: 0.86em;
  line-height: 1.4;
}

#__yt_workspace .ytws-link {
  display: block;
  color: #3ea6ff;
  font-size: 0.86em;
  padding: 4px 0;
  text-decoration: none;
  word-break: break-all;
}

#__yt_workspace .ytws-link:hover {
  text-decoration: underline;
}

#__yt_workspace .ytws-ask-input {
  width: 100%;
  padding: 6px 10px;
  background: #0f0f0f;
  border: 1px solid #303030;
  border-radius: 4px;
  color: #f1f1f1;
  font-size: 0.93em;
  font-family: inherit;
  margin-bottom: 8px;
}

#__yt_workspace .ytws-ask-input:focus {
  outline: none;
  border-color: #3ea6ff;
}

#__yt_workspace .ytws-ask-input::placeholder {
  color: #717171;
}

#__yt_workspace .ytws-ask-results {
  min-height: 40px;
}

#__yt_workspace .ytws-ask-hint {
  font-size: 0.79em;
  color: #717171;
  padding: 4px 0;
}

#__yt_workspace .ytws-ask-highlight {
  background: #3ea6ff30;
  color: #3ea6ff;
  border-radius: 2px;
  padding: 0 1px;
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
