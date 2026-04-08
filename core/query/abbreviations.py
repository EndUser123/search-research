"""Abbreviation mappings for query expansion.

Migrated from research_skill/expansion/abbreviations.py
"""


# Default abbreviation mappings
DEFAULT_ABBREVIATIONS: dict[str, str] = {
    # Web/HTTP
    "api": "application programming interface",
    "http": "hypertext transfer protocol",
    "https": "secure hypertext transfer protocol",
    "url": "uniform resource locator",
    "uri": "uniform resource identifier",

    # Data formats
    "json": "javascript object notation",
    "xml": "extensible markup language",
    "yaml": "yaml ain't markup language",
    "yml": "yaml ain't markup language",

    # Security
    "jwt": "json web token",
    "oauth": "open authentication",
    "saml": "security assertion markup language",
    "ssl": "secure sockets layer",
    "tls": "transport layer security",
    "ssh": "secure shell",
    "sftp": "ssh file transfer protocol",
    "ftp": "file transfer protocol",

    # Email protocols
    "smtp": "simple mail transfer protocol",
    "imap": "internet message access protocol",
    "pop3": "post office protocol version 3",

    # Networking
    "tcp": "transmission control protocol",
    "udp": "user datagram protocol",
    "ip": "internet protocol",
    "dns": "domain name system",
    "dhcp": "dynamic host configuration protocol",
    "vpn": "virtual private network",
    "cdn": "content delivery network",

    # Security attacks
    "xss": "cross site scripting",
    "csrf": "cross site request forgery",
    "sqli": "sql injection",

    # Denial of service
    "dos": "denial of service",
    "ddos": "distributed denial of service",

    # Database
    "sql": "structured query language",
    "nosql": "not only sql",
    "rdbms": "relational database management system",
    "orm": "object relational mapper",

    # API styles
    "rest": "representational state transfer",
    "soap": "simple object access protocol",
    "graphql": "graph query language",
    "grpc": "google remote procedure call",

    # DevOps
    "cicd": "continuous integration continuous deployment",
    "ci": "continuous integration",
    "cd": "continuous deployment",
    "iac": "infrastructure as code",

    # Containers
    "docker": "docker container",
    "k8s": "kubernetes",

    # Cloud
    "aws": "amazon web services",
    "azure": "microsoft azure",
    "gcp": "google cloud platform",
    "saas": "software as a service",
    "paas": "platform as a service",
    "iaas": "infrastructure as a service",

    # Authentication
    "2fa": "two factor authentication",
    "mfa": "multi factor authentication",
    "oidc": "open id connect",
    "sso": "single sign on",

    # Programming languages
    "js": "javascript",
    "ts": "typescript",
    "py": "python",

    # Frontend
    "html": "hypertext markup language",
    "css": "cascading style sheets",
    "dom": "document object model",
    "spa": "single page application",

    # Testing
    "tdd": "test driven development",
    "bdd": "behavior driven development",
    "ddd": "domain driven design",
    "e2e": "end to end testing",

    # Architecture
    "mvc": "model view controller",
    "mvvm": "model view viewmodel",
    "mvp": "model view presenter",
    "crud": "create read update delete",

    # Data processing
    "etl": "extract transform load",
    "elt": "extract load transform",
    "csv": "comma separated values",

    # Version control
    "vcs": "version control system",
    "git": "git version control",

    # Other
    "ide": "integrated development environment",
    "cli": "command line interface",
    "gui": "graphical user interface",
        "sdk": "software development kit",
    "llm": "large language model",
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "nlp": "natural language processing",
    "rag": "retrieval augmented generation",
    "mcp": "model context protocol",
}


def get_abbreviation_mappings() -> dict[str, str]:
    """Get the default abbreviation mappings.

    Returns:
        A dictionary mapping abbreviations to their full expansions.
    """
    return DEFAULT_ABBREVIATIONS.copy()


def expand_abbreviation(abbr: str) -> str:
    """Expand an abbreviation to its full form.

    Args:
        abbr: The abbreviation to expand.

    Returns:
        The expanded form if found, otherwise the original abbreviation.
    """
    abbr_lower = abbr.lower()
    return DEFAULT_ABBREVIATIONS.get(abbr_lower, abbr)
