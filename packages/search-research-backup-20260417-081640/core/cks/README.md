# Cks Module

**Path**: `src/features/cks/`
**Python Files**: 37
**Classes**: 140
**Functions**: 403

## Overview

This module contains 37 Python files with 140 classes and 403 functions.

## Components

### Classes

- `AdaptiveOptimizer`
- `AuthenticationException`
- `AuthorizationException`
- `BaseIntegrationClient`
- `CKSMigrator`
- `CKSValidator`
- `CSFNIPValidator`
- `CausalGraphOperations`
- `ChatHistoryClient`
- `ChatHistoryConfig`
- `ChatHistoryRequest`
- `ChatHistoryResult`
- `ChatMessage`
- `ComplianceLevel`
- `ComplianceReport`
- `ConfigurationException`
- `ConstitutionalException`
- `ConstitutionalMetric`
- `ConstitutionalValidator`
- `ContentSecurityLevel`
- `ContentType`
- `ContinuousLearner`
- `ConversationPattern`
- `CrossGraphRelationship`
- `DependencyException`
- `DeviceManager`
- `ErrorCategory`
- `ErrorContext`
- `ErrorSeverity`
- `EvidenceBasedLearning`
- `FaissMigrationHelper`
- `FaissToPyTorchAdapter`
- `GPUMemoryConfig`
- `GPUMemoryManager`
- `GPUMemoryStats`
- `GraphEdge`
- `GraphNode`
- `GraphType`
- `HDMAAnalysisRequest`
- `HDMAAnalysisResult`
- `HDMAConfig`
- `HDMAPattern`
- `HMAClient`
- `HealthCheck`
- `IntegrationClientFactory`
- `IntegrationConfig`
- `IntegrationException`
- `IntegrationFactory`
- `IntegrationResult`
- `IntegrationStatus`
- `IntegrationSystemConfig`
- `KnowledgeGraphOperations`
- `KnowledgeQualityScorer`
- `LSPRequestType`
- `Language`
- `LearningConfig`
- `LearningInsight`
- `LegacyEntry`
- `MessageRole`
- `MigrationConfig`
- `MockAsyncResponse`
- `MockLSPServer`
- `MultiGraphConfig`
- `MultiGraphEngine`
- `NetworkException`
- `PyTorchStorageConfig`
- `PyTorchVectorStorage`
- `QualityMetrics`
- `RateLimitException`
- `RelationshipType`
- `SecurityException`
- `SecurityLevel`
- `SecurityScanResult`
- `SerenaAnalysisRequest`
- `SerenaAnalysisResult`
- `SerenaClient`
- `SerenaConfig`
- `SerenaDiagnostic`
- `SerenaServerConfig`
- `SerenaSymbol`
- `SocialGraphOperations`
- `StorageConfig`
- `StorageManager`
- `SystemGraphOperations`
- `TestCKSConfig`
- `TestCKSIntegration`
- `TestCKSQueryInterface`
- `TestCLIInterface`
- `TestCausalGraphOperations`
- `TestConcurrentOperations`
- `TestContinuousLearnerIntegration`
- `TestConvenienceFunctions`
- `TestCrossGraphRelationship`
- `TestDataImportExport`
- `TestErrorHandling`
- `TestErrorHandlingAndEdgeCases`
- `TestFactoryErrorHandling`
- `TestFactoryPerformance`
- `TestGPUMemoryConfig`
- `TestGPUMemoryManager`
- `TestGraphNodeAndEdge`
- `TestHDMAErrorHandling`
- `TestHDMAPerformance`
- `TestHDMASecurity`
- `TestHMAClient`
- `TestIntegration`
- `TestIntegrationFactory`
- `TestIntegrationSystemConfig`
- `TestKnowledgeEntry`
- `TestKnowledgeGraphOperations`
- `TestKnowledgeManager`
- `TestMultiGraphEngineBasics`
- `TestPerformanceAndOptimization`
- `TestPerformanceAndScalability`
- `TestQueryRequest`
- `TestRealGPUIntegration`
- `TestSocialGraphOperations`
- `TestStorageConfig`
- `TestStorageManager`
- `TestSystemGraphOperations`
- `TestUsagePatternTracker`
- `TestVectorGraphOperations`
- `TimeoutException`
- `UsagePattern`
- `UsagePatternTracker`
- `ValidationException`
- `ValidationResult`
- `ValidationSeverity`
- `VectorGraphOperations`
- `WebContent`
- `WebContentClient`
- `WebContentConfig`
- `WebContentRequest`
- `WebContentResult`

