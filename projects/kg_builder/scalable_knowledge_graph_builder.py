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

# NLP libraries
try:
    import spacy
    NLP_AVAILABLE = True
except ImportError:
    print("Warning: spaCy not available. Using basic entity extraction.")
    NLP_AVAILABLE = False

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
        self.nlp = None

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

        # Initialize spaCy model
        if NLP_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("spaCy model loaded: en_core_web_sm")
            except OSError:
                logger.warning("spaCy English model not found. Using basic entity extraction.")
                self.nlp = None

    def extract_entities_basic(self, text: str) -> list[dict[str, Any]]:
        """
        Basic entity extraction using regex patterns.
        Fallback method when spaCy is not available.
        """
        entities = []

        # File paths
        file_pattern = r'[\w\-\/\.]+\.(py|md|txt|json|yaml|yml|csv|tsv|log|sh|bat|ps1|js|ts|html|css|sql|xml|ini|cfg|conf|toml|lock|env|gitignore|dockerfile|requirements\.txt|package\.json|setup\.py|makefile|readme|license|changelog|manifest|setup\.cfg|pyproject\.toml|pytest\.ini|tox\.ini|mypy\.ini|flake8\.cfg|black\.py|isort\.cfg|pre-commit-config\.yaml|\.pre-commit-config\.yaml|\.gitignore|\.dockerignore|\.editorconfig|\.babelrc|\.eslintrc|\.prettierrc|tsconfig\.json|webpack\.config\.js|vite\.config\.js|rollup\.config\.js|gulpfile\.js|gruntfile\.js|rakefile|gemfile|composer\.json|package\.lock\.json|yarn\.lock|pipfile|pipfile\.lock|poetry\.lock|cargo\.toml|cargo\.lock|go\.mod|go\.sum|requirements\.dev\.txt|requirements\.test\.txt|requirements\.prod\.txt|requirements\.base\.txt|requirements\.local\.txt|requirements\.txt|setup\.cfg|setup\.py|pyproject\.toml|tox\.ini|pytest\.ini|conftest\.py|test_.*\.py|.*_test\.py|.*_spec\.py|spec_.*\.py|tests?/.*\.py)'

        # Commands and tools
        command_pattern = r'\/\w+(?:\s+\w+)*|git\s+\w+|npm\s+\w+|pip\s+\w+|python\s+\w+|pytest\s+\w+|docker\s+\w+|kubectl\s+\w+|aws\s+\w+|azure\s+\w+|gcloud\s+\w+|terraform\s+\w+|ansible\s+\w+|vagrant\s+\w+|make\s+\w+|cmake\s+\w+|gradle\s+\w+|mvn\s+\w+|yarn\s+\w+|bower\s+\w+|composer\s+\w+|bundle\s+\w+|gem\s+\w+|cargo\s+\w+|go\s+\w+|rustc\s+\w+|gcc\s+\w+|g\+\+\s+\w+|clang\s+\w+|javac\s+\w+|java\s+\w+|python\s+\w+|python3\s+\w+|pip3\s+\w+|node\s+\w+|npm\s+\w+|npx\s+\w+|yarn\s+\w+|pnpm\s+\w+|deno\s+\w+|bun\s+\w+'

        # URLs and domains
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+|www\.[^\s<>"{}|\\^`\[\]]+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s<>"{}|\\^`\[\]]*)?'

        # Technical terms and frameworks
        tech_pattern = r'\b(?:API|REST|GraphQL|SQL|NoSQL|MongoDB|PostgreSQL|MySQL|Redis|Elasticsearch|Kafka|RabbitMQ|Docker|Kubernetes|AWS|Azure|GCP|Terraform|Ansible|Jenkins|GitLab|GitHub|Bitbucket|Jira|Confluence|Slack|Discord|Teams|Zoom|Webex|TensorFlow|PyTorch|Keras|Scikit-learn|Pandas|NumPy|Matplotlib|Seaborn|Plotly|Dash|Streamlit|Flask|Django|FastAPI|Spring|React|Vue|Angular|Svelte|Next\.js|Nuxt\.js|Gatsby|Webpack|Vite|Rollup|Parcel|Babel|ESLint|Prettier|Jest|Mocha|Chai|Cypress|Selenium|Playwright|Puppeteer|Cypress|Postman|Swagger|OpenAPI|GraphQL|gRPC|Protocol Buffers|Thrift|Avro|JSON|YAML|XML|CSV|TSV|Markdown|LaTeX|HTML|CSS|SASS|SCSS|LESS|TypeScript|JavaScript|Python|Java|C\+\+|C#|Go|Rust|Ruby|PHP|Swift|Kotlin|Scala|Haskell|Erlang|Elixir|Clojure|F#|Objective-C|Dart|Lua|Perl|R|MATLAB|Julia|Bash|PowerShell|Zsh|Fish|CMD|BAT|Shell|Linux|Windows|macOS|Ubuntu|Debian|CentOS|RHEL|Alpine|Arch|Fedora|openSUSE|FreeBSD|NetBSD|OpenBSD|Darwin|iOS|Android|Windows|Linux|macOS)\b'

        # File extensions
        extension_pattern = r'\.\w{1,10}\b'

        # Extract entities
        for pattern, entity_type in [
            (file_pattern, 'FILE_PATH'),
            (command_pattern, 'COMMAND'),
            (url_pattern, 'URL'),
            (tech_pattern, 'TECHNOLOGY'),
            (extension_pattern, 'FILE_EXTENSION')
        ]:
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

        return entities

    def extract_entities_spacy(self, text: str) -> list[dict[str, Any]]:
        """
        Extract entities using spaCy NLP model.
        """
        if not self.nlp:
            return self.extract_entities_basic(text)

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
            'USES': ['uses', 'using', 'use', 'used', 'implemented with', 'built with'],
            'CONTAINS': ['contains', 'including', 'includes', 'has', 'with', 'features'],
            'RELATED_TO': ['related', 'associated', 'connected', 'linked', 'similar'],
            'LOCATED_IN': ['in', 'at', 'on', 'located', 'found', 'directory', 'path'],
            'REFERENCES': ['references', 'refers', 'mentions', 'cites', 'points to'],
            'DEPENDS_ON': ['depends', 'requires', 'needs', 'imports', 'extends'],
            'CREATES': ['creates', 'generates', 'produces', 'builds', 'makes'],
            'MODIFIES': ['modifies', 'updates', 'changes', 'edits', 'alters']
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
            ('ORG', 'PERSON'): 'EMPLOYS'
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
            entity_id = entity['text'].lower().replace(' ', '_')
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
                'spacy_loaded': self.nlp is not None
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
            f.write(f"Device: {self.device} (GPU: {GPU_AVAILABLE})\n\n")

            f.write("SUMMARY STATISTICS:\n")
            f.write("-" * 20 + "\n")
            for key, value in report['summary'].items():
                f.write(f"{key.replace('_', ' ').title()}: {value:,}\n")

            f.write("\nENTITY ANALYSIS:\n")
            f.write("-" * 20 + "\n")
            f.write(f"Total Unique Entities: {report['entity_analysis']['type_distribution']}\n")
            f.write("Top Entities:\n")
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
