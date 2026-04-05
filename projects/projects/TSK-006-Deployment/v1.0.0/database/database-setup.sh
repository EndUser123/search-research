#!/bin/bash
# TSK-006 Persistent Learning Agent Ecosystem - Database Setup Script
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
DEFAULT_DB_TYPE="sqlite"
DEFAULT_ENVIRONMENT="development"
DEFAULT_DB_HOST="localhost"
DEFAULT_DB_PORT="5432"
DEFAULT_DB_NAME="tsk006"
DEFAULT_DB_USER="tsk006_user"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -t, --type TYPE         Database type (sqlite|postgresql) [default: sqlite]"
    echo "  -e, --env ENVIRONMENT   Environment (development|staging|production) [default: development]"
    echo "  -h, --host HOST         Database host [default: localhost]"
    echo "  -p, --port PORT         Database port [default: 5432]"
    echo "  -d, --database DB_NAME   Database name [default: tsk006]"
    echo "  -u, --user DB_USER      Database user [default: tsk006_user]"
    echo "  -P, --password          Prompt for database password"
    echo "  -f, --file SQL_FILE     Custom SQL initialization file"
    echo "  --dry-run               Show commands without executing them"
    echo "  --help                  Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # SQLite setup (default)"
    echo "  $0 -t postgresql -e production       # PostgreSQL production setup"
    echo "  $0 -t postgresql -h db.example.com   # PostgreSQL with custom host"
}

# Parse command line arguments
DB_TYPE="$DEFAULT_DB_TYPE"
ENVIRONMENT="$DEFAULT_ENVIRONMENT"
DB_HOST="$DEFAULT_DB_HOST"
DB_PORT="$DEFAULT_DB_PORT"
DB_NAME="$DEFAULT_DB_NAME"
DB_USER="$DEFAULT_DB_USER"
DB_PASSWORD=""
SQL_FILE=""
DRY_RUN=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            DB_TYPE="$2"
            shift 2
            ;;
        -e|--env|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -h|--host)
            DB_HOST="$2"
            shift 2
            ;;
        -p|--port)
            DB_PORT="$2"
            shift 2
            ;;
        -d|--database)
            DB_NAME="$2"
            shift 2
            ;;
        -u|--user)
            DB_USER="$2"
            shift 2
            ;;
        -P|--password)
            read -s -p "Enter database password: " DB_PASSWORD
            echo
            shift
            ;;
        -f|--file)
            SQL_FILE="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN="--dry-run"
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate database type
if [[ "$DB_TYPE" != "sqlite" && "$DB_TYPE" != "postgresql" ]]; then
    print_error "Invalid database type: $DB_TYPE. Must be 'sqlite' or 'postgresql'"
    exit 1
fi

