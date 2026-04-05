#!/usr/bin/env python3
"""
Complete knowledge graph export with proper handling of embeddings.
"""

import gc
import json
import logging
import re
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

# GPU acceleration libraries
try:
    import numpy as np
    import torch
    from sentence_transformers import SentenceTransformer
    GPU_AVAILABLE = torch.cuda.is_available()
except ImportError:
    print("Warning: GPU libraries not available. Using CPU-only mode.")
    GPU_AVAILABLE = False

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('knowledge_graph_export.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CompleteKnowledgeGraphExporter:
    """
    Complete knowledge graph exporter with proper handling of all data types.
    """

    def __init__(self):
        # Graph storage
        self.entities = {}  # entity_id -> entity_info
        self.relationships = []  # List of relationships
        self.entity_types = defaultdict(set)  # type -> set of entity_ids
        self.conversation_entities = {}  # conversation_id -> set of entity_ids

        # Performance metrics
        self.metrics = {
            'total_conversations': 0,
            'processed_conversations': 0,
            'total_entities': 0,
            'total_relationships': 0,
            'processing_time': 0,
            'entity_extraction_time': 0,
            'relationship_extraction_time': 0,
            'embedding_time': 0,
            'gpu_memory_used': 0,
            'batches_processed': 0
        }

    def extract_entities_basic(self, text: str) -> list[dict[str, Any]]:
        """
        Enhanced entity extraction using regex patterns with CSF NIP specific patterns.
        """
        entities = []

        # File paths - comprehensive pattern
        file_pattern = r'[\w\-\/\.]+\.(py|md|txt|json|yaml|yml|csv|tsv|log|sh|bat|ps1|js|ts|html|css|sql|xml|ini|cfg|conf|toml|lock|env|gitignore|dockerfile|requirements\.txt|package\.json|setup\.py|makefile|readme|license|changelog|manifest|setup\.cfg|pyproject\.toml|pytest\.ini|tox\.ini|mypy\.ini|flake8\.cfg|black\.py|isort\.cfg|pre-commit-config\.yaml|\.pre-commit-config\.yaml|\.gitignore|\.dockerignore|\.editorconfig|\.babelrc|\.eslintrc|\.prettierrc|tsconfig\.json|webpack\.config\.js|vite\.config\.js|rollup\.config\.js|gulpfile\.js|gruntfile\.js|rakefile|gemfile|composer\.json|package\.lock\.json|yarn\.lock|pipfile|pipfile\.lock|poetry\.lock|cargo\.toml|cargo\.lock|go\.mod|go\.sum|requirements\.dev\.txt|requirements\.test\.txt|requirements\.prod\.txt|requirements\.base\.txt|requirements\.local\.txt|requirements\.txt|setup\.cfg|setup\.py|pyproject\.toml|tox\.ini|pytest\.ini|conftest\.py|test_.*\.py|.*_test\.py|.*_spec\.py|spec_.*\.py|tests?/.*\.py)'

        # Commands and tools
        command_pattern = r'\/[a-zA-Z][a-zA-Z0-9_-]*(?:\s+[a-zA-Z0-9_-]+)*|git\s+[a-zA-Z0-9_-]+|npm\s+[a-zA-Z0-9_-]+|pip\s+[a-zA-Z0-9_-]+|python\s+[a-zA-Z0-9_-]+|pytest\s+[a-zA-Z0-9_-]+|docker\s+[a-zA-Z0-9_-]+|kubectl\s+[a-zA-Z0-9_-]+|aws\s+[a-zA-Z0-9_-]+|azure\s+[a-zA-Z0-9_-]+|gcloud\s+[a-zA-Z0-9_-]+|terraform\s+[a-zA-Z0-9_-]+|ansible\s+[a-zA-Z0-9_-]+|vagrant\s+[a-zA-Z0-9_-]+|make\s+[a-zA-Z0-9_-]+|cmake\s+[a-zA-Z0-9_-]+|gradle\s+[a-zA-Z0-9_-]+|mvn\s+[a-zA-Z0-9_-]+|yarn\s+[a-zA-Z0-9_-]+|bower\s+[a-zA-Z0-9_-]+|composer\s+[a-zA-Z0-9_-]+|bundle\s+[a-zA-Z0-9_-]+|gem\s+[a-zA-Z0-9_-]+|cargo\s+[a-zA-Z0-9_-]+|go\s+[a-zA-Z0-9_-]+|rustc\s+[a-zA-Z0-9_-]+|gcc\s+[a-zA-Z0-9_-]+|g\+\+\s+[a-zA-Z0-9_-]+|clang\s+[a-zA-Z0-9_-]+|javac\s+[a-zA-Z0-9_-]+|java\s+[a-zA-Z0-9_-]+|node\s+[a-zA-Z0-9_-]+|npx\s+[a-zA-Z0-9_-]+|pnpm\s+[a-zA-Z0-9_-]+|deno\s+[a-zA-Z0-9_-]+|bun\s+[a-zA-Z0-9_-]+'

        # URLs and domains
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+|www\.[^\s<>"{}|\\^`\[\]]+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s<>"{}|\\^`\[\]]*)?'

        # Technical terms and frameworks - expanded pattern
        tech_pattern = r'\b(?:API|REST|GraphQL|SQL|NoSQL|MongoDB|PostgreSQL|MySQL|Redis|Elasticsearch|Kafka|RabbitMQ|Docker|Kubernetes|AWS|Azure|GCP|Terraform|Ansible|Jenkins|GitLab|GitHub|Bitbucket|Jira|Confluence|Slack|Discord|Teams|Zoom|Webex|TensorFlow|PyTorch|Keras|Scikit-learn|Pandas|NumPy|Matplotlib|Seaborn|Plotly|Dash|Streamlit|Flask|Django|FastAPI|Spring|React|Vue|Angular|Svelte|Next\.js|Nuxt\.js|Gatsby|Webpack|Vite|Rollup|Parcel|Babel|ESLint|Prettier|Jest|Mocha|Chai|Cypress|Selenium|Playwright|Puppeteer|Postman|Swagger|OpenAPI|gRPC|Protocol Buffers|Thrift|Avro|JSON|YAML|XML|CSV|TSV|Markdown|LaTeX|HTML|CSS|SASS|SCSS|LESS|TypeScript|JavaScript|Python|Java|C\+\+|C#|Go|Rust|Ruby|PHP|Swift|Kotlin|Scala|Haskell|Erlang|Elixir|Clojure|F#|Objective-C|Dart|Lua|Perl|R|MATLAB|Julia|Bash|PowerShell|Zsh|Fish|CMD|BAT|Shell|Linux|Windows|macOS|Ubuntu|Debian|CentOS|RHEL|Alpine|Arch|Fedora|openSUSE|FreeBSD|NetBSD|OpenBSD|Darwin|iOS|Android|HTTP|HTTPS|TCP|UDP|IP|DNS|SSH|FTP|SFTP|VPN|CDN|CI|CD|DevOps|Agile|Scrum|Kanban|TDD|BDD|OOP|FP|SOA|Microservices|Serverless|Containers|Orchestration|Monitoring|Logging|Metrics|Tracing|Testing|Debugging|Profiling|Optimization|Security|Authentication|Authorization|Encryption|Hashing|JWT|OAuth|SAML|LDAP|Database|Data Warehouse|Data Lake|ETL|ELT|Big Data|Data Science|Machine Learning|Deep Learning|Neural Networks|CNN|RNN|LSTM|GAN|Reinforcement Learning|Supervised Learning|Unsupervised Learning|Semi-supervised Learning|Transfer Learning|Ensemble Learning|Random Forest|Decision Tree|SVM|K-means|Clustering|Classification|Regression|NLP|Computer Vision|Time Series|Forecasting|Anomaly Detection|Recommendation Systems|Search Engines|Information Retrieval|Web Crawling|Web Scraping|API Design|RESTful|WebSocket|WebRTC|PWA|SPA|MVC|MVP|MVVM|Design Patterns|SOLID|DRY|KISS|YAGNI|Big O|Algorithm|Data Structure|Queue|Stack|Heap|Tree|Graph|Linked List|Array|Hash Table|Sorting|Searching|Dynamic Programming|Recursion|Iteration|Concurrency|Parallelism|Multithreading|Async|Await|Promise|Callback|Closure|Lambda|Function|Class|Object|Inheritance|Polymorphism|Encapsulation|Abstraction|Interface|Abstract Class|Constructor|Destructor|Method|Property|Field|Variable|Constant|Enum|Struct|Union|Pointer|Reference|Memory Management|Garbage Collection|Stack Overflow|Heap Overflow|Memory Leak|Deadlock|Race Condition|Semaphore|Mutex|Lock|Thread Safety|Atomic Operations|Consistency|Availability|Partition Tolerance|CAP Theorem|ACID|BASE|Normalization|Denormalization|Indexing|Query Optimization|Caching|Load Balancing|Scaling|Horizontal Scaling|Vertical Scaling|Redundancy|Failover|Disaster Recovery|Backup|Restore|Migration|Version Control|Git|GitHub|GitLab|Bitbucket|Branching|Merging|Rebasing|Cherry-picking|Conflict Resolution|Code Review|Pull Request|Merge Request|Continuous Integration|Continuous Deployment|Pipeline|Build|Test|Deploy|Infrastructure as Code|Configuration Management|Provisioning|Monitoring|Alerting|Logging|Tracing|Observability|SLO|SLA|SLI|Uptime|Downtime|Performance|Latency|Throughput|Response Time|Time to First Byte|Page Load|Core Web Vitals|SEO|SEM|Social Media|Content Marketing|Email Marketing|CRM|ERP|Business Intelligence|Analytics|Dashboard|KPI|Metrics|ROI|CAC|LTV|Churn|Retention|Engagement|Conversion|A/B Testing|Multivariate Testing|User Experience|User Interface|Design System|Component Library|Style Guide|Brand Guidelines|Typography|Color Theory|Layout|Grid|Responsive Design|Mobile First|Progressive Enhancement|Graceful Degradation|Accessibility|WCAG|Screen Reader|Keyboard Navigation|Focus Management|Internationalization|Localization|Globalization|Translation|Right-to-Left|Unicode|UTF-8|Character Encoding|Escape Sequences|Regular Expressions|Pattern Matching|Validation|Sanitization|XSS|CSRF|SQL Injection|Input Validation|Output Encoding|Content Security Policy|Same Origin Policy|CORS|JSONP|WebSockets|Server-Sent Events|Push Notifications|Service Workers|Web App Manifest|Offline First|Progressive Web App|Native App|Hybrid App|Cross Platform|Flutter|React Native|Ionic|Cordova|PhoneGap|Electron|NW\.js|Desktop Application|System Tray|Menu Bar|Dock|Task Manager|Process Management|Job Scheduling|Cron|Task Queue|Message Queue|Event Bus|Publisher Subscriber|Observer Pattern|Strategy Pattern|Factory Pattern|Singleton Pattern|Builder Pattern|Decorator Pattern|Adapter Pattern|Facade Pattern|Command Pattern|Iterator Pattern|Composite Pattern|Flyweight Pattern|Proxy Pattern|Bridge Pattern|Chain of Responsibility|Mediator Pattern|Memento Pattern|State Pattern|Template Method|Visitor Pattern)\b'

        # CSF NIP specific patterns - comprehensive pattern
        csf_pattern = r'\b(?:CSF|NIP|Knowledge\s*Graph|Entity\s*Extraction|Relationship\s*Mapping|Constitution\s*Compliance|Quality\s*Gate|Validation\s*Gate|TaskMaster|CWO|Executive|Command|Agent|Skill|Workflow|Orchestration|Session\s*Management|Context\s*Compression|Memory\s*Pressure|Evidence\s*Correlation|Cognitive\s*Enhancement|Deliberate\s*Changes|Subagent\s*Injection|Violation\s*Reporting|Path\s*Validation|Goal\s*Anchoring|Truth\s*Audit|Anti-Deception|Handover\s*Documentation|Session\s*Continuity|Cross\s*Session\s*Tracking|Memory\s*Preservation|Context\s*Reconstruction|Compaction\s*Management|RAG\s*Integration|CKS\s*Knowledge|Search\s*Intelligence|Multi-Agent\s*Systems|Cognitive\s*Stack|Production\s*Deployment|Conformance\s*Validation|Technical\s*Debt\s*Analysis|Code\s*Quality\s*Standards|Architecture\s*Decision\s*Framework|System\s*Improvement|Integration\s*Refactoring|Compliance\s*Checking|Automated\s*Testing|Continuous\s*Learning|Performance\s*Optimization|Resource\s*Management|Error\s*Handling|Recovery\s*Procedures|Security\s*Validation|Access\s*Control|Permission\s*Management|User\s*Authentication|Role\s*Based\s*Access|Audit\s*Trail|Compliance\s*Reporting|Regulatory\s*Requirements|Data\s*Privacy|GDPR\s*Compliance|Security\s*Standards|Best\s*Practices|Industry\s*Standards|ISO\s*Certification|Quality\s*Assurance|Process\s*Improvement|Lean\s*Methodology|Six\s*Sigma|Agile\s*Development|Scrum\s*Framework|Kanban\s*Board|Sprint\s*Planning|Retrospective|Daily\s*Standup|User\s*Stories|Epic\s*Features|Backlog\s*Management|Release\s*Planning|Version\s*Control|Branch\s*Strategy|Merge\s*Conflict\s*Resolution|Code\s*Review\s*Process|Peer\s*Programming|Pair\s*Programming|Test\s*Driven\s*Development|Behavior\s*Driven\s*Development|Acceptance\s*Test\s*Driven\s*Development|Continuous\s*Integration|Continuous\s*Deployment|DevOps\s*Pipeline|Infrastructure\s*as\s*Code|Configuration\s*Management|Provisioning\s*Automation|Monitoring\s*and\s*Alerting|Log\s*Aggregation|Performance\s*Monitoring|Error\s*Tracking|Application\s*Performance\s*Management|User\s*Experience\s*Monitoring|Synthetic\s*Monitoring|Real\s*User\s*Monitoring|Distributed\s*Tracing|APM\s*Tools|New\s*Relic|Datadog|Splunk|ELK\s*Stack|Grafana|Prometheus|Kubernetes|Docker\s*Swarm|Container\s*Orchestration|Service\s*Mesh|Istio|Linkerd|Envoy|Load\s*Balancing|API\s*Gateway|Rate\s*Limiting|Circuit\s*Breaker|Retry\s*Logic|Timeout\s*Handling|Graceful\s*Degradation|Fallback\s*Mechanisms|Error\s*Recovery|Self\s*Healing|Auto\s*Scaling|Horizontal\s*Pod\s*Autoscaler|Cluster\s*Autoscaling|Resource\s*Quotas|Namespace\s*Management|Pod\s*Security|Network\s*Policies|Storage\s*Classes|Persistent\s*Volumes|Volume\s*Claims|StatefulSets|DaemonSets|Jobs|CronJobs|Init\s*Containers|Sidecar\s*Pattern|Ambassador\s*Pattern|Adapter\s*Pattern|Multi\s*Container\s*Pods|Health\s*Checks|Readiness\s*Probes|Liveness\s*Probes|Startup\s*Probes|Resource\s*Limits|Resource\s*Requests|Quality\s*of\s*Service|Priority\s*Classes|Preemption|Pod\s*Disruption\s*Budgets|Eviction\s*Policies|Node\s*Maintenance|Cluster\s*Upgrades|Rolling\s*Updates|Blue\s*Green\s*Deployment|Canary\s*Release|A/B\s*Testing|Feature\s*Flags|Dark\s*Launching|Progressive\s*Delivery|GitOps|Flux|Argo\s*CD|Jenkins\s*X|Tekton|Spinnaker|Keel|Flagger|Prometheus\s*Operator|Grafana\s*Operator|Alertmanager|Thanos|Cortex|Mimir|Victoria\s*Metrics|Loki|Fluentd|Fluent\s*Bit|Filebeat|Metricbeat|Heartbeat|Auditbeat|Packetbeat|Winlogbeat|Journalbeat|OpenTelemetry|Jaeger|Zipkin|SkyWalking|Pinpoint|Istio\s*Telemetry|Kiali|Service\s*Mesh\s*Interface|Envoy\s*Proxy|Contour|NGINX\s*Ingress\s*Controller|Traefik|HAProxy|Cert\s*Manager|External\s*DNS|MetalLB|Calico|Cilium|Flannel|Weave\s*Net|Antrea|Multus|CNI|CSI|Cinder|Ceph|Rook|Longhorn|OpenEBS|Portworx|StorageOS|Robin\s*CSI|FlexVolume|HostPath|EmptyDir|Downward\s*API|ConfigMap|Secret|Projected\s*Volume|Ephemeral\s*Volumes|Generic\s*Ephemeral\s*Volumes|CSI\s*Ephemeral\s*Volumes|Volume\s*Snapshots|Volume\s*Cloning|Volume\s*Expansion|Topology\s*Aware\s*Scheduling|Topology\s*Aware\s*Provisioning|Volume\s*Binding\s*Mode|Volume\s*Snapshot\s*Class|Volume\s*Snapshot\s*Content|Volume\s*Group\s*Snapshot|CSI\s*Migration|In\s*Tree\s*Volume\s*Plugins|Out\s*of\s*Tree\s*Volume\s*Plugins|FlexVolume\s*Drivers|CSI\s*Drivers|Volume\s*Plugins|Storage\s*Drivers|Provisioners|Attachers|Snapshotter|Resizer|Node\s*Stage\s*Volume|Expand\s*Volume|Cleanup\s*Controller|Provisioner|External\s*Provisioner|CSI\s*External\s*Provisioner|CSI\s*Driver\s*Registrar|CSI\s*Liveness\s*Probe|Node\s*Driver\s*Registrar|CSI\s*Node\s*Driver\s*External\s*Attacher|CSI\s*External\s*Resizer|CSI\s*External\s*Snapshotter|CSI\s*External\s*Health\s*Monitor|CSI\s*External\s*Provisioner)\b'

        # File extensions
        extension_pattern = r'\.[a-zA-Z0-9_-]{1,15}\b'

        # Directory paths
        dir_pattern = r'[a-zA-Z]:\\[^"<>|*\s]*|/[^"<>|\s]*[/\\]'

        # Environment variables
        env_pattern = r'\$[A-Z_][A-Z0-9_]*|%[A-Z_][A-Z0-9_]*%'

        # Extract entities with more robust error handling
        patterns = [
            (file_pattern, 'FILE_PATH'),
            (command_pattern, 'COMMAND'),
            (url_pattern, 'URL'),
            (tech_pattern, 'TECHNOLOGY'),
            (csf_pattern, 'CSF_NIP'),
            (extension_pattern, 'FILE_EXTENSION'),
            (dir_pattern, 'DIRECTORY'),
            (env_pattern, 'ENVIRONMENT_VAR')
        ]

        for pattern, entity_type in patterns:
            try:
                # Limit pattern complexity to avoid regex engine issues
                if entity_type == 'CSF_NIP':
                    # Use a simpler pattern for CSF_NIP to avoid complexity issues
                    simplified_csf = r'\b(?:CSF|NIP|Knowledge\s*Graph|Entity|Relationship|Constitution|Quality\s*Gate|Validation|TaskMaster|CWO|Executive|Command|Agent|Skill|Workflow|Orchestration|Session|Context|Memory|Evidence|Cognitive|Deliberate|Violation|Path|Goal|Truth|Handover|Continuity|Cross|Preservation|Reconstruction|Compaction|RAG|CKS|Search|Multi-Agent|Stack|Production|Conformance|Technical|Debt|Code|Standards|Architecture|Framework|System|Integration|Refactoring|Compliance|Testing|Learning|Performance|Resource|Error|Recovery|Security|Access|Permission|Authentication|Role|Audit|Reporting|Requirements|Privacy|GDPR|Best|Practices|Industry|ISO|Quality|Assurance|Process|Improvement|Lean|Six|Sigma|Agile|Development|Scrum|Framework|Kanban|Sprint|Planning|Retrospective|Daily|Standup|User|Stories|Epic|Features|Backlog|Management|Release|Version|Control|Branch|Strategy|Merge|Conflict|Resolution|Review|Pull|Request|Peer|Pair|Test|Driven|Behavior|Acceptance|Continuous|Integration|Deployment|Pipeline|Build|Deploy|Infrastructure|Configuration|Provisioning|Monitoring|Alerting|Log|Aggregation|Observability|SLO|SLA|SLI|Uptime|Downtime|Latency|Throughput|Response|Page|Load|Core|Vitals|SEO|SEM|Social|Media|Content|Marketing|Email|CRM|ERP|Business|Intelligence|Analytics|Dashboard|KPI|Metrics|ROI|CAC|LTV|Churn|Retention|Engagement|Conversion|Testing|Multivariate|User|Experience|Interface|Design|Component|Library|Style|Brand|Guidelines|Typography|Color|Theory|Layout|Grid|Responsive|Mobile|First|Progressive|Graceful|Accessibility|WCAG|Screen|Reader|Keyboard|Navigation|Focus|Internationalization|Localization|Globalization|Translation|Unicode|UTF|Character|Encoding|Escape|Sequences|Regular|Expressions|Pattern|Matching|Validation|Sanitization|XSS|CSRF|SQL|Injection|Input|Output|Content|Security|Policy|Same|Origin|CORS|JSONP|WebSockets|Server|Sent|Events|Push|Notifications|Service|Workers|App|Manifest|Offline|Progressive|Native|Hybrid|Cross|Platform|Flutter|React|Ionic|Cordova|PhoneGap|Electron|Desktop|Application|System|Tray|Menu|Bar|Dock|Task|Manager|Process|Management|Job|Scheduling|Cron|Queue|Message|Event|Bus|Publisher|Subscriber|Observer|Strategy|Factory|Singleton|Builder|Decorator|Adapter|Facade|Mediator|Memento|State|Template|Visitor)\b'
                    matches = re.finditer(simplified_csf, text, re.IGNORECASE)
                else:
                    matches = re.finditer(pattern, text, re.IGNORECASE)

                for match in matches:
                    entity_text = match.group().strip()
                    if len(entity_text) > 1:  # Filter out single characters
                        entities.append({
                            'text': entity_text,
                            'type': entity_type,
                            'start': match.start(),
                            'end': match.end(),
                            'confidence': 0.8
                        })
            except re.error as e:
                logger.warning(f"Regex error in pattern {entity_type}: {e}")
                continue
            except Exception as e:
                logger.warning(f"Unexpected error in pattern {entity_type}: {e}")
                continue

        return entities

    def extract_relationships(self, entities: list[dict[str, Any]], text: str) -> list[dict[str, Any]]:
        """
        Extract relationships between entities based on co-occurrence and linguistic patterns.
        """
        relationships = []

        # Co-occurrence relationships (entities appearing close to each other)
        window_size = 100  # characters

        for i, entity1 in enumerate(entities):
            for entity2 in entities[i+1:]:
                distance = abs(entity1['start'] - entity2['start'])

                if distance <= window_size:
                    # Check for relationship indicators
                    relationship_type = self._determine_relationship_type(entity1, entity2, text)
                    confidence = max(0.1, 1.0 - (distance / window_size))

                    relationships.append({
                        'source': entity1['text'],
                        'target': entity2['text'],
                        'type': relationship_type,
                        'confidence': confidence,
                        'context': text[max(0, min(entity1['start'], entity2['start'])-50):
                                     min(len(text), max(entity1['end'], entity2['end'])+50)]
                    })

        return relationships

    def _determine_relationship_type(self, entity1: dict, entity2: dict, text: str) -> str:
        """
        Determine the type of relationship between two entities.
        """
        # Extract context between entities
        start = min(entity1['end'], entity2['end'])
        end = max(entity1['start'], entity2['start'])
        context = text[start:end].lower()

        # Define relationship indicators
        indicators = {
            'USES': ['uses', 'using', 'use', 'used', 'implemented with', 'built with', 'leveraging'],
            'CONTAINS': ['contains', 'including', 'includes', 'has', 'with', 'features', 'comprises'],
            'RELATED_TO': ['related', 'associated', 'connected', 'linked', 'similar', 'corresponds'],
            'LOCATED_IN': ['in', 'at', 'on', 'located', 'found', 'directory', 'path', 'within'],
            'REFERENCES': ['references', 'refers', 'mentions', 'cites', 'points to', 'links to'],
            'DEPENDS_ON': ['depends', 'requires', 'needs', 'imports', 'extends', 'relies on'],
            'CREATES': ['creates', 'generates', 'produces', 'builds', 'makes', 'outputs'],
            'MODIFIES': ['modifies', 'updates', 'changes', 'edits', 'alters', 'adjusts'],
            'IMPLEMENTS': ['implements', 'realizes', 'executes', 'applies', 'enforces'],
            'VALIDATES': ['validates', 'checks', 'verifies', 'confirms', 'ensures'],
            'INTEGRATES': ['integrates', 'combines', 'merges', 'joins', 'connects'],
            'MANAGES': ['manages', 'handles', 'controls', 'oversees', 'supervises'],
            'PROCESSES': ['processes', 'handles', 'executes', 'runs', 'operates']
        }

        # Check for relationship indicators
        for rel_type, words in indicators.items():
            if any(word in context for word in words):
                return rel_type

        # Default relationship based on entity types
        type_combinations = {
            ('FILE_PATH', 'COMMAND'): 'MODIFIES',
            ('COMMAND', 'FILE_PATH'): 'MODIFIES',
            ('TECHNOLOGY', 'FILE_PATH'): 'USES',
            ('URL', 'TECHNOLOGY'): 'REFERENCES',
            ('PERSON', 'ORG'): 'WORKS_FOR',
            ('ORG', 'PERSON'): 'EMPLOYS',
            ('CSF_NIP', 'COMMAND'): 'IMPLEMENTS',
            ('COMMAND', 'CSF_NIP'): 'VALIDATES',
            ('CSF_NIP', 'FILE_PATH'): 'REFERENCES',
            ('CSF_NIP', 'TECHNOLOGY'): 'USES'
        }

        key = (entity1['type'], entity2['type'])
        return type_combinations.get(key, 'RELATED_TO')

    def process_conversation_batch(self, conversations: list[dict[str, Any]], batch_idx: int) -> dict[str, Any]:
        """
        Process a batch of conversations and extract knowledge graph data.
        """
        batch_start_time = time.time()
        batch_entities = []
        batch_relationships = []
        batch_conversation_entities = {}

        logger.info(f"Processing batch {batch_idx + 1} with {len(conversations)} conversations")

        for conv_idx, conversation in enumerate(conversations):
            conv_id = conversation.get('timestamp', f"conv_{batch_idx}_{conv_idx}")
            display_text = conversation.get('display', '')
            project = conversation.get('project', '')

            # Combine display text and project for entity extraction
            full_text = f"{display_text} {project}".strip()

            if not full_text:
                continue

            # Extract entities
            entity_start_time = time.time()
            entities = self.extract_entities_basic(full_text)
            self.metrics['entity_extraction_time'] += time.time() - entity_start_time

            # Extract relationships
            rel_start_time = time.time()
            relationships = self.extract_relationships(entities, full_text)
            self.metrics['relationship_extraction_time'] += time.time() - rel_start_time

            # Store conversation data
            batch_entities.extend(entities)
            batch_relationships.extend(relationships)
            batch_conversation_entities[conv_id] = [e['text'] for e in entities]

            self.metrics['processed_conversations'] += 1

        batch_processing_time = time.time() - batch_start_time
        logger.info(f"Batch {batch_idx + 1} processed in {batch_processing_time:.2f}s")

        return {
            'entities': batch_entities,
            'relationships': batch_relationships,
            'conversation_entities': batch_conversation_entities,
            'processing_time': batch_processing_time
        }

    def build_knowledge_graph(self, input_file: str) -> dict[str, Any]:
        """
        Build the complete knowledge graph from the conversation dataset.
        """
        logger.info(f"Starting knowledge graph construction from {input_file}")
        start_time = time.time()

        # Read and process conversations in batches
        conversations = []
        total_lines = 0
        batch_size = 64

        try:
            with open(input_file, encoding='utf-8') as f:
                for line_num, line in enumerate(f):
                    total_lines += 1
                    try:
                        conversation = json.loads(line.strip())
                        conversations.append(conversation)

                        # Process batch when full
                        if len(conversations) >= batch_size:
                            self._process_batch(conversations, len(conversations) // batch_size - 1)
                            conversations = []
                            gc.collect()  # Clean up memory

                    except json.JSONDecodeError as e:
                        logger.warning(f"Skipping malformed line {line_num + 1}: {e}")
                        continue

                # Process remaining conversations
                if conversations:
                    self._process_batch(conversations, total_lines // batch_size)
                    conversations = []
                    gc.collect()

        except Exception as e:
            logger.error(f"Error processing input file: {e}")
            raise

        self.metrics['total_conversations'] = total_lines
        self.metrics['processing_time'] = time.time() - start_time

        logger.info(f"Knowledge graph construction completed in {self.metrics['processing_time']:.2f}s")

        return self._generate_final_report()

    def _process_batch(self, conversations: list[dict], batch_idx: int):
        """Process a single batch and update the knowledge graph."""
        batch_result = self.process_conversation_batch(conversations, batch_idx)

        # Update global graph data
        for entity in batch_result['entities']:
            # Create a safe entity ID
            entity_id = re.sub(r'[^\w]', '_', entity['text'].lower())
            entity_id = re.sub(r'_+', '_', entity_id).strip('_')

            if not entity_id:  # If empty after cleaning, use a hash
                entity_id = f"entity_{hash(entity['text']) % 1000000}"

            if entity_id not in self.entities:
                self.entities[entity_id] = {
                    'id': entity_id,
                    'text': entity['text'],
                    'type': entity['type'],
                    'confidence': entity['confidence'],
                    'occurrences': 0,
                    'contexts': [],
                    # Note: Excluding embeddings from this version to avoid serialization issues
                }

            self.entities[entity_id]['occurrences'] += 1
            self.entity_types[entity['type']].add(entity_id)

        self.relationships.extend(batch_result['relationships'])
        self.conversation_entities.update(batch_result['conversation_entities'])
        self.metrics['batches_processed'] += 1

    def _generate_final_report(self) -> dict[str, Any]:
        """Generate comprehensive statistics and performance report."""
        # Calculate entity type distribution
        entity_type_counts = {}
        for entity_type, entity_ids in self.entity_types.items():
            entity_type_counts[entity_type] = len(entity_ids)

        # Calculate relationship type distribution
        relationship_type_counts = Counter(rel['type'] for rel in self.relationships)

        # Calculate top entities by frequency
        top_entities = sorted(
            [(entity['text'], entity['occurrences']) for entity in self.entities.values()],
            key=lambda x: x[1],
            reverse=True
        )[:20]

        # Memory usage
        entities_memory = len(str(self.entities)) / (1024**2)  # MB
        relationships_memory = len(str(self.relationships)) / (1024**2)  # MB

        # Performance metrics
        avg_conversations_per_second = self.metrics['processed_conversations'] / max(1, self.metrics['processing_time'])
        avg_entities_per_conversation = self.metrics['total_entities'] / max(1, self.metrics['processed_conversations'])
        avg_relationships_per_conversation = self.metrics['total_relationships'] / max(1, self.metrics['processed_conversations'])

        report = {
            'summary': {
                'total_conversations': self.metrics['total_conversations'],
                'processed_conversations': self.metrics['processed_conversations'],
                'total_unique_entities': len(self.entities),
                'total_relationships': len(self.relationships),
                'total_entity_types': len(self.entity_types),
                'total_batches_processed': self.metrics['batches_processed'],
                'processing_time_seconds': round(self.metrics['processing_time'], 2),
                'average_conversations_per_second': round(avg_conversations_per_second, 2)
            },
            'entity_analysis': {
                'type_distribution': entity_type_counts,
                'top_entities_by_frequency': top_entities,
                'average_entities_per_conversation': round(avg_entities_per_conversation, 2)
            },
            'relationship_analysis': {
                'type_distribution': dict(relationship_type_counts),
                'average_relationships_per_conversation': round(avg_relationships_per_conversation, 2)
            },
            'performance_metrics': {
                'entity_extraction_time_seconds': round(self.metrics['entity_extraction_time'], 2),
                'relationship_extraction_time_seconds': round(self.metrics['relationship_extraction_time'], 2),
                'embedding_time_seconds': round(self.metrics['embedding_time'], 2),
                'gpu_memory_used_gb': round(self.metrics['gpu_memory_used'], 2),
                'estimated_memory_usage_mb': {
                    'entities': round(entities_memory, 2),
                    'relationships': round(relationships_memory, 2),
                    'total': round(entities_memory + relationships_memory, 2)
                }
            },
            'gpu_acceleration': {
                'gpu_available': GPU_AVAILABLE,
                'device_used': 'cpu',  # Using CPU for this version
                'model_loaded': False,
                'spacy_loaded': False,
                'processing_mode': 'CPU-only processing (embeddings excluded for stability)'
            }
        }

        # Update total counts
        self.metrics['total_entities'] = len(self.entities)
        self.metrics['total_relationships'] = len(self.relationships)

        return report

    def export_knowledge_graph(self, output_dir: str = "knowledge_graph_output"):
        """
        Export the knowledge graph data to files with proper JSON serialization.
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        logger.info(f"Exporting knowledge graph to {output_path}")

        # Export entities (without embeddings to avoid serialization issues)
        entities_file = output_path / "entities.json"
        entities_to_export = []
        for entity_id, entity_data in self.entities.items():
            export_entity = entity_data.copy()
            if 'embedding' in export_entity:
                del export_entity['embedding']  # Remove embeddings for JSON compatibility
            entities_to_export.append(export_entity)

        with open(entities_file, 'w', encoding='utf-8') as f:
            json.dump(entities_to_export, f, indent=2, ensure_ascii=False)

        # Export relationships
        relationships_file = output_path / "relationships.json"
        with open(relationships_file, 'w', encoding='utf-8') as f:
            json.dump(self.relationships, f, indent=2, ensure_ascii=False)

        # Export conversation entities mapping
        conv_entities_file = output_path / "conversation_entities.json"
        with open(conv_entities_file, 'w', encoding='utf-8') as f:
            json.dump(self.conversation_entities, f, indent=2, ensure_ascii=False)

        # Export final report
        report = self._generate_final_report()
        report_file = output_path / "knowledge_graph_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        # Export human-readable summary
        summary_file = output_path / "summary.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("KNOWLEDGE GRAPH CONSTRUCTION SUMMARY\n")
            f.write("=" * 50 + "\n\n")

            f.write("Dataset: E:/Users/brsth/.claude/history.jsonl\n")
            f.write(f"Processing Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("Device: CPU\n")
            f.write("Processing Mode: CPU-only processing (embeddings excluded for stability)\n\n")

            f.write("SUMMARY STATISTICS:\n")
            f.write("-" * 20 + "\n")
            for key, value in report['summary'].items():
                f.write(f"{key.replace('_', ' ').title()}: {value:,}\n")

            f.write("\nENTITY ANALYSIS:\n")
            f.write("-" * 20 + "\n")
            for entity_type, count in report['entity_analysis']['type_distribution'].items():
                f.write(f"  {entity_type}: {count:,}\n")
            f.write("\nTop Entities by Frequency:\n")
            for entity, count in report['entity_analysis']['top_entities_by_frequency'][:10]:
                f.write(f"  - {entity}: {count:,} occurrences\n")

            f.write("\nRELATIONSHIP ANALYSIS:\n")
            f.write("-" * 25 + "\n")
            for rel_type, count in report['relationship_analysis']['type_distribution'].items():
                f.write(f"  - {rel_type}: {count:,}\n")

            f.write("\nPERFORMANCE METRICS:\n")
            f.write("-" * 20 + "\n")
            for key, value in report['performance_metrics'].items():
                if isinstance(value, dict):
                    f.write(f"{key.replace('_', ' ').title()}:\n")
                    for sub_key, sub_value in value.items():
                        f.write(f"  - {sub_key.replace('_', ' ').title()}: {sub_value}\n")
                else:
                    f.write(f"{key.replace('_', ' ').title()}: {value}\n")

        logger.info(f"Knowledge graph exported successfully to {output_path}")

        return {
            'entities_file': str(entities_file),
            'relationships_file': str(relationships_file),
            'conversation_entities_file': str(conv_entities_file),
            'report_file': str(report_file),
            'summary_file': str(summary_file)
        }

def main():
    """Main function to run the complete knowledge graph exporter."""
    # Configuration
    INPUT_FILE = "E:/Users/brsth/.claude/history.jsonl"
    OUTPUT_DIR = "P:/projects/kg_builder/knowledge_graph_output"

    logger.info("=" * 60)
    logger.info("COMPLETE KNOWLEDGE GRAPH EXPORTER")
    logger.info("=" * 60)
    logger.info(f"Input file: {INPUT_FILE}")
    logger.info(f"Output directory: {OUTPUT_DIR}")
    logger.info("=" * 60)

    # Initialize the exporter
    exporter = CompleteKnowledgeGraphExporter()

    try:
        # Build the knowledge graph
        start_time = time.time()

        # Process the entire dataset
        report = exporter.build_knowledge_graph(INPUT_FILE)

        # Export results
        export_files = exporter.export_knowledge_graph(OUTPUT_DIR)

        total_time = time.time() - start_time

        # Print final summary
        logger.info("=" * 60)
        logger.info("KNOWLEDGE GRAPH CONSTRUCTION AND EXPORT COMPLETED")
        logger.info("=" * 60)
        logger.info(f"Total processing time: {total_time:.2f} seconds")
        logger.info(f"Conversations processed: {report['summary']['processed_conversations']:,}")
        logger.info(f"Unique entities extracted: {report['summary']['total_unique_entities']:,}")
        logger.info(f"Relationships identified: {report['summary']['total_relationships']:,}")
        logger.info(f"Entity types discovered: {report['summary']['total_entity_types']}")
        logger.info(f"Processing speed: {report['summary']['average_conversations_per_second']:.2f} conv/sec")

        logger.info("\nExport files:")
        for file_type, file_path in export_files.items():
            logger.info(f"  - {file_type}: {file_path}")

        logger.info("=" * 60)
        logger.info("SUCCESS: Knowledge graph construction and export completed!")
        logger.info("=" * 60)

        return report

    except Exception as e:
        logger.error(f"Error during knowledge graph construction: {e}")
        raise

if __name__ == "__main__":
    main()
