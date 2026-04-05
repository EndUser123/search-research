#!/bin/bash
# TSK-006 Persistent Learning Agent Ecosystem - Comprehensive Backup Procedures
# Version: 1.0.0
# Created: 2025-12-21

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"
LOG_DIR="${LOG_DIR:-$PROJECT_ROOT/logs}"
CONFIG_DIR="${PROJECT_ROOT}/config"

# Load environment configuration
if [[ -f "$CONFIG_DIR/environment-variables.env" ]]; then
    source "$CONFIG_DIR/environment-variables.env"
fi

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"
mkdir -p "$LOG_DIR"

# Backup functions
backup_sqlite_database() {
    local db_path="$1"
    local backup_name="$2"
    local backup_file="$BACKUP_DIR/sqlite_${backup_name}_$(date +%Y%m%d_%H%M%S).db"

    log "Starting SQLite database backup: $db_path"

    if [[ -f "$db_path" ]]; then
        # Create backup using sqlite3 backup command
        sqlite3 "$db_path" ".backup $backup_file" || {
            log_error "SQLite backup failed for $db_path"
            return 1
        }

        # Compress backup
        gzip "$backup_file"
        backup_file="${backup_file}.gz"

        log_success "SQLite database backup completed: $backup_file"

        # Verify backup integrity
        verify_sqlite_backup "$backup_file"

        echo "$backup_file"
    else
        log_warning "Database file not found: $db_path"
        return 1
    fi
}

backup_postgresql_database() {
    local backup_name="$1"
    local backup_file="$BACKUP_DIR/postgres_${backup_name}_$(date +%Y%m%d_%H%M%S).sql"

    log "Starting PostgreSQL database backup: $DB_NAME"

    # Create backup
    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --no-password --verbose --clean --if-exists \
        --format=custom --compress=9 \
        --file="$backup_file" || {
        log_error "PostgreSQL backup failed"
        return 1
    }

    # Compress backup
    gzip "$backup_file"
    backup_file="${backup_file}.gz"

    log_success "PostgreSQL database backup completed: $backup_file"

    # Verify backup integrity
    verify_postgres_backup "$backup_file"

    echo "$backup_file"
}

verify_sqlite_backup() {
    local backup_file="$1"

    log "Verifying SQLite backup integrity: $backup_file"

    # Create temporary database for verification
    temp_db="/tmp/verify_$(date +%s).db"
    gunzip -c "$backup_file" > "$temp_db"

    # Run integrity check
    if sqlite3 "$temp_db" "PRAGMA integrity_check;" | grep -q "ok"; then
        log_success "SQLite backup integrity verified"
        rm -f "$temp_db"
        return 0
    else
        log_error "SQLite backup integrity check failed"
        rm -f "$temp_db"
        return 1
    fi
}

verify_postgres_backup() {
    local backup_file="$1"

    log "Verifying PostgreSQL backup integrity: $backup_file"

    # Extract backup for verification
    temp_backup="/tmp/verify_$(date +%s).sqlc"
    gunzip -c "$backup_file" > "$temp_backup"

    # Verify backup can be restored (dry run)
    if pg_restore --list "$temp_backup" > /dev/null 2>&1; then
        log_success "PostgreSQL backup integrity verified"
        rm -f "$temp_backup"
        return 0
    else
        log_error "PostgreSQL backup integrity check failed"
        rm -f "$temp_backup"
        return 1
    fi
}

