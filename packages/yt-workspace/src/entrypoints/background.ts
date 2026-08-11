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
} from "../background/service-worker";

export default defineBackground(() => {
  chrome.action.onClicked.addListener((tab) => {
    void handleToolbarClick(tab);
  });

  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (
      message?.type === "yt-navigate-finish" &&
      sender.tab?.id &&
      sender.tab.url
    ) {
      void handleNavigationMessage(sender.tab.id, sender.tab.url);
      return false;
    }

    if (message?.type === "seek" && sender.tab?.id) {
      void handleSeekRequest(
        sender.tab.id,
        message.seconds as number,
      ).then(sendResponse);
      return true;
    }

    if (message?.type === "query-workspace-state" && sender.tab?.id) {
      void handleQueryWorkspaceState(sender.tab.id).then(sendResponse);
      return true;
    }

    return false;
  });

  chrome.tabs.onRemoved.addListener((tabId) => {
    handleTabClosed(tabId);
  });
});
