#!/usr/bin/env python3
"""
Scalable GPU-Accelerated Knowledge Graph Builder for Conversation Data

Processes 20,880 conversations with entity extraction, relationship mapping,
and GPU acceleration for optimal performance.

Author: Claude ML Engineer
Date: 2025-12-19
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

# NLP libraries - handle spaCy compatibility issues
NLP_AVAILABLE = False
nlp = None

try:
    import spacy
    # Try to load spaCy model, but handle Python 3.14 compatibility issues
    try:
        nlp = spacy.load("en_core_web_sm")
        NLP_AVAILABLE = True
        print("spaCy model loaded successfully")
    except Exception as e:
        print(f"spaCy model loading failed: {e}. Using basic entity extraction.")
        NLP_AVAILABLE = False
except ImportError:
    print("spaCy not available. Using basic entity extraction.")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('knowledge_graph_construction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GPUGraphBuilder:
    """
    GPU-accelerated knowledge graph builder for conversation data.
    """

    def __init__(self, batch_size: int = 128, device: str = 'auto'):
        """
        Initialize the GPU-accelerated graph builder.

        Args:
            batch_size: Number of conversations to process in each batch
            device: 'auto', 'cuda', or 'cpu'
        """
        self.batch_size = batch_size
        self.device = self._setup_device(device)

        # Initialize GPU models if available
        self.sentence_model = None
        self.nlp = nlp  # Use the global nlp variable

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

        self._initialize_models()

    def _setup_device(self, device: str) -> str:
        """Setup and return the appropriate device."""
        if device == 'auto':
            return 'cuda' if GPU_AVAILABLE else 'cpu'
        elif device == 'cuda' and not GPU_AVAILABLE:
            logger.warning("CUDA requested but not available. Using CPU.")
            return 'cpu'
        return device

    def _initialize_models(self):
        """Initialize NLP and embedding models."""
        logger.info(f"Initializing models on device: {self.device}")

        # Initialize sentence transformer for embeddings
        try:
            model_name = 'all-MiniLM-L6-v2'  # Fast, efficient model
            self.sentence_model = SentenceTransformer(model_name)
            if self.device == 'cuda':
                self.sentence_model = self.sentence_model.to(self.device)
            logger.info(f"Sentence transformer loaded: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load sentence transformer: {e}")
            self.sentence_model = None

        logger.info(f"NLP available: {NLP_AVAILABLE}")

    def extract_entities_basic(self, text: str) -> list[dict[str, Any]]:
        """
        Basic entity extraction using regex patterns.
        Fallback method when spaCy is not available.
        """
        entities = []

        # File paths - comprehensive pattern
        file_pattern = r'[\w\-\/\.]+\.(py|md|txt|json|yaml|yml|csv|tsv|log|sh|bat|ps1|js|ts|html|css|sql|xml|ini|cfg|conf|toml|lock|env|gitignore|dockerfile|requirements\.txt|package\.json|setup\.py|makefile|readme|license|changelog|manifest|setup\.cfg|pyproject\.toml|pytest\.ini|tox\.ini|mypy\.ini|flake8\.cfg|black\.py|isort\.cfg|pre-commit-config\.yaml|\.pre-commit-config\.yaml|\.gitignore|\.dockerignore|\.editorconfig|\.babelrc|\.eslintrc|\.prettierrc|tsconfig\.json|webpack\.config\.js|vite\.config\.js|rollup\.config\.js|gulpfile\.js|gruntfile\.js|rakefile|gemfile|composer\.json|package\.lock\.json|yarn\.lock|pipfile|pipfile\.lock|poetry\.lock|cargo\.toml|cargo\.lock|go\.mod|go\.sum|requirements\.dev\.txt|requirements\.test\.txt|requirements\.prod\.txt|requirements\.base\.txt|requirements\.local\.txt|requirements\.txt|setup\.cfg|setup\.py|pyproject\.toml|tox\.ini|pytest\.ini|conftest\.py|test_.*\.py|.*_test\.py|.*_spec\.py|spec_.*\.py|tests?/.*\.py)'

        # Commands and tools
        command_pattern = r'\/\w+(?:\s+\w+)*|git\s+\w+|npm\s+\w+|pip\s+\w+|python\s+\w+|pytest\s+\w+|docker\s+\w+|kubectl\s+\w+|aws\s+\w+|azure\s+\w+|gcloud\s+\w+|terraform\s+\w+|ansible\s+\w+|vagrant\s+\w+|make\s+\w+|cmake\s+\w+|gradle\s+\w+|mvn\s+\w+|yarn\s+\w+|bower\s+\w+|composer\s+\w+|bundle\s+\w+|gem\s+\w+|cargo\s+\w+|go\s+\w+|rustc\s+\w+|gcc\s+\w+|g\+\+\s+\w+|clang\s+\w+|javac\s+\w+|java\s+\w+|python\s+\w+|python3\s+\w+|pip3\s+\w+|node\s+\w+|npm\s+\w+|npx\s+\w+|yarn\s+\w+|pnpm\s+\w+|deno\s+\w+|bun\s+\w+'

        # URLs and domains
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+|www\.[^\s<>"{}|\\^`\[\]]+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s<>"{}|\\^`\[\]]*)?'

        # Technical terms and frameworks - expanded pattern
        tech_pattern = r'\b(?:API|REST|GraphQL|SQL|NoSQL|MongoDB|PostgreSQL|MySQL|Redis|Elasticsearch|Kafka|RabbitMQ|Docker|Kubernetes|AWS|Azure|GCP|Terraform|Ansible|Jenkins|GitLab|GitHub|Bitbucket|Jira|Confluence|Slack|Discord|Teams|Zoom|Webex|TensorFlow|PyTorch|Keras|Scikit-learn|Pandas|NumPy|Matplotlib|Seaborn|Plotly|Dash|Streamlit|Flask|Django|FastAPI|Spring|React|Vue|Angular|Svelte|Next\.js|Nuxt\.js|Gatsby|Webpack|Vite|Rollup|Parcel|Babel|ESLint|Prettier|Jest|Mocha|Chai|Cypress|Selenium|Playwright|Puppeteer|Cypress|Postman|Swagger|OpenAPI|GraphQL|gRPC|Protocol Buffers|Thrift|Avro|JSON|YAML|XML|CSV|TSV|Markdown|LaTeX|HTML|CSS|SASS|SCSS|LESS|TypeScript|JavaScript|Python|Java|C\+\+|C#|Go|Rust|Ruby|PHP|Swift|Kotlin|Scala|Haskell|Erlang|Elixir|Clojure|F#|Objective-C|Dart|Lua|Perl|R|MATLAB|Julia|Bash|PowerShell|Zsh|Fish|CMD|BAT|Shell|Linux|Windows|macOS|Ubuntu|Debian|CentOS|RHEL|Alpine|Arch|Fedora|openSUSE|FreeBSD|NetBSD|OpenBSD|Darwin|iOS|Android|Windows|Linux|macOS|CSF|NIP|CLI|LLM|ML|AI|GPU|CPU|RAM|SSD|HDD|HTTP|HTTPS|TCP|UDP|IP|DNS|SSH|FTP|SFTP|VPN|CDN|CI|CD|DevOps|Agile|Scrum|Kanban|TDD|BDD|OOP|FP|SOA|Microservices|Serverless|Containers|Orchestration|Monitoring|Logging|Metrics|Tracing|Testing|Debugging|Profiling|Optimization|Security|Authentication|Authorization|Encryption|Hashing|Salting|JWT|OAuth|SAML|LDAP|Active Directory|Database|Data Warehouse|Data Lake|ETL|ELT|Big Data|Data Science|Machine Learning|Deep Learning|Neural Networks|CNN|RNN|LSTM|GAN|Reinforcement Learning|Supervised Learning|Unsupervised Learning|Semi-supervised Learning|Transfer Learning|Ensemble Learning|Random Forest|Decision Tree|SVM|K-means|Clustering|Classification|Regression|NLP|Computer Vision|Time Series|Forecasting|Anomaly Detection|Recommendation Systems|Search Engines|Information Retrieval|Web Crawling|Web Scraping|API Design|RESTful|GraphQL|WebSocket|WebRTC|PWA|SPA|MVC|MVP|MVVM|Design Patterns|SOLID|DRY|KISS|YAGNI|Big O|Algorithm|Data Structure|Queue|Stack|Heap|Tree|Graph|Linked List|Array|Hash Table|Sorting|Searching|Dynamic Programming|Recursion|Iteration|Concurrency|Parallelism|Multithreading|Async|Await|Promise|Callback|Closure|Lambda|Function|Class|Object|Inheritance|Polymorphism|Encapsulation|Abstraction|Interface|Abstract Class|Constructor|Destructor|Method|Property|Field|Variable|Constant|Enum|Struct|Union|Pointer|Reference|Memory Management|Garbage Collection|Stack Overflow|Heap Overflow|Memory Leak|Deadlock|Race Condition|Semaphore|Mutex|Lock|Thread Safety|Atomic Operations|Consistency|Availability|Partition Tolerance|CAP Theorem|ACID|BASE|Normalization|Denormalization|Indexing|Query Optimization|Caching|Load Balancing|Scaling|Horizontal Scaling|Vertical Scaling|Redundancy|Failover|Disaster Recovery|Backup|Restore|Migration|Version Control|Git|GitHub|GitLab|Bitbucket|Branching|Merging|Rebasing|Cherry-picking|Conflict Resolution|Code Review|Pull Request|Merge Request|Continuous Integration|Continuous Deployment|Pipeline|Build|Test|Deploy|Infrastructure as Code|Configuration Management|Provisioning|Monitoring|Alerting|Logging|Tracing|Observability|SLO|SLA|SLI|Uptime|Downtime|Performance|Latency|Throughput|Response Time|Time to First Byte|Page Load|Core Web Vitals|SEO|SEM|Social Media|Content Marketing|Email Marketing|CRM|ERP|Business Intelligence|Analytics|Dashboard|KPI|Metrics|ROI|CAC|LTV|Churn|Retention|Engagement|Conversion|A/B Testing|Multivariate Testing|User Experience|User Interface|Design System|Component Library|Style Guide|Brand Guidelines|Typography|Color Theory|Layout|Grid|Responsive Design|Mobile First|Progressive Enhancement|Graceful Degradation|Accessibility|WCAG|Screen Reader|Keyboard Navigation|Focus Management|Internationalization|Localization|Globalization|Translation|Right-to-Left|Unicode|UTF-8|Character Encoding|Escape Sequences|Regular Expressions|Pattern Matching|Validation|Sanitization|XSS|CSRF|SQL Injection|Input Validation|Output Encoding|Content Security Policy|Same Origin Policy|CORS|JSONP|WebSockets|Server-Sent Events|Push Notifications|Service Workers|Web App Manifest|Offline First|Progressive Web App|Native App|Hybrid App|Cross Platform|Flutter|React Native|Ionic|Cordova|PhoneGap|Electron|NW.js|Desktop Application|System Tray|Menu Bar|Dock|Task Manager|Process Management|Job Scheduling|Cron|Task Queue|Message Queue|Event Bus|Publisher Subscriber|Observer Pattern|Strategy Pattern|Factory Pattern|Singleton Pattern|Builder Pattern|Decorator Pattern|Adapter Pattern|Facade Pattern|Command Pattern|Iterator Pattern|Composite Pattern|Flyweight Pattern|Proxy Pattern|Bridge Pattern|Chain of Responsibility|Mediator Pattern|Memento Pattern|State Pattern|Template Method|Visitor Pattern)\b'

        # File extensions
        extension_pattern = r'\.\w{1,10}\b'

        # CSF NIP specific patterns
        csf_pattern = r'\b(?:CSF\s+NIP|NIP\s+System|Knowledge\s+Graph|Entity\s+Extraction|Relationship\s+Mapping|Constitution\s+Compliance|Quality\s+Gate|Validation\s+Gate|TaskMaster|CWO|Executive|Command|Agent|Skill|Workflow|Orchestration|Session\s+Management|Context\s+Compression|Memory\s+Pressure|Evidence\s+Correlation|Cognitive\s+Enhancement|Deliberate\s+Changes|Subagent\s+Injection|Violation\s+Reporting|Path\s+Validation|Goal\s|Anchoring|Truth\s+Audit|Anti-Deception|Handover\s|Documentation|Session\s+Continuity|Cross\s+Session\s|Tracking|Memory\s+Preservation|Context\s|Reconstruction|Compaction\s+Management|RAG\s+Integration|CKS\s+Knowledge|Search\s+Intelligence|Multi-Agent\s+Systems|Cognitive\s+Stack|Production\s+Deployment|Conformance\s+Validation|Technical\s+Debt\s+Analysis|Code\s+Quality\s+Standards|Architecture\s+Decision\s|Framework|System\s+Improvement|Integration\s+Refactoring|Compliance\s+Checking|Automated\s+Testing|Continuous\s+Learning|Performance\s+Optimization|Resource\s+Management|Error\s+Handling|Recovery\s|Procedures|Security\s+Validation|Access\s+Control|Permission\s+Management|User\s+Authentication|Role\s+Based\s+Access|Audit\s+Trail|Compliance\s+Reporting|Regulatory\s+Requirements|Data\s+Privacy|GDPR\s+Compliance|Security\s+Standards|Best\s+Practices|Industry\s+Standards|ISO\s+Certification|Quality\s+Assurance|Process\s+Improvement|Lean\s+Methodology|Six\s+Sigma|Agile\s+Development|Scrum\s+Framework|Kanban\s+Board|Sprint\s+Planning|Retrospective|Daily\s+Standup|User\s+Stories|Epic\s+Features|Backlog\s+Management|Release\s+Planning|Version\s+Control|Branch\s+Strategy|Merge\s+Conflict|Resolution|Code\s+Review|Process|Peer\s+Programming|Pair\s+Programming|Test\s+Driven\s+Development|Behavior\s+Driven\s+Development|Acceptance\s+Test\s+Driven|Development|Continuous\s+Integration|Continuous\s+Deployment|DevOps\s+Pipeline|Infrastructure\s+as\s+Code|Configuration\s+Management|Provisioning|Automation|Monitoring\s+and\s+Alerting|Log\s+Aggregation|Performance\s+Monitoring|Error\s+Tracking|Application\s+Performance\s+Management|User\s+Experience|Monitoring|Synthetic\s+Monitoring|Real\s+User\s+Monitoring|Distributed\s+Tracing|APM|Tools|New\s+Relic|Datadog|Splunk|ELK\s+Stack|Grafana|Prometheus|Kubernetes|Docker\s+Swarm|Container\s+Orchestration|Service\s+Mesh|Istio|Linkerd|Envoy|Load\s+Balancing|API\s+Gateway|Rate\s+Limiting|Circuit\s+Breaker|Retry\s+Logic|Timeout\s+Handling|Graceful\s+Degradation|Fallback\s+Mechanisms|Error\s+Recovery|Self\s+Healing|Auto\s+Scaling|Horizontal\s+Pod\s+Autoscaler|Cluster\s+Autoscaling|Resource\s+Quotas|Namespace\s+Management|Pod\s+Security|Network\s+Policies|Storage\s+Classes|Persistent\s+Volumes|Volume\s|Claims|StatefulSets|DaemonSets|Jobs|CronJobs|Init\s+Containers|Sidecar\s+Pattern|Ambassador\s+Pattern|Adapter\s+Pattern|Multi\s+Container|Pods|Health\s+Checks|Readiness\s+Probes|Liveness\s+Probes|Startup\s+Probes|Resource\s+Limits|Resource\s+Requests|Quality\s+of\s+Service|Priority\s+Classes|Preemption|Pod\s+Disruption\s+Budg|ets|Eviction\s+Policies|Node\s+Maintenance|Cluster\s+Upgrades|Rolling\s+Updates|Blue\s|Green\s+Deployment|Canary\s+Release|A/B\s+Testing|Feature\s+Flags|Dark\s+Launching|Progressive\s+Delivery|GitOps|Flux|Argo\s+CD|Jenkins\s+X|Tekton|Spinnaker|Keel|Flagger|Prometheus\s+Operator|Grafana\s+Operator|Alertmanager|Thanos|Cortex|Mimir|Victoria\s+Metrics|Loki|Fluentd|Fluent\s+Bit|Filebeat|Metricbeat|Heartbeat|Auditbeat|Packetbeat|Winlogbeat|Journalbeat|OpenTelemetry|Jaeger|Zipkin|SkyWalking|Pinpoint|Istio\s+Telemetry|Kiali|Service\s+Mesh\s+Interface|Envoy\s+Proxy|Contour|NGINX\s+Ingress|Controller|Traefik|HAProxy|Cert\s|Manager|External\s+DNS|MetalLB|Calico|Cilium|Flannel|Weave\s+Net|Antrea|Multus|CNI|CSI|Cinder|Ceph|Rook|Longhorn|OpenEBS|Portworx|StorageOS|Robin\s+CSI|FlexVolume|HostPath|EmptyDir|Downward\s+API|ConfigMap|Secret|Projected\s+Volume|Ephemeral\s+Volumes|Generic\s+Ephemeral\s+Volumes|CSI\s+Ephemeral\s+Volumes|Volume\s|Snapshots|Volume\s|Cloning|Volume\s+Expansion|Topology\s|Aware\s+Scheduling|Topology\s|Aware\s+Provisioning|Volume\s|Binding\s+Mode|Volume\s|Snapshot\s+Class|Volume\s|Snapshot|Content|Volume\s+Group\s+Snapshot|CSI\s+Migration|In\s+Tree\s+Volume\s+Plugins|Out\s+of\s+Tree\s+Volume\s+Plugins|FlexVolume|Drivers|CSI\s+Drivers|Volume\s|Plugins|Storage\s+Drivers|Provisioners|Attachers|Snapshotter|Resizer|Node\s|Stage|Volume|Expand|Volume|Cleanup|Controller|Provisioner|External\s+Provisioner|CSI\s+External|Provisioner|CSI\s+Driver|Registrar|CSI\s|Liveness|Probe|Node\s|Driver|Registrar|CSI\s|Node|Driver|External|Attacher|CSI\s|External|Resizer|CSI\s|External|Snapshotter|CSI\s|External|Health|Monitor|CSI\s|External|Provisioner|CSI\s|External|Attacher|CSI\s|External|Resizer|CSI\s|External|Snapshotter|CSI\s|External|Health|Monitor|CSI)\b'

        # Extract entities
        patterns = [
            (file_pattern, 'FILE_PATH'),
            (command_pattern, 'COMMAND'),
            (url_pattern, 'URL'),
            (tech_pattern, 'TECHNOLOGY'),
            (csf_pattern, 'CSF_NIP'),
            (extension_pattern, 'FILE_EXTENSION')
        ]

        for pattern, entity_type in patterns:
            try:
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

        return entities

    def extract_entities_spacy(self, text: str) -> list[dict[str, Any]]:
        """
        Extract entities using spaCy NLP model.
        """
        if not NLP_AVAILABLE or not self.nlp:
            return self.extract_entities_basic(text)

        try:
            entities = []
            doc = self.nlp(text)

            for ent in doc.ents:
                # Map spaCy entity types to our categories
                entity_type = ent.label_
                if ent.label_ in ['PERSON', 'ORG', 'GPE', 'PRODUCT', 'EVENT', 'WORK_OF_ART', 'LAW', 'LANGUAGE', 'DATE', 'TIME', 'PERCENT', 'MONEY', 'QUANTITY', 'ORDINAL', 'CARDINAL']:
                    entity_type = ent.label_
                else:
                    entity_type = 'MISC'

                entities.append({
                    'text': ent.text,
                    'type': entity_type,
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'confidence': 0.9
                })

            # Add basic pattern matching for technical entities
            basic_entities = self.extract_entities_basic(text)
            entities.extend(basic_entities)

            # Remove duplicates
            seen = set()
            unique_entities = []
            for entity in entities:
                key = (entity['text'].lower(), entity['type'], entity['start'], entity['end'])
                if key not in seen:
                    seen.add(key)
                    unique_entities.append(entity)

            return unique_entities

        except Exception as e:
            logger.warning(f"spaCy processing failed: {e}. Falling back to basic extraction.")
            return self.extract_entities_basic(text)

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

    def generate_embeddings(self, texts: list[str]) -> np.ndarray | None:
        """
        Generate embeddings for a list of texts using GPU acceleration.
        """
        if not self.sentence_model or not texts:
            return None

        try:
            start_time = time.time()
            embeddings = self.sentence_model.encode(
                texts,
                batch_size=self.batch_size,
                device=self.device,
                show_progress_bar=False,
                convert_to_numpy=True
            )
            self.metrics['embedding_time'] += time.time() - start_time

            if self.device == 'cuda':
                self.metrics['gpu_memory_used'] = torch.cuda.memory_allocated() / (1024**3)  # GB

            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return None

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
            entities = self.extract_entities_spacy(full_text)
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

        # Generate embeddings for unique entity texts
        unique_entity_texts = list(set(entity['text'] for entity in batch_entities))
        if unique_entity_texts and self.sentence_model:
            embeddings = self.generate_embeddings(unique_entity_texts)
            if embeddings is not None:
                # Add embeddings to entities
                embedding_map = {text: emb for text, emb in zip(unique_entity_texts, embeddings, strict=False)}
                for entity in batch_entities:
                    entity['embedding'] = embedding_map.get(entity['text'])

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

        try:
            with open(input_file, encoding='utf-8') as f:
                for line_num, line in enumerate(f):
                    total_lines += 1
                    try:
                        conversation = json.loads(line.strip())
                        conversations.append(conversation)

                        # Process batch when full
                        if len(conversations) >= self.batch_size:
                            self._process_batch(conversations, len(conversations) // self.batch_size - 1)
                            conversations = []
                            gc.collect()  # Clean up memory

                    except json.JSONDecodeError as e:
                        logger.warning(f"Skipping malformed line {line_num + 1}: {e}")
                        continue

                # Process remaining conversations
                if conversations:
                    self._process_batch(conversations, total_lines // self.batch_size)
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
            entity_id = entity['text'].lower().replace(' ', '_').replace('.', '_').replace('/', '_').replace('\\', '_')
            if entity_id not in self.entities:
                self.entities[entity_id] = {
                    'id': entity_id,
                    'text': entity['text'],
                    'type': entity['type'],
                    'confidence': entity['confidence'],
                    'occurrences': 0,
                    'contexts': [],
                    'embedding': entity.get('embedding')
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
                'device_used': self.device,
                'model_loaded': self.sentence_model is not None,
                'spacy_loaded': NLP_AVAILABLE and self.nlp is not None
            }
        }

        # Update total counts
        self.metrics['total_entities'] = len(self.entities)
        self.metrics['total_relationships'] = len(self.relationships)

        return report

    def export_knowledge_graph(self, output_dir: str = "knowledge_graph_output"):
        """
        Export the knowledge graph data to files.
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        logger.info(f"Exporting knowledge graph to {output_path}")

        # Export entities
        entities_file = output_path / "entities.json"
        with open(entities_file, 'w', encoding='utf-8') as f:
            json.dump(list(self.entities.values()), f, indent=2, ensure_ascii=False)

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
            f.write(f"Device: {self.device} (GPU: {GPU_AVAILABLE})\n")
            f.write(f"NLP Available: {NLP_AVAILABLE}\n\n")

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
    """Main function to run the scalable knowledge graph builder."""
    # Configuration
    INPUT_FILE = "E:/Users/brsth/.claude/history.jsonl"
    OUTPUT_DIR = "P:/projects/kg_builder/knowledge_graph_output"
    BATCH_SIZE = 128  # Adjust based on available memory

    logger.info("=" * 60)
    logger.info("SCALABLE GPU-ACCELERATED KNOWLEDGE GRAPH BUILDER")
    logger.info("=" * 60)
    logger.info(f"Input file: {INPUT_FILE}")
    logger.info(f"Output directory: {OUTPUT_DIR}")
    logger.info(f"Batch size: {BATCH_SIZE}")
    logger.info(f"GPU available: {GPU_AVAILABLE}")
    logger.info(f"NLP available: {NLP_AVAILABLE}")
    logger.info("=" * 60)

    # Initialize the graph builder
    graph_builder = GPUGraphBuilder(batch_size=BATCH_SIZE)

    try:
        # Build the knowledge graph
        start_time = time.time()

        # Process the entire dataset
        report = graph_builder.build_knowledge_graph(INPUT_FILE)

        # Export results
        export_files = graph_builder.export_knowledge_graph(OUTPUT_DIR)

        total_time = time.time() - start_time

        # Print final summary
        logger.info("=" * 60)
        logger.info("KNOWLEDGE GRAPH CONSTRUCTION COMPLETED")
        logger.info("=" * 60)
        logger.info(f"Total processing time: {total_time:.2f} seconds")
        logger.info(f"Conversations processed: {report['summary']['processed_conversations']:,}")
        logger.info(f"Unique entities extracted: {report['summary']['total_unique_entities']:,}")
        logger.info(f"Relationships identified: {report['summary']['total_relationships']:,}")
        logger.info(f"Entity types discovered: {report['summary']['total_entity_types']}")
        logger.info(f"Processing speed: {report['summary']['average_conversations_per_second']:.2f} conv/sec")

        if GPU_AVAILABLE and report['gpu_acceleration']['gpu_memory_used_gb'] > 0:
            logger.info(f"GPU memory used: {report['gpu_acceleration']['gpu_memory_used_gb']:.2f} GB")

        logger.info("\nExport files:")
        for file_type, file_path in export_files.items():
            logger.info(f"  - {file_type}: {file_path}")

        logger.info("=" * 60)
        logger.info("SUCCESS: Knowledge graph construction completed!")
        logger.info("=" * 60)

        return report

    except Exception as e:
        logger.error(f"Error during knowledge graph construction: {e}")
        raise

if __name__ == "__main__":
    main()