# Validate environment
if [[ "$ENVIRONMENT" != "development" && "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "production" ]]; then
    print_error "Invalid environment: $ENVIRONMENT. Must be 'development', 'staging', or 'production'"
    exit 1
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Set default SQL file based on database type if not provided
if [[ -z "$SQL_FILE" ]]; then
    if [[ "$DB_TYPE" == "sqlite" ]]; then
        SQL_FILE="$SCRIPT_DIR/init-sqlite.sql"
    else
        SQL_FILE="$SCRIPT_DIR/init-postgresql.sql"
    fi
fi

# Check if SQL file exists
if [[ ! -f "$SQL_FILE" ]]; then
    print_error "SQL file not found: $SQL_FILE"
    exit 1
fi

print_status "Starting TSK-006 Database Setup"
print_status "Database Type: $DB_TYPE"
print_status "Environment: $ENVIRONMENT"
print_status "SQL File: $SQL_FILE"

# SQLite Setup
setup_sqlite() {
    local db_path="$PROJECT_ROOT/data/${ENVIRONMENT}_agent_ecosystem.db"
    local db_dir=$(dirname "$db_path")

    print_status "Setting up SQLite database"
    print_status "Database path: $db_path"

    # Create data directory if it doesn't exist
    if [[ "$DRY_RUN" != "--dry-run" ]]; then
        mkdir -p "$db_dir"
        print_success "Created data directory: $db_dir"
    else
        print_status "Would create data directory: $db_dir"
    fi

    # Initialize database
    local cmd="sqlite3 '$db_path' < '$SQL_FILE'"
    if [[ "$DRY_RUN" == "--dry-run" ]]; then
        print_status "Would execute: $cmd"
    else
        if sqlite3 "$db_path" < "$SQL_FILE"; then
            print_success "SQLite database initialized successfully"
            print_success "Database created at: $db_path"
        else
            print_error "Failed to initialize SQLite database"
            exit 1
        fi
    fi
}

# PostgreSQL Setup
setup_postgresql() {
    print_status "Setting up PostgreSQL database"
    print_status "Host: $DB_HOST:$DB_PORT"
    print_status "Database: $DB_NAME"
    print_status "User: $DB_USER"

    # Set connection string
    local psql_cmd="psql"
    local connection_opts=""

    if [[ -n "$DB_HOST" && "$DB_HOST" != "localhost" ]]; then
        connection_opts="$connection_opts -h $DB_HOST"
    fi

    if [[ -n "$DB_PORT" && "$DB_PORT" != "5432" ]]; then
        connection_opts="$connection_opts -p $DB_PORT"
    fi

    if [[ -n "$DB_USER" ]]; then
        connection_opts="$connection_opts -U $DB_USER"
    fi

    if [[ -n "$DB_NAME" ]]; then
        connection_opts="$connection_opts -d $DB_NAME"
    fi

    # Set password in environment if provided
    if [[ -n "$DB_PASSWORD" ]]; then
        export PGPASSWORD="$DB_PASSWORD"
    fi

    local full_cmd="$psql_cmd $connection_opts"

    if [[ "$DRY_RUN" == "--dry-run" ]]; then
        print_status "Would execute: $full_cmd < $SQL_FILE"
    else
        # Test connection
        print_status "Testing database connection..."
        if $psql_cmd $connection_opts -c "SELECT 1;" > /dev/null 2>&1; then
            print_success "Database connection successful"
        else
            print_error "Failed to connect to PostgreSQL database"
            print_error "Please check your connection parameters and ensure the database exists"
            exit 1
        fi

        # Initialize database
        print_status "Initializing database schema..."
        if $psql_cmd $connection_opts < "$SQL_FILE"; then
            print_success "PostgreSQL database initialized successfully"
        else
            print_error "Failed to initialize PostgreSQL database"
            exit 1
        fi
    fi

    # Unset password for security
    unset PGPASSWORD
}

# Create environment-specific configuration file
create_env_config() {
    local config_file="$PROJECT_ROOT/config/.env.$ENVIRONMENT"

    print_status "Creating environment configuration file: $config_file"

    cat > "$config_file" << EOF
# TSK-006 Database Configuration - $ENVIRONMENT Environment
# Generated on: $(date)

# Database Type
DB_TYPE=$DB_TYPE

EOF

    if [[ "$DB_TYPE" == "sqlite" ]]; then
        cat >> "$config_file" << EOF
# SQLite Configuration
SQLITE_DB_PATH=$PROJECT_ROOT/data/${ENVIRONMENT}_agent_ecosystem.db

EOF
    else
        cat >> "$config_file" << EOF
# PostgreSQL Configuration
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DB_NAME=$DB_NAME
DB_USER=$DB_USER
EOF

        if [[ -n "$DB_PASSWORD" ]]; then
            echo "DB_PASSWORD=$DB_PASSWORD" >> "$config_file"
        fi
        echo "" >> "$config_file"
    fi

    print_success "Environment configuration created: $config_file"
}

# Create backup script
create_backup_script() {
    local backup_script="$PROJECT_ROOT/scripts/backup-$ENVIRONMENT.sh"

    print_status "Creating backup script: $backup_script"

    mkdir -p "$(dirname "$backup_script")"

    cat > "$backup_script" << 'EOF'
#!/bin/bash
# TSK-006 Database Backup Script

set -e

# Load environment configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/../config/.env.ENVIRONMENT"

if [[ -f "$CONFIG_FILE" ]]; then
    source "$CONFIG_FILE"
fi

# Create backup directory
BACKUP_DIR="$PROJECT_ROOT/backups"
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

# Backup based on database type
if [[ "$DB_TYPE" == "sqlite" ]]; then
    BACKUP_FILE="$BACKUP_DIR/sqlite_backup_$BACKUP_DATE.db"
    cp "$SQLITE_DB_PATH" "$BACKUP_FILE"
    echo "SQLite backup created: $BACKUP_FILE"
else
    BACKUP_FILE="$BACKUP_DIR/postgres_backup_$BACKUP_DATE.sql"
    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_FILE"
    gzip "$BACKUP_FILE"
    echo "PostgreSQL backup created: $BACKUP_FILE.gz"
fi
EOF

    # Replace ENVIRONMENT placeholder
    sed -i "s/ENVIRONMENT/$ENVIRONMENT/g" "$backup_script"

    chmod +x "$backup_script"
    print_success "Backup script created: $backup_script"
}

# Main execution
main() {
    print_status "Starting database setup process..."

    case "$DB_TYPE" in
        sqlite)
            setup_sqlite
            ;;
        postgresql)
            setup_postgresql
            ;;
    esac

    # Create configuration and backup files
    if [[ "$DRY_RUN" != "--dry-run" ]]; then
        create_env_config
        create_backup_script

        print_success "Database setup completed successfully!"
        print_status "Environment: $ENVIRONMENT"
        print_status "Database Type: $DB_TYPE"
        print_status "Configuration: $PROJECT_ROOT/config/.env.$ENVIRONMENT"
        print_status "Backup Script: $PROJECT_ROOT/scripts/backup-$ENVIRONMENT.sh"
    else
        print_status "Dry run completed. No changes were made."
    fi
}

# Check for required dependencies
check_dependencies() {
    if [[ "$DB_TYPE" == "sqlite" ]]; then
        if ! command -v sqlite3 &> /dev/null; then
            print_error "sqlite3 is not installed or not in PATH"
            exit 1
        fi
    elif [[ "$DB_TYPE" == "postgresql" ]]; then
        if ! command -v psql &> /dev/null; then
            print_error "psql is not installed or not in PATH"
            exit 1
        fi
    fi
}

# Run the setup
check_dependencies
main