### Functions

- `IndexFlatIP()`
- `IndexFlatL2()`
- `StandardGpuResources()`
- `add()`
- `add_result()`
- `allocate_gpu_array()`
- `assess_knowledge_quality()`
- `assess_quality()`
- `assess_quality_worker()`
- `basic_config()`
- `batch_create_embeddings()`
- `batch_create_knowledge_nodes()`
- `batch_store_vectors()`
- `calculate_causal_strength()`
- `calculate_influence()`
- `calculate_overall_score()`
- `calculate_storage_compliance_score()`
- `causal_ops()`
- `check_memory_availability()`
- `cleanup()`
- `cleanup_gpu_memory()`
- `clear_cache()`
- `continuous_learning_session()`
- `cpu_fallback_config()`
- `cpu_manager()`
- `create_authentication_error()`
- `create_causal_event()`
- `create_causal_node()`
- `create_causal_relationship()`
- `create_client()`
- `create_component()`
- `create_concept()`
- `create_constitutional_violation()`
- `create_continuous_learner()`
- `create_cross_graph_relationship()`
- `create_dependency()`
- `create_development()`
- `create_embedding()`
- `create_engine()`
- `create_entity()`
- `create_error()`
- `create_fact()`
- `create_faiss_index()`
- `create_from_environment()`
- `create_gpu_dataframe()`
- `create_knowledge_edge()`
- `create_knowledge_node()`
- `create_minimal()`
- `create_pytorch_vector_storage()`
- `create_rate_limit_error()`
- `create_relationship()`
- `create_rule()`
- `create_success()`
- `db_connection()`
- `delete_vector()`
- `dfs()`
- `engine()`
- `engine_config()`
- `event_loop()`
- `example_01_basic_setup()`
- `example_02_knowledge_graph()`
- `example_03_vector_operations()`
- `example_04_causal_analysis()`
- `example_05_social_network()`
- `example_06_system_orchestration()`
- `example_07_cross_graph_operations()`
- `example_08_performance_optimization()`
- `example_09_data_management()`
- `example_10_convenience_functions()`
- `example_1_basic_gpu_management()`
- `example_2_rapids_integration()`
- `example_3_faiss_gpu_operations()`
- `example_4_memory_monitoring_and_cleanup()`
- `example_5_integrated_storage_and_gpu()`
- `example_6_solo_developer_optimization()`
- `execute_with_fallback()`
- `export_data()`
- `factory()`
- `faiss_index()`
- `find_bottlenecks()`
- `find_causal_chains()`
- `find_communities()`
- `find_semantic_clusters()`
- `from_dict()`
- `generate_migration_script()`
- `generate_optimizations()`
- `get_active_clients()`
- `get_audit_trail()`
- `get_compliance_report()`
- `get_compliance_score()`
- `get_constitutional_compliance_score()`
- `get_cross_graph_insights()`
- `get_cross_graph_relationships()`
- `get_default_config()`
- `get_device()`
- `get_engine_metrics()`
- `get_execution_order()`
- `get_import()`
- `get_insights()`
- `get_knowledge_node()`
- `get_learning_history()`
- `get_low_quality_knowledge()`
- `get_memory_stats()`
- `get_memory_usage()`
- `get_optimization_history()`
- `get_pattern()`
- `get_patterns()`
- `get_patterns_by_component()`
- `get_performance_statistics()`
- `get_performance_stats()`
- `get_quality_metrics()`
- `get_relationship_path()`
- `get_stats()`
- `get_storage_stats()`
- `get_summary()`
- `get_system_status()`
- `get_top_patterns()`
- `get_top_quality_knowledge()`
- `get_vector()`
- `gpu_context()`
- `gpu_manager()`
- `hdma_client()`
- `import_data()`
- `import_export_engine()`
- `index_cpu_to_gpu()`
- `initialize()`
- `is_healthy()`
- `knowledge_manager()`
- `knowledge_ops()`
- `load()`
- `main()`
- `ntotal()`
- `optimize()`
- `optimize_performance()`
- `performance_engine()`
- `predict_effects()`
- `pytest_configure()`
- `query_across_graphs()`
- `query_concepts()`
- `query_interface()`
- `quick_semantic_search()`
- `real_config()`
- `reconstruct()`
- `replace_faiss_with_pytorch()`
- `reset()`
- `reset_statistics()`
- `sample_analysis_request()`
- `sample_config()`
- `sample_entries()`
- `sample_python_file()`
- `save()`
- `score_insight()`
- `search()`
- `search_similar()`
- `search_similar_vectors()`
- `semantic_reasoning()`
- `semantic_similarity()`
- `setUp()`
- `shutdown()`
- `social_ops()`
- `store_vector()`
- `system_ops()`
- `tearDown()`
- `temp_db_path()`
- `temp_dir()`
- `temp_python_file()`
- `temp_storage_manager()`
- `test_anomaly_detection()`
- `test_batch_create_embeddings_without_model()`
- `test_batch_operations()`
- `test_cache_management()`
- `test_calculate_causal_strength()`
- `test_calculate_influence()`
- `test_calculate_statistics()`
- `test_client_initialization()`
- `test_client_initialization_disabled()`
- `test_client_initialization_without_api_url()`
- `test_concurrent_operations()`
- `test_concurrent_tracking()`
- `test_config()`
- `test_config_post_processing()`
- `test_config_validation()`
- `test_config_validation_errors()`
- `test_configuration_integration()`
- `test_configuration_violations()`
- `test_constitutional_compliance()`
- `test_constitutional_compliance_score()`
- `test_constitutional_compliance_validation()`
- `test_create_causal_event()`
- `test_create_causal_relationship()`
- `test_create_component()`
- `test_create_concept()`
- `test_create_dependency()`
- `test_create_embedding_without_model()`
- `test_create_engine()`
- `test_create_engine_default_config()`
- `test_create_entity()`
- `test_create_fact()`
- `test_create_knowledge_relationship()`
- `test_create_relationship()`
- `test_create_rule()`
- `test_cross_graph_insights()`
- `test_cross_graph_relationship_creation()`
- `test_cross_graph_relationship_serialization()`
- `test_cross_graph_relationship_validation()`
- `test_cross_graph_relationships()`
- `test_custom_configuration()`
- `test_data_consistency_across_restarts()`
- `test_data_export()`
- `test_data_import()`
- `test_default_config()`
- `test_default_configuration()`
- `test_development_factory_creation()`
- `test_double_initialization()`
- `test_end_to_end_workflow()`
- `test_engine_context_manager()`
- `test_engine_initialization()`
- `test_engine_metrics()`
- `test_env_config()`
- `test_error_handling_and_recovery()`
- `test_error_rate_calculation()`
- `test_extract_patterns_from_response()`
- `test_factory_from_environment()`
- `test_factory_initialization()`
- `test_factory_initialization_with_config()`
- `test_faiss_index_creation()`
- `test_faiss_index_invalid_type()`
- `test_fallback_count_tracking()`
- `test_find_bottlenecks()`
- `test_find_causal_chains()`
- `test_find_communities()`
- `test_forced_memory_cleanup()`
- `test_generate_request_hash()`
- `test_get_execution_order()`
- `test_get_relationship_path()`
- `test_gpu_acceleration()`
- `test_gpu_array_allocation()`
- `test_gpu_array_allocation_large_memory()`
- `test_gpu_context_manager()`
- `test_gpu_dataframe_creation()`
- `test_gpu_fallback_handling()`
- `test_graceful_shutdown()`
- `test_graph_edge_creation()`
- `test_graph_edge_serialization()`
- `test_graph_edge_updates()`
- `test_graph_node_creation()`
- `test_graph_node_serialization()`
- `test_graph_node_update()`
- `test_hdma_configuration()`
- `test_initialization()`
- `test_initialization_with_invalid_config()`
- `test_invalid_config_cleanup_threshold_exceeds_limit()`
- `test_invalid_config_memory_limit_too_high()`
- `test_invalid_config_threshold_exceeds_limit()`
- `test_invalid_configuration()`
- `test_invalid_entry()`
- `test_knowledge_graph_operations()`
- `test_manager_context_manager()`
- `test_manager_initialization_cpu_fallback()`
- `test_manager_initialization_success()`
- `test_memory_and_resource_management()`
- `test_memory_availability_check()`
- `test_memory_cleanup()`
- `test_memory_leak_detection()`
- `test_memory_management()`
- `test_memory_stats_collection()`
- `test_metrics_tracking()`
- `test_minimal_factory_creation()`
- `test_multiple_operations_same_pattern()`
- `test_node_and_edge_validation()`
- `test_operation_history_limits()`
- `test_operation_without_initialization()`
- `test_optimization_cycle()`
- `test_pattern_evolution_tracking()`
- `test_pattern_id_generation()`
- `test_pattern_persistence()`
- `test_pattern_serialization()`
- `test_peak_hours_analysis()`
- `test_performance_optimization()`
- `test_performance_stats()`
- `test_predict_effects()`
- `test_quality_degradation_detection()`
- `test_query_across_graphs()`
- `test_quick_semantic_search()`
- `test_rapids_integration_status()`
- `test_real_gpu_operations()`
- `test_request_validation()`
- `test_resource_usage_calculation()`
- `test_search_similar_without_model()`
- `test_semantic_similarity()`
- `test_shutdown_without_initialization()`
- `test_single_operation_tracking()`
- `test_sqlite_persistence()`
- `test_storage_config_defaults()`
- `test_storage_config_paths()`
- `test_storage_config_validation()`
- `test_storage_manager_initialization()`
- `test_system_resilience()`
- `test_tag_validation()`
- `test_top_patterns_ranking()`
- `test_uninitialized_engine_operations()`
- `test_valid_config_creation()`
- `test_valid_entry()`
- `test_valid_request()`
- `test_validate_system_state()`
- `test_vector_operations()`
- `test_web_content_configuration()`
- `to_dict()`
- `track_operation()`
- `track_operations()`
- `track_usage()`
- `track_usage_worker()`
- `transaction()`
- `update_confidence()`
- `update_content()`
- `update_knowledge_node()`
- `update_strength()`
- `validate_config()`
- `validate_constitutional_compliance()`
- `validate_csf_compliance()`
- `validate_faiss_code()`
- `validate_learning_framework_compliance()`
- `validate_operation()`
- `validate_storage_config()`
- `validate_system_state()`
- `vector_ops()`

