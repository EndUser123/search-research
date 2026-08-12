/**
 * Background service worker entry point (WXT entrypoint).
 *
 * VS-02: delegates to service-worker module for acquisition + workspace logic.
 */

import { defineBackground } from "wxt/utils/define-background";
import {
  handleToolbarClick,
  handleNavigationMessage,
  handleTabClosed,
  handleSeekRequest,
  handleQueryWorkspaceState,
  handleAutoOpen,
} from "../background/service-worker";

export default defineBackground(() => {
  chrome.action.onClicked.addListener((tab) => {
    void handleToolbarClick(tab);
  });

  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (
      message?.type === "yt-navigate-finish" &&
      sender.tab?.id &&
      typeof message.url === "string"
    ) {
      // Use message.url (location.href from content script), NOT sender.tab.url.
      // During SPA navigation, sender.tab.url is stale — Chrome's tab model
      // hasn't caught up to history.pushState yet. message.url is always current.
      void handleNavigationMessage(sender.tab.id, message.url);
      return false;
    }

    if (message?.type === "seek" && sender.tab?.id) {
      void handleSeekRequest(
        sender.tab.id,
        message.seconds as number,
      ).then(sendResponse).catch((err) => {
        console.error("yt-workspace seek failed", err);
        sendResponse({ ok: false, error: String(err), beforeTime: -1, afterTime: -1 });
      });
      return true;
    }

    if (message?.type === "query-workspace-state" && sender.tab?.id) {
      void handleQueryWorkspaceState(sender.tab.id).then(sendResponse).catch((err) => {
        console.error("yt-workspace query failed", err);
        sendResponse({ open: false, videoContext: null });
      });
      return true;
    }

    if (message?.type === "auto-open" && sender.tab?.id) {
      void handleAutoOpen(sender.tab.id);
      return false;
    }

    if (message?.type === "acquire" && sender.tab?.id) {
      void handleAutoOpen(sender.tab.id);
      return false;
    }

    return false;
  });

  chrome.tabs.onRemoved.addListener((tabId) => {
    handleTabClosed(tabId);
  });
});
