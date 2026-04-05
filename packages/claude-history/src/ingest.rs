use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};
use std::path::Path;
use tracing::{debug, info};
use std::io::{BufRead, BufReader};

/// History entry from JSONL file
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type")]
#[serde(rename_all = "lowercase")]
enum HistoryEntry {
    #[serde(rename = "assistant")]
    Assistant {
        parent_uuid: Option<String>,
        #[serde(default)]
        is_sidechain: bool,
        #[serde(default)]
        user_type: String,
        cwd: String,
        session_id: String,
        version: String,
        git_branch: Option<String>,
        message: MessageContent,
        uuid: String,
        timestamp: String,
    },
    #[serde(rename = "user")]
    User {
        parent_uuid: Option<String>,
        #[serde(default)]
        is_sidechain: bool,
        #[serde(default)]
        user_type: String,
        cwd: String,
        session_id: String,
        version: String,
        git_branch: Option<String>,
        message: MessageContent,
        uuid: String,
        timestamp: String,
    },
    #[serde(rename = "system")]
    System {
        session_id: String,
        message: MessageContent,
        timestamp: String,
    },
    #[serde(rename = "summary")]
    Summary {
        summary: String,
        #[serde(rename = "leafUuid")]
        leaf_uuid: String,
    },
    #[serde(rename = "custom-title")]
    CustomTitle {
        #[serde(rename = "sessionId")]
        session_id: String,
        title: String,
    },
    #[serde(rename = "file-history-snapshot")]
    FileHistorySnapshot {
        #[serde(rename = "messageId")]
        message_id: String,
        snapshot: serde_json::Value,
    },
    #[serde(rename = "queue-operation")]
    QueueOperation {
        #[serde(rename = "sessionId")]
        session_id: String,
        operation: serde_json::Value,
    },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct MessageContent {
    #[serde(rename = "type")]
    msg_type: String,
    role: String,
    content: Vec<ContentBlock>,
    #[serde(default)]
    stop_reason: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(untagged)]
enum ContentBlock {
    Text { text: String },
    ToolUse {
        #[serde(rename = "type")]
        tool_type: String,
        id: String,
        name: String,
        input: serde_json::Value,
    },
    ToolResult {
        #[serde(rename = "type")]
        result_type: String,
        tool_use_id: String,
        content: Option<String>,
        is_error: Option<bool>,
    },
    Other(serde_json::Value),
}

impl HistoryEntry {
    fn session_id(&self) -> Option<&str> {
        match self {
            HistoryEntry::Assistant { session_id, .. } => Some(session_id),
            HistoryEntry::User { session_id, .. } => Some(session_id),
            HistoryEntry::System { session_id, .. } => Some(session_id),
            HistoryEntry::Summary { .. } => None,
            HistoryEntry::CustomTitle { session_id, .. } => Some(session_id),
            HistoryEntry::FileHistorySnapshot { .. } => None,
            HistoryEntry::QueueOperation { session_id, .. } => Some(session_id),
        }
    }

    fn timestamp(&self) -> Option<&str> {
        match self {
            HistoryEntry::Assistant { timestamp, .. } => Some(timestamp),
            HistoryEntry::User { timestamp, .. } => Some(timestamp),
            HistoryEntry::System { timestamp, .. } => Some(timestamp),
            HistoryEntry::Summary { .. } => None,
            HistoryEntry::CustomTitle { .. } => None,
            HistoryEntry::FileHistorySnapshot { .. } => None,
            HistoryEntry::QueueOperation { .. } => None,
        }
    }

    fn message_type(&self) -> &str {
        match self {
            HistoryEntry::Assistant { .. } => "assistant",
            HistoryEntry::User { .. } => "user",
            HistoryEntry::System { .. } => "system",
            HistoryEntry::Summary { .. } => "summary",
            HistoryEntry::CustomTitle { .. } => "custom-title",
            HistoryEntry::FileHistorySnapshot { .. } => "file-history-snapshot",
            HistoryEntry::QueueOperation { .. } => "queue-operation",
        }
    }

    fn content(&self) -> Option<String> {
        match self {
            HistoryEntry::Assistant { message, .. } => extract_text_content(message),
            HistoryEntry::User { message, .. } => extract_text_content(message),
            HistoryEntry::System { message, .. } => extract_text_content(message),
            HistoryEntry::Summary { summary, .. } => Some(summary.clone()),
            HistoryEntry::CustomTitle { title, .. } => Some(format!("Title: {}", title)),
            HistoryEntry::FileHistorySnapshot { .. } => Some("[File history snapshot]".to_string()),
            HistoryEntry::QueueOperation { .. } => Some("[Queue operation]".to_string()),
        }
    }