## Files

- [`__init__.py`](__init__.py)
- [`__init__.py`](__init__.py)
- [`faiss_pytorch_adapter.py`](faiss_pytorch_adapter.py)
- [`gpu_manager.py`](gpu_manager.py)
- [`multi_graph_engine.py`](multi_graph_engine.py)
- [`pytorch_vector_storage.py`](pytorch_vector_storage.py)
- [`storage_manager.py`](storage_manager.py)
- [`storage_manager_optimized.py`](storage_manager_optimized.py)
- [`storage_manager_original.py`](storage_manager_original.py)
- [`gpu_manager_examples.py`](gpu_manager_examples.py)
- [`multi_graph_engine_examples.py`](multi_graph_engine_examples.py)
- [`__init__.py`](__init__.py)
- [`chat_history_client.py`](chat_history_client.py)
- [`hdma_client.py`](hdma_client.py)
- [`serena_client.py`](serena_client.py)
- [`web_content_client.py`](web_content_client.py)
- [`integration_exceptions.py`](integration_exceptions.py)
- [`integration_interfaces.py`](integration_interfaces.py)
- [`__init__.py`](__init__.py)
- [`test_hdma_client.py`](test_hdma_client.py)
- [`test_integration_factory.py`](test_integration_factory.py)
- [`integration_factory.py`](integration_factory.py)
- [`__init__.py`](__init__.py)
- [`continuous_learner.py`](continuous_learner.py)
- [`__init__.py`](__init__.py)
- [`test_continuous_learner_integration.py`](test_continuous_learner_integration.py)
- [`test_usage_pattern_tracker.py`](test_usage_pattern_tracker.py)
- [`validation.py`](validation.py)
- [`migrate_to_2025.py`](migrate_to_2025.py)
- [`__init__.py`](__init__.py)
- [`test_cks_2025.py`](test_cks_2025.py)
- [`test_gpu_manager.py`](test_gpu_manager.py)
- [`test_multi_graph_engine.py`](test_multi_graph_engine.py)
- [`test_storage_manager.py`](test_storage_manager.py)
- [`__init__.py`](__init__.py)
- [`constitutional_validator.py`](constitutional_validator.py)
- [`validate_cks_2025.py`](validate_cks_2025.py)

