use anyhow::{Context, Result};
use serde_json::{json, Value};
use std::io::{self, BufRead, BufReader, Write};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use tracing::{error, info};

/// Start the MCP server (stdio JSON-RPC mode) with graceful shutdown support
pub async fn run_server() -> Result<()> {
    info!("Starting MCP server on stdio...");

    let running = Arc::new(AtomicBool::new(true));
    let running_clone = running.clone();

    // Set up Ctrl+C handler for graceful shutdown
    #[cfg(unix)]
    {
        use tokio::signal::unix::{signal, SignalKind};
        let mut sigint = signal(SignalKind::interrupt())?;
        let mut sigterm = signal(SignalKind::terminate())?;

        tokio::spawn(async move {
            tokio::select! {
                _ = sigint.recv() => {
                    info!("Received SIGINT, shutting down gracefully...");
                    running_clone.store(false, Ordering::SeqCst);
                }
                _ = sigterm.recv() => {
                    info!("Received SIGTERM, shutting down gracefully...");
                    running_clone.store(false, Ordering::SeqCst);
                }
            }
        });
    }

    let stdin = io::stdin();
    let stdout = io::stdout();
    let mut reader = BufReader::new(stdin.lock());
    let mut writer = stdout.lock();

    // Send initialize notification
    send_notification(
        &mut writer,
        "notifications/initialized",
        json!({}),
    )?;

    info!("MCP server ready, waiting for requests...");

    for line_result in reader.lines() {
        // Check if we should stop (for graceful shutdown)
        if !running.load(Ordering::SeqCst) {
            info!("Shutdown signal received, stopping...");
            break;
        }

        let line = match line_result {
            Ok(l) => l,
            Err(e) => {
                error!("Failed to read line from stdin: {}", e);
                break;
            }
        };

        if line.trim().is_empty() {
            continue;
        }

        info!("Received request: {}", line);

        let request: Value = serde_json::from_str(&line)
            .with_context(|| format!("Failed to parse JSON-RPC request: {}", line))?;

        let response = handle_request(request).await;

        if let Err(ref e) = response {
            error!("Error handling request: {}", e);
        }

        send_response(&mut writer, response)?;
    }

    info!("MCP server shutting down...");

    Ok(())
}

fn send_response<W: Write>(writer: &mut W, response: Result<Value>) -> Result<()> {
    let response = match response {
        Ok(result) => result,
        Err(e) => {
            let error = json!({
                "code": -32603,
                "message": e.to_string(),
            });
            json!({
                "jsonrpc": "2.0",
                "error": error,
                "id": null
            })
        }
    };

    writeln!(writer, "{}", response)?;
    writer.flush()?;
    Ok(())
}

fn send_notification<W: Write>(writer: &mut W, method: &str, params: Value) -> Result<()> {
    let notification = json!({
        "jsonrpc": "2.0",
        "method": method,
        "params": params
    });

    writeln!(writer, "{}", notification)?;
    writer.flush()?;
    Ok(())
}

async fn handle_request(request: Value) -> Result<Value> {
    let method = request
        .get("method")
        .and_then(|m| m.as_str())
        .ok_or_else(|| anyhow::anyhow!("Missing 'method' in request"))?;

    let id = request.get("id");

    info!("Handling method: {}", method);

    let result: Value = match method {
        "tools/list" => handle_list_tools().await?,
        "tools/call" => {
            let params = request
                .get("params")
                .ok_or_else(|| anyhow::anyhow!("Missing 'params' in request"))?;
            handle_tool_call(params).await?
        }
        "resources/list" => handle_list_resources().await?,
        "initialize" => handle_initialize().await?,
        "ping" => json!({"status": "ok"}),
        _ => return Err(anyhow::anyhow!("Unknown method: {}", method)),
    };

    Ok(json!({
        "jsonrpc": "2.0",
        "result": result,
        "id": id
    }))
}

async fn handle_initialize() -> Result<Value> {
    Ok(json!({
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {},
            "resources": {}
        },
        "serverInfo": {
            "name": "claude-history",
            "version": "0.1.0"
        }
    }))
}

async fn handle_list_resources() -> Result<Value> {
    Ok(json!({
        "resources": [
            {
                "uri": "chat-history://sessions",
                "name": "Chat Sessions",
                "description": "All chat sessions from history",
                "mimeType": "application/json"
            },
            {
                "uri": "chat-history://stats",
                "name": "Statistics",
                "description": "Chat history database statistics",
                "mimeType": "application/json"
            }
        ]
    }))
}

async fn handle_list_tools() -> Result<Value> {
    Ok(json!({
        "tools": [
            {
                "name": "search_sessions",
                "description": "Search chat history for matching sessions and messages",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query string"
                        },
                        "project": {
                            "type": "string",
                            "description": "Filter by project path (optional)"
                        },
                        "limit": {
                            "type": "number",
                            "description": "Maximum number of results (default 10)",
                            "default": 10
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_session",
                "description": "Get full details of a specific session",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "session_id": {
                            "type": "string",
                            "description": "Session ID to retrieve"
                        }
                    },
                    "required": ["session_id"]
                }
            },
            {
                "name": "list_projects",
                "description": "List all unique project paths in chat history",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "stats",
                "description": "Get statistics about the chat history database",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    }))
}

async fn handle_tool_call(params: &Value) -> Result<Value> {
    let tool_name = params
        .get("name")
        .and_then(|n| n.as_str())
        .ok_or_else(|| anyhow::anyhow!("Missing 'name' in tool call"))?;

    let arguments = params
        .get("arguments")
        .ok_or_else(|| anyhow::anyhow!("Missing 'arguments' in tool call"))?;

    info!("Calling tool: {}", tool_name);

    let result = match tool_name {
        "search_sessions" => {
            let query = arguments
                .get("query")
                .and_then(|q| q.as_str())
                .ok_or_else(|| anyhow::anyhow!("Missing 'query' argument"))?;
            let project = arguments.get("project").and_then(|p| p.as_str());
            let limit = arguments
                .get("limit")
                .and_then(|l| l.as_u64())
                .unwrap_or(10) as usize;

            let results = super::ingest::search_jsonl(
                &super::cli::default_jsonl_path(),
                query,
                project,
                limit,
            )
            .await?;

            json!({
                "results": results,
                "count": results.len()
            })
        }
        "get_session" => {
            let session_id = arguments
                .get("session_id")
                .and_then(|s| s.as_str())
                .ok_or_else(|| anyhow::anyhow!("Missing 'session_id' argument"))?;

            let messages = super::ingest::get_session(
                &super::cli::default_jsonl_path(),
                session_id,
            )
            .await?;

            json!({
                "session_id": session_id,
                "messages": messages,
                "count": messages.len()
            })
        }
        "list_projects" => {
            let projects = super::ingest::list_projects(&super::cli::default_jsonl_path()).await?;

            json!({
                "projects": projects,
                "count": projects.len()
            })
        }
        "stats" => {
            let total_sessions =
                super::ingest::count_sessions(&super::cli::default_jsonl_path()).await?;
            let total_messages =
                super::ingest::count_messages(&super::cli::default_jsonl_path()).await?;
            let projects = super::ingest::list_projects(&super::cli::default_jsonl_path()).await?;

            json!({
                "total_sessions": total_sessions,
                "total_messages": total_messages,
                "projects": projects,
                "jsonl_path": super::cli::default_jsonl_path().to_string_lossy().to_string()
            })
        }
        _ => Err(anyhow::anyhow!("Unknown tool: {}", tool_name))?,
    };

    Ok(json!({
        "content": [
            {
                "type": "text",
                "text": serde_json::to_string_pretty(&result)?
            }
        ]
    }))
}