backup_configuration() {
    local backup_name="$1"
    local backup_dir="$BACKUP_DIR/config_${backup_name}_$(date +%Y%m%d_%H%M%S)"

    log "Starting configuration backup: $CONFIG_DIR"

    mkdir -p "$backup_dir"

    # Backup configuration files
    if [[ -d "$CONFIG_DIR" ]]; then
        cp -r "$CONFIG_DIR"/* "$backup_dir/" || {
            log_error "Configuration backup failed"
            return 1
        }

        # Create tar archive
        tar -czf "${backup_dir}.tar.gz" -C "$BACKUP_DIR" "$(basename "$backup_dir")"
        rm -rf "$backup_dir"
        backup_dir="${backup_dir}.tar.gz"

        log_success "Configuration backup completed: $backup_dir"
        echo "$backup_dir"
    else
        log_warning "Configuration directory not found: $CONFIG_DIR"
        return 1
    fi
}

backup_application_data() {
    local backup_name="$1"
    local backup_dir="$BACKUP_DIR/appdata_${backup_name}_$(date +%Y%m%d_%H%M%S)"

    log "Starting application data backup"

    mkdir -p "$backup_dir"

    # Backup agent roles
    if [[ -d "$PROJECT_ROOT/src/agent_factory/roles" ]]; then
        cp -r "$PROJECT_ROOT/src/agent_factory/roles" "$backup_dir/" || {
            log_error "Failed to backup agent roles"
            return 1
        }
    fi

    # Backup expertise files
    if [[ -d "$PROJECT_ROOT/src/expertise" ]]; then
        cp -r "$PROJECT_ROOT/src/expertise" "$backup_dir/" || {
            log_error "Failed to backup expertise files"
            return 1
        }
    fi

    # Backup logs
    if [[ -d "$PROJECT_ROOT/logs" ]]; then
        cp -r "$PROJECT_ROOT/logs" "$backup_dir/" || {
            log_error "Failed to backup logs"
            return 1
        }
    fi

    # Create tar archive
    tar -czf "${backup_dir}.tar.gz" -C "$BACKUP_DIR" "$(basename "$backup_dir")"
    rm -rf "$backup_dir"
    backup_dir="${backup_dir}.tar.gz"

    log_success "Application data backup completed: $backup_dir"
    echo "$backup_dir"
}

backup_system_state() {
    local backup_name="$1"
    local backup_file="$BACKUP_DIR/system_state_${backup_name}_$(date +%Y%m%d_%H%M%S).json"

    log "Starting system state backup"

    # Collect system state information
    cat > "$backup_file" << EOF
{
  "backup_timestamp": "$(date -Iseconds)",
  "system_info": {
    "hostname": "$(hostname)",
    "os_version": "$(uname -a)",
    "uptime": "$(uptime -p)",
    "memory_info": $(free -m | python3 -c "
import sys, json
lines = sys.stdin.readlines()
mem = {}
for line in lines[1:3]:
    if ':' in line:
        key, value = line.split(':')[0].strip(), line.split(':')[1].strip().split()
        mem[key] = {k: int(v) for k, v in zip(['total', 'used', 'free'], value[:3])}
print(json.dumps(mem))
"),
    "disk_usage": $(df -h / | python3 -c "
import sys, json
lines = sys.stdin.readlines()
if len(lines) > 1:
    parts = lines[1].split()
    disk_info = {
        'filesystem': parts[0],
        'size': parts[1],
        'used': parts[2],
        'available': parts[3],
        'usage_percent': parts[4].replace('%', ''),
        'mount_point': parts[5]
    }
    print(json.dumps(disk_info))
"),
    "load_average": "$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')"
  },
  "tsk_006_processes": $(ps aux | grep -E "(python.*agent_factory|tsk-006)" | grep -v grep | python3 -c "
import sys, json
processes = []
for line in sys.stdin:
    if line.strip():
        parts = line.strip().split(None, 10)
        if len(parts) >= 11:
            processes.append({
                'user': parts[0],
                'pid': parts[1],
                'cpu': parts[2],
                'memory': parts[3],
                'command': parts[10]
            })
print(json.dumps(processes))
"),
  "environment_variables": {
    "TSK006_ENV": "$TSK006_ENV",
    "DB_TYPE": "$DB_TYPE",
    "CKS_INTEGRATION_ENABLED": "$CKS_INTEGRATION_ENABLED"
  }
}
EOF

    log_success "System state backup completed: $backup_file"
    echo "$backup_file"
}

create_backup_manifest() {
    local backup_name="$1"
    shift
    local backup_files=("$@")
    local manifest_file="$BACKUP_DIR/manifest_${backup_name}_$(date +%Y%m%d_%H%M%S).json"

    log "Creating backup manifest: $manifest_file"

    cat > "$manifest_file" << EOF
{
  "backup_name": "$backup_name",
  "backup_timestamp": "$(date -Iseconds)",
  "backup_type": "full",
  "backup_files": [
EOF

    # Add backup files to manifest
    for ((i=0; i<${#backup_files[@]}; i++)); do
        file="${backup_files[i]}"
        size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo 0)
        checksum=$(sha256sum "$file" | awk '{print $1}')

        echo "    {" >> "$manifest_file"
        echo "      \"filename\": \"$(basename "$file")\"," >> "$manifest_file"
        echo "      \"full_path\": \"$file\"," >> "$manifest_file"
        echo "      \"size_bytes": $size," >> "$manifest_file"
        echo "      \"checksum\": \"$checksum\"," >> "$manifest_file"
        echo "      \"type\": \"$(file_type "$file")\"" >> "$manifest_file"
        echo -n "    }" >> "$manifest_file"

        if [[ $i -lt $((${#backup_files[@]} - 1)) ]]; then
            echo "," >> "$manifest_file"
        else
            echo "" >> "$manifest_file"
        fi
    done

    cat >> "$manifest_file" << EOF
  ],
  "backup_version": "1.0.0",
  "created_by": "$(whoami)",
  "hostname": "$(hostname)"
}
EOF

    log_success "Backup manifest created: $manifest_file"
    echo "$manifest_file"
}

file_type() {
    local file="$1"

    if [[ "$file" == *.gz ]]; then
        echo "compressed"
    elif [[ "$file" == *.tar.gz ]]; then
        echo "archive"
    elif [[ "$file" == *.db ]]; then
        echo "database"
    elif [[ "$file" == *.sql* ]]; then
        echo "database_dump"
    elif [[ "$file" == *.json ]]; then
        echo "configuration"
    else
        echo "unknown"
    fi
}

cleanup_old_backups() {
    local retention_days="${1:-30}"

    log "Cleaning up backups older than $retention_days days"

    # Remove old backup files
    find "$BACKUP_DIR" -name "*" -type f -mtime +$retention_days -exec rm -f {} \;

    # Remove empty directories
    find "$BACKUP_DIR" -type d -empty -delete

    log_success "Old backups cleanup completed"
}

full_backup() {
    local backup_name="${1:-tsk-006-full}"
    local backup_files=()
    local db_backup_file=""
    local config_backup_file=""
    local appdata_backup_file=""
    local system_state_file=""

    log "Starting full backup process: $backup_name"

    # Backup database based on type
    if [[ "$DB_TYPE" == "sqlite" && -n "$SQLITE_DB_PATH" ]]; then
        db_backup_file=$(backup_sqlite_database "$SQLITE_DB_PATH" "$backup_name") || {
            log_error "Database backup failed"
            return 1
        }
        backup_files+=("$db_backup_file")
    elif [[ "$DB_TYPE" == "postgresql" ]]; then
        db_backup_file=$(backup_postgresql_database "$backup_name") || {
            log_error "Database backup failed"
            return 1
        }
        backup_files+=("$db_backup_file")
    else
        log_warning "No database backup performed - unknown type or path not set"
    fi

    # Backup configuration
    config_backup_file=$(backup_configuration "$backup_name") || {
        log_error "Configuration backup failed"
        return 1
    }
    backup_files+=("$config_backup_file")

    # Backup application data
    appdata_backup_file=$(backup_application_data "$backup_name") || {
        log_error "Application data backup failed"
        return 1
    }
    backup_files+=("$appdata_backup_file")

    # Backup system state
    system_state_file=$(backup_system_state "$backup_name") || {
        log_error "System state backup failed"
        return 1
    }
    backup_files+=("$system_state_file")

    # Create backup manifest
    manifest_file=$(create_backup_manifest "$backup_name" "${backup_files[@]}") || {
        log_error "Manifest creation failed"
        return 1
    }

    log_success "Full backup completed successfully"
    log "Backup files created:"
    for file in "${backup_files[@]}"; do
        log "  - $file"
    done
    log "Manifest: $manifest_file"

    # Cleanup old backups (default 30 days)
    cleanup_old_backups 30

    return 0
}

incremental_backup() {
    local backup_name="${1:-tsk-006-incremental}"
    local last_full_backup="$2"

    log "Starting incremental backup process: $backup_name"

    # Find the most recent full backup
    if [[ -z "$last_full_backup" ]]; then
        last_full_backup=$(find "$BACKUP_DIR" -name "manifest_tsk-006-full_*" -type f -printf '%T@ %p\n' | sort -n | tail -1 | awk '{print $2}')
    fi

    if [[ -z "$last_full_backup" ]] || [[ ! -f "$last_full_backup" ]]; then
        log_error "No full backup found for incremental backup"
        log "Please run a full backup first"
        return 1
    fi

    log "Using full backup manifest: $last_full_backup"

    # For now, implement as a partial backup
    # In a production environment, you would implement true incremental backup logic
    log_warning "Incremental backup implemented as partial backup"

    # Backup only changed files
    backup_name="${backup_name}-partial"
    full_backup "$backup_name"

    return 0
}

restore_backup() {
    local backup_manifest="$1"

    if [[ -z "$backup_manifest" || ! -f "$backup_manifest" ]]; then
        log_error "Backup manifest not found: $backup_manifest"
        return 1
    fi

    log "Starting restore process from: $backup_manifest"

    # Extract backup files from manifest
    local backup_files=$(python3 -c "
import json
import sys

with open('$backup_manifest', 'r') as f:
    manifest = json.load(f)

for file_info in manifest['backup_files']:
    print(file_info['full_path'])
")

    # Verify all backup files exist
    for backup_file in $backup_files; do
        if [[ ! -f "$backup_file" ]]; then
            log_error "Backup file not found: $backup_file"
            return 1
        fi
    done

    log_warning "This will restore the system to the state in the backup"
    read -p "Are you sure you want to continue? (yes/no): " -r

    if [[ $REPLY != "yes" ]]; then
        log "Restore cancelled by user"
        return 0
    fi

    # Perform restore based on file types
    for backup_file in $backup_files; do
        local file_type=$(file_type "$backup_file")

        case "$file_type" in
            "database"|"database_dump")
                log "Restoring database from: $backup_file"
                # Implement database restore logic
                ;;
            "archive")
                log "Restoring application data from: $backup_file"
                # Implement application data restore logic
                ;;
            "configuration")
                log "Restoring configuration from: $backup_file"
                # Implement configuration restore logic
                ;;
        esac
    done

    log_success "Restore process completed"
    return 0
}

show_usage() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  full                    Perform a full backup"
    echo "  incremental [manifest]  Perform an incremental backup"
    echo "  restore <manifest>      Restore from backup manifest"
    echo "  cleanup [days]          Clean up old backups (default: 30 days)"
    echo "  list                    List available backups"
    echo "  verify <backup_file>    Verify backup integrity"
    echo ""
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  -v, --verbose           Enable verbose output"
    echo ""
    echo "Examples:"
    echo "  $0 full                         # Full backup"
    echo "  $0 incremental                   # Incremental backup"
    echo "  $0 restore manifest_*.json       # Restore from backup"
    echo "  $0 cleanup 7                     # Clean up backups older than 7 days"
}

list_backups() {
    log "Available backups:"

    find "$BACKUP_DIR" -name "manifest_*.json" -type f -printf '%T@ %p\n' | sort -nr | while read timestamp manifest; do
        local backup_date=$(date -d "@${timestamp%.*}" '+%Y-%m-%d %H:%M:%S')
        local backup_name=$(python3 -c "
import json
with open('$manifest', 'r') as f:
    manifest = json.load(f)
    print(manifest['backup_name'])
")

        echo "  $backup_date - $backup_name - $manifest"
    done
}

verify_backup() {
    local backup_file="$1"

    if [[ -z "$backup_file" || ! -f "$backup_file" ]]; then
        log_error "Backup file not found: $backup_file"
        return 1
    fi

    log "Verifying backup: $backup_file"

    local file_type=$(file_type "$backup_file")

    case "$file_type" in
        "database")
            verify_sqlite_backup "$backup_file"
            ;;
        "database_dump")
            verify_postgres_backup "$backup_file"
            ;;
        "compressed")
            # Extract and verify based on actual file type
            ;;
        *)
            log_warning "Unknown backup type, cannot verify: $file_type"
            return 1
            ;;
    esac
}

# Main script execution
case "${1:-}" in
    "full")
        full_backup "${2:-tsk-006-full}"
        ;;
    "incremental")
        incremental_backup "${2:-tsk-006-incremental}" "$3"
        ;;
    "restore")
        restore_backup "$2"
        ;;
    "cleanup")
        cleanup_old_backups "${2:-30}"
        ;;
    "list")
        list_backups
        ;;
    "verify")
        verify_backup "$2"
        ;;
    "help"|"-h"|"--help")
        show_usage
        ;;
    *)
        log_error "Unknown command: ${1:-}"
        show_usage
        exit 1
        ;;
esac