*Documentation generated automatically on 2025-11-27 23:34:31*

---

# Unified CKS Interface (v2.0)

**Status:** Production Ready | **Database:** `data/cks.db`

## Quick Start

```python
from features.cks.unified import CKS

# Initialize (defaults to data/cks.db)
cks = CKS()

# Store memories and patterns
cks.ingest_memory("What is JWT?", "JWT is JSON Web Tokens...")
cks.ingest_pattern("Dual Sink Logging", "Route logs to both JSON and text...")

# Search
results = cks.search("logging")
stats = cks.get_statistics()

# Close or use context manager
with CKS() as cks:
    results = cks.search("authentication")
```

## API Reference

### `CKS(db_path=None)`
Initialize with optional database path (default: `data/cks.db`)

### Memory Operations
- `ingest_memory(question, answer, **metadata)` → Store conversation memory
- `search_memories(query, limit=5)` → Search memories

### Pattern Operations
- `ingest_pattern(title, content, entry_type="pattern", **metadata)` → Store patterns/knowledge/code
- `search_patterns(query, limit=5)` → Search patterns

### Universal Operations
- `search(query, entry_type=None, limit=5)` → Search all or filter by type
- `get_statistics()` → Get entry counts and database size

## Database Schema

```sql
CREATE TABLE entries (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,        -- 'memory', 'pattern', 'code', 'knowledge'
    title TEXT,
    content TEXT NOT NULL,
    metadata TEXT,              -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Migration from Legacy CKS

```python
from pathlib import Path
from features.cks.unified import migrate_from_legacy

source_dbs = [
    Path('src/data/cks.db'),
    Path('src/data/cks_hypergraph/cks_hypergraph.db'),
]

counts = migrate_from_legacy(source_dbs)
print(f"Migrated {counts['total']} entries")
```

## Consolidation Results

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Database files | 53 | 1 | -98% |
| Total size | ~9 MB | 0.86 MB | -90% |
| Active schemas | 3 | 1 | -67% |

**Migrated:** 368 entries (309 memories + 59 patterns/knowledge)
**Legacy:** Archived to `docs/archived/cks_legacy/`
**Backup:** `src/data_backup_20251222_184758/`

## Limitations

- LIKE-based search (adequate for <1000 entries)
- SQLite file-based (single-user)
- Vector search not implemented (future enhancement)

---

**Last Updated:** 2025-12-22
