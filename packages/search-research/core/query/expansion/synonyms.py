"""Synonym mappings for query expansion."""

from typing import Dict, List


# Default synonym mappings for technical terms
DEFAULT_SYNONYMS: Dict[str, List[str]] = {
    # Database related
    "db": ["database", "data store", "storage"],
    "database": ["db", "data store", "storage"],
    "sql": ["structured query language", "sql database"],
    "nosql": ["non-relational database", "document store", "key-value store"],

    # API related
    "api": ["application programming interface", "endpoint", "interface", "rest api"],
    "rest": ["representational state transfer", "restful", "rest api"],
    "graphql": ["graph ql", "graph query language"],

    # Authentication/Authorization
    "auth": ["authentication", "authorization", "login", "security"],
    "authentication": ["auth", "login", "verification", "identity"],
    "authorization": ["auth", "access control", "permissions", "authz"],

    # Code/Development
    "code": ["source code", "implementation", "programming", "script"],
    "function": ["method", "procedure", "routine", "lambda"],
    "class": ["type", "object type", "blueprint"],
    "bug": ["error", "defect", "issue", "problem", "glitch"],
    "error": ["exception", "bug", "issue", "failure"],
    "exception": ["error", "runtime error", "throw"],

    # Performance/Speed
    "fast": ["quick", "rapid", "swift", "high-performance", "optimized"],
    "quick": ["fast", "rapid", "swift", "speedy"],
    "rapid": ["fast", "quick", "swift", "accelerated"],
    "slow": ["laggy", "unresponsive", "performance issue"],

    # Creation/Building
    "create": ["make", "build", "construct", "generate", "develop"],
    "make": ["create", "build", "construct", "generate"],
    "build": ["create", "make", "construct", "compile", "develop"],
    "construct": ["create", "make", "build", "assemble"],

    # Web/HTTP
    "http": ["hypertext transfer protocol", "web protocol", "http request"],
    "https": ["secure http", "ssl", "tls", "secure connection"],
    "url": ["uniform resource locator", "web address", "link", "uri"],
    "uri": ["uniform resource identifier", "resource identifier"],

    # Data formats
    "json": ["javascript object notation", "data format", "json format"],
    "xml": ["extensible markup language", "markup format"],
    "yaml": ["yml", "configuration format"],

    # DevOps/Infrastructure
    "docker": ["container", "containerization", "docker container"],
    "kubernetes": ["k8s", "k8s cluster", "container orchestration"],
    "k8s": ["kubernetes", "container orchestration"],
    "ci/cd": ["continuous integration", "continuous deployment", "cicd", "pipeline"],
    "cicd": ["ci/cd", "continuous integration deployment"],

    # Architecture patterns
    "mvc": ["model view controller", "mvvm", "mvp"],
    "mvvm": ["model view viewmodel", "mv pattern"],
    "mvp": ["model view presenter", "mv pattern"],

    # Testing
    "tdd": ["test driven development", "test-first"],
    "bdd": ["behavior driven development"],
    "ddd": ["domain driven design"],

    # Security
    "jwt": ["json web token", "token auth", "bearer token"],
    "oauth": ["open authentication", "social login", "sso"],
    "saml": ["security assertion markup language", "sso"],
    "ssl": ["secure sockets layer", "tls", "https"],
    "tls": ["transport layer security", "ssl", "encryption"],
    "ssh": ["secure shell", "remote login"],
    "xss": ["cross-site scripting", "injection"],
    "csrf": ["cross-site request forgery", "csrf protection"],
    "sqli": ["sql injection", "database injection"],

    # Networking
    "tcp": ["transmission control protocol", "tcp/ip"],
    "udp": ["user datagram protocol", "datagram"],
    "ip": ["internet protocol", "ip address"],
    "dns": ["domain name system", "name resolution"],
    "dhcp": ["dynamic host configuration protocol"],
    "vpn": ["virtual private network", "tunnel"],
    "cdn": ["content delivery network", "edge network"],

    # Protocols
    "ftp": ["file transfer protocol"],
    "sftp": ["ssh file transfer", "secure ftp"],
    "smtp": ["simple mail transfer protocol", "email protocol"],
    "imap": ["internet message access protocol", "email protocol"],
    "pop3": ["post office protocol", "email protocol"],

    # Attacks
    "dos": ["denial of service", "availability attack"],
    "ddos": ["distributed denial of service", "ddos attack"],

    # Async/Concurrency
    "async": ["asynchronous", "non-blocking", "callback"],
    "await": ["async wait", "promise"],
    "promise": ["future", "async result"],
    "future": ["promise", "async result"],

    # Frontend
    "html": ["hypertext markup language", "markup"],
    "css": ["cascading style sheets", "stylesheet", "styling"],
    "javascript": ["js", "ecmascript", "client-side script"],
    "js": ["javascript", "ecmascript"],

    # Backend languages
    "python": ["py", "python script"],
    "typescript": ["ts", "typed javascript"],

    # General tech
    "app": ["application", "software", "program"],
    "service": ["microservice", "api", "backend service"],
    "server": ["backend", "host", "machine"],
    "client": ["frontend", "consumer", "app"],

    # Search/Query
    "search": ["query", "find", "lookup", "retrieve"],
    "query": ["search", "request", "lookup"],
    "find": ["search", "locate", "discover"],
    "lookup": ["search", "query", "find"],

    # Learning
    "ml": ["machine learning", "ai"],
    "ai": ["artificial intelligence", "machine learning"],
}


def get_synonym_mappings() -> Dict[str, List[str]]:
    """Get the default synonym mappings.

    Returns:
        A dictionary mapping terms to their synonym lists.
    """
    return DEFAULT_SYNONYMS.copy()