    fn project(&self) -> Option<&str> {
        match self {
            HistoryEntry::Assistant { cwd, .. } => Some(cwd.as_str()),
            HistoryEntry::User { cwd, .. } => Some(cwd.as_str()),
            HistoryEntry::System { .. } => None,
            HistoryEntry::Summary { .. } => None,
            HistoryEntry::CustomTitle { .. } => None,
            HistoryEntry::FileHistorySnapshot { .. } => None,
            HistoryEntry::QueueOperation { .. } => None,
        }
    }
}

fn extract_text_content(msg: &MessageContent) -> Option<String> {
    let mut text_parts = Vec::new();
    for block in &msg.content {
        match block {
            ContentBlock::Text { text } => {
                text_parts.push(text.clone());
            }
            ContentBlock::ToolUse { name, input, .. } => {
                text_parts.push(format!("Tool: {}", name));
                if let Ok(s) = serde_json::to_string(input) {
                    text_parts.push(s);
                }
            }
            ContentBlock::ToolResult { content, is_error, .. } => {
                let is_err = is_error.unwrap_or(false);
                if is_err {
                    let content_str = content.as_deref().unwrap_or("");
                    text_parts.push(format!("Error: {}", content_str));
                } else if let Some(c) = content {
                    text_parts.push(c.clone());
                }
            }
            ContentBlock::Other(_) => {}
        }
    }
    if text_parts.is_empty() {
        None
    } else {
        Some(text_parts.join("\n"))
    }
}

/// Search JSONL file for matching messages
pub async fn search_jsonl(
    jsonl_path: &Path,
    query: &str,
    project_filter: Option<&str>,
    limit: usize,
) -> Result<Vec<crate::cli::SearchResult>> {
    info!(
        "Searching JSONL: path='{}', query='{}', project={:?}, limit={}",
        jsonl_path.display(),
        query,
        project_filter,
        limit
    );

    if !jsonl_path.exists() {
        info!("JSONL file not found at {}", jsonl_path.display());
        return Ok(Vec::new());
    }

    let file = std::fs::File::open(jsonl_path).context("Failed to open JSONL file")?;
    let reader = BufReader::new(file);

    let query_lower = query.to_lowercase();
    let mut results = Vec::new();

    for line in reader.lines() {
        if results.len() >= limit {
            break;
        }

        let line = line.context("Failed to read line")?;
        if line.is_empty() {
            continue;
        }

        let entry: serde_json::Value = serde_json::from_str(&line)
            .with_context(|| format!("Failed to parse JSON: {}", &line[..100.min(line.len())]))?;

        // Check if entry has content we can search
        let content = entry.get("message")
            .and_then(|m| m.get("content"))
            .and_then(|c| c.as_array());

        let entry_type = entry.get("type").and_then(|t| t.as_str()).unwrap_or("unknown");
        let session_id = entry.get("sessionId").and_then(|s| s.as_str());
        let cwd = entry.get("cwd").and_then(|c| c.as_str());
        let timestamp = entry.get("timestamp").and_then(|t| t.as_str());

        // Filter by project if specified
        if let Some(proj) = project_filter {
            if let Some(cwd) = cwd {
                if !cwd.contains(proj) {
                    continue;
                }
            }
        }

        // Search in content
        let mut found = false;
        let mut matched_content = String::new();

        if let Some(content_array) = content {
            for block in content_array {
                if let Some(text) = block.get("text") {
                    let text_str = text.as_str().unwrap_or("");
                    if text_str.to_lowercase().contains(&query_lower) {
                        found = true;
                        matched_content = text_str.to_string();
                        break;
                    }
                }
                // Also check tool names
                if let Some(name) = block.get("name") {
                    let name_str = name.as_str().unwrap_or("");
                    if name_str.to_lowercase().contains(&query_lower) {
                        found = true;
                        matched_content = format!("Tool: {}", name_str);
                        break;
                    }
                }
            }
        }

        // Also check summaries
        if !found && entry_type == "summary" {
            if let Some(summary) = entry.get("summary") {
                let summary_str = summary.as_str().unwrap_or("");
                if summary_str.to_lowercase().contains(&query_lower) {
                    found = true;
                    matched_content = summary_str.to_string();
                }
            }
        }

        if found {
            let dt = timestamp
                .and_then(|t| DateTime::parse_from_rfc3339(t).ok())
                .map(|dt| dt.with_timezone(&Utc))
                .unwrap_or_else(|| Utc::now());

            results.push(super::cli::SearchResult {
                session_id: session_id.unwrap_or("unknown").to_string(),
                message_type: entry_type.to_string(),
                timestamp: dt,
                content: matched_content.clone(),
                project: cwd.unwrap_or("unknown").to_string(),
                score: None,
                snippet: Some(if matched_content.chars().count() > 200 {
                    format!("{}...", matched_content.chars().take(200).collect::<String>())
                } else {
                    matched_content.clone()
                }),
            });
        }
    }

    info!("Found {} results in JSONL", results.len());
    Ok(results)
}

/// List sessions from JSONL file
pub async fn list_sessions(
    jsonl_path: &Path,
    project_filter: Option<&str>,
    sort: super::cli::SortOrder,
    limit: usize,
) -> Result<Vec<super::cli::SessionSummary>> {
    info!(
        "Listing sessions: path='{}', project={:?}, sort={:?}, limit={}",
        jsonl_path.display(),
        project_filter,
        sort,
        limit
    );

    if !jsonl_path.exists() {
        return Ok(Vec::new());
    }

    let file = std::fs::File::open(jsonl_path)?;
    let reader = BufReader::new(file);

    let mut sessions: HashMap<String, SessionData> = HashMap::new();

    for line in reader.lines() {
        let line = line?;
        if line.is_empty() {
            continue;
        }

        // Parse JSON, skip if invalid
        let entry: serde_json::Value = match serde_json::from_str(&line) {
            Ok(v) => v,
            Err(_) => continue,
        };

        // Extract fields with proper error handling
        let session_id = match entry.get("sessionId").and_then(|s| s.as_str()) {
            Some(s) => s,
            None => continue,
        };

        let cwd = entry.get("cwd").and_then(|c| c.as_str()).unwrap_or("unknown");

        // Filter by project
        if let Some(proj) = project_filter {
            if !cwd.contains(proj) {
                continue;
            }
        }

        let entry_type = entry.get("type").and_then(|t| t.as_str()).unwrap_or("unknown");
        let timestamp = entry.get("timestamp").and_then(|t| t.as_str());

        let data = sessions.entry(session_id.to_string()).or_insert_with(|| SessionData {
            session_id: session_id.to_string(),
            project: cwd.to_string(),
            message_count: 0,
            first_timestamp: None,
            last_timestamp: None,
            title: None,
        });

        if let Some(ts) = timestamp {
            if let Ok(dt) = DateTime::parse_from_rfc3339(ts) {
                let dt = dt.with_timezone(&Utc);
                if data.first_timestamp.is_none() || dt < data.first_timestamp.unwrap() {
                    data.first_timestamp = Some(dt);
                }
                if data.last_timestamp.is_none() || dt > data.last_timestamp.unwrap() {
                    data.last_timestamp = Some(dt);
                }
            }
        }

        if matches!(entry_type, "assistant" | "user" | "system") {
            data.message_count += 1;
        }

        // Extract custom title
        if entry_type == "custom-title" {
            if let Some(title) = entry.get("title").and_then(|t| t.as_str()) {
                data.title = Some(title.to_string());
            }
        }
    }

    let mut results: Vec<super::cli::SessionSummary> = sessions
        .into_values()
        .map(|d| super::cli::SessionSummary {
            session_id: d.session_id,
            start_time: d.first_timestamp.unwrap_or_else(|| Utc::now()),
            end_time: d.last_timestamp,
            project: d.project,
            message_count: d.message_count,
            title: d.title,
        })
        .collect();

    // Sort
    match sort {
        crate::cli::SortOrder::Recent => {
            results.sort_by(|a, b| b.start_time.cmp(&a.start_time));
        }
        crate::cli::SortOrder::Oldest => {
            results.sort_by(|a, b| a.start_time.cmp(&b.start_time));
        }
        crate::cli::SortOrder::Project => {
            results.sort_by(|a, b| a.project.cmp(&b.project));
        }
    }

    results.truncate(limit);
    Ok(results)
}

/// Get all messages for a session
pub async fn get_session(jsonl_path: &Path, session_id: &str) -> Result<Vec<super::cli::SearchResult>> {
    info!(
        "Getting session: path='{}', session_id='{}'",
        jsonl_path.display(),
        session_id
    );

    if !jsonl_path.exists() {
        return Ok(Vec::new());
    }

    let file = std::fs::File::open(jsonl_path)?;
    let reader = BufReader::new(file);

    let mut results = Vec::new();

    for line in reader.lines() {
        let line = line?;
        if line.is_empty() {
            continue;
        }

        // Parse JSON, skip if invalid
        let entry: serde_json::Value = match serde_json::from_str(&line) {
            Ok(v) => v,
            Err(_) => continue,
        };

        let entry_session_id = match entry.get("sessionId").and_then(|s| s.as_str()) {
            Some(s) => s,
            None => continue,
        };

        if entry_session_id != session_id {
            continue;
        }

        let entry_type = entry.get("type").and_then(|t| t.as_str()).unwrap_or("unknown");
        let cwd = entry.get("cwd").and_then(|c| c.as_str()).unwrap_or("unknown");
        let timestamp = entry.get("timestamp").and_then(|t| t.as_str());

        let content = if let Some(msg) = entry.get("message") {
            if let Some(content_array) = msg.get("content").and_then(|c| c.as_array()) {
                let mut text = String::new();
                for block in content_array {
                    if let Some(t) = block.get("text").and_then(|t| t.as_str()) {
                        text.push_str(t);
                        text.push('\n');
                    }
                    if let Some(name) = block.get("name").and_then(|n| n.as_str()) {
                        text.push_str(&format!("Tool: {}\n", name));
                    }
                }
                text
            } else {
                String::new()
            }
        } else if let Some(summary) = entry.get("summary").and_then(|s| s.as_str()) {
            summary.to_string()
        } else {
            String::new()
        };

        let dt = timestamp
            .and_then(|t| DateTime::parse_from_rfc3339(t).ok())
            .map(|dt| dt.with_timezone(&Utc))
            .unwrap_or_else(|| Utc::now());

        results.push(crate::cli::SearchResult {
            session_id: session_id.to_string(),
            message_type: entry_type.to_string(),
            timestamp: dt,
            content,
            project: cwd.to_string(),
            score: None,
            snippet: None,
        });
    }

    Ok(results)
}

/// Count total sessions in JSONL
pub async fn count_sessions(jsonl_path: &Path) -> Result<usize> {
    if !jsonl_path.exists() {
        return Ok(0);
    }

    let file = std::fs::File::open(jsonl_path)?;
    let reader = BufReader::new(file);

    let mut sessions = HashSet::new();

    for line in reader.lines() {
        let line = line?;
        if line.is_empty() {
            continue;
        }

        if let Ok(entry) = serde_json::from_str::<serde_json::Value>(&line) {
            if let Some(session_id) = entry.get("sessionId").and_then(|s| s.as_str()) {
                sessions.insert(session_id.to_string());
            }
        }
    }

    Ok(sessions.len())
}

/// Count total messages in JSONL
pub async fn count_messages(jsonl_path: &Path) -> Result<usize> {
    if !jsonl_path.exists() {
        return Ok(0);
    }

    let file = std::fs::File::open(jsonl_path)?;
    let reader = BufReader::new(file);

    let mut count = 0;

    for line in reader.lines() {
        let line = line?;
        if line.is_empty() {
            continue;
        }

        if let Ok(entry) = serde_json::from_str::<serde_json::Value>(&line) {
            if let Some(entry_type) = entry.get("type").and_then(|t| t.as_str()) {
                if matches!(entry_type, "assistant" | "user" | "system") {
                    count += 1;
                }
            }
        }
    }

    Ok(count)
}

/// List all unique projects
pub async fn list_projects(jsonl_path: &Path) -> Result<Vec<String>> {
    if !jsonl_path.exists() {
        return Ok(Vec::new());
    }

    let file = std::fs::File::open(jsonl_path)?;
    let reader = BufReader::new(file);

    let mut projects = HashSet::new();

    for line in reader.lines() {
        let line = line?;
        if line.is_empty() {
            continue;
        }

        if let Ok(entry) = serde_json::from_str::<serde_json::Value>(&line) {
            if let Some(cwd) = entry.get("cwd").and_then(|c| c.as_str()) {
                projects.insert(cwd.to_string());
            }
        }
    }

    let mut result: Vec<String> = projects.into_iter().collect();
    result.sort();
    Ok(result)
}

struct SessionData {
    session_id: String,
    project: String,
    message_count: usize,
    first_timestamp: Option<DateTime<Utc>>,
    last_timestamp: Option<DateTime<Utc>>,
    title: Option<String>,
}
