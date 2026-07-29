---
source_id: "acb34fa9-eead-49a2-aa92-8a41e2e9eb9c"
title: "NVIDIA-NeMo-Guardrails-part-2.md"
notebook_id: 29bbaa7b-965f-40b5-a404-76b4d2e7308c
url: null
type: generated_text
exported: 2026-07-27
---

# NVIDIA-NeMo-Guardrails-part-2.md
NVIDIA/NeMo-Guardrails — continued — docs

Branch:

 

main

  |  

Source:

 https://github.com/NVIDIA/NeMo-Guardrails

File tree

file AGENTS.md

 

file AI_POLICY.md

 

file CHANGELOG-Colang.md

 

file CHANGELOG.md

 

file CLAUDE.md

 

file CONTRIBUTING.md

 

file Dockerfile

 

file LICENCES-3rd-party

 

file LICENSE-Apache-2.0.txt

 

file LICENSE.md

 

file Makefile

 

file README.md

 

file SECURITY.md

 

py build_notebook_docs.py

 

file cliff.toml

 

file greptile.json

 

file package-lock.json

 

file package.json

 

file pyproject.toml

 

file pytest.ini

 

file ruff.toml

 

file settings.ini

 

dir benchmark/

 

file Procfile

 

file README.md

 

dir benchmark/aiperf/

 

file README.md

 

py 

init

.py

 

py 

main

.py

 

py aiperf_models.py

 

py run_aiperf.py

 

dir benchmark/aiperf/configs/

 

file single_concurrency.yaml

 

file sweep_concurrency.yaml

 

file sweep_concurrency_benchmark.yaml

 

dir benchmark/embedding_backend/

 

file README.md

 

py bench_embedding_backend.py

 

dir benchmark/locust/

 

file README.md

 

py 

init

.py

 

py 

main

.py

 

py locust_models.py

 

py locustfile.py

 

py run_locust.py

 

dir benchmark/locust/configs/

 

file local.yaml

 

dir benchmark/mock_llm_server/

 

py 

init

.py

 

py api.py

 

py config.py

 

py models.py

 

py response_data.py

 

py run_server.py

 

dir benchmark/mock_llm_server/configs/

 

file meta-llama-3.3-70b-instruct.env

 

file nvidia-llama-3.1-nemoguard-8b-content-safety.env

 

dir benchmark/scripts/

 

file validate_mocks.sh

 

dir benchmark/tests/

 

file mock_model_config.yaml

 

py test_aiperf_models.py

 

py test_locust_models.py

 

py test_mock_api.py

 

py test_mock_config.py

 

py test_mock_models.py

 

py test_mock_response_data.py

 

py test_run_aiperf.py

 

py test_run_locust.py

 

py test_run_server.py

 

dir docs/

 

file AGENTS.md

 

file LIVE_DOCS.mdx

 

file README.mdx

 

file index.mdx

 

file index.yml

 

file telemetry.mdx

 

file troubleshooting.mdx

 

dir docs/_components/

 

file StarterPromptButton.tsx

 

dir docs/_static/css/

 

file custom.css

 

dir docs/_static/html/

 

file abc_bare_llm.report.html

 

file abc_with_full_guardrails.report.html

 

file abc_with_general_instructions.report.html

 

file abc_with_general_instructions_and_dialog_rails.report.html

 

dir docs/_static/js/

 

file table-expander.js

 

dir docs/_static/puml/

 

file core_colang_concepts_fig_1.puml

 

file core_colang_concepts_fig_2.puml

 

file dialog_rails_flow.puml

 

file input_rails_fig_1.puml

 

file input_rails_fig_2.puml

 

file master_rails_flow.puml

 

file output_rails_fig_1.puml

 

file programmable_guardrails.puml

 

file single_llm_call_flow.puml

 

dir docs/about/

 

file how-it-works.mdx

 

file overview.mdx

 

file rail-types.mdx

 

file release-notes.mdx

 

file supported-llms.mdx

 

dir docs/configure-rails/

 

file before-configuration.mdx

 

file configuration-reference.mdx

 

file exceptions.mdx

 

file index.mdx

 

file overview.mdx

 

dir docs/configure-rails/actions/

 

file action-parameters.mdx

 

file built-in-actions.mdx

 

file creating-actions.mdx

 

file index.mdx

 

file registering-actions.mdx

 

dir docs/configure-rails/caching/

 

file index.mdx

 

file kv-cache-reuse.mdx

 

file model-memory-cache.mdx

 

dir docs/configure-rails/colang/

 

file index.mdx

 

dir docs/configure-rails/colang/colang-1/

 

file bot-thinking-guardrails.mdx

 

file colang-language-syntax-guide.mdx

 

file index.mdx

 

dir docs/configure-rails/colang/colang-1/tutorials/

 

file index.mdx

 

dir docs/configure-rails/colang/colang-1/tutorials/1-hello-world/

 

file README.mdx

 

file hello-world.ipynb

 

dir docs/configure-rails/colang/colang-1/tutorials/2-core-colang-concepts/

 

file README.mdx

 

file core-colang-concepts.ipynb

 

dir docs/configure-rails/colang/colang-1/tutorials/3-demo-use-case/

 

file README.mdx

 

file demo-use-case.ipynb

 

dir docs/configure-rails/colang/colang-1/tutorials/4-input-rails/

 

file README.mdx

 

file input-rails.ipynb

 

dir docs/configure-rails/colang/colang-1/tutorials/5-output-rails/

 

file README.mdx

 

file output-rails.ipynb

 

dir docs/configure-rails/colang/colang-1/tutorials/6-topical-rails/

 

file README.mdx

 

file topical-rails.ipynb

 

dir docs/configure-rails/colang/colang-1/tutorials/7-rag/

 

file README.mdx

 

file rag.ipynb

 

dir docs/configure-rails/colang/colang-1/tutorials/8-tracing/

 

file 1_tracing_quickstart.ipynb

 

file 2_tracing_with_jaeger.ipynb

 

dir docs/configure-rails/colang/colang-2/

 

file VERSION.txt

 

file index.mdx

 

file migration-guide.mdx

 

file whats-changed.mdx

 

dir docs/configure-rails/colang/colang-2/examples/

 

py csl.py

 

py utils.py

 

dir docs/configure-rails/colang/colang-2/getting-started/

 

file dialog-rails.mdx

 

file hello-world.mdx

 

file index.mdx

 

file input-rails.mdx

 

file interaction-loop.mdx

 

file llm-flows.mdx

 

file multimodal-rails.mdx

 

file recommended-next-steps.mdx

 

dir docs/configure-rails/colang/colang-2/images/

 

file guardrails_events_stream.puml

 

dir docs/configure-rails/colang/colang-2/language-reference/

 

file defining-flows.mdx

 

file development-and-debugging.mdx

 

file event-generation-and-matching.mdx

 

file flow-control.mdx

 

file index.mdx

 

file introduction.mdx

 

file make-use-of-llms.mdx

 

file more-on-flows.mdx

 

file python-actions.mdx

 

file the-standard-library.mdx

 

file working-with-actions.mdx

 

file working-with-variables-and-expressions.mdx

 

dir docs/configure-rails/colang/colang-2/language-reference/csl/

 

file attention.mdx

 

file avatars.mdx

 

file core.mdx

 

file guardrails.mdx

 

file lmm.mdx

 

file timing.mdx

 

dir docs/configure-rails/colang/usage-examples/

 

file bot-message-instructions.mdx

 

file extract-user-provided-values.mdx

 

file index.mdx

 

dir docs/configure-rails/custom-initialization/

 

file custom-data.mdx

 

file custom-embedding-providers.mdx

 

file custom-llm-framework.mdx

 

file custom-llm-model.mdx

 

file custom-llm-providers.mdx

 

file index.mdx

 

file init-function.mdx

 

file testing-your-config.mdx

 

dir docs/configure-rails/guardrail-catalog/

 

file agentic-security.mdx

 

file content-safety.mdx

 

file fact-checking.mdx

 

file index.mdx

 

file jailbreak-protection.mdx

 

file pii-detection.mdx

 

file self-check.mdx

 

file third-party.mdx

 

file tool-calling.mdx

 

file topic-control.mdx

 

dir docs/configure-rails/guardrail-catalog/community/

 

file active-fence.mdx

 

file ai-defense.mdx

 

file alignscore.mdx

 

file auto-align.mdx

 

file clavata.mdx

 

file cleanlab.mdx

 

file crowdstrike-aidr.mdx

 

file fiddler.mdx

 

file gcp-text-moderations.mdx

 

file gliner.mdx

 

file guardrails-ai.mdx

 

file llama-guard.mdx

 

file pangea.mdx

 

file patronus-evaluate-api.mdx

 

file patronus-lynx.mdx

 

file policyai.mdx

 

file polygraf.mdx

 

file presidio.mdx

 

file privateai.mdx

 

file prompt-security.mdx

 

file regex.mdx

 

file trend-micro.mdx

 

dir docs/configure-rails/other-configurations/

 

file embedding-search-providers.mdx

 

file index.mdx

 

file knowledge-base.mdx

 

dir docs/configure-rails/yaml-schema/

 

file guardrails-configuration.mdx

 

file index.mdx

 

file model-configuration.mdx

 

file prompt-configuration.mdx

 

file tracing-configuration.mdx

 

dir docs/configure-rails/yaml-schema/streaming/

 

file global-streaming.mdx

 

file index.mdx

 

file output-rail-streaming.mdx

 

dir docs/deployment/

 

file index.mdx

 

file using-docker.mdx

 

file using-microservice.mdx

 

dir docs/evaluation/

 

file evaluate-configuration.mdx

 

file evaluate-guardrails.mdx

 

file evaluation-methodology.mdx

 

file llm-vulnerability-scanning.mdx

 

dir docs/getting-started/

 

file installation-guide.mdx

 

file integrate-into-application.mdx

 

file use-with-ai-agent.mdx

 

dir docs/getting-started/tutorials/

 

file index.mdx

 

file jailbreak-detection-heuristics.mdx

 

file multimodal.mdx

 

file nemoguard-jailbreakdetect-deployment.mdx

 

file nemoguard-topiccontrol-deployment.mdx

 

file nemotron-content-safety-reasoning-deployment.mdx

 

file nemotron-safety-guard-deployment.mdx

 

dir docs/integration/

 

file tools-integration.mdx

 

dir docs/integration/langchain/

 

file agent-middleware.mdx

 

file index.mdx

 

file langchain-integration.mdx

 

file langgraph-integration.mdx

 

file runnable-rails.mdx

 

dir docs/integration/langchain/chain-with-guardrails/

 

file chain-with-guardrails.ipynb

 

file index.mdx

 

dir docs/integration/langchain/runnable-as-action/

 

file index.mdx

 

file runnable-as-action.ipynb

 

dir docs/migration/

 

file 0.22.mdx

 

dir docs/observability/

 

file index.mdx

 

dir docs/observability/logging/

 

file detailed-logging.ipynb

 

file index.mdx

 

dir docs/observability/metrics/

 

file enable-metrics.mdx

 

file index.mdx

 

file opentelemetry-integration.mdx

 

file reference.mdx

 

dir docs/observability/tracing/

 

file adapter-configurations.mdx

 

file content-capture.mdx

 

file index.mdx

 

file opentelemetry-integration.mdx

 

file opentelemetry-logs.mdx

 

file quick-start.mdx

 

file span-reference.mdx

 

file troubleshooting.mdx

 

dir docs/reference/

 

file colang-architecture-guide.mdx

 

file engine-feature-support.mdx

 

file guardrails-sequence-diagrams.mdx

 

file use-case-diagrams.drawio

 

file use-case-diagrams.mdx

 

dir docs/reference/cli/

 

file index.mdx

 

dir docs/resources/

 

file research.mdx

 

dir docs/resources/security/

 

file guidelines.mdx

 

dir docs/run-rails/

 

file index.mdx

 

dir docs/run-rails/using-fastapi-server/

 

file actions-server.mdx

 

file chat-with-guardrailed-model.mdx

 

file index.mdx

 

file list-guardrail-configs.mdx

 

file list-models.mdx

 

file overview.mdx

 

file run-guardrails-server.mdx

 

dir docs/run-rails/using-python-apis/

 

file check-messages.mdx

 

file core-classes.mdx

 

file event-based-api.mdx

 

file generation-options.mdx

 

file index.mdx

 

file overview.mdx

 

file streaming.mdx

 

dir docs/scripts/

 

file convert-docs-to-fern.mjs

 

dir examples/

 

file sample_config.yml

 

dir examples/bots/

 

file README.md

 

dir examples/bots/abc/

 

file README.md

 

file config.yml

 

file prompts.yml

 

dir examples/bots/abc/kb/

 

file employee-handbook.md

 

dir examples/bots/abc/rails/

 

file disallowed.co

 

dir examples/bots/abc_v2/

 

file README.md

 

file config.yml

 

file main.co

 

file prompts.yml

 

file rails.co

 

dir examples/bots/abc_v2/kb/

 

file employee-handbook.md

 

dir examples/bots/abc_v2/rails/

 

file disallowed.co

 

dir examples/bots/hello_world/

 

file README.md

 

file config.yml

 

file rails.co

 

dir examples/configs/

 

file README.md

 

py 

init

.py

 

dir examples/configs/ai_defense/

 

file README.md

 

file config.yml

 

dir examples/configs/ai_defense_v2/

 

file README.md

 

file config.yaml

 

file main.co

 

file rails.co

 

dir examples/configs/autoalign/

 

file README.md

 

dir examples/configs/autoalign/autoalign_config/

 

file config.yml

 

dir examples/configs/autoalign/autoalign_factcheck_config/

 

file config.yml

 

dir examples/configs/autoalign/autoalign_groundness_config/

 

file config.yml

 

dir examples/configs/autoalign/autoalign_groundness_config/kb/

 

file kb.md

 

dir examples/configs/autoalign/autoalign_groundness_config/rails/

 

file factcheck.co

 

file general.co

 

dir examples/configs/clavata/

 

file README.md

 

file config.yml

 

dir examples/configs/clavata_v2/

 

file README.md

 

file config.yml

 

file main.co

 

file rails.co

 

dir examples/configs/content_safety/

 

file README.md

 

file config.yml

 

file prompts.yml

 

dir examples/configs/content_safety_api_keys/

 

file README.md

 

file config.yml

 

file prompts.yml

 

dir examples/configs/content_safety_local/

 

file config.yml

 

file prompts.yml

 

dir examples/configs/content_safety_multilingual/

 

file config.yml

 

file prompts.yml

 

dir examples/configs/content_safety_reasoning/

 

file config.yml

 

py demo.py

 

file prompts.yml

 

dir examples/configs/content_safety_vision/

 

file config.yml

 

py demo.py

 

file prompts.yml

 

dir examples/configs/crowdstrike_aidr/

 

file README.md

 

file config.yml

 

dir examples/configs/crowdstrike_aidr_v2/

 

file README.md

 

file config.yml

 

file main.co

 

file rails.co

 

dir examples/configs/gliner/

 

file README.md

 

dir examples/configs/gliner/pii_detection/

 

file config.yml

 

dir examples/configs/gliner/pii_masking/

 

file config.yml

 

dir examples/configs/gs_content_safety/

 

file demo-out.txt

 

py demo.py

 

dir examples/configs/gs_content_safety/config/

 

file config.yml

 

file prompts.yml

 

dir examples/configs/guardrails_ai/

 

file README.md

 

file config.yml

 

dir examples/configs/guardrails_only/

 

file README.md

 

py demo.py

 

dir examples/configs/guardrails_only/input/

 

file config.co

 

file config.yml

 

dir examples/configs/guardrails_only/output/

 

file config.co

 

file config.yml

 

dir examples/configs/injection_detection/

 

file demo-out.txt

 

py demo.py

 

dir examples/configs/injection_detection/config/

 

file config.yml

 

dir examples/configs/jailbreak_detection/

 

file README.md

 

file config.yml

 

file flows.co

 

dir examples/configs/jailbreak_detection_nim/

 

file README.md

 

file config.yml

 

dir examples/configs/llama_guard/

 

file README.md

 

file config.yml

 

file prompts.yml

 

dir examples/configs/llm/

 

file README.md

 

py 

init

.py

 

dir examples/configs/llm/deepseek-r1/

 

file README.md

 

file config.yml

 

dir examples/configs/llm/hf_endpoint/

 

file README.md

 

file config.yml

 

file rails.co

 

dir examples/configs/llm/hf_pipeline_dolly/

 

file README.md

 

py config.py

 

file config.yml

 

file rails.co

 

dir examples/configs/llm/hf_pipeline_falcon/

 

file README.md

 

py 

init

.py

 

py config.py

 

file config.yml

 

file rails.co

 

dir examples/configs/llm/hf_pipeline_llama2/

 

file README.md

 

py 

init

.py

 

py config.py

 

file config.yml

 

dir examples/configs/llm/hf_pipeline_llama2/kb/

 

file report.md

 

dir examples/configs/llm/hf_pipeline_llama2/rails/

 

file factcheck.co

 

file general.co

 

dir examples/configs/llm/hf_pipeline_mosaic/

 

file README.md

 

py config.py

 

file config.yml

 

file rails.co

 

dir examples/configs/llm/hf_pipeline_vicuna/

 

file README.md

 

py config.py

 

file config.yml

 

file rails.co

 

dir examples/configs/llm/llama-3/

 

file config.yml

 

dir examples/configs/llm/nim/

 

file config.yml

 

dir examples/configs/llm/openai-responses-api/

 

file README.md

 

file config.yml

 

dir examples/configs/llm/vertexai/

 

file README.md

 

file config.yml

 

file prompts.yml

 

file rails.co

 

dir examples/configs/nemoguards/

 

file README.md

 

file config.yml

 

file prompts.yaml

 

dir examples/configs/nemoguards_cache/

 

file README.md

 

file config.yml

 

file prompts.yaml

 

dir examples/configs/nemoguards_v2/

 

file README.md

 

file config.yml

 

file main.co

 

file prompts.yml

 

file rails.co

 

dir examples/configs/nemotron/

 

file README.md

 

file config.yml

 

dir examples/configs/pangea/

 

file README.md

 

file config.yml

 

dir examples/configs/pangea_v2/

 

file README.md

 

file config.yml

 

file main.co

 

file rails.co

 

dir examples/configs/pangea_v2_no_llm/

 

file config.yml

 

file main.co

 

file rails.co

 

dir examples/configs/patronusai/

 

file README.md

 

file evaluate_api_config.yml

 

file lynx_config.yml

 

file prompts.yml

 

dir examples/configs/polygraf/pii_detection/

 

file config.yml

 

dir examples/configs/polygraf/pii_masking/

 

file config.yml

 

dir examples/configs/privateai/

 

file README.md

 

dir examples/configs/privateai/pii_detection/

 

file config.yml

 

dir examples/configs/privateai/pii_masking/

 

file config.yml

 

dir examples/configs/prompt_security/

 

file README.md

 

file config.yml

 

dir examples/configs/rag/

 

file README.md

 

py 

init

.py

 

dir examples/configs/rag/custom_rag_output_rails/

 

file README.md

 

py config.py

 

file config.yml

 

dir examples/configs/rag/custom_rag_output_rails/kb/

 

file report.md

 

dir examples/configs/rag/custom_rag_output_rails/rails/

 

file output.co

 

dir examples/configs/rag/fact_checking/

 

file README.md

 

file config.yml

 

dir examples/configs/rag/fact_checking/kb/

 

file report.md

 

dir examples/configs/rag/fact_checking/rails/

 

file factcheck.co

 

file general.co

 

dir examples/configs/rag/pinecone/

 

file README.md

 

py 

init

.py

 

py config.py

 

file config.yml

 

file rails.co

 

dir examples/configs/rag/pinecone/kb/

 

file data-00000-of-00001.arrow

 

file dataset_info.json

 

file nvidia.pdf

 

file state.json

 

dir examples/configs/sample/

 

file config.co

 

file config.yml

 

dir examples/configs/self_check_thinking/

 

file config.yml

 

file prompts.yml

 

dir examples/configs/sensitive_data_detection_v2/

 

file README.md

 

file config.yml

 

file flows.co

 

file main.co

 

dir examples/configs/streaming/

 

file README.md

 

file config.co

 

file config.yml

 

dir examples/configs/threads/

 

file README.md

 

py config.py

 

dir examples/configs/threads/config_1/

 

file config.yml

 

file rails.co

 

dir examples/configs/topic_safety/

 

file README.md

 

file config.yml

 

file prompts.yml

 

dir examples/configs/tracing/

 

file README.md

 

file config.yml

 

py working_example.py

 

dir examples/configs/trend_micro/

 

file README.md

 

file config.yml

 

dir examples/configs/trend_micro_v2/

 

file README.md

 

file config.yaml

 

file main.co

 

file rails.co

 

dir examples/deployment/gliner_server/

 

file README.md

 

file pyproject.toml

 

file test_integration.sh

 

dir examples/deployment/gliner_server/src/gliner_server/

 

py 

init

.py

 

py models.py

 

py pii_utils.py

 

py server.py

 

dir examples/deployment/gliner_server/tests/

 

py 

init

.py

 

py test_pii_utils.py

 

dir examples/eval/sample_abc/config/

 

file interactions.yml

 

file latencies.yml

 

file llm-judge.yml

 

file policies.yml

 

dir examples/notebooks/

 

file clavataai_detection.ipynb

 

file combined_guardrails_nim.ipynb

 

file content_safety_nim.ipynb

 

file generate_events_and_streaming.ipynb

 

file gliner_pii_detection_nim.ipynb

 

file privateai_pii_detection.ipynb

 

file topic_control_nim.ipynb

 

dir examples/notebooks/data/

 

py build_content_safety_subset.py

 

py build_pii_detection_subset.py

 

py build_topic_control_subset.py

 

file content_safety_subset.csv

 

file pii_detection_subset.csv

 

file topic_control_subset.csv

 

dir examples/scripts/

 

py 

init

.py

 

py demo_llama_index_guardrails.py

 

py demo_streaming.py

 

dir examples/scripts/langchain/

 

py experiments.py

 

dir examples/server_configs/atomic/input_checking/

 

file config.yml

 

dir examples/server_configs/atomic/main/

 

file config.yml

 

dir examples/server_configs/atomic/output_checking/

 

file config.yml

 

dir examples/v2_x/language_reference/actions/action_events/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/actions/action_grouping/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/actions/await_keyword/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/actions/dialog_pattern/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/actions/omit_wait_keyword/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/actions/start_keyword/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/actions/stop_action/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/actions/wait_for_first_action_only/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/control_flow_tools/catch_failing_flow/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/control_flow_tools/catch_failing_flow copy/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/control_flow_tools/concurrent_patterns/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/control_flow_tools/conditional_branching/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/control_flow_tools/event_branching/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/control_flow_tools/loop/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/development_and_debugging/flows_info/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/development_and_debugging/print_statement/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/events/dictionary_parameters/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/events/event_grouping/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/events/event_grouping_advanced/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/events/event_groups/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/events/event_matching/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/events/integer_parameter_match/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/events/list_parameters/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/events/match_event_reference/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/events/regular_expression_parameters/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/events/send_event_reference/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/events/set_parameters/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/flows/action_conflict_resolution/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/flows/call_a_flow/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/flows/concurrent_flows_basics/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/flows/concurrent_flows_basics_wrapper/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/flows/flow_hierarchy/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/flows/flow_parameters/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/flows/flows_failing/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/flows/parallel_flows/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/flows/start_flow/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/flows/undefined_flow/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/internal_events/undefined_flow/hello_world/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/introduction/hello_world/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/introduction/hello_world_umim/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/introduction/interaction_sequence/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/more_on_flows/activate_flow/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/more_on_flows/interaction_loops/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/more_on_flows/non-repeating-flows/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/more_on_flows/restart_flow_instance/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/more_on_flows/start_new_flow_instance/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/use_llms/bot_intent_generation_example/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/use_llms/interaction_loop/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/use_llms/nld_example/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/use_llms/user_intent_match_example/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/variables/assignment/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/variables/flow_attributes/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/variables/global_variables/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/variables/references/

 

file config.yml

 

file main.co

 

dir examples/v2_x/language_reference/variables/string_expression_evaluation/

 

file config.yml

 

file main.co

 

dir examples/v2_x/other/llm_flow/

 

file README.md

 

file config.yml

 

file rails.co

 

dir examples/v2_x/tutorial/guardrails_1/

 

file README.md

 

file config.yml

 

file rails.co

 

dir examples/v2_x/tutorial/hello_world_1/

 

file README.md

 

file config.yml

 

file rails.co

 

dir examples/v2_x/tutorial/hello_world_2/

 

file README.md

 

file config.yml

 

file rails.co

 

dir examples/v2_x/tutorial/hello_world_3/

 

file README.md

 

file config.yml

 

file rails.co

 

dir examples/v2_x/tutorial/interaction_loop/

 

file README.md

 

file config.yml

 

file main.co

 

dir examples/v2_x/tutorial/llm_flows/

 

file config.yml

 

file rails.co

 

dir examples/v2_x/tutorial/multi_modal/

 

file README.md

 

file config.yml

 

file main.co

 

dir fern/

 

file docs.yml

 

file fern.config.json

 

file generators.yml

 

file main.css

 

file openapi.yml

 

dir fern/assets/

 

file NVIDIA_symbol.svg

 

dir nemoguardrails/

 

file AGENTS.md

 

file CLAUDE.md

 

py 

init

.py

 

py 

main

.py

 

py base_guardrails.py

 

py context.py

 

py exceptions.py

 

py imports.py

 

py patch_asyncio.py

 

py registry.py

 

py singleton.py

 

py streaming.py

 

py telemetry.py

 

py types.py

 

py utils.py

 

dir nemoguardrails/_compat/

 

py 

init

.py

 

py langchain_kwargs.py

 

dir nemoguardrails/actions/

 

py 

init

.py

 

py action_dispatcher.py

 

py actions.py

 

py core.py

 

py math.py

 

py output_mapping.py

 

py retrieve_relevant_chunks.py

 

dir nemoguardrails/actions/llm/

 

py 

init

.py

 

py generation.py

 

py utils.py

 

dir nemoguardrails/actions/v2_x/

 

file README.md

 

py 

init

.py

 

py generation.py

 

dir nemoguardrails/actions/validation/

 

py 

init

.py

 

py base.py

 

py filter_secrets.py

 

dir nemoguardrails/actions_server/

 

py 

init

.py

 

py actions_server.py

 

dir nemoguardrails/cli/

 

py 

init

.py

 

py chat.py

 

py debugger.py

 

py migration.py

 

py providers.py

 

dir nemoguardrails/colang/

 

py 

init

.py

 

py runtime.py

 

dir nemoguardrails/colang/v1_0/

 

py 

init

.py

 

dir nemoguardrails/colang/v1_0/lang/

 

file README.md

 

py 

init

.py

 

py colang_parser.py

 

py comd_parser.py

 

py coyml_parser.py

 

py parser.py

 

py utils.py

 

dir nemoguardrails/colang/v1_0/runtime/

 

file README.md

 

py 

init

.py

 

py eval.py

 

py flows.py

 

py runtime.py

 

py sliding.py

 

py utils.py

 

dir nemoguardrails/colang/v2_x/

 

py 

init

.py

 

dir nemoguardrails/colang/v2_x/lang/

 

file README.md

 

py 

init

.py

 

py colang_ast.py

 

py expansion.py

 

py parser.py

 

py transformer.py

 

py utils.py

 

dir nemoguardrails/colang/v2_x/lang/grammar/

 

py 

init

.py

 

file colang.lark

 

py load.py

 

dir nemoguardrails/colang/v2_x/library/

 

file attention.co

 

file avatars.co

 

file core.co

 

file guardrails.co

 

file llm.co

 

file passthrough.co

 

file timing.co

 

dir nemoguardrails/colang/v2_x/runtime/

 

file README.md

 

py 

init

.py

 

py errors.py

 

py eval.py

 

py flows.py

 

py runtime.py

 

py serialization.py

 

py statemachine.py

 

py system_functions.py

 

py utils.py

 

dir nemoguardrails/embeddings/

 

py 

init

.py

 

py basic.py

 

py cache.py

 

py index.py

 

dir nemoguardrails/embeddings/providers/

 

py 

init

.py

 

py azureopenai.py

 

py base.py

 

py cohere.py

 

py fastembed.py

 

py google.py

 

py nim.py

 

py openai.py

 

py registry.py

 

py sentence_transformers.py

 

dir nemoguardrails/eval/

 

py 

init

.py

 

py check.py

 

py cli.py

 

py eval.py

 

py models.py

 

py utils.py

 

dir nemoguardrails/eval/ui/

 

file README.md

 

py README.py

 

py 

init

.py

 

py chart_utils.py

 

py common.py

 

py streamlit_utils.py

 

py utils.py

 

dir nemoguardrails/eval/ui/pages/

 

py 0_Config.py

 

py 1_Review.py

 

py 2_Summary - Short.py

 

py 3_Summary - Detailed.py

 

dir nemoguardrails/evaluate/

 

file README.md

 

py 

init

.py

 

py evaluate_factcheck.py

 

py evaluate_hallucination.py

 

py evaluate_moderation.py

 

py evaluate_topical.py

 

py utils.py

 

dir nemoguardrails/evaluate/cli/

 

py 

init

.py

 

py evaluate.py

 

py simplify_formatter.py

 

dir nemoguardrails/evaluate/data/factchecking/

 

file README.md

 

py 

init

.py

 

py process_msmarco_data.py

 

file sample.json

 

dir nemoguardrails/evaluate/data/hallucination/

 

py 

init

.py

 

file sample.txt

 

dir nemoguardrails/evaluate/data/moderation/

 

file README.md

 

py 

init

.py

 

file harmful.txt

 

file helpful.txt

 

py process_anthropic_dataset.py

 

dir nemoguardrails/evaluate/data/topical/

 

file README.md

 

py 

init

.py

 

py create_colang_intent_file.py

 

py dataset_tools.py

 

dir nemoguardrails/evaluate/data/topical/banking/

 

file categories_canonical_forms.json

 

file config.yml

 

file flows.co

 

dir nemoguardrails/evaluate/data/topical/chitchat/

 

file bot.co

 

file config.yml

 

file flows.co

 

file intent_canonical_forms.json

 

file user-other.co

 

dir nemoguardrails/guardrails/

 

py 

init

.py

 

py _http.py

 

py api_engine.py

 

py async_work_queue.py

 

py base_engine.py

 

py engine_registry.py

 

py guardrails.py

 

py guardrails_types.py

 

py iorails.py

 

py model_engine.py

 

py rail_action.py

 

py rails_manager.py

 

py telemetry.py

 

py tool_rail_action.py

 

py tool_schema.py

 

dir nemoguardrails/guardrails/actions/

 

py content_safety_action.py

 

py jailbreak_detection_action.py

 

py tool_call_action.py

 

py tool_result_action.py

 

py topic_safety_action.py

 

dir nemoguardrails/integrations/

 

py 

init

.py

 

dir nemoguardrails/integrations/langchain/

 

py 

init

.py

 

py exceptions.py

 

py helpers.py

 

py langchain_initializer.py

 

py llm_adapter.py

 

py message_utils.py

 

py middleware.py

 

py runnable_rails.py

 

py utils.py

 

dir nemoguardrails/integrations/langchain/actions/

 

py 

init

.py

 

py actions.py

 

py safetools.py

 

dir nemoguardrails/integrations/langchain/providers/

 

py 

init

.py

 

py providers.py

 

dir nemoguardrails/integrations/langchain/providers/huggingface/

 

py 

init

.py

 

py pipeline.py

 

py streamers.py

 

dir nemoguardrails/integrations/langchain/providers/trtllm/

 

py 

init

.py

 

py client.py

 

py llm.py

 

dir nemoguardrails/kb/

 

py 

init

.py

 

py kb.py

 

py utils.py

 

dir nemoguardrails/library/

 

file README.md

 

py 

init

.py

 

dir nemoguardrails/library/activefence/

 

py 

init

.py

 

py actions.py

 

file flows.co

 

file flows.v1.co

 

dir nemoguardrails/library/ai_defense/

 

py 

init

.py

 

py actions.py

 

file flows.co

 

file flows.v1.co

 

dir nemoguardrails/library/attention/

 

py actions.py

 

dir nemoguardrails/library/autoalign/

 

py 

init

.py

 

py actions.py

 

file flows.co

 

file flows.v1.co

 

dir nemoguardrails/library/clavata/

 

py 

init

.py

 

py actions.py

 

py errs.py

 

file flows.co

 

file flows.v1.co

 

py request.py

 

py utils.py

 

dir nemoguardrails/library/cleanlab/

 

file README.md

 

py 

init

.py

 

py actions.py

 

file flows.co

 

file flows.v1.co

 

dir nemoguardrails/library/content_safety/

 

py 

init

.py

 

py actions.py

 

file flows.co

 

file flows.v1.co

 

dir nemoguardrails/library/context_bloat_detection/

 

file README.md

 

py 

init

.py

 

py actions.py

 

file flows.co

 

file flows.v1.co

 

dir nemoguardrails/library/crowdstrike_aidr/

 

py 

init

.py

 

py actions.py

 

file flows.co

 

file flows.v1.co

 

dir nemoguardrails/library/factchecking/

 

py 

init

.py

 

dir nemoguardrails/library/factchecking/align_score/

 

file Dockerfile

 

py 

init

.py

 

py actions.py

 

file constraints.txt

 

file flows.co

 

file flows.v1.co

 

py request.py

 

file requirements.txt

 

py server.py

 

dir nemoguardrails/library/fiddler/

 

py 

init

.py

 

py actions.py

 

file flows.co

 

file flows.v1.co

 

dir nemoguardrails/library/gcp_moderate_text/

 

py 

init

.py

 

py actions.py

 

file flows.co

 

dir nemoguardrails/library/gliner/

 

py 

init

.py

 

py actions.py

 

file flows.co

 

file flows.v1.co

 

py models.py

 

py request.py

 

dir nemoguardrails/library/guardrails_ai/

 

py 

init

.py

 

py actions.py

 

py errors.py

 

file flows.co

 

file flows.v1.co

 

py registry.py

 

dir nemoguardrails/library/hallucination/

 

py 

init

.py

 

py actions.py

 

file flows.co

 

file flows.v1.co

 

dir nemoguardrails/library/hf_classifier/

 

py 

init

.py

 

py actions.py

 

py backends.py

 

file flows.co

 

file flows.v1.co

 

dir nemoguardrails/library/injection_detection/

 

py 

init

.py

 

py actions.py

 

file flows.co

 

file flows.v1.co

 

py yara_config.py

 

dir nemoguardrails/library/injection_detection/yara_rules/

 

file code.yara

 

file sqli.yara

 

file template.yara

 

file xss.yara

 

dir nemoguardrails/library/jailbreak_detection/

 

file Dockerfile

 

file Dockerfile-GPU

 

py 

init

.py

 

py actions.py

 

file flows.co

 

file flows.v1.co

 

py request.py

 

file requirements.txt

 

py server.py

 

dir nemoguardrails/library/jailbreak_detection/heuristics/

 

py 

init

.py

 

py checks.py

 

dir nemoguardrails/library/jailbreak_detection/model_based/

 

py 

init

.py

 

py checks.py

 

py models.py

 

dir nemoguardrails/library/llama_guard/

 

file README.md

 

py 

init

.py

 

py actions.py

 

file flows.co

 

file flows.v1.co

 

dir nemoguardrails/library/pangea/

 

py 

init

.py

 

py actions.py

 

file flows.co

 

file flows.v1.co

 

dir nemoguardrails/library/patronusai/

 

py 

init

.py

 

py actions.py

 

file flows.co

 

file flows.v1.co

 

dir nemoguardrails/library/policyai/

 

py 

init

.py

 

py actions.py

 

file flows.co

 

file flows.v1.co

 

dir nemoguardrails/library/polygraf/

 

py 

init

.py

 

py actions.py

 

file flows.co

 

file flows.v1.co

 

py request.py

 

dir nemoguardrails/library/privateai/

 

py 

init

.py

 

py actions.py

 

file flows.co

 

file flows.v1.co

 

py request.py

 

dir nemoguardrails/library/prompt_security/

 

py 

init

.py

 

py actions.py

 

file flows.co

 

file flows.v1.co

 

dir nemoguardrails/library/regex/

 

py 

init

.py

 

py actions.py

 

file flows.co

 

file flows.v1.co

 

dir nemoguardrails/library/self_check/

 

py 

init

.py

 

dir nemoguardrails/library/self_check/facts/

 

py 

init

.py

 

py actions.py

 

file flows.co

 

file flows.v1.co

 

dir nemoguardrails/library/self_check/input_check/

 

py 

init

.py

 

py actions.py

 

file flows.co

 

file flows.v1.co

 

dir nemoguardrails/library/self_check/output_check/

 

py 

init

.py

 

py actions.py

 

file flows.co

 

file flows.v1.co

 

dir nemoguardrails/library/sensitive_data_detection/

 

py 

init

.py

 

py actions.py

 

file flows.co

 

file flows.v1.co

 

dir nemoguardrails/library/topic_safety/

 

py 

init

.py

 

py actions.py

 

file flows.co

 

file flows.v1.co

 

dir nemoguardrails/library/trend_micro/

 

py 

init

.py

 

py actions.py

 

file flows.co

 

file flows.v1.co

 

dir nemoguardrails/library/utils/

 

py actions.py

 

dir nemoguardrails/llm/

 

py 

init

.py

 

py constants.py

 

py filters.py

 

py helpers.py

 

py openai_reasoning.py

 

py output_parsers.py

 

py prompts.py

 

py taskmanager.py

 

py types.py

 

dir nemoguardrails/llm/cache/

 

py 

init

.py

 

py interface.py

 

py lfu.py

 

py utils.py

 

dir nemoguardrails/llm/clients/

 

py 

init

.py

 

py _errors.py

 

py _sse.py

 

py base.py

 

py constants.py

 

py openai_compatible.py

 

dir nemoguardrails/llm/frameworks/

 

py 

init

.py

 

py default.py

 

py registry.py

 

dir nemoguardrails/llm/models/

 

py initializer.py

 

py openai_chat.py

 

dir nemoguardrails/llm/prompts/

 

file cohere.yml

 

file deepseek.yml

 

file dolly.yml

 

file general.yml

 

file llama3.yml

 

file mosaic.yml

 

file nemotron_reasoning.yml

 

file openai-chatgpt.yml

 

file openai.yml

 

file unknown.yml

 

dir nemoguardrails/llm/providers/

 

py 

init

.py

 

dir nemoguardrails/llm/providers/huggingface/

 

py 

init

.py

 

dir nemoguardrails/llm/providers/trtllm/

 

py 

init

.py

 

dir nemoguardrails/logging/

 

py 

init

.py

 

py explain.py

 

py llm_tracker.py

 

py processing_log.py

 

py simplify_formatter.py

 

py stats.py

 

py verbose.py

 

dir nemoguardrails/rails/

 

py 

init

.py

 

dir nemoguardrails/rails/llm/

 

py 

init

.py

 

py buffer.py

 

py config.py

 

file default_config.yml

 

file default_config_v2.yml

 

file llm_flows.co

 

py llmrails.py

 

py options.py

 

py utils.py

 

dir nemoguardrails/server/

 

py 

init

.py

 

py api.py

 

py app.py

 

dir nemoguardrails/server/datastore/

 

py 

init

.py

 

py datastore.py

 

py memory_store.py

 

py redis_store.py

 

dir nemoguardrails/server/schemas/

 

py openai.py

 

py utils.py

 

dir nemoguardrails/testing/

 

py 

init

.py

 

py chat_harness.py

 

py fake_model.py

 

py fixtures.py

 

dir nemoguardrails/tracing/

 

py 

init

.py

 

py constants.py

 

py interaction_types.py

 

py span_extractors.py

 

py span_format.py

 

py span_formatting.py

 

py spans.py

 

py tracer.py

 

dir nemoguardrails/tracing/adapters/

 

py 

init

.py

 

py base.py

 

py filesystem.py

 

py opentelemetry.py

 

py registry.py

 

dir qa/

 

file Dockerfile.qa

 

file README.md

 

py 

init

.py

 

py chatter.py

 

py latency_report.py

 

file latency_report_detailed_openai.tsv

 

file latency_report_openai.tsv

 

py logger.py

 

py test_execution_rails.py

 

py test_grounding_rail.py

 

py test_jailbreak_check.py

 

py test_moderation_rail.py

 

py test_topical_rail.py

 

py utils.py

 

py validator.py

 

dir qa/bots/latency_0_baseline/

 

file config.yml

 

dir qa/bots/latency_1_normal/

 

file README.md

 

file config.yml

 

file general.co

 

file report.co

 

dir qa/bots/latency_1_normal/kb/

 

file report.md

 

dir qa/bots/latency_2_single_call/

 

file README.md

 

file config.yml

 

file general.co

 

file report.co

 

dir qa/bots/latency_2_single_call/kb/

 

file report.md

 

dir qa/bots/latency_3_embeddings_only/

 

file README.md

 

file config.yml

 

file general.co

 

file report.co

 

dir qa/bots/latency_3_embeddings_only/kb/

 

file report.md

 

dir qa/bots/latency_4_compact/

 

file README.md

 

file config.yml

 

file general.co

 

file report.co

 

dir qa/bots/latency_4_compact/kb/

 

file report.md

 

dir qa/bots/latency_5_fact_checking_ask_llm/

 

file README.md

 

file config.yml

 

file general.co

 

file report.co

 

dir qa/bots/latency_5_fact_checking_ask_llm/kb/

 

file report.md

 

dir qa/bots/latency_6_fact_checking_align_score/

 

file README.md

 

file config.yml

 

file general.co

 

file report.co

 

dir qa/bots/latency_6_fact_checking_align_score/kb/

 

file report.md

 

dir schemas/

 

file anonymous_events.snapshot.json

 

dir scripts/

 

py 

init

.py

 

py extract_telemetry_snapshot.py

 

file fix-empty-fern-links.mjs

 

py kibana_verify_export.py

 

file normalize-fern-sdk-reference.mjs

 

file telemetry-smoke.md

 

py telemetry_smoke.py

 

file watch-fern-preview.mjs

 

dir tests/

 

py 

init

.py

 

py conftest.py

 

py input_tool_rails_actions.py

 

py test_action_dispatcher.py

 

py test_action_error.py

 

py test_action_params_types.py

 

py test_actions.py

 

py test_actions_core.py

 

py test_actions_llm_embedding_lazy_init.py

 

py test_actions_llm_utils_multimodal.py

 

py test_actions_math.py

 

py test_actions_output_mapping.py

 

py test_actions_server.py

 

py test_actions_validation.py

 

py test_activefence_rail.py

 

py test_ai_defense.py

 

py test_autoalign.py

 

py test_autoalign_factcheck.py

 

py test_basic_embeddings_index_numpy.py

 

py test_batch_embeddings.py

 

py test_bot_message_rendering.py

 

py test_bot_thinking_events.py

 

py test_bot_tool_call_events.py

 

py test_buffer_strategy.py

 

py test_bug_1.py

 

py test_bug_2.py

 

py test_bug_3.py

 

py test_bug_4.py

 

py test_bug_5.py

 

py test_bug_rail_flows_in_prompt.py

 

py test_cache_embeddings.py

 

py test_cache_interface.py

 

py test_cache_lfu.py

 

py test_cache_utils.py

 

py test_clavata.py

 

py test_clavata_models.py

 

py test_clavata_utils.py

 

py test_combine_configs.py

 

py test_config_loading.py

 

py test_config_validation.py

 

py test_content_safety_actions.py

 

py test_content_safety_cache.py

 

py test_content_safety_integration.py

 

py test_content_safety_output_parsers.py

 

py test_context_bloat_detection.py

 

py test_context_updates.py

 

py test_context_updates_2.py

 

py test_crowdstrike_aidr_guard.py

 

py test_custom_init.py

 

py test_dialog_tasks.py

 

py test_embedding_providers.py

 

py test_embeddings_azureopenai.py

 

py test_embeddings_cohere.py

 

py test_embeddings_fastembed.py

 

py test_embeddings_google.py

 

py test_embeddings_only_user_messages.py

 

py test_embeddings_openai.py

 

py test_embeddings_providers_mock.py

 

py test_event_based_api.py

 

py test_example_rails.py

 

py test_execute_action.py

 

py test_extension_flows.py

 

py test_extension_flows_2.py

 

py test_fact_checking.py

 

py test_fiddler_rails.py

 

py test_filters.py

 

py test_flow_set.py

 

py test_flow_when.py

 

py test_flows.py

 

py test_gcp_text_moderation_input_rail.py

 

py test_general_instructions.py

 

py test_generate_value.py

 

py test_generation_options.py

 

py test_gliner.py

 

py test_guardrail_exceptions.py

 

py test_guardrails_ai_actions.py

 

py test_guardrails_ai_config.py

 

py test_guardrails_ai_e2e_actions.py

 

py test_guardrails_ai_e2e_v1.py

 

py test_hallucination_check.py

 

py test_hf_classifier.py

 

py test_imports.py

 

py test_injection_detection.py

 

py test_input_ouput_rails_no_dialog.py

 

py test_input_rails_only.py

 

py test_input_tool_rails.py

 

py test_integration_cache.py

 

py test_internal_error_parallel_rails.py

 

py test_issue_216.py

 

py test_issue_385.py

 

py test_jailbreak_actions.py

 

py test_jailbreak_cache.py

 

py test_jailbreak_config.py

 

py test_jailbreak_heuristics.py

 

py test_jailbreak_model_based.py

 

py test_jailbreak_models.py

 

py test_jailbreak_nim.py

 

py test_jailbreak_request.py

 

py test_kb_openai_embeddings.py

 

py test_llama_guard.py

 

py test_llm_params_e2e.py

 

py test_llm_rails_context_message.py

 

py test_llm_rails_context_variables.py

 

py test_llm_task_manager.py

 

py test_llm_task_manager_multimodal.py

 

py test_llmrails.py

 

py test_llmrails_check_async.py

 

py test_llmrails_multiline.py

 

py test_llmrails_singlecall.py

 

py test_logging.py

 

py test_multi_step_generation.py

 

py test_nemotron_prompt_modes.py

 

py test_nest_asyncio.py

 

py test_output_parsers.py

 

py test_output_rails_tool_calls.py

 

py test_pangea_ai_guard.py

 

py test_parallel_rails.py

 

py test_parallel_rails_exceptions.py

 

py test_parallel_streaming_output_rails.py

 

py test_parser_utils.py

 

py test_patronus_evaluate_api.py

 

py test_patronus_lynx.py

 

py test_perf_1.py

 

py test_policyai_rail.py

 

py test_polygraf.py

 

py test_privateai.py

 

py test_prompt_generation.py

 

py test_prompt_modes.py

 

py test_prompt_override.py

 

py test_prompt_security.py

 

py test_provider_selection.py

 

py test_providers.py

 

py test_rails_config.py

 

py test_rails_llm_config.py

 

py test_rails_llm_utils.py

 

py test_railsignore.py

 

py test_reasoning_trace_extraction.py

 

py test_regex_detection.py

 

py test_registry.py

 

py test_retrieve_relevant_chunks.py

 

py test_runtime_event_logging.py

 

py test_sensitive_data_detection.py

 

py test_state_api_1_0.py

 

py test_streaming_handler.py

 

py test_streaming_internal_errors.py

 

py test_streaming_output_rails.py

 

py test_subflows.py

 

py test_supported_llm_providers.py

 

py test_sync_generate_no_event_loop.py

 

py test_system_message_conversion.py

 

py test_task_specific_model.py

 

py test_taskmanager_multimodal.py

 

py test_testing_chat_harness.py

 

py test_token_usage_integration.py

 

py test_tool_calling_passthrough_integration.py

 

py test_tool_calling_passthrough_only.py

 

py test_tool_calls_context.py

 

py test_tool_calls_event_extraction.py

 

py test_tool_output_rails.py

 

py test_topic_safety_cache.py

 

py test_topic_safety_internalevent.py

 

py test_trend_ai_guard.py

 

py test_types.py

 

py test_types_exports.py

 

py test_utils.py

 

py test_with_actions_override.py

 

py test_with_custom_embedding_search_provider.py

 

py utils.py

 

dir tests/_compat/

 

py 

init

.py

 

py test_langchain_kwargs.py

 

dir tests/cli/

 

py test_chat.py

 

py test_chat_v2x_integration.py

 

py test_cli_main.py

 

py test_debugger.py

 

py test_llm_providers.py

 

py test_migration.py

 

dir tests/colang/

 

py 

init

.py

 

dir tests/colang/parser/

 

py 

init

.py

 

py test_basic.py

 

dir tests/colang/parser/v2_x/

 

py test_ast.py

 

py test_basic.py

 

py test_multiline_bot_action.py

 

py test_syntax_parsing.py

 

dir tests/colang/parser/v2_x/inputs/

 

file test.co

 

file test10.co

 

file test11.co

 

file test12.co

 

file test13.co

 

file test2.co

 

file test3.co

 

file test4.co

 

file test5.co

 

file test6.co

 

file test7.co

 

file test8.co

 

file test9.co

 

dir tests/eval/

 

py test_eval_check.py

 

py test_eval_cli.py

 

py test_eval_config.py

 

py test_eval_runtime.py

 

py test_eval_ui_utils.py

 

py test_models.py

 

py test_utils_safe_yaml.py

 

dir tests/eval/config_yml/

 

file interactions.yml

 

file policies.yml

 

dir tests/evaluate/

 

py test_evaluate_cli_and_data.py

 

py test_evaluate_runtime_classes.py

 

py test_evaluate_topical.py

 

dir tests/guardrails/

 

py async_helpers.py

 

py metric_helpers.py

 

py test__http.py

 

py test_api_engine.py

 

py test_async_work_queue.py

 

py test_base_engine.py

 

py test_configure_logging.py

 

py test_content_safety_iorails_actions.py

 

py test_data.py

 

py test_engine_registry.py

 

py test_guardrails.py

 

py test_guardrails_types.py

 

py test_iorails.py

 

py test_iorails_reasoning.py

 

py test_iorails_streaming.py

 

py test_iorails_telemetry.py

 

py test_jailbreak_detection_iorails_actions.py

 

py test_model_engine.py

 

py test_public_api_deprecations.py

 

py test_rail_action.py

 

py test_rails_manager.py

 

py test_request_id.py

 

py test_speculative_generation.py

 

py test_telemetry.py

 

py test_telemetry_content_capture.py

 

py test_telemetry_metrics.py

 

py test_telemetry_spans.py

 

py test_tool_call_action.py

 

py test_tool_rail_action.py

 

py test_tool_rails_e2e.py

 

py test_tool_rails_iorails.py

 

py test_tool_result_action.py

 

py test_tool_schema.py

 

py test_topic_safety_iorails_actions.py

 

py tool_helpers.py

 

dir tests/integrations/langchain/

 

py conftest.py

 

py test_actions_llm_utils.py

 

py test_custom_llm.py

 

py test_langchain_llm_adapter.py

 

py test_middleware.py

 

py test_middleware_e2e.py

 

py test_openai_param_filter.py

 

py test_output_rails_tool_calls.py

 

py test_reasoning_trace_extraction.py

 

py test_server_streaming.py

 

py test_streaming.py

 

py test_tool_calling_passthrough_only.py

 

py test_tool_calling_utils.py

 

py test_tool_calls_event_extraction.py

 

py test_tool_output_rails.py

 

py utils.py

 

dir tests/integrations/langchain/data/

 

file openai_reasoning_probe_baseline.json

 

dir tests/integrations/langchain/llm/

 

py 

init

.py

 

file langchain_provider_snapshot.json

 

py test_langchain_integration.py

 

py test_version_compatibility.py

 

py update_provider_snapshot.py

 

dir tests/integrations/langchain/llm/models/

 

py 

init

.py

 

py test_langchain_init_scenarios.py

 

py test_langchain_initialization_methods.py

 

py test_langchain_initializer.py

 

py test_langchain_special_cases.py

 

dir tests/integrations/langchain/llm/providers/

 

py 

init

.py

 

py test_deprecated_providers.py

 

py test_providers.py

 

py test_trtllm_provider.py

 

dir tests/integrations/langchain/runnable_rails/

 

py 

init

.py

 

py test_basic_operations.py

 

py test_batch_as_completed.py

 

py test_batching.py

 

py test_composition.py

 

py test_format_output.py

 

py test_history.py

 

py test_message_utils.py

 

py test_metadata.py

 

py test_piping.py

 

py test_runnable_rails.py

 

py test_streaming.py

 

py test_tool_calling.py

 

py test_transform_input.py

 

py test_types.py

 

dir tests/integrations/langchain/test_configs/with_custom_chat_model/

 

file config.co

 

py config.py

 

file config.yml

 

py custom_chat_model.py

 

dir tests/integrations/langchain/test_configs/with_custom_llm/

 

file config.co

 

py config.py

 

file config.yml

 

py custom_llm.py

 

dir tests/integrations/langchain/test_configs/with_custom_llm_prompt_action_v2_x/

 

py actions.py

 

file config.co

 

file config.yml

 

dir tests/llm/

 

py test_openai_reasoning.py

 

dir tests/llm/clients/

 

py 

init

.py

 

py _helpers.py

 

py record_fixtures.py

 

py test_client_config.py

 

py test_errors.py

 

py test_openai_compatible.py

 

py test_openai_compatible_400_enrichment.py

 

py test_openai_compatible_live.py

 

py test_sse.py

 

py test_stream_llm_call.py

 

dir tests/llm/clients/fixtures/

 

file nim_generate_reasoning.json

 

file nim_generate_text.json

 

file nim_generate_tool_call.json

 

file nim_multiturn_tool_roundtrip.json

 

file nim_stream_reasoning.json

 

file nim_stream_text.json

 

file nim_stream_tool_calls.json

 

file openai_error_400_context_length.json

 

file openai_error_401.json

 

file openai_generate_finish_length.json

 

file openai_generate_multimodal.json

 

file openai_generate_refusal.json

 

file openai_generate_text.json

 

file openai_generate_tool_call.json

 

file openai_multiturn_tool_roundtrip.json

 

file openai_stream_multimodal.json

 

file openai_stream_text.json

 

file openai_stream_tool_calls.json

 

dir tests/llm/frameworks/

 

py test_registry.py

 

dir tests/llm/models/

 

py test_openai_chat.py

 

dir tests/rails/llm/

 

py test_config.py

 

py test_options.py

 

dir tests/recorded/

 

file README.md

 

py 

init

.py

 

py assertions.py

 

py cassette.py

 

py conftest.py

 

py fake_cassettes.py

 

py inspect_cassette.py

 

py normalization.py

 

py rails_config.py

 

py sanitization.py

 

py snapshots.py

 

py test_cassette_sanitization.py

 

py test_fake_cassettes.py

 

py test_inspect_cassette.py

 

py test_recorded_helpers.py

 

py utils.py

 

dir tests/recorded/clients/

 

py 

init

.py

 

py test_openai_chat.py

 

py test_openai_embeddings.py

 

dir tests/recorded/clients/cassettes/test_openai_chat/

 

file test_openai_chat_generate_text.yaml

 

dir tests/recorded/clients/cassettes/test_openai_embeddings/

 

file test_openai_embeddings_sync.yaml

 

dir tests/recorded/rails/

 

py 

init

.py

 

py conftest.py

 

py helpers.py

 

dir tests/recorded/rails/library/

 

file README.md

 

py 

init

.py

 

py configs.py

 

py helpers.py

 

py test_composition.py

 

py test_content_safety.py

 

py test_injection.py

 

py test_jailbreak.py

 

py test_regex.py

 

py test_self_check.py

 

py test_topic_control.py

 

dir tests/recorded/rails/library/cassettes/test_composition/

 

file test_input_content_safety_runs_after_self_check_passes.yaml

 

file test_input_jailbreak_runs_before_content_safety.yaml

 

file test_input_self_check_runs_before_provider_rails.yaml

 

file test_input_topic_control_runs_after_content_safety_passes.yaml

 

file test_output_content_safety_runs_after_self_check_passes.yaml

 

file test_output_self_check_runs_before_content_safety.yaml

 

dir tests/recorded/rails/library/cassettes/test_content_safety/

 

file test_content_safety_input_allows_safe_user_message.yaml

 

file test_content_safety_input_blocks_unsafe_user_message.yaml

 

file test_content_safety_input_provider_error_raises.yaml

 

file test_content_safety_output_blocks_fake_main_generation.yaml

 

file test_content_safety_output_blocks_fake_main_stream.yaml

 

file test_content_safety_output_blocks_unsafe_assistant_message.yaml

 

dir tests/recorded/rails/library/cassettes/test_jailbreak/

 

file test_jailbreak_detection_input_blocks_jailbreak_prompt.yaml

 

dir tests/recorded/rails/library/cassettes/test_self_check/

 

file test_self_check_facts_blocks_unsupported_response.yaml

 

file test_self_check_input_blocks_user_message.yaml

 

file test_self_check_output_blocks_assistant_message.yaml

 

file test_self_check_output_blocks_fake_main_stream.yaml

 

dir tests/recorded/rails/library/cassettes/test_topic_control/

 

file test_topic_control_input_allows_on_topic_user_message.yaml

 

file test_topic_control_input_blocks_off_topic_user_message.yaml

 

dir tests/recorded/rails/library/configs/full_stack/

 

file config.yml

 

dir tests/recorded/rails/library/configs/full_stack_no_topic/

 

file config.yml

 

dir tests/recorded/rails/library/configs/injection_detection/

 

file config.yml

 

dir tests/recorded/rails/library/configs/injection_detection_omit/

 

file config.yml

 

dir tests/recorded/rails/library/configs/nim_content_safety/

 

file config.yml

 

dir tests/recorded/rails/library/configs/nim_content_safety_invalid_model/

 

file config.yml

 

dir tests/recorded/rails/library/configs/nim_jailbreak/

 

file config.yml

 

dir tests/recorded/rails/library/configs/nim_topic_control/

 

file config.yml

 

dir tests/recorded/rails/library/configs/openai_input_stack/

 

file config.yml

 

dir tests/recorded/rails/library/configs/openai_output_stack/

 

file config.yml

 

dir tests/recorded/rails/library/configs/openai_self_check/

 

file config.yml

 

dir tests/recorded/rails/library/configs/regex_detection/

 

file config.yml

 

dir tests/recorded/rails/public_api/

 

py 

init

.py

 

py configs.py

 

py simple_embedding_provider.py

 

py test_check.py

 

py test_dialog.py

 

py test_generate.py

 

py test_requests.py

 

py test_stream.py

 

dir tests/recorded/rails/public_api/cassettes/test_check/

 

file test_nemoguards_full_check_async.yaml

 

dir tests/recorded/rails/public_api/cassettes/test_dialog/

 

file test_dialog_generate_async_public_contract.yaml

 

file test_single_call_generate_async_public_contract.yaml

 

dir tests/recorded/rails/public_api/cassettes/test_generate/

 

file test_nemoguards_full_generate_async.yaml

 

file test_nim_generate_async_log_matches_recorded_usage.yaml

 

file test_nim_generate_async_public_contract.yaml

 

file test_nim_generate_sync_public_contract.yaml

 

file test_openai_generate_async_invalid_model_raises.yaml

 

file test_openai_generate_async_log_matches_recorded_chat_completion.yaml

 

file test_openai_generate_async_public_contract.yaml

 

file test_openai_generate_sync_public_contract.yaml

 

dir tests/recorded/rails/public_api/cassettes/test_requests/

 

file test_nim_llm_params_generate_async_request.yaml

 

file test_nim_llm_params_stream_async_request.yaml

 

file test_openai_llm_params_generate_async_request.yaml

 

file test_openai_llm_params_stream_async_request.yaml

 

file test_task_specific_models_generate_async.yaml

 

dir tests/recorded/rails/public_api/cassettes/test_stream/

 

file test_nim_stream_async_public_contract.yaml

 

file test_openai_stream_async_public_contract.yaml

 

file test_stream_async_matches_recorded_chat_completion_metadata.yaml

 

dir tests/recorded/rails/public_api/configs/dialog/

 

py config.py

 

file config.yml

 

file rails.co

 

dir tests/recorded/rails/public_api/configs/nemoguards_full/

 

file config.yml

 

file prompts.yaml

 

dir tests/recorded/rails/public_api/configs/nim_baseline/

 

file config.yml

 

dir tests/recorded/rails/public_api/configs/parallel_rails/

 

py config.py

 

file config.yml

 

file rails.co

 

dir tests/recorded/rails/public_api/configs/single_call/

 

py config.py

 

file config.yml

 

file rails.co

 

dir tests/recorded/rails/public_api/configs/streaming_output_rails/

 

py config.py

 

file config.yml

 

file rails.co

 

dir tests/recorded/rails/public_api/configs/task_models/

 

py config.py

 

file config.yml

 

file rails.co

 

dir tests/server/

 

py test_api.py

 

py test_guardrail_checks.py

 

py test_iorails_engine_compat.py

 

py test_openai_integration.py

 

py test_schema_utils.py

 

py test_server_calls_with_state.py

 

py test_threads.py

 

dir tests/telemetry/

 

py test_usage_reporting.py

 

dir tests/telemetry/smoke_fixtures/

 

file README.md

 

dir tests/telemetry/smoke_fixtures/cfg1/

 

file config.yml

 

dir tests/telemetry/smoke_fixtures/cfg2/

 

file config.yml

 

dir tests/telemetry/smoke_fixtures/cfg3/

 

file config.yml

 

dir tests/telemetry/smoke_fixtures/feature_aliases/

 

file config.yml

 

dir tests/telemetry/smoke_fixtures/rich/

 

file config.yml

 

file rails.co

 

dir tests/telemetry/smoke_fixtures/rich/kb/

 

file kb.md

 

dir tests/telemetry/smoke_fixtures/v2_custom_flow/

 

file config.yml

 

file rails.co

 

dir tests/test_configs/

 

py demo.py

 

dir tests/test_configs/autoalign/

 

file config.yml

 

dir tests/test_configs/autoalign_factchecker/

 

file config.yml

 

dir tests/test_configs/autoalign_groundness/

 

file config.yml

 

dir tests/test_configs/autoalign_groundness/kb/

 

file kb.md

 

dir tests/test_configs/autoalign_groundness/rails/

 

file factcheck.co

 

file general.co

 

dir tests/test_configs/fact_checking/

 

file config.co

 

file config.yml

 

file factcheck.co

 

file prompts.yml

 

dir tests/test_configs/fact_checking/kb/

 

file kb.md

 

dir tests/test_configs/fiddler/faithfulness/

 

file config.yml

 

file fiddler_check.co

 

dir tests/test_configs/fiddler/safety/

 

file config.yml

 

file fiddler_check.co

 

dir tests/test_configs/fiddler/thresholds/

 

file config.yml

 

file fiddler_check.co

 

dir tests/test_configs/game/

 

file config.yml

 

file game.co

 

dir tests/test_configs/general/

 

file README.md

 

file general.yml

 

dir tests/test_configs/generate_value/

 

file README.md

 

file config.co

 

file config.yml

 

dir tests/test_configs/injection_detection/

 

file config.yml

 

file flows.co

 

file test.yara

 

dir tests/test_configs/input_rails/

 

file config.yml

 

file prompts.yml

 

dir tests/test_configs/jailbreak_heuristics/

 

file config.yml

 

file flows.co

 

dir tests/test_configs/jailbreak_models/

 

file config.yml

 

file flows.co

 

dir tests/test_configs/jailbreak_nim/

 

file config.yml

 

file flows.co

 

dir tests/test_configs/multi_modal_demo_v2_x/

 

file demo.co

 

file demo.yml

 

file llm_example_flows.co

 

dir tests/test_configs/multi_modal_demo_v2_x/show_cases/

 

file show_case_action_alignment.co

 

file show_case_back_channelling_interaction.co

 

file show_case_number_guessing_game.co

 

file show_case_posture_capabilities.co

 

file show_case_proactive_turn_taking.co

 

dir tests/test_configs/multi_step_generation/

 

file config.co

 

file config.yml

 

file scheduling.co

 

dir tests/test_configs/mvp_v2_x/

 

file config.yml

 

file mvp_v2_x.co

 

dir tests/test_configs/mvp_v2_x_b/

 

file config.yml

 

file mvp_v2_x.co

 

dir tests/test_configs/mvp_v2_x_c/

 

file config.co

 

file config.yml

 

dir tests/test_configs/mvp_v2_x_d/

 

py actions.py

 

file config.co

 

file config.yml

 

file testing.md

 

dir tests/test_configs/mvp_v2_x_e/

 

file config.yml

 

dir tests/test_configs/output_rails/

 

py actions.py

 

file config.yml

 

file prompts.yml

 

dir tests/test_configs/output_rails/rails/

 

file blocked_terms.co

 

dir tests/test_configs/parallel_rails/

 

py actions.py

 

file config.yml

 

file prompts.yml

 

dir tests/test_configs/parallel_rails/rails/

 

file blocked_terms.co

 

dir tests/test_configs/parallel_rails_with_exceptions/

 

py actions.py

 

file config.yml

 

file rails.co

 

dir tests/test_configs/railsignore_config/

 

file config_to_load.co

 

file ignored_config.co

 

dir tests/test_configs/simple_actions/

 

file config.yml

 

file sample.co

 

dir tests/test_configs/simple_server/config_1/

 

py config.py

 

file config.yml

 

file rails.co

 

dir tests/test_configs/simple_server_2_x/config_2/

 

py config.py

 

file config.yml

 

file rails.co

 

dir tests/test_configs/summarization/

 

file article.txt

 

file config.yml

 

file summarization.co

 

dir tests/test_configs/system_variable_access_v2/

 

file config.yml

 

file system_variable_access_v2.co

 

dir tests/test_configs/with_actions_override/

 

file config.co

 

py config.py

 

file config.yml

 

dir tests/test_configs/with_azureopenai_embeddings/

 

file config.co

 

file config.yml

 

dir tests/test_configs/with_cohere_embeddings/

 

file config.co

 

file config.yml

 

dir tests/test_configs/with_custom_action/

 

py actions.py

 

file config.co

 

file config.yml

 

py demo_custom_action.py

 

dir tests/test_configs/with_custom_action_v2_x/

 

py actions.py

 

file config.co

 

file config.yml

 

dir tests/test_configs/with_custom_chat_model/

 

file config.co

 

py config.py

 

file config.yml

 

py custom_chat_model.py

 

dir tests/test_configs/with_custom_embedding_search_provider/

 

file config.co

 

py config.py

 

file config.yml

 

dir tests/test_configs/with_custom_embedding_search_provider/kb/

 

file kb.md

 

dir tests/test_configs/with_custom_init/

 

py actions.py

 

file config.co

 

py config.py

 

file config.yml

 

dir tests/test_configs/with_custom_llm/

 

file config.co

 

py config.py

 

file config.yml

 

py custom_llm.py

 

dir tests/test_configs/with_custom_llm_prompt_action_v2_x/

 

py actions.py

 

file config.co

 

file config.yml

 

dir tests/test_configs/with_google_embeddings/

 

file config.co

 

file config.yml

 

dir tests/test_configs/with_imports_1/

 

file config.yml

 

file main.co

 

dir tests/test_configs/with_kb_openai_embeddings/

 

file config.co

 

file config.yml

 

dir tests/test_configs/with_kb_openai_embeddings/kb/

 

file kb.md

 

dir tests/test_configs/with_langchain_safetool/

 

file config.co

 

file config.yml

 

dir tests/test_configs/with_openai_embeddings/

 

file config.co

 

file config.yml

 

dir tests/test_configs/with_prompt_modes/prompts/

 

file prompts.yml

 

dir tests/test_configs/with_prompt_override/

 

file config.co

 

file config.yml

 

dir tests/testing/

 

py 

init

.py

 

py conftest.py

 

py embeddings.py

 

py test_public_surface.py

 

dir tests/tracing/

 

py test_span_formatting.py

 

py test_tracing.py

 

dir tests/tracing/adapters/

 

py test_filesystem.py

 

py test_log_adapter_registry.py

 

py test_opentelemetry.py

 

py test_opentelemetry_v2.py

 

dir tests/tracing/spans/

 

py test_span_extractors.py

 

py test_span_format_enum.py

 

py test_span_models_and_extractors.py

 

py test_span_v2_integration.py

 

py test_span_v2_otel_semantics.py

 

py test_spans.py

 

dir tests/v2_x/

 

py 

init

.py

 

py chat.py

 

py test_attention_library.py

 

py test_bot_flow_composite_spec.py

 

py test_compound_statements.py

 

py test_decorator_parsing.py

 

py test_event_mechanics.py

 

py test_expr_statement.py

 

py test_flow_mechanics.py

 

py test_flow_params.py

 

py test_generation_actions_unit.py

 

py test_group_mechanics.py

 

py test_import_paths.py

 

py test_imports.py

 

py test_input_output_rails_transformations.py

 

py test_llm_continuation.py

 

py test_llm_embedding_lazy_init.py

 

py test_llm_user_intents_detection.py

 

py test_llm_value_generation.py

 

py test_module_flow_activation.py

 

py test_mvp_v2_x.py

 

py test_mvp_v2_x_b.py

 

py test_mvp_v2_x_c.py

 

py test_mvp_v2_x_d.py

 

py test_outgoing_events.py

 

py test_passthroug_mode.py

 

py test_python_api.py

 

py test_run_actions.py

 

py test_slide_mechanics.py

 

py test_state_serialization.py

 

py test_story_mechanics.py

 

py test_system_actions.py

 

py test_system_functions.py

 

py test_system_variable_access.py

 

py test_tutorial_examples.py

 

py test_various_mechanics.py

 

dir vscode_extension/

 

file README.md

 

dir vscode_extension/colang-2-lang/

 

file LICENSE.md

 

file README.md

 

file colang-configuration.json

 

file package.json

 

file sample.co

 

dir vscode_extension/colang-2-lang/syntaxes/

 

file colang.tmLanguage.json

============================================================

Documentation

============================================================

AI_POLICY.md

# AI Usage Policy

NeMo Guardrails welcomes responsible AI-assisted contributions. AI tools can be
useful for exploration, implementation, review, and documentation, but the human
submitter remains responsible for the contribution.

## Contributor Responsibilities

- Disclose AI assistance in the pull request description when AI tools create or
  substantially modify code, tests, docs, issues, or comments. Include the tool
  used and the extent of assistance.
- Issues must be opened manually by a human through the repository issue
  templates. AI tools may help draft an issue, but agents must not submit issues
  directly.
- Review, edit, and verify AI-generated content before submitting it. Do not
  paste unreviewed AI output into issues, PR descriptions, code comments, docs,
  or review comments.
- Understand every submitted change well enough to explain what it does, why it
  is needed, and how it interacts with the surrounding code.
- Keep AI-assisted pull requests cohesive, scoped, and useful. Duplicate,
  low-value, mechanical, or noisy contributions may be closed.
- Do not add AI tools as commit co-authors. Contributions should be authored by
  the human submitter and must still satisfy the DCO or GPG-signing
  requirements in `CONTRIBUTING.md`.

## Safety and Privacy

- Do not commit API keys, credentials, private endpoints, proprietary prompts,
  raw provider logs, or sensitive request/response data.
- Do not use AI tools to fabricate test results, benchmark results, citations,
  maintainer approvals, or compatibility claims.
- Generated media, large generated assets, or synthetic datasets require clear
  provenance and maintainer alignment before inclusion.

## Maintainer Expectations

AI assistance does not lower the review bar. Maintainers may ask contributors to
explain, simplify, test, rewrite, or withdraw AI-assisted work that is not ready
for review.



CHANGELOG-Colang.md

# Changelog

All notable changes to the Colang language and runtime will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0-beta.7] - 2025-07-16

### Fixed

* Use processed user and bot messages after input/output rails transformations to prevent leakage of unfiltered data ([#1297](https://github.com/NVIDIA-NeMo/Guardrails/pull/1297)) by @lapinek

## [2.0-beta.6] - 2025-01-16

### Added

* Add support for llama-3.2 models ([#877](https://github.com/NVIDIA-NeMo/Guardrails/pull/877)) by @schuellc-nvidia
* Add `it finished` utility flow in core.co library ([#913]<https://github.com/NVIDIA-NeMo/Guardrails/pull/913>) by @schuellc-nvidia

## [2.0-beta.5] - 2024-11-19

### Added

* Prompt template name to verbose logging ([#811](https://github.com/NVIDIA-NeMo/Guardrails/pull/811)) by @schuellc-nvidia
* New configuration setting to change UMIM event source id ([#823](https://github.com/NVIDIA-NeMo/Guardrails/pull/823)) by @sklinglernv
* New attention module to standard library ([#829](https://github.com/NVIDIA-NeMo/Guardrails/pull/829)) by @sklinglernv
* Passthrough mode support ([#779](https://github.com/NVIDIA-NeMo/Guardrails/pull/779)) by @Pouyanpi

### Fixed

* Activation of flows with default parameters ([#758](https://github.com/NVIDIA-NeMo/Guardrails/pull/758)) by @schuellc-nvidia
* ``pretty_str`` string formatting function ([#759](https://github.com/NVIDIA-NeMo/Guardrails/pull/759)) by @schuellc-nvidia
* Consistent uuid generation in debug mode ([#760](https://github.com/NVIDIA-NeMo/Guardrails/pull/760)) by @schuellc-nvidia
* Avatar posture management function in standard library ([#771](https://github.com/NVIDIA-NeMo/Guardrails/pull/771)) by @sklinglernv
* Nested ``if else`` construct parsing ([#833](https://github.com/NVIDIA-NeMo/Guardrails/pull/833)) by @radinshayanfar
* Multiline string values in interaction history prompting ([#765](https://github.com/NVIDIA-NeMo/Guardrails/pull/765)) by @radinshayanfar

## [2.0-beta.4] - 2024-10-02

### Fixed

* LLM prompt template ``generate_value_from_instruction`` for GPT and LLama model chat interface ([#775](https://github.com/NVIDIA-NeMo/Guardrails/pull/775)) by @schuellc-nvidia

## [2.0-beta.3] - 2024-09-27

### Added

* Support for new Colang 2 keyword `deactivate` ([#673](https://github.com/NVIDIA-NeMo/Guardrails/pull/673)) by @schuellc-nvidia
* Bot configuration as variable `$system.config` ([#703](https://github.com/NVIDIA-NeMo/Guardrails/pull/703)) by @schuellc-nvidia
* Basic support for most OpenAI and LLame 3 models ([#709](https://github.com/NVIDIA-NeMo/Guardrails/pull/709)) by @schuellc-nvidia
* Interaction loop priority levels for flows ([#712](https://github.com/NVIDIA-NeMo/Guardrails/pull/712)) by @schuellc-nvidia
* CLI chat debugging commands ([#717](https://github.com/NVIDIA-NeMo/Guardrails/pull/717)) by @schuellc-nvidia

### Changed

* Merged (and removed) utils library file with core library ([#669](https://github.com/NVIDIA-NeMo/Guardrails/pull/669)) by @schuellc-nvidia

### Fixed

* Fixes a event group match bug (e.g. `match $flow_ref.Finished() or $flow_ref.Failed()`) ([#672](https://github.com/NVIDIA-NeMo/Guardrails/pull/672)) by @schuellc-nvidia
* Fix issues with ActionUpdated events and user utterance action extraction ([#699](https://github.com/NVIDIA-NeMo/Guardrails/pull/699)) by @schuellc-nvidia

## [2.0-beta.2] - 2024-07-25

This second beta version of Colang brings a set of improvements and fixes.

### Added

Language and runtime:

* Colang 2.0 syntax error details ([#504](https://github.com/NVIDIA-NeMo/Guardrails/pull/504)) by @rgstephens
* Expose global variables in prompting templates ([#533](https://github.com/NVIDIA-NeMo/Guardrails/pull/533)) by @schuellc-nvidia
* `continuation on unhandled user utterance` flow to the standard library (`llm.co`) ([#534](https://github.com/NVIDIA-NeMo/Guardrails/pull/534)) by @schuellc-nvidia
* Support for NLD intents ([#554](https://github.com/NVIDIA-NeMo/Guardrails/pull/554)) by @schuellc-nvidia
* Support for the `@active` decorator which activates flows automatically ([#559](https://github.com/NVIDIA-NeMo/Guardrails/pull/559)) by @schuellc-nvidia

Other:

* Unit tests for runtime exception handling in flows ([#591](https://github.com/NVIDIA-NeMo/Guardrails/pull/591)) by @schuellc-nvidia

### Changed

* Make `if` / `while` / `when` statements compatible with python syntax, i.e., allow `:` at the end of line ([#576](https://github.com/NVIDIA-NeMo/Guardrails/pull/576)) by @schuellc-nvidia
* Allow `not`, `in`, `is` in generated flow names ([#596](https://github.com/NVIDIA-NeMo/Guardrails/pull/596)) by @schuellc-nvidia
* Improve bot action generation ([#578](https://github.com/NVIDIA-NeMo/Guardrails/pull/578)) by @schuellc-nvidia
* Add more information to Colang syntax errors ([#594](https://github.com/NVIDIA-NeMo/Guardrails/pull/594)) by @schuellc-nvidia
* Runtime processing loop also consumes generated events before completion ([#599](https://github.com/NVIDIA-NeMo/Guardrails/pull/599)) by @schuellc-nvidia
* LLM prompting improvements targeting `gpt-4o` ([#540](https://github.com/NVIDIA-NeMo/Guardrails/pull/540)) by @schuellc-nvidia

### Fixed

* Fix string expression double braces ([#525](https://github.com/NVIDIA-NeMo/Guardrails/pull/525)) by @schuellc-nvidia
* Fix Colang 2 flow activation ([#531](https://github.com/NVIDIA-NeMo/Guardrails/pull/531)) by @schuellc-nvidia
* Remove unnecessary print statements in runtime ([#577](https://github.com/NVIDIA-NeMo/Guardrails/pull/577)) by @schuellc-nvidia
* Fix `match` statement issue ([#593](https://github.com/NVIDIA-NeMo/Guardrails/pull/593)) by @schuellc-nvidia
* Fix multiline string expressions issue ([#579](https://github.com/NVIDIA-NeMo/Guardrails/pull/579)) by @schuellc-nvidia
* Fix tracking user talking state issue ([#604](https://github.com/NVIDIA-NeMo/Guardrails/pull/604)) by @schuellc-nvidia
* Fix issue related to a race condition ([#598](https://github.com/NVIDIA-NeMo/Guardrails/pull/598)) by @schuellc-nvidia

## [2.0-beta] - 2024-05-08

### Added

* [Standard library of flows](https://docs.nvidia.com/nemo/guardrails/colang-2/language-reference/the-standard-library.html): `core.co`, `llm.co`, `guardrails.co`, `avatars.co`, `timing.co`, `utils.co`.

### Changed

* Syntax changes:
  * Meta comments have been replaced by the `@meta` and `@loop` decorators:
    * `# meta: user intent` -> `@meta(user_intent=True)` (also user_action, bot_intent, bot_action)
    * `# meta: exclude from llm` -> `@meta(exclude_from_llm=True)`
    * `# meta: loop_id=<loop_id>`  -> `@loop("<loop_id>")`
  * `orwhen` -> `or when`
  * NLD instructions `"""<NLD>"""` -> `..."<NLD>"`
  * Support for `import` statement
  * Regular expressions syntax change `r"<regex>"` -> `regex("<regex>")`
  * String expressions change: `"{{<expression>}}"` -> `"{<expression>}"`

* Chat CLI runtime flags `--verbose` logging format improvements
* Internal event parameter renaming: `flow_start_uid` -> `flow_instance_uid`
* Colang function name changes: `findall` -> `find_all` ,

* Changes to flow names that were previously part of `ccl_*.co` files (which are now part of the standard library):
  * `catch colang errors` -> `notification of colang errors` (core.co)
  * `catch undefined flows` -> `notification of undefined flow start` (core.co)
  * `catch unexpected user utterance` -> `notification of unexpected user utterance` (core.co)
  * `poll llm request response` -> `polling llm request response` (llm.co)
  * `trigger user intent for unhandled user utterance` -> `generating user intent for unhandled user utterance` (llm.co)
  * `generate then continue interaction` -> `llm continue interaction` (llm.co)
  * `track bot talking state` -> `tracking bot talking state` (core.co)
  * `track user talking state` -> `tracking user talking state` (core.co)
  * `track unhandled user intent state` -> `tracking unhandled user intent state` (llm.co)
  * `track visual choice selection state` -> `track visual choice selection state` (avatars.co)
  * `track user utterance state` -> `tracking user talking state` (core.co)
  * `track bot utterance state` -> No replacement yet (copy to your bot script)
  * `interruption handling bot talking` -> `handling bot talking interruption` (avatars.co)
  * `generate then continue interaction` -> `llm continue interaction` (llm.co)

## [2.0-alpha] - 2024-02-28

[Colang 2.0](https://docs.nvidia.com/nemo/guardrails/colang-2/overview.html) represents a complete overhaul of both the language and runtime. Key enhancements include:

### Added

* A more powerful flows engine supporting multiple parallel flows and advanced pattern matching over the stream of events.
* A standard library to simplify bot development.
* Smaller set of core abstractions: flows, events, and actions.
* Explicit entry point through the main flow and explicit activation of flows.
* Asynchronous actions execution.
* Adoption of terminology and syntax akin to Python to reduce the learning curve for new developers.



CHANGELOG.md

# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.23.0] - 2026-07-01

### 🚀 Features

- *(library)* Add lightweight Hugging Face classifier rails for input, output, and retrieval, with local Transformers, vLLM, KServe, and FMS backends ([#1853](https://github.com/NVIDIA-NeMo/Guardrails/issues/1853))
- *(embeddings)* Replace Annoy with exact NumPy search and add migration benchmarks ([#1957](https://github.com/NVIDIA-NeMo/Guardrails/issues/1957), [#1958](https://github.com/NVIDIA-NeMo/Guardrails/issues/1958))
- *(iorails)* Add opt-in OpenTelemetry content capture and LLM request, response, and usage attributes ([#1972](https://github.com/NVIDIA-NeMo/Guardrails/issues/1972), [#2009](https://github.com/NVIDIA-NeMo/Guardrails/issues/2009))
- *(iorails)* Add streaming and non-streaming tool calling and local rails for validating tool calls and results ([#2016](https://github.com/NVIDIA-NeMo/Guardrails/issues/2016), [#2024](https://github.com/NVIDIA-NeMo/Guardrails/issues/2024), [#2030](https://github.com/NVIDIA-NeMo/Guardrails/issues/2030), [#2058](https://github.com/NVIDIA-NeMo/Guardrails/issues/2058))
- *(library)* Add context bloat detection rail ([#1941](https://github.com/NVIDIA-NeMo/Guardrails/issues/1941))
- *(server)* Add `/v1/checks` endpoint for standalone input and output rail validation ([#2013](https://github.com/NVIDIA-NeMo/Guardrails/issues/2013))
- *(server)* Add tool calling support ([#1942](https://github.com/NVIDIA-NeMo/Guardrails/issues/1942))
- *(examples)* Introduce NIM-based example notebooks, retire superseded ones ([#1906](https://github.com/NVIDIA-NeMo/Guardrails/issues/1906))
- *(library)* Add Polygraf PII detection and masking integration ([#1693](https://github.com/NVIDIA-NeMo/Guardrails/issues/1693))

### 🐛 Bug Fixes

- *(library)* Fix regex detection during output streaming so matches block correctly without raising `TypeError` ([#1932](https://github.com/NVIDIA-NeMo/Guardrails/issues/1932), [#1937](https://github.com/NVIDIA-NeMo/Guardrails/issues/1937))
- *(actions)* Avoid empty-string crash in create_event ([#1701](https://github.com/NVIDIA-NeMo/Guardrails/issues/1701))
- *(iorails)* Make OTEL recording best-effort ([#1997](https://github.com/NVIDIA-NeMo/Guardrails/issues/1997))
- *(docs)* Skip Fern bash-script tests on Windows ([#2017](https://github.com/NVIDIA-NeMo/Guardrails/issues/2017))
- *(iorails)* Apply inference-time llm_params on top of Model.parameters in ModelEngine ([#2020](https://github.com/NVIDIA-NeMo/Guardrails/issues/2020))
- *(llm)* Handle multi-line bot say responses in flow continuation([#1650](https://github.com/NVIDIA-NeMo/Guardrails/issues/1650))
- *(generation)* Use correct task enum for stop tokens in generate_value ([#1699](https://github.com/NVIDIA-NeMo/Guardrails/issues/1699))
- *(colang)* Guard ' or' line continuation at end of file ([#1947](https://github.com/NVIDIA-NeMo/Guardrails/issues/1947))
- *(iorails)* Add no-op events_history_cache when IORails is used ([#2072](https://github.com/NVIDIA-NeMo/Guardrails/issues/2072))
- *(llmrails)* Load library files deterministically ([#1975](https://github.com/NVIDIA-NeMo/Guardrails/issues/1975))
- *(embeddings)* EmbeddingsCache.from_dict drops store_config on round-trip ([#1951](https://github.com/NVIDIA-NeMo/Guardrails/issues/1951))
- *(eval)* Use safe dumper and yaml load ([#2082](https://github.com/NVIDIA-NeMo/Guardrails/issues/2082))
- *(streaming)* Pass user content to output rails ([#2081](https://github.com/NVIDIA-NeMo/Guardrails/issues/2081))
- *(streaming)* Avoid duplicate usage metadata chunk ([#2079](https://github.com/NVIDIA-NeMo/Guardrails/issues/2079))
- *(streaming)* Don't reuse resolved action parameters across output-rail chunks or requests ([#1935](https://github.com/NVIDIA-NeMo/Guardrails/issues/1935), [#1943](https://github.com/NVIDIA-NeMo/Guardrails/issues/1943))
- *(ci)* Update README version during releases ([#2104](https://github.com/NVIDIA-NeMo/Guardrails/issues/2104))
- *(llmrails)* Preserve tool calls for LLMRails tool rails ([#2073](https://github.com/NVIDIA-NeMo/Guardrails/issues/2073))
- *(langchain)* OpenAI Responses API and Harmony response format support ([#2102](https://github.com/NVIDIA-NeMo/Guardrails/issues/2102))

### 💼 Other

- Stop bundling examples and repo files in the wheel (10x smaller) ([#2069](https://github.com/NVIDIA-NeMo/Guardrails/issues/2069))
- Exclude repository agent instruction files from source and wheel packages ([#2111](https://github.com/NVIDIA-NeMo/Guardrails/issues/2111))

### 🚜 Refactor

- Refine the Guardrails public API and deprecate direct access to internal `LLMRails` attributes ([#1933](https://github.com/NVIDIA-NeMo/Guardrails/issues/1933))
- [**breaking**] Require Pydantic `>=2.5,<3.0` and migrate validators and model APIs to Pydantic 2 ([#967](https://github.com/NVIDIA-NeMo/Guardrails/issues/967))

### 📚 Documentation

- Clarify NGC_API_KEY handling for local GLiNER/PII NIM deployment ([#1945](https://github.com/NVIDIA-NeMo/Guardrails/issues/1945))
- Migrate documentation to Fern, document the publishing workflow, and complete link and template cleanup ([#1973](https://github.com/NVIDIA-NeMo/Guardrails/issues/1973), [#2015](https://github.com/NVIDIA-NeMo/Guardrails/issues/2015), [#2018](https://github.com/NVIDIA-NeMo/Guardrails/issues/2018), [#2019](https://github.com/NVIDIA-NeMo/Guardrails/issues/2019))
- *(readme)* Fix broken links to the Guardrails website ([#2046](https://github.com/NVIDIA-NeMo/Guardrails/issues/2046))
- *(skills)* Add skills ([#2025](https://github.com/NVIDIA-NeMo/Guardrails/issues/2025))
- *(iorails)* Telemetry - Span Reference Docs ([#2098](https://github.com/NVIDIA-NeMo/Guardrails/issues/2098))
- *(iorails)* Tool calling docs ([#2099](https://github.com/NVIDIA-NeMo/Guardrails/issues/2099))
- *(iorails)* Telemetry - Content Capture docs ([#2083](https://github.com/NVIDIA-NeMo/Guardrails/issues/2083))

### 🧪 Testing

- Make xdist the default Makefile test path ([#1970](https://github.com/NVIDIA-NeMo/Guardrails/issues/1970))
- Isolate flaky wall-clock perf tests behind a perf marker ([#2070](https://github.com/NVIDIA-NeMo/Guardrails/issues/2070))
- *(recorded)* Add a replay harness, client cassette coverage, public API coverage, and rails library coverage ([#1974](https://github.com/NVIDIA-NeMo/Guardrails/issues/1974), [#1976](https://github.com/NVIDIA-NeMo/Guardrails/issues/1976), [#1977](https://github.com/NVIDIA-NeMo/Guardrails/issues/1977), [#1978](https://github.com/NVIDIA-NeMo/Guardrails/issues/1978))
- *(langchain)* Make provider compat tests version-tolerant, add drift canary ([#2071](https://github.com/NVIDIA-NeMo/Guardrails/issues/2071))
- Support aiohttp 3.14 in aioresponses mocks ([#2091](https://github.com/NVIDIA-NeMo/Guardrails/issues/2091))
- Remove flaky streaming timing diagnostic ([#2097](https://github.com/NVIDIA-NeMo/Guardrails/issues/2097))

## [0.22.0] - 2026-05-22

### 🚀 Features

- *(iorails)* IORails support for streaming output rails ([#1765](https://github.com/NVIDIA-NeMo/Guardrails/issues/1765), [#1766](https://github.com/NVIDIA-NeMo/Guardrails/issues/1766))
- *(iorails)* IORails OpenTelemetry tracing support ([#1793](https://github.com/NVIDIA-NeMo/Guardrails/issues/1793), [#1794](https://github.com/NVIDIA-NeMo/Guardrails/issues/1794), [#1798](https://github.com/NVIDIA-NeMo/Guardrails/issues/1798))
- *(iorails)* IORails OpenTelemetry token-level metrics support ([#1812](https://github.com/NVIDIA-NeMo/Guardrails/issues/1812), [#1846](https://github.com/NVIDIA-NeMo/Guardrails/issues/1846))
- *(iorails)* IORails reasoning model support ([#1842](https://github.com/NVIDIA-NeMo/Guardrails/issues/1842), [#1843](https://github.com/NVIDIA-NeMo/Guardrails/issues/1843))
- *(llm)* Add LangChain adapter and framework registry ([#1759](https://github.com/NVIDIA-NeMo/Guardrails/issues/1759))
- *(llm)* Add streaming tool call accumulation and LLMResponse parity ([#1789](https://github.com/NVIDIA-NeMo/Guardrails/issues/1789))
- *(llm)* Add default framework with OpenAI-compatible client ([#1797](https://github.com/NVIDIA-NeMo/Guardrails/issues/1797))
- *(llm/frameworks)* Validate framework on registration ([#1863](https://github.com/NVIDIA-NeMo/Guardrails/issues/1863))
- *(types)* Add framework-agnostic LLM type system ([#1745](https://github.com/NVIDIA-NeMo/Guardrails/issues/1745))
- *(compat)* Transitional compat layer to migrate from 0.21 to 0.22+ ([#1841](https://github.com/NVIDIA-NeMo/Guardrails/issues/1841))
- *(testing)* Add public testing surface under nemoguardrails.testing ([#1860](https://github.com/NVIDIA-NeMo/Guardrails/issues/1860))
- *(api)* Canonical top-level imports for LLM types and registry functions ([#1882](https://github.com/NVIDIA-NeMo/Guardrails/issues/1882))
- *(config)* Forbade extra fields in GLiNER rails configs ([#1898](https://github.com/NVIDIA-NeMo/Guardrails/issues/1898))
- *(framework)* Support Azure as a first-class default framework preset ([#1896](https://github.com/NVIDIA-NeMo/Guardrails/issues/1896))

### 🐛 Bug Fixes

- [**breaking**] Reject Colang 2.0 public runtime state ([#1885](https://github.com/NVIDIA-NeMo/Guardrails/issues/1885))
- *(server)* Prioritize env var API key over forwarded client header ([#1688](https://github.com/NVIDIA-NeMo/Guardrails/issues/1688))
- *(utils)* Removing extra space from UtteranceBotActionScriptUpdated ([#1708](https://github.com/NVIDIA-NeMo/Guardrails/issues/1708))
- *(actions)* Remove redundant embedding search in generate_user_intent ([#1754](https://github.com/NVIDIA-NeMo/Guardrails/issues/1754))
- *(llmrails)* Backfill embedding model params into search provider config (fixes stale KB cache) ([#1753](https://github.com/NVIDIA-NeMo/Guardrails/issues/1753))
- *(embeddings)* Persist in-memory embedding cache instance across calls ([#1755](https://github.com/NVIDIA-NeMo/Guardrails/issues/1755))
- *(ci)* Pin baseline x86-64 compiler target to prevent SIGILL on cached venvs ([#1785](https://github.com/NVIDIA-NeMo/Guardrails/issues/1785))
- *(tests)* Use asyncio.run instead of get_event_loop in middleware tests ([#1804](https://github.com/NVIDIA-NeMo/Guardrails/issues/1804))
- *(actions)* Guard bot message extraction against composite specs ([#1810](https://github.com/NVIDIA-NeMo/Guardrails/issues/1810))
- *(llm)* Drop stop param for OpenAI reasoning models ([#1811](https://github.com/NVIDIA-NeMo/Guardrails/issues/1811))
- *(llmrails)* Scope no main LLM warning to generation path ([#1813](https://github.com/NVIDIA-NeMo/Guardrails/issues/1813))
- *(chat-ui)* Replace Chatbot UI with Chainlit ([#1734](https://github.com/NVIDIA-NeMo/Guardrails/issues/1734))
- *(library)* Unblock reasoning models in self-check and content-safety actions ([#1816](https://github.com/NVIDIA-NeMo/Guardrails/issues/1816))
- *(llm)* Drop temperature/stop and rename max_tokens for OpenAI reasoning models ([#1837](https://github.com/NVIDIA-NeMo/Guardrails/issues/1837))
- *(build)* Remove chat-ui references from wheel build script ([#1835](https://github.com/NVIDIA-NeMo/Guardrails/issues/1835))
- *(ci)* Override annoy's -march=native to actually enforce baseline x86-64 ([#1839](https://github.com/NVIDIA-NeMo/Guardrails/issues/1839))
- *(llm/clients)* Retry on stale event loop binding ([#1840](https://github.com/NVIDIA-NeMo/Guardrails/issues/1840))
- *(llm/frameworks)* Point users to LangChain when DefaultFramework has no base_url ([#1865](https://github.com/NVIDIA-NeMo/Guardrails/issues/1865))
- *(taskmanager)* Preserve multimodal list content in vision safety prompts ([#1815](https://github.com/NVIDIA-NeMo/Guardrails/issues/1815))
- *(actions)* Extract text from multimodal events in colang history ([#1636](https://github.com/NVIDIA-NeMo/Guardrails/issues/1636))
- *(iorails)* Route to LLMRails if Guardrails inits with provided LLM ([#1844](https://github.com/NVIDIA-NeMo/Guardrails/issues/1844))
- *(iorails)* Strip trailing /v1 from base_url to avoid doubled path ([#1862](https://github.com/NVIDIA-NeMo/Guardrails/issues/1862))
- *(iorails)* Add all LLMRails methods, `llm` and `runtime` getters to Guardrails facade ([#1886](https://github.com/NVIDIA-NeMo/Guardrails/issues/1886), [#1889](https://github.com/NVIDIA-NeMo/Guardrails/issues/1889))
- *(iorails)* Annotate cancelled OTEL spans with error ([#1897](https://github.com/NVIDIA-NeMo/Guardrails/issues/1897))

### 🚜 Refactor

- *(llm)* [**breaking**] Atomic switch to LLMModel protocol ([#1760](https://github.com/NVIDIA-NeMo/Guardrails/issues/1760))
- *(iorails)* [**breaking**] Move AsyncWorkQueue from Guardrails to IORails ([#1817](https://github.com/NVIDIA-NeMo/Guardrails/issues/1817))
- *(deps)* [**breaking**] Demote LangChain and LangChain-providers from core to dev ([#1806](https://github.com/NVIDIA-NeMo/Guardrails/issues/1806))
- *(iorails)* Return LLMResponse(Chunk) from ModelEngine ([#1827](https://github.com/NVIDIA-NeMo/Guardrails/issues/1827))
- *(iorails)* Refactor ModelManager ([#1778](https://github.com/NVIDIA-NeMo/Guardrails/issues/1778))
- *(iorails)* Refactor Guardrails and IORails for top-level import and clean separation ([#1893](https://github.com/NVIDIA-NeMo/Guardrails/issues/1893))
- *(iorails)* Refactor RailsManager and Nemoguard Actions ([#1762](https://github.com/NVIDIA-NeMo/Guardrails/issues/1762))
- *(llm)* Rename generate/stream to generate_async/stream_async ([#1769](https://github.com/NVIDIA-NeMo/Guardrails/issues/1769))
- *(llm)* Remove LangChain imports from core modules ([#1770](https://github.com/NVIDIA-NeMo/Guardrails/issues/1770))
- *(llm)* Move LangChain implementations into integrations/langchain/ ([#1772](https://github.com/NVIDIA-NeMo/Guardrails/issues/1772))
- *(llm)* Framework-owned provider registry ([#1773](https://github.com/NVIDIA-NeMo/Guardrails/issues/1773))
- *(llm)* Share OpenAI reasoning-model classifier across adapters ([#1836](https://github.com/NVIDIA-NeMo/Guardrails/issues/1836))
- *(llm)* Reorganize llm package into clients/models/frameworks ([#1801](https://github.com/NVIDIA-NeMo/Guardrails/issues/1801))
- *(llm/clients)* Return HTTPResponse(body, headers, status_code) from_apost ([#1830](https://github.com/NVIDIA-NeMo/Guardrails/issues/1830))
- *(llm/default_framework)* Split reset() into aclose() + clear_providers() ([#1829](https://github.com/NVIDIA-NeMo/Guardrails/issues/1829))
- *(tests)* Framework-agnostic test infrastructure ([#1790](https://github.com/NVIDIA-NeMo/Guardrails/issues/1790))
- *(deps)* Make server-only dependencies optional ([#1689](https://github.com/NVIDIA-NeMo/Guardrails/issues/1689))
- *(jailbreak)* Use onnx instead of pickle to load model ([#1715](https://github.com/NVIDIA-NeMo/Guardrails/issues/1715))
- *(logging)* Remove LangChain LoggingCallbackHandler dependency ([#1616](https://github.com/NVIDIA-NeMo/Guardrails/issues/1616))

### 📚 Documentation

- Document release notes for 0.21 and additional details ([#1726](https://github.com/NVIDIA-NeMo/Guardrails/issues/1726))
- *(middleware)* Fix incorrect example query and expected output in agent-middleware guide ([#1784](https://github.com/NVIDIA-NeMo/Guardrails/issues/1784))
- *(iorails)* OTEL Logging page ([#1807](https://github.com/NVIDIA-NeMo/Guardrails/issues/1807))
- Fix jira 407 ([#1809](https://github.com/NVIDIA-NeMo/Guardrails/issues/1809))
- Update README ([#1820](https://github.com/NVIDIA-NeMo/Guardrails/issues/1820))
- Mark LangChain integration as opt-in in 0.22 entry-point docs ([#1856](https://github.com/NVIDIA-NeMo/Guardrails/issues/1856))
- Documentation for langchain decoupling ([#1854](https://github.com/NVIDIA-NeMo/Guardrails/issues/1854))
- *(configure-rails)* Align with 0.22 DefaultFramework / LangChain split ([#1855](https://github.com/NVIDIA-NeMo/Guardrails/issues/1855))
- *(custom-initialization)* Add customLLM and customFramework guides ([#1857](https://github.com/NVIDIA-NeMo/Guardrails/issues/1857))
- *(examples)* Align example configs and deployment docs with 0.22 DefaultFramework / LangChain split ([#1858](https://github.com/NVIDIA-NeMo/Guardrails/issues/1858))
- *(iorails)* IORails OTEL Metrics ([#1864](https://github.com/NVIDIA-NeMo/Guardrails/issues/1864))
- *(iorails)* Speculative Generation ([#1876](https://github.com/NVIDIA-NeMo/Guardrails/issues/1876))
- *(migration)* Explain the "No default base_url" config-load error ([#1881](https://github.com/NVIDIA-NeMo/Guardrails/issues/1881))
- *(iorails)* Use Guardrails entry-point not IORails ([#1892](https://github.com/NVIDIA-NeMo/Guardrails/issues/1892))
- Prometheus client install instructions ([#1894](https://github.com/NVIDIA-NeMo/Guardrails/issues/1894))
- *(guardrails)* Document max_tokens fallback and reasoning model guidance ([#1833](https://github.com/NVIDIA-NeMo/Guardrails/issues/1833))
- *(colang-1)* Fix Hello World tutorial issues (NGUARD-666) ([#1834](https://github.com/NVIDIA-NeMo/Guardrails/issues/1834))
- *(telemetry)* Document anonymous usage reporting ([#1891](https://github.com/NVIDIA-NeMo/Guardrails/issues/1891))
- Add prompts.yml to code snippets ([#1904](https://github.com/NVIDIA-NeMo/Guardrails/issues/1904))
- Update Benchmark README with updated configs ([#1905](https://github.com/NVIDIA-NeMo/Guardrails/issues/1905))

### 🧪 Testing

- *(llm)* Probe OpenAI API to validate _is_openai_reasoning_model ([#1814](https://github.com/NVIDIA-NeMo/Guardrails/issues/1814))
- *(llm)* Expand reasoning-model param probe + regenerate baseline ([#1838](https://github.com/NVIDIA-NeMo/Guardrails/issues/1838))
- *(telemetry)* Add smoke driver and fixtures  ([#1879](https://github.com/NVIDIA-NeMo/Guardrails/issues/1879))

### ⚙️ Miscellaneous Tasks

- Restore original 2023-2026 copyright dates on moved files ([#1831](https://github.com/NVIDIA-NeMo/Guardrails/issues/1831))
- Include scripts in docker image ([#1902](https://github.com/NVIDIA-NeMo/Guardrails/issues/1902))

## [0.21.0] - 2026-03-12

### 🚀 Features

- *(library)* Update Trend Micro Vision One AI Guard official endpoint ([#1546](https://github.com/NVIDIA-NeMo/Guardrails/issues/1546))
- *(llmrails)* Add check_async method for input/output rails validation ([#1605](https://github.com/NVIDIA-NeMo/Guardrails/issues/1605))
- *(server)* Make guardrails server OpenAI compatible ([#1340](https://github.com/NVIDIA-NeMo/Guardrails/issues/1340))
- New top-level scaffold ([#1613](https://github.com/NVIDIA-NeMo/Guardrails/issues/1613))
- Add Async work queue ([#1620](https://github.com/NVIDIA-NeMo/Guardrails/issues/1620))
- *(integration)* Add GuardrailsMiddleware for LangChain agent ([#1606](https://github.com/NVIDIA-NeMo/Guardrails/issues/1606))
- *(library)* Update Fiddler Guardrails API to match new specification ([#1619](https://github.com/NVIDIA-NeMo/Guardrails/issues/1619))
- *(library)* Add CrowdStrike AIDR community integration ([#1601](https://github.com/NVIDIA-NeMo/Guardrails/issues/1601))
- *(iorails)* Introduce IORails optimized Input/Output rail engine. Supports non-streaming parallel nemoguard input/output rails (content-safety, topic-safety, jailbreak detection) ([#1638](https://github.com/NVIDIA-NeMo/Guardrails/issues/1638), [#1649](https://github.com/NVIDIA-NeMo/Guardrails/issues/1649), [#1654](https://github.com/NVIDIA-NeMo/Guardrails/issues/1654), [#1656](https://github.com/NVIDIA-NeMo/Guardrails/issues/1656), [#1658](https://github.com/NVIDIA-NeMo/Guardrails/issues/1658), [#1660](https://github.com/NVIDIA-NeMo/Guardrails/issues/1660), [#1661](https://github.com/NVIDIA-NeMo/Guardrails/issues/1661), [#1674](https://github.com/NVIDIA-NeMo/Guardrails/issues/1674))
- *(server)* Add OpenAI compatible v1/models endpoint ([#1637](https://github.com/NVIDIA-NeMo/Guardrails/issues/1637))
- *(benchmark)* Add Locust stress-test ([#1629](https://github.com/NVIDIA-NeMo/Guardrails/issues/1629))
- *(jailbreak)* Validate Jailbreak Detection config at create-time ([#1675](https://github.com/NVIDIA-NeMo/Guardrails/issues/1675))
- *(library)* Add PolicyAI Integration for Content Moderation ([#1576](https://github.com/NVIDIA-NeMo/Guardrails/issues/1576))

### 🐛 Bug Fixes

- *(server)* Make openai an optional server-only dependency ([#1623](https://github.com/NVIDIA-NeMo/Guardrails/issues/1623))
- *(actions)* Rename generate_next_step to generate_next_steps for task-specific LLM support ([#1603](https://github.com/NVIDIA-NeMo/Guardrails/issues/1603))
- *(library)* Add `valid` alias to action results in GuardrailsAI integration ([#1578](https://github.com/NVIDIA-NeMo/Guardrails/issues/1578)) ([#1611](https://github.com/NVIDIA-NeMo/Guardrails/issues/1611))
- *(llm)* Filter stop parameter for OpenAI reasoning models ([#1653](https://github.com/NVIDIA-NeMo/Guardrails/issues/1653))
- *(logging)* Show cache hits in Stats log and fix duplicate metadata restore ([#1666](https://github.com/NVIDIA-NeMo/Guardrails/issues/1666))
- *(cache)* Make cache stats log visible in verbose mode ([#1667](https://github.com/NVIDIA-NeMo/Guardrails/issues/1667))
- *(library)* Use bot refuse to respond in gliner PII detection flows ([#1671](https://github.com/NVIDIA-NeMo/Guardrails/issues/1671))
- *(streaming)* Handle None stop tokens in streaming handler ([#1685](https://github.com/NVIDIA-NeMo/Guardrails/issues/1685))
- *(streaming)* Handle dict chunks in RollingBuffer.format_chunks ([#1687](https://github.com/NVIDIA-NeMo/Guardrails/issues/1687))
- *(middleware)* Handle MODIFIED status in GuardrailsMiddleware instead of silently dropping it ([#1714](https://github.com/NVIDIA-NeMo/Guardrails/issues/1714))

### 🚜 Refactor

- *(streaming)* Remove LangChain callback dependencies from StreamingHandler ([#1547](https://github.com/NVIDIA-NeMo/Guardrails/issues/1547))
- *(streaming)* Remove ChatNVIDIA streaming patch ([#1607](https://github.com/NVIDIA-NeMo/Guardrails/issues/1607))
- *(streaming)* [**breaking**] Remove stream_usage and fix streaming metadata capture ([#1624](https://github.com/NVIDIA-NeMo/Guardrails/issues/1624))

### ⚡ Performance

- *(actions)* Lazy initialization of embedding indexes ([#1572](https://github.com/NVIDIA-NeMo/Guardrails/issues/1572))

### ⚙️ Miscellaneous Tasks

- Update Pangea User-Agent repo URL ([#1595](https://github.com/NVIDIA-NeMo/Guardrails/issues/1595)) ([#1610](https://github.com/NVIDIA-NeMo/Guardrails/issues/1610))
- *(jailbreak)* Update dependencies for jailbreak detection docker container. ([#1596](https://github.com/NVIDIA-NeMo/Guardrails/issues/1596))
- Remove multi_kb example ([#1673](https://github.com/NVIDIA-NeMo/Guardrails/issues/1673))
- *(iorails)* Increase work queue concurrency and depth ([#1674](https://github.com/NVIDIA-NeMo/Guardrails/issues/1674))
- *(docs)* Remove AI Virtual Assistant Blueprint notebook ([#1682](https://github.com/NVIDIA-NeMo/Guardrails/issues/1682))
- Update dependencies ahead of v0.21 release ([#1617](https://github.com/NVIDIA-NeMo/Guardrails/issues/1617))

## [0.20.0] - 2026-01-22

### 🚀 Features

- *(llm)* Propagate model and base URL in LLMCallException; improve error handling ([#1502](https://github.com/NVIDIA-NeMo/Guardrails/issues/1502))
- *(content_safety)* Add support to auto select multilingual refusal bot messages ([#1530](https://github.com/NVIDIA-NeMo/Guardrails/issues/1530))
- *(library)* Adding GLiNER for PII detection (open alternative to PrivateAI) ([#1545](https://github.com/NVIDIA-NeMo/Guardrails/issues/1545))
- *(benchmark)* Implement Mock LLM streaming ([#1564](https://github.com/NVIDIA-NeMo/Guardrails/issues/1564))
- *(library)* Add reasoning guardrail connector ([#1565](https://github.com/NVIDIA-NeMo/Guardrails/issues/1565))

### 🐛 Bug Fixes

- *(models)* Surface relevant exception when initializing langchain model ([#1516](https://github.com/NVIDIA-NeMo/Guardrails/issues/1516))
- *(llm)* Filter temperature parameter for OpenAI reasoning models ([#1526](https://github.com/NVIDIA-NeMo/Guardrails/issues/1526))
- *(bot-thinking)* Tackle bug with reasoning trace leak across llm calls ([#1582](https://github.com/NVIDIA-NeMo/Guardrails/issues/1582))
- *(providers)* Handle langchain 1.2.1 dict type for _SUPPORTED_PROVIDERS ([#1589](https://github.com/NVIDIA-NeMo/Guardrails/issues/1589))

### 🚜 Refactor

- *(streaming)* [**breaking**] Drop streaming field from config ([#1538](https://github.com/NVIDIA-NeMo/Guardrails/issues/1538))

### ⚙️ Miscellaneous Tasks

- *(test)* Reduce default pytest log level from DEBUG to WARNING ([#1523](https://github.com/NVIDIA-NeMo/Guardrails/issues/1523))
- *(docker)* Upgrade to Python 3.12-slim base image ([#1522](https://github.com/NVIDIA-NeMo/Guardrails/issues/1522))
- Run pre-commits to update license date for 2026 ([#1562](https://github.com/NVIDIA-NeMo/Guardrails/issues/1562))
- Move Benchmark code to top-level ([#1559](https://github.com/NVIDIA-NeMo/Guardrails/issues/1559))
- Update repo to <https://github.com/NVIDIA-NeMo/Guardrails> ([#1594](https://github.com/NVIDIA-NeMo/Guardrails/issues/1594))

## [0.19.0] - 2025-12-03

### 🚀 Features

- Support langchain v1 ([#1472](https://github.com/NVIDIA-NeMo/Guardrails/issues/1472))
- *(llm)* Add LangChain 1.x content blocks support for reasoning and tool calls ([#1496](https://github.com/NVIDIA-NeMo/Guardrails/issues/1496))
- *(benchmark)* Add Procfile to run Guardrails and mock LLMs ([#1490](https://github.com/NVIDIA-NeMo/Guardrails/issues/1490))
- *(benchmark)*: Add AIPerf run script (([#1501](https://github.com/NVIDIA-NeMo/Guardrails/issues/1501)))

### 🐛 Bug Fixes

- *(llm)* Add async streaming support to ChatNVIDIA provider patch ([#1504](https://github.com/NVIDIA-NeMo/Guardrails/issues/1504))
- ensure stream_async background task completes before exit ([#1508](https://github.com/NVIDIA-NeMo/Guardrails/issues/1508))
- *(cli)* Fix TypeError in v2.x chat due to incorrect State/dict conversion ([#1509](https://github.com/NVIDIA-NeMo/Guardrails/issues/1509))
- *(llmrails)*: skip output rails when dialog disabled and no bot_message provided ([#1518](https://github.com/NVIDIA-NeMo/Guardrails/issues/1518))
- *(llm)*: ensure that stop token is not ignored if llm_params is None ([#1529](https://github.com/NVIDIA-NeMo/Guardrails/issues/1529))

### ⚙️ Miscellaneous Tasks

- *(llm)* Remove deprecated llm_params module ([#1475](https://github.com/NVIDIA-NeMo/Guardrails/issues/1475))

### ◀️ Revert

- *(llm)* Remove custom HTTP headers patch now in langchain-nvidia-ai-endpoints v0.3.19 ([#1503](https://github.com/NVIDIA-NeMo/Guardrails/issues/1503))

## [0.18.0] - 2025-11-06

### 🚀 Features

- *(bot-thinking)* Implement BotThinking events to process reasoning traces in Guardrails ([#1431](https://github.com/NVIDIA-NeMo/Guardrails/issues/1431)), ([#1432](https://github.com/NVIDIA-NeMo/Guardrails/issues/1432)), ([#1434](https://github.com/NVIDIA-NeMo/Guardrails/issues/1434)).
- *(embeddings)* Add Azure OpenAI embedding provider ([#702](https://github.com/NVIDIA-NeMo/Guardrails/issues/702)).
- *(embeddings)* Add Cohere embedding integration ([#1305](https://github.com/NVIDIA-NeMo/Guardrails/issues/1305)).
- *(embeddings)* Add Google embedding integration ([#1304](https://github.com/NVIDIA-NeMo/Guardrails/issues/1304)).
- *(library)* Add Cisco AI Defense integration ([#1433](https://github.com/NVIDIA-NeMo/Guardrails/issues/1433)).
- *(cache)* Add in-memory LFU caches for content-safety, topic-control, and jailbreak detection models ([#1436](https://github.com/NVIDIA-NeMo/Guardrails/issues/1436)), ([#1456](https://github.com/NVIDIA-NeMo/Guardrails/issues/1456)),  ([#1457](https://github.com/NVIDIA-NeMo/Guardrails/issues/1457)), ([#1458](https://github.com/NVIDIA-NeMo/Guardrails/issues/1458)).
- *(llm)* Add automatic provider inference for LangChain LLMs ([#1460](https://github.com/NVIDIA-NeMo/Guardrails/issues/1460)).
- *(llm)* Add custom HTTP headers support to ChatNVIDIA provider ([#1461](https://github.com/NVIDIA-NeMo/Guardrails/issues/1461)).

### 🐛 Bug Fixes

- *(config)* Validate content safety and topic control configs at creation time ([#1450](https://github.com/NVIDIA-NeMo/Guardrails/issues/1450)).
- *(jailbreak)* Capitalization of `Snowflake` in use of `snowflake-arctic-embed-m-long` name. ([#1464](https://github.com/NVIDIA-NeMo/Guardrails/issues/1464)).
- *(runtime)* Ensure stop flag is set for policy violations in parallel rails ([#1467](https://github.com/NVIDIA-NeMo/Guardrails/issues/1467)).
- *(llm)* [**breaking**] Extract reasoning traces to separate field instead of prepending ([#1468](https://github.com/NVIDIA-NeMo/Guardrails/issues/1468)).
- *(streaming)* [**breaking**] Raise error when stream_async used with disabled output rails streaming ([#1470](https://github.com/NVIDIA-NeMo/Guardrails/issues/1470)).
- *(llm)* Add fallback extraction for reasoning traces from <think> tags ([#1474](https://github.com/NVIDIA-NeMo/Guardrails/issues/1474)).
- *(runtime)* Set stop flag for exception-based rails in parallel mode ([#1487](https://github.com/NVIDIA-NeMo/Guardrails/issues/1487)).

### 🚜 Refactor

- [**breaking**] Replace reasoning trace extraction with LangChain additional_kwargs ([#1427](https://github.com/NVIDIA-NeMo/Guardrails/issues/1427))

### 📚 Documentation

- *(examples)* Add Nemoguard in-memory cache configuration example ([#1459](https://github.com/NVIDIA-NeMo/Guardrails/issues/1459)), ([#1480](https://github.com/NVIDIA-NeMo/Guardrails/issues/1480)).
- Add guide for bot reasoning guardrails ([#1479](https://github.com/NVIDIA-NeMo/Guardrails/issues/1479)).
- Update LLM reasoning traces configuration ([#1483](https://github.com/NVIDIA-NeMo/Guardrails/issues/1483)).

### 🧪 Testing

- Add mock embedding provider tests ([#1446](https://github.com/NVIDIA-NeMo/Guardrails/issues/1446))
- *(cli)* Add comprehensive CLI test suite and reorganize files ([#1339](https://github.com/NVIDIA-NeMo/Guardrails/issues/1339))
- Skip FastEmbed tests when not in live mode ([#1462](https://github.com/NVIDIA-NeMo/Guardrails/issues/1462))
- Fix flaky stats logging interval timing test ([#1463](https://github.com/NVIDIA-NeMo/Guardrails/issues/1463))
- Restore test that was skipped due to Colang 2.0 serialization issue ([#1449](https://github.com/NVIDIA-NeMo/Guardrails/issues/1449))

### ⚙️ Miscellaneous Tasks

- Resolve PyPI publish workflow trigger and reliability issues ([#1443](https://github.com/NVIDIA-NeMo/Guardrails/issues/1443))
- Fix sparse checkout for publish pypi workflow ([#1444](https://github.com/NVIDIA-NeMo/Guardrails/issues/1444))
- Drop Python 3.9 support ahead of October 2025 EOL ([#1426](https://github.com/NVIDIA-NeMo/Guardrails/issues/1426))
- *(types)* Add type-annotations and pre-commit checks for tracing ([#1388](https://github.com/NVIDIA-NeMo/Guardrails/issues/1388)), logging ([#1395](https://github.com/NVIDIA-NeMo/Guardrails/issues/1395)), kb  ([#1385](https://github.com/NVIDIA-NeMo/Guardrails/issues/1385)), cli ([#1380](https://github.com/NVIDIA-NeMo/Guardrails/issues/1380)), embeddings ([#1383](https://github.com/NVIDIA-NeMo/Guardrails/issues/1383)), server ([#1397](https://github.com/NVIDIA-NeMo/Guardrails/issues/1397)), and llm ([#1394](https://github.com/NVIDIA-NeMo/Guardrails/issues/1394)) code.
- Update insert licenser pe-commit-hooks to use current year ([#1452](https://github.com/NVIDIA-NeMo/Guardrails/issues/1452)).
- *(library)* Remove unused vllm requirements.txt files ([#1466](https://github.com/NVIDIA-NeMo/Guardrails/issues/1466)).

## [0.17.0] - 2025-10-09

### 🚀 Features

- *(tool-calling)* Add tool call passthrough support in LLMRails ([#1364](https://github.com/NVIDIA-NeMo/Guardrails/issues/1364))
- *(runnable-rails)* Complete rewrite of RunnableRails with full LangChain Runnable protocol support ([#1366](https://github.com/NVIDIA-NeMo/Guardrails/issues/1366), [#1369](https://github.com/NVIDIA-NeMo/Guardrails/issues/1369), [#1370](https://github.com/NVIDIA-NeMo/Guardrails/issues/1370), [#1405](https://github.com/NVIDIA-NeMo/Guardrails/issues/1405))
- *(tool-rails)* Add support for tool output rails and validation ([#1382](https://github.com/NVIDIA-NeMo/Guardrails/issues/1382))
- *(tool-rails)* Implement tool input rails for tool message validation and processing ([#1386](https://github.com/NVIDIA-NeMo/Guardrails/issues/1386))
- *(library)* Add Trend Micro Vision One AI Application Security community integration ([#1355](https://github.com/NVIDIA-NeMo/Guardrails/issues/1355))
- *(llm)* Pass llm params directly ([#1387](https://github.com/NVIDIA-NeMo/Guardrails/issues/1387))

### 🐛 Bug Fixes

- *(jailbreak)* Handle URL joining with/without trailing slashes ([#1346](https://github.com/NVIDIA-NeMo/Guardrails/issues/1346))
- *(logging)* Handle missing id and task in verbose logs ([#1343](https://github.com/NVIDIA-NeMo/Guardrails/issues/1343))
- *(library)* Fix import package declaration to new cleanlab-tlm name ([#1401](https://github.com/NVIDIA-NeMo/Guardrails/issues/1401))
- *(logging)* Add "Tool" type to message sender labeling ([#1412](https://github.com/NVIDIA-NeMo/Guardrails/issues/1412))
- *(logging)* Correct message type formatting in logs ([#1416](https://github.com/NVIDIA-NeMo/Guardrails/issues/1416))

### 🚜 Refactor

- *(llm)* Remove LLMs isolation for actions ([#1408](https://github.com/NVIDIA-NeMo/Guardrails/issues/1408))

### 📚 Documentation

- *(examples)* Add NeMoGuard safety rails config example for Colang 1.0 ([#1365](https://github.com/NVIDIA-NeMo/Guardrails/issues/1365))
- Add hardware reqs ([#1411](https://github.com/NVIDIA-NeMo/Guardrails/issues/1411))
- Add tools integration guide ([#1414](https://github.com/NVIDIA-NeMo/Guardrails/issues/1414))
- *(langgraph)* Add integration guide for LangGraph ([#1422](https://github.com/NVIDIA-NeMo/Guardrails/issues/1422))
- *(langchain)* Update with full support and add tool calling guide … ([#1419](https://github.com/NVIDIA-NeMo/Guardrails/issues/1419))
- *(langgraph)* Clarify tool examples and replace calculate_math with multiply ([#1439](https://github.com/NVIDIA-NeMo/Guardrails/issues/1439))

### ⚙️ Miscellaneous Tasks

- *(docs)* Update v0.16.0 release date in changelog ([#1377](https://github.com/NVIDIA-NeMo/Guardrails/issues/1377))
- *(docs)* Add link to demo.py script in Getting-Started section ([#1399](https://github.com/NVIDIA-NeMo/Guardrails/issues/1399))
- *(types)* Type-clean rails (86 errors) ([#1396](https://github.com/NVIDIA-NeMo/Guardrails/issues/1396))
- *(jailbreak-detection)* Update transformers and torch ([#1417](https://github.com/NVIDIA-NeMo/Guardrails/issues/1417))
- *(types)* Type-clean /actions (189 errors) ([#1361](https://github.com/NVIDIA-NeMo/Guardrails/issues/1361))
- *(docs)* Update repository owner ([#1425](https://github.com/NVIDIA-NeMo/Guardrails/issues/1425))

## [0.16.0] - 2025-09-05

### 🚀 Features

- *(llmrails)* Support method chaining by returning self from LLMRails.register_* methods ([#1296](https://github.com/NVIDIA-NeMo/Guardrails/issues/1296))
- Add Pangea AI Guard community integration ([#1300](https://github.com/NVIDIA-NeMo/Guardrails/issues/1300))
- *(llmrails)* Isolate LLMs only for configured actions ([#1342](https://github.com/NVIDIA-NeMo/Guardrails/issues/1342))
- Enhance tracing system with OpenTelemetry semantic conventions ([#1331](https://github.com/NVIDIA-NeMo/Guardrails/issues/1331))
- Add GuardrailsAI community integration ([#1298](https://github.com/NVIDIA-NeMo/Guardrails/issues/1298))

### 🐛 Bug Fixes

- *(models)* Suppress langchain_nvidia_ai_endpoints warnings ([#1371](https://github.com/NVIDIA-NeMo/Guardrails/issues/1371))
- *(tracing)* Respect the user-provided log options regardless of tracing configuration
- *(config)* Ensure adding RailsConfig objects handles None values ([#1328](https://github.com/NVIDIA-NeMo/Guardrails/issues/1328))
- *(config)* Add handling for config directory with `.yml`/`.yaml` extension ([#1293](https://github.com/NVIDIA-NeMo/Guardrails/issues/1293))
- *(colang)* Apply guardrails transformations to LLM inputs and bot outputs. ([#1297](https://github.com/NVIDIA-NeMo/Guardrails/issues/1297))
- *(topic_safety)* Handle InternalEvent objects in topic safety actions for Colang 2.0 ([#1335](https://github.com/NVIDIA-NeMo/Guardrails/issues/1335))
- *(prompts)* Prevent IndexError when LLM provided via constructor with empty models config ([#1334](https://github.com/NVIDIA-NeMo/Guardrails/issues/1334))
- *(llmrails)* Handle LLM models without model_kwargs field in isolation ([#1336](https://github.com/NVIDIA-NeMo/Guardrails/issues/1336))
- *(llmrails)* Move LLM isolation setup to after KB initialization ([#1348](https://github.com/NVIDIA-NeMo/Guardrails/issues/1348))

### 🚜 Refactor

- *(llm)* Move get_action_details_from_flow_id from llmrails.py to utils.py ([#1341](https://github.com/NVIDIA-NeMo/Guardrails/issues/1341))

### 📚 Documentation

- Integrate with multilingual NIM ([#1354](https://github.com/NVIDIA-NeMo/Guardrails/issues/1354))
- *(tracing)* Update tracing notebooks with VDR feedback ([#1376](https://github.com/NVIDIA-NeMo/Guardrails/issues/1376))
- Add kv cache reuse documentation ([#1330](https://github.com/NVIDIA-NeMo/Guardrails/issues/1330))
- *(examples)* Add Colang 2.0 example for sensitive data detection ([#1301](https://github.com/NVIDIA-NeMo/Guardrails/issues/1301))
- Add extra slash to jailbreak detect nim_base_url([#1345](https://github.com/NVIDIA-NeMo/Guardrails/issues/1345))
- Add tracing notebook ([#1337](https://github.com/NVIDIA-NeMo/Guardrails/issues/1337))
- Jaeger tracing notebook ([#1353](https://github.com/NVIDIA-NeMo/Guardrails/issues/1353))
- *(examples)* Add NeMoGuard rails config for colang 2 ([#1289](https://github.com/NVIDIA-NeMo/Guardrails/issues/1289))
- *(tracing)* Add OpenTelemetry span format guide ([#1350](https://github.com/NVIDIA-NeMo/Guardrails/issues/1350))
- Add GuardrailsAI integration user guide and example ([#1357](https://github.com/NVIDIA-NeMo/Guardrails/issues/1357))

### 🧪 Testing

- *(jailbreak)* Add missing pytest.mark.asyncio decorators ([#1352](https://github.com/NVIDIA-NeMo/Guardrails/issues/1352))

### ⚙️ Miscellaneous Tasks

- *(docs)* Rename test_csl.py to csl.py ([#1347](https://github.com/NVIDIA-NeMo/Guardrails/issues/1347))

## [0.15.0] - 2025-08-08

### 🚀 Features

- *(tracing)* [**breaking**] Update tracing to use otel api ([#1269](https://github.com/NVIDIA-NeMo/Guardrails/issues/1269))
- *(streaming)* Implement parallel streaming output rails execution ([#1263](https://github.com/NVIDIA-NeMo/Guardrails/issues/1263), [#1324](https://github.com/NVIDIA-NeMo/Guardrails/pull/1324))
- *(streaming)* Support external async token generators ([#1286](https://github.com/NVIDIA-NeMo/Guardrails/issues/1286))
- Support parallel rails execution ([#1234](https://github.com/NVIDIA-NeMo/Guardrails/issues/1234), [#1323](https://github.com/NVIDIA-NeMo/Guardrails/pull/1323))

### 🐛 Bug Fixes

- *(streaming)* Resolve word concatenation in streaming output rails ([#1259](https://github.com/NVIDIA-NeMo/Guardrails/issues/1259))
- *(streaming)* Enable token usage tracking for streaming LLM calls ([#1264](https://github.com/NVIDIA-NeMo/Guardrails/issues/1264), [#1285](https://github.com/NVIDIA-NeMo/Guardrails/issues/1285))
- *(tracing)* Prevent mutation of user options when tracing is enabled ([#1273](https://github.com/NVIDIA-NeMo/Guardrails/issues/1273))
- *(rails)* Prevent LLM parameter contamination in rails ([#1306](https://github.com/NVIDIA-NeMo/Guardrails/issues/1306))

### 📚 Documentation

- Release notes 0.14.1 ([#1272](https://github.com/NVIDIA-NeMo/Guardrails/issues/1272))
- Update guardrails-library.md to include Clavata as a third party API ([#1294](https://github.com/NVIDIA-NeMo/Guardrails/issues/1294))
- *(streaming)* Add section on token usage tracking ([#1282](https://github.com/NVIDIA-NeMo/Guardrails/issues/1282))
- Add parallel rail section and split config page ([#1295](https://github.com/NVIDIA-NeMo/Guardrails/issues/1295))
- Show complete prompts.yml content in getting started tutorial ([#1311](https://github.com/NVIDIA-NeMo/Guardrails/issues/1311))
- *(tracing)* Update and streamline tracing guide ([#1307](https://github.com/NVIDIA-NeMo/Guardrails/issues/1307))

### ⚙️ Miscellaneous Tasks

- *(dependabot)* Remove dependabot configuration ([#1281](https://github.com/NVIDIA-NeMo/Guardrails/issues/1281))
- *(CI)* Add release workflow ([#1309](https://github.com/NVIDIA-NeMo/Guardrails/issues/1309), [#1318](https://github.com/NVIDIA-NeMo/Guardrails/issues/1318))

## [0.14.1] - 2025-07-02

### 🚀 Features

- *(jailbreak)* Add direct API key configuration support ([#1260](https://github.com/NVIDIA-NeMo/Guardrails/issues/1260))

### 🐛 Bug Fixes

- *(jailbreak)* Lazy load jailbreak detection dependencies ([#1223](https://github.com/NVIDIA-NeMo/Guardrails/issues/1223),)
- *(llmrails)* Constructor LLM should not skip loading other config models ([#1221](https://github.com/NVIDIA-NeMo/Guardrails/issues/1221), [#1247](https://github.com/NVIDIA-NeMo/Guardrails/issues/1247), [#1250](https://github.com/NVIDIA-NeMo/Guardrails/issues/1250), [#1258](https://github.com/NVIDIA-NeMo/Guardrails/issues/1258))
- *(content_safety)* Replace try-except with iterable unpacking for policy violations ([#1207](https://github.com/NVIDIA-NeMo/Guardrails/issues/1207))
- *(jailbreak)* Pin numpy==1.23.5 for scikit-learn compatibility ([#1249](https://github.com/NVIDIA-NeMo/Guardrails/issues/1249))
- *(output_parsers)* Iterable unpacking compatibility in content safety parsers ([#1242](https://github.com/NVIDIA-NeMo/Guardrails/issues/1242))

### 📚 Documentation

- More heading levels so RNs resolve links ([#1228](https://github.com/NVIDIA-NeMo/Guardrails/issues/1228))
- Update docs version ([#1219](https://github.com/NVIDIA-NeMo/Guardrails/issues/1219))
- Fix jailbreak detection build instructions ([#1248](https://github.com/NVIDIA-NeMo/Guardrails/issues/1248))
- Change ABC bot link at docs ([#1261](https://github.com/NVIDIA-NeMo/Guardrails/issues/1261))

### 🧪 Testing

- Fix async test failures in cache embeddings and buffer strategy tests ([#1237](https://github.com/NVIDIA-NeMo/Guardrails/issues/1237))
- *(content_safety)* Add tests for content safety actions ([#1240](https://github.com/NVIDIA-NeMo/Guardrails/issues/1240))

### ⚙️ Miscellaneous Tasks

- Update pre-commit-hooks to v5.0.0 ([#1238](https://github.com/NVIDIA-NeMo/Guardrails/issues/1238))

## [0.14.0] - 2025-05-28

### 🚀 Features

- Change topic following prompt to allow chitchat ([#1097](https://github.com/NVIDIA-NeMo/Guardrails/issues/1097))
- Validate model name configuration ([#1084](https://github.com/NVIDIA-NeMo/Guardrails/issues/1084))
- Add support for langchain partner and community chat models ([#1085](https://github.com/NVIDIA-NeMo/Guardrails/issues/1085))
- Add fuzzy find provider capability to cli ([#1088](https://github.com/NVIDIA-NeMo/Guardrails/issues/1088))
- Add code injection detection to guardrails library ([#1091](https://github.com/NVIDIA-NeMo/Guardrails/issues/1091))
- Add clavata community integration ([#1027](https://github.com/NVIDIA-NeMo/Guardrails/issues/1027))
- Implement validation to forbid dialog rails with reasoning traces ([#1137](https://github.com/NVIDIA-NeMo/Guardrails/issues/1137))
- Load yara lazily to avoid action dispatcher error ([#1162](https://github.com/NVIDIA-NeMo/Guardrails/issues/1162))
- Add support for system messages to RunnableRails ([#1106](https://github.com/NVIDIA-NeMo/Guardrails/issues/1106))
- Add api_key_env_var to Model, pass in kwargs to langchain initializer ([#1142](https://github.com/NVIDIA-NeMo/Guardrails/issues/1142))
- Add inline YARA rules support ([#1164](https://github.com/NVIDIA-NeMo/Guardrails/issues/1164))
- [**breaking**] Add support for preserving and optionally applying guardrails to reasoning traces ([#1145](https://github.com/NVIDIA-NeMo/Guardrails/issues/1145))
- Prevent reasoning traces from contaminating LLM prompt history ([#1169](https://github.com/NVIDIA-NeMo/Guardrails/issues/1169))
- Add RailException support to injection detection and improve error handling ([#1178](https://github.com/NVIDIA-NeMo/Guardrails/issues/1178))
- Add Nemotron model support with message-based prompts ([#1199](https://github.com/NVIDIA-NeMo/Guardrails/issues/1199))

### 🐛 Bug Fixes

- Correct task name for self_check_facts ([#1040](https://github.com/NVIDIA-NeMo/Guardrails/issues/1040))
- Error in LLMRails with tracing enabled ([#1103](https://github.com/NVIDIA-NeMo/Guardrails/issues/1103))
- Self check output colang 1 flow ([#1126](https://github.com/NVIDIA-NeMo/Guardrails/issues/1126))
- Use ValueError in TaskPrompt to resolve TypeError raised by Pydantic ([#1132](https://github.com/NVIDIA-NeMo/Guardrails/issues/1132))
- Correct dialog rails activation logic ([#1161](https://github.com/NVIDIA-NeMo/Guardrails/issues/1161))
- Allow reasoning traces when embeddings_only is True ([#1170](https://github.com/NVIDIA-NeMo/Guardrails/issues/1170))
- Prevent explain_info overwrite during stream_async ([#1194](https://github.com/NVIDIA-NeMo/Guardrails/issues/1194))
- Colang 2 issues in community integrations ([#1140](https://github.com/NVIDIA-NeMo/Guardrails/issues/1140))
- Ensure proper asyncio task cleanup in test_streaming_handler.py ([#1182](https://github.com/NVIDIA-NeMo/Guardrails/issues/1182))

### 🚜 Refactor

- Reorganize HuggingFace provider structure ([#1083](https://github.com/NVIDIA-NeMo/Guardrails/issues/1083))
- Remove support for deprecated nemollm engine ([#1076](https://github.com/NVIDIA-NeMo/Guardrails/issues/1076))
- [**breaking**] Remove deprecated return_context argument ([#1147](https://github.com/NVIDIA-NeMo/Guardrails/issues/1147))
- Rename `remove_thinking_traces` field to `remove_reasoning_traces` ([#1176](https://github.com/NVIDIA-NeMo/Guardrails/issues/1176))
- Update deprecated field handling  for remove_thinking_traces ([#1196](https://github.com/NVIDIA-NeMo/Guardrails/issues/1196))
- Introduce END_OF_STREAM sentinel and update handling ([#1185](https://github.com/NVIDIA-NeMo/Guardrails/issues/1185))

### 📚 Documentation

- Remove markup from code block ([#1081](https://github.com/NVIDIA-NeMo/Guardrails/issues/1081))
- Replace img tag with Markdown images ([#1087](https://github.com/NVIDIA-NeMo/Guardrails/issues/1087))
- Remove NeMo Service (nemollm) documentation ([#1077](https://github.com/NVIDIA-NeMo/Guardrails/issues/1077))
- Update cleanlab integration description ([#1080](https://github.com/NVIDIA-NeMo/Guardrails/issues/1080))
- Add providers fuzzy search cli command ([#1089](https://github.com/NVIDIA-NeMo/Guardrails/issues/1089))
- Clarify purpose of model parameters field in configuration guide ([#1181](https://github.com/NVIDIA-NeMo/Guardrails/issues/1181))
- Output rails are supported with streaming ([#1007](https://github.com/NVIDIA-NeMo/Guardrails/issues/1007))
- Add mention of Nemotron ([#1200](https://github.com/NVIDIA-NeMo/Guardrails/issues/1200))
- Fix output rail doc ([#1159](https://github.com/NVIDIA-NeMo/Guardrails/issues/1159))
- Revise GS example in getting started doc ([#1146](https://github.com/NVIDIA-NeMo/Guardrails/issues/1146))
- Possible update to injection detection ([#1144](https://github.com/NVIDIA-NeMo/Guardrails/issues/1144))

### ⚙️ Miscellaneous Tasks

- Dynamically set version using importlib.metadata ([#1072](https://github.com/NVIDIA-NeMo/Guardrails/issues/1072))
- Add link to topic control config and prompts ([#1098](https://github.com/NVIDIA-NeMo/Guardrails/issues/1098))
- Reorganize GitHub workflows for better test coverage ([#1079](https://github.com/NVIDIA-NeMo/Guardrails/issues/1079))
- Add summary jobs for workflow branch protection ([#1120](https://github.com/NVIDIA-NeMo/Guardrails/issues/1120))
- Add Adobe Analytics configuration ([#1138](https://github.com/NVIDIA-NeMo/Guardrails/issues/1138))
- Fix and revert poetry lock to its stable state ([#1133](https://github.com/NVIDIA-NeMo/Guardrails/issues/1133))
- Add Codecov integration to workflows ([#1143](https://github.com/NVIDIA-NeMo/Guardrails/issues/1143))
- Add Python 3.12 and 3.13 test jobs to gitlab workflow ([#1171](https://github.com/NVIDIA-NeMo/Guardrails/issues/1171))
- Identify OS packages to install in contribution guide([#1136](https://github.com/NVIDIA-NeMo/Guardrails/issues/1136))
- Remove Got It AI from ToC in 3rd party docs([#1213](https://github.com/NVIDIA-NeMo/Guardrails/issues/1213))

## [0.13.0] - 2025-03-25

### 🚀 Features

- Support models with reasoning traces ([#996](https://github.com/NVIDIA-NeMo/Guardrails/issues/996))
- Add SHA-256 hashing option ([#988](https://github.com/NVIDIA-NeMo/Guardrails/issues/988))
- Add Fiddler Guardrails integration ([#964](https://github.com/NVIDIA-NeMo/Guardrails/issues/964), [#1043](https://github.com/NVIDIA-NeMo/Guardrails/issues/1043))
- Add generation metadata to streaming chunks ([#1011](https://github.com/NVIDIA-NeMo/Guardrails/issues/1011))
- Improve alpha to beta bot migration ([#878](https://github.com/NVIDIA-NeMo/Guardrails/issues/878))
- Support multimodal input and output rails ([#1033](https://github.com/NVIDIA-NeMo/Guardrails/issues/1033))
- Add support for NemoGuard JailbreakDetect NIM.  ([#1038](https://github.com/NVIDIA-NeMo/Guardrails/issues/1038))
- Set default start and end reasoning tokens ([#1050](https://github.com/NVIDIA-NeMo/Guardrails/issues/1050))
- Improve output rails error handling for SSE format ([#1058](https://github.com/NVIDIA-NeMo/Guardrails/issues/1058))

### 🐛 Bug Fixes

- Ensure parse_task_output is called after all llm_call invocations ([#1047](https://github.com/NVIDIA-NeMo/Guardrails/issues/1047))
- Handle exceptions in generate_events to propagate errors in streaming ([#1012](https://github.com/NVIDIA-NeMo/Guardrails/issues/1012))
- Ensure output rails streaming is enabled explicitly ([#1045](https://github.com/NVIDIA-NeMo/Guardrails/issues/1045))
- Improve multimodal prompt length calculation for base64 images ([#1053](https://github.com/NVIDIA-NeMo/Guardrails/issues/1053))

### 🚜 Refactor

- Move startup and shutdown logic to lifespan in server  ([#999](https://github.com/NVIDIA-NeMo/Guardrails/issues/999))

### 📚 Documentation

- Add multimodal rails documentation ([#1061](https://github.com/NVIDIA-NeMo/Guardrails/issues/1061))
- Add content safety tutorial ([#1042](https://github.com/NVIDIA-NeMo/Guardrails/issues/1042))
- Revise reasoning model info ([#1062](https://github.com/NVIDIA-NeMo/Guardrails/issues/1062))
- Consider new GS experience ([#1005](https://github.com/NVIDIA-NeMo/Guardrails/issues/1005))
- Restore deleted configuration files ([#963](https://github.com/NVIDIA-NeMo/Guardrails/issues/963))

### ⚙️ Miscellaneous Tasks

- Add Python 3.12 support ([#984](https://github.com/NVIDIA-NeMo/Guardrails/issues/984))

## [0.12.0] - 2025-02-26

### 🚀 Features

- Support Output Rails Streaming ([#966](https://github.com/NVIDIA-NeMo/Guardrails/issues/966), [#1003](https://github.com/NVIDIA-NeMo/Guardrails/issues/1003))
- Add unified output mapping for actions ([#965](https://github.com/NVIDIA-NeMo/Guardrails/issues/965))
- Add output rails support to activefence integration ([#940](https://github.com/NVIDIA-NeMo/Guardrails/issues/940))
- Add Prompt Security integration ([#920](https://github.com/NVIDIA-NeMo/Guardrails/issues/920))
- Add pii masking capability to PrivateAI integration ([#901](https://github.com/NVIDIA-NeMo/Guardrails/issues/901))
- Add embedding_params to BasicEmbeddingsIndex ([#898](https://github.com/NVIDIA-NeMo/Guardrails/issues/898))
- Add score threshold to AnalyzerEngine ([#845](https://github.com/NVIDIA-NeMo/Guardrails/issues/845))

### 🐛 Bug Fixes

- Fix dependency resolution issues in AlignScore Dockerfile([#1002](https://github.com/NVIDIA-NeMo/Guardrails/issues/1002), [#982](https://github.com/NVIDIA-NeMo/Guardrails/issues/982))
- Fix JailbreakDetect docker files([#981](https://github.com/NVIDIA-NeMo/Guardrails/issues/981), [#1001](https://github.com/NVIDIA-NeMo/Guardrails/pull/1001))
- Fix TypeError from attempting to unpack already-unpacked dictionary. ([#959](https://github.com/NVIDIA-NeMo/Guardrails/issues/959))
- Fix token stats usage in LLM call info. ([#953](https://github.com/NVIDIA-NeMo/Guardrails/issues/953))
- Handle unescaped quotes in generate_value using safe_eval ([#946](https://github.com/NVIDIA-NeMo/Guardrails/issues/946))
- Handle non-relative file paths ([#897](https://github.com/NVIDIA-NeMo/Guardrails/issues/897))
- Set workdir to models and specify entrypoint explicitly ([#1001](https://github.com/NVIDIA-NeMo/Guardrails/pull/1001)).

### 📚 Documentation

- Output streaming ([#976](https://github.com/NVIDIA-NeMo/Guardrails/issues/976))
- Fix typos with oauthtoken ([#957](https://github.com/NVIDIA-NeMo/Guardrails/issues/957))
- Fix broken link in prompt security ([#978](https://github.com/NVIDIA-NeMo/Guardrails/issues/978))
- Update advanced user guides per v0.11.1 doc release ([#937](https://github.com/NVIDIA-NeMo/Guardrails/issues/937))

### ⚙️ Miscellaneous Tasks

- Tolerate prompt in code blocks ([#1004](https://github.com/NVIDIA-NeMo/Guardrails/issues/1004))
- Update YAML indent to use two spaces ([#1009](https://github.com/NVIDIA-NeMo/Guardrails/issues/1009))

## [0.11.1] - 2025-01-16

### Added

- **ContentSafety**: Add ContentSafety NIM connector ([#930](https://github.com/NVIDIA-NeMo/Guardrails/pull/930)) by @prasoonvarshney
- **TopicControl**: Add TopicControl NIM connector ([#930](https://github.com/NVIDIA-NeMo/Guardrails/pull/930)) by @makeshn
- **JailbreakDetect**: Add jailbreak detection NIM connector ([#930](https://github.com/NVIDIA-NeMo/Guardrails/pull/930)) by @erickgalinkin

## Changed

- **AutoAlign Integration**: Add further enhancements and refactoring to AutoAlign integration ([#867](https://github.com/NVIDIA-NeMo/Guardrails/pull/867)) by @KimiJL

## Fixed

- **PrivateAI Integration**: Fix Incomplete URL substring sanitization Error ([#883](https://github.com/NVIDIA-NeMo/Guardrails/pull/883)) by @NJ-186

## Documentation

- **NVIDIA Blueprint**: Add Safeguarding AI Virtual Assistant NIM Blueprint NemoGuard NIMs ([#932](https://github.com/NVIDIA-NeMo/Guardrails/pull/932)) by @abodhankar

- **ActiveFence Integration**: Fix flow definition in community docs ([#890](https://github.com/NVIDIA-NeMo/Guardrails/pull/890)) by @noamlevy81

## [0.11.0] - 2024-11-19

### Added

- **Observability**: Add observability support with support for different backends ([#844](https://github.com/NVIDIA-NeMo/Guardrails/pull/844)) by @Pouyanpi
- **Private AI Integration**: Add Private AI Integration ([#815](https://github.com/NVIDIA-NeMo/Guardrails/pull/815)) by @letmerecall
- **Patronus Evaluate API Integration**: Patronus Evaluate API Integration ([#834](https://github.com/NVIDIA-NeMo/Guardrails/pull/834)) by @varjoshi
- **railsignore**: Add support for .railsignore file ([#790](https://github.com/NVIDIA-NeMo/Guardrails/pull/790)) by @ajanitshimanga

### Changed

- **Sandboxed Environment in Jinja2**: Add sandboxed environment in Jinja2 ([#799](https://github.com/NVIDIA-NeMo/Guardrails/pull/799)) by @Pouyanpi
- **Langchain 3 support**: Upgrade LangChain to Version 0.3 ([#784](https://github.com/NVIDIA-NeMo/Guardrails/pull/784)) by @Pouyanpi
- **Python 3.8**: Drop support for Python 3.8 ([#803](https://github.com/NVIDIA-NeMo/Guardrails/pull/803)) by @Pouyanpi
- **vllm**: Bump vllm from 0.2.7 to 0.5.5 for llama_guard and patronusai([#836](https://github.com/NVIDIA-NeMo/Guardrails/pull/836))

### Fixed

- **Guardrails Library documentation**": Fix a typo in guardrails library documentation ([#793](https://github.com/NVIDIA-NeMo/Guardrails/pull/793)) by @vedantnaik19
- **Contributing Guide**: Fix incorrect folder name & pre-commit setup in CONTRIBUTING.md ([#800](https://github.com/NVIDIA-NeMo/Guardrails/pull/800))
- **Contributing Guide**: Added correct Python command version in documentation([#801](https://github.com/NVIDIA-NeMo/Guardrails/pull/801)) by @ravinder-tw
- **retrieve chunk action**: Fix presence of new line in retrieve chunk action ([#809](https://github.com/NVIDIA-NeMo/Guardrails/pull/809)) by @Pouyanpi
- **Standard Library import**: Fix guardrails standard library import path in Colang 2.0 ([#835](https://github.com/NVIDIA-NeMo/Guardrails/pull/835)) by @Pouyanpi
- **AlignScore Dockerfile**: Add nltk's punkt_tab in align_score Dockerfile ([#841](https://github.com/NVIDIA-NeMo/Guardrails/pull/841)) by @yonromai
- **Eval dependencies**: Make pandas version constraint explicit for eval optional dependency ([#847](https://github.com/NVIDIA-NeMo/Guardrails/pull/847)) by @Pouyanpi
- **tests**: Mock PromptSession to prevent console error ([#851](https://github.com/NVIDIA-NeMo/Guardrails/pull/851)) by @Pouyanpi
- **Streaming*: Handle multiple output parsers in generation ([#854](https://github.com/NVIDIA-NeMo/Guardrails/pull/854)) by @Pouyanpi

### Documentation

- **User Guide**: Update role from bot to assistant ([#852](https://github.com/NVIDIA-NeMo/Guardrails/pull/852)) by @Pouyanpi
- **Installation Guide**: Update optional dependencies install ([#853](https://github.com/NVIDIA-NeMo/Guardrails/pull/853)) by @Pouyanpi
- **Documentation Restructuring**: Restructure the docs and several style enhancements ([#855](https://github.com/NVIDIA-NeMo/Guardrails/pull/855)) by @Pouyanpi
- **Got It AI deprecation**: Add deprecation notice for Got It AI integration ([#857](https://github.com/NVIDIA-NeMo/Guardrails/pull/857)) by @mlmonk

## [0.10.1] - 2024-10-02

- Colang 2.0-beta.4 patch

## [0.10.0] - 2024-09-27

### Added

- **content safety**: Implement content safety module ([#674](https://github.com/NVIDIA-NeMo/Guardrails/pull/674)) by @Pouyanpi
- **migration tool**: Enhance migration tool capabilities ([#624](https://github.com/NVIDIA-NeMo/Guardrails/pull/624)) by @Pouyanpi
- **Cleanlab Integration**: Add Cleanlab's Trustworthiness Score ([#572](https://github.com/NVIDIA-NeMo/Guardrails/pull/572)) by @AshishSardana
- **Colang 2**: LLM chat interface development ([#709](https://github.com/NVIDIA-NeMo/Guardrails/pull/709)) by @schuellc-nvidia
- **embeddings**: Add relevant chunk support to Colang 2 ([#708](https://github.com/NVIDIA-NeMo/Guardrails/pull/708)) by @Pouyanpi
- **library**: Migrate Cleanlab to Colang 2 and add exception handling ([#714](https://github.com/NVIDIA-NeMo/Guardrails/pull/714)) by @Pouyanpi
- **Colang debug library**: Develop debugging tools for Colang ([#560](https://github.com/NVIDIA-NeMo/Guardrails/pull/560)) by @schuellc-nvidia
- **debug CLI**: Extend debugging command-line interface ([#717](https://github.com/NVIDIA-NeMo/Guardrails/pull/717)) by @schuellc-nvidia
- **embeddings**: Add support for embeddings only with search threshold ([#733](https://github.com/NVIDIA-NeMo/Guardrails/pull/733)) by @Pouyanpi
- **embeddings**: Add embedding-only support to Colang 2 ([#737](https://github.com/NVIDIA-NeMo/Guardrails/pull/737)) by @Pouyanpi
- **embeddings**: Add relevant chunks prompts ([#745](https://github.com/NVIDIA-NeMo/Guardrails/pull/745)) by @Pouyanpi
- **gcp moderation**: Implement GCP-based moderation tools ([#727](https://github.com/NVIDIA-NeMo/Guardrails/pull/727)) by @kauabh
- **migration tool**: Sample conversation syntax conversion ([#764](https://github.com/NVIDIA-NeMo/Guardrails/pull/764)) by @Pouyanpi
- **llmrails**: Add serialization support for LLMRails ([#627](https://github.com/NVIDIA-NeMo/Guardrails/pull/627)) by @Pouyanpi
- **exceptions**: Initial support for exception handling ([#384](https://github.com/NVIDIA-NeMo/Guardrails/pull/384)) by @drazvan
- **evaluation tooling**: Develop new evaluation tools ([#677](https://github.com/NVIDIA-NeMo/Guardrails/pull/677)) by @drazvan
- **Eval UI**: Add support for tags in the Evaluation UI ([#731](https://github.com/NVIDIA-NeMo/Guardrails/pull/731)) by @drazvan
- **guardrails library**: Launch Colang 2.0 Guardrails Library ([#689](https://github.com/NVIDIA-NeMo/Guardrails/pull/689)) by @drazvan
- **configuration**: Revert abc bot to Colang v1 and separate v2 configuration ([#698](https://github.com/NVIDIA-NeMo/Guardrails/pull/698)) by @drazvan

### Changed

- **api**: Update Pydantic validators ([#688](https://github.com/NVIDIA-NeMo/Guardrails/pull/688)) by @Pouyanpi
- **standard library**: Refactor and migrate standard library components ([#625](https://github.com/NVIDIA-NeMo/Guardrails/pull/625)) by @Pouyanpi

- Upgrade langchain-core and jinja2 dependencies ([#766](https://github.com/NVIDIA-NeMo/Guardrails/pull/766)) by @Pouyanpi

### Fixed

- **documentation**: Fix broken links ([#670](https://github.com/NVIDIA-NeMo/Guardrails/pull/670)) by @buvnswrn
- **hallucination-check**: Correct hallucination-check functionality ([#679](https://github.com/NVIDIA-NeMo/Guardrails/pull/679)) by @Pouyanpi
- **streaming**: Fix NVIDIA AI endpoints streaming issues ([#654](https://github.com/NVIDIA-NeMo/Guardrails/pull/654)) by @Pouyanpi
- **hallucination-check**: Resolve non-OpenAI hallucination check issue ([#681](https://github.com/NVIDIA-NeMo/Guardrails/pull/681)) by @Pouyanpi
- **import error**: Fix Streamlit import error ([#686](https://github.com/NVIDIA-NeMo/Guardrails/pull/686)) by @Pouyanpi
- **prompt override**: Fix override prompt self-check facts ([#621](https://github.com/NVIDIA-NeMo/Guardrails/pull/621)) by @Pouyanpi
- **output parser**: Resolve deprecation warning in output parser ([#691](https://github.com/NVIDIA-NeMo/Guardrails/pull/691)) by @Pouyanpi
- **patch**: Fix langchain_nvidia_ai_endpoints patch ([#697](https://github.com/NVIDIA-NeMo/Guardrails/pull/697)) by @Pouyanpi
- **runtime issues**: Address Colang 2 runtime issues ([#699](https://github.com/NVIDIA-NeMo/Guardrails/pull/699)) by @schuellc-nvidia
- **send event**: Change 'send event' to 'send' ([#701](https://github.com/NVIDIA-NeMo/Guardrails/pull/701)) by @Pouyanpi
- **output parser**: Fix output parser validation ([#704](https://github.com/NVIDIA-NeMo/Guardrails/pull/704)) by @Pouyanpi
- **passthrough_fn**: Pass config and kwargs to passthrough_fn runnable ([#695](https://github.com/NVIDIA-NeMo/Guardrails/pull/695)) by @vpr1995
- **rails exception**: Fix rails exception migration ([#705](https://github.com/NVIDIA-NeMo/Guardrails/pull/705)) by @Pouyanpi
- **migration**: Replace hyphens and apostrophes in migration ([#725](https://github.com/NVIDIA-NeMo/Guardrails/pull/725)) by @Pouyanpi
- **flow generation**: Fix LLM flow continuation generation ([#724](https://github.com/NVIDIA-NeMo/Guardrails/pull/724)) by @schuellc-nvidia
- **server command**: Fix CLI server command ([#723](https://github.com/NVIDIA-NeMo/Guardrails/pull/723)) by @Pouyanpi
- **embeddings filesystem**: Fix cache embeddings filesystem ([#722](https://github.com/NVIDIA-NeMo/Guardrails/pull/722)) by @Pouyanpi
- **outgoing events**: Process all outgoing events ([#732](https://github.com/NVIDIA-NeMo/Guardrails/pull/732)) by @sklinglernv
- **generate_flow**: Fix a small bug in the generate_flow action for Colang 2 ([#710](https://github.com/NVIDIA-NeMo/Guardrails/pull/710)) by @drazvan
- **triggering flow id**: Fix the detection of the triggering flow id ([#728](https://github.com/NVIDIA-NeMo/Guardrails/pull/728)) by @drazvan
- **LLM output**: Fix multiline LLM output syntax error for dynamic flow generation ([#748](https://github.com/NVIDIA-NeMo/Guardrails/pull/748)) by @radinshayanfar
- **scene form**: Fix the scene form and choice flows in the Colang 2 standard library ([#741](https://github.com/NVIDIA-NeMo/Guardrails/pull/741)) by @sklinglernv

### Documentation

- **Cleanlab**: Update community documentation for Cleanlab integration ([#713](https://github.com/NVIDIA-NeMo/Guardrails/pull/713)) by @Pouyanpi
- **rails exception handling**: Add notes for Rails exception handling in Colang 2.x ([#744](https://github.com/NVIDIA-NeMo/Guardrails/pull/744)) by @Pouyanpi
- **LLM per task**: Document LLM per task functionality ([#676](https://github.com/NVIDIA-NeMo/Guardrails/pull/676)) by @Pouyanpi

### Others

- **relevant_chunks**: Add the `relevant_chunks` to the GPT-3.5 general prompt template ([#678](https://github.com/NVIDIA-NeMo/Guardrails/pull/678)) by @drazvan
- **flow names**: Ensure flow names don't start with keywords ([#637](https://github.com/NVIDIA-NeMo/Guardrails/pull/637)) by @schuellc-nvidia

## [0.9.1.1] - 2024-07-26

### Fixed

- [#650](https://github.com/NVIDIA-NeMo/Guardrails/pull/650) Fix gpt-3.5-turbo-instruct prompts #651.

## [0.9.1] - 2024-07-25

### Added

- Colang version [2.0-beta.2](./CHANGELOG-Colang.md#20-beta2---unreleased)
- [#370](https://github.com/NVIDIA-NeMo/Guardrails/pull/370) Add Got It AI's Truthchecking service for RAG applications by @mlmonk.
- [#543](https://github.com/NVIDIA-NeMo/Guardrails/pull/543) Integrating AutoAlign's guardrail library with NeMo Guardrails by @abhijitpal1247.
- [#566](https://github.com/NVIDIA-NeMo/Guardrails/pull/566) Autoalign factcheck examples by @abhijitpal1247.
- [#518](https://github.com/NVIDIA-NeMo/Guardrails/pull/518) Docs: add example config for using models with ollama by @vedantnaik19.
- [#538](https://github.com/NVIDIA-NeMo/Guardrails/pull/538) Support for `--default-config-id` in the server.
- [#539](https://github.com/NVIDIA-NeMo/Guardrails/pull/539) Support for `LLMCallException`.
- [#548](https://github.com/NVIDIA-NeMo/Guardrails/pull/548) Support for custom embedding models.
- [#617](https://github.com/NVIDIA-NeMo/Guardrails/pull/617) NVIDIA AI Endpoints embeddings.
- [#462](https://github.com/NVIDIA-NeMo/Guardrails/pull/462) Support for calling embedding models from langchain-nvidia-ai-endpoints.
- [#622](https://github.com/NVIDIA-NeMo/Guardrails/pull/622) Patronus Lynx Integration.

### Changed

- [#597](https://github.com/NVIDIA-NeMo/Guardrails/pull/597) Make UUID generation predictable in debug-mode.
- [#603](https://github.com/NVIDIA-NeMo/Guardrails/pull/603) Improve chat cli logging.
- [#551](https://github.com/NVIDIA-NeMo/Guardrails/pull/551) Upgrade to Langchain 0.2.x by @nicoloboschi.
- [#611](https://github.com/NVIDIA-NeMo/Guardrails/pull/611) Change default templates.
- [#545](https://github.com/NVIDIA-NeMo/Guardrails/pull/545) NVIDIA API Catalog and NIM documentation update.
- [#463](https://github.com/NVIDIA-NeMo/Guardrails/pull/463) Do not store pip cache during docker build by @don-attilio.
- [#629](https://github.com/NVIDIA-NeMo/Guardrails/pull/629) Move community docs to separate folder.
- [#647](https://github.com/NVIDIA-NeMo/Guardrails/pull/647) Documentation updates.
- [#648](https://github.com/NVIDIA-NeMo/Guardrails/pull/648) Prompt improvements for Llama-3 models.

### Fixed

- [#482](https://github.com/NVIDIA-NeMo/Guardrails/pull/482) Update README.md by @curefatih.
- [#530](https://github.com/NVIDIA-NeMo/Guardrails/pull/530) Improve the test serialization test to make it more robust.
- [#570](https://github.com/NVIDIA-NeMo/Guardrails/pull/570) Add support for FacialGestureBotAction by @elisam0.
- [#550](https://github.com/NVIDIA-NeMo/Guardrails/pull/550) Fix issue #335 - make import errors visible.
- [#547](https://github.com/NVIDIA-NeMo/Guardrails/pull/547) Fix LLMParams bug and add unit tests (fixes #158).
- [#537](https://github.com/NVIDIA-NeMo/Guardrails/pull/537) Fix directory traversal bug.
- [#536](https://github.com/NVIDIA-NeMo/Guardrails/pull/536) Fix issue #304 NeMo Guardrails packaging.
- [#539](https://github.com/NVIDIA-NeMo/Guardrails/pull/539) Fix bug related to the flow abort logic in Colang 1.0 runtime.
- [#612](https://github.com/NVIDIA-NeMo/Guardrails/pull/612) Follow-up fixes for the default prompt change.
- [#585](https://github.com/NVIDIA-NeMo/Guardrails/pull/585) Fix Colang 2.0 state serialization issue.
- [#486](https://github.com/NVIDIA-NeMo/Guardrails/pull/486) Fix select model type and custom prompts task.py by @cyun9601.
- [#487](https://github.com/NVIDIA-NeMo/Guardrails/pull/487) Fix custom prompts configuration manual.md.
- [#479](https://github.com/NVIDIA-NeMo/Guardrails/pull/479) Fix static method and classmethod action decorators by @piotrm0.
- [#544](https://github.com/NVIDIA-NeMo/Guardrails/pull/544) Fix issue #216 bot utterance.
- [#616](https://github.com/NVIDIA-NeMo/Guardrails/pull/616) Various fixes.
- [#623](https://github.com/NVIDIA-NeMo/Guardrails/pull/623) Fix path traversal check.

## [0.9.0] - 2024-05-08

### Added

- [Colang 2.0 Documentation](https://docs.nvidia.com/nemo/guardrails/colang-2/overview.html).
- Revamped [NeMo Guardrails Documentation](https://docs.nvidia.com/nemo-guardrails).

### Fixed

- [#461](https://github.com/NVIDIA-NeMo/Guardrails/pull/461) Feature/ccl cleanup.
- [#483](https://github.com/NVIDIA-NeMo/Guardrails/pull/483) Fix dictionary expression evaluation bug.
- [#467](https://github.com/NVIDIA-NeMo/Guardrails/pull/467) Feature/colang doc related cleanups.
- [#484](https://github.com/NVIDIA-NeMo/Guardrails/pull/484) Enable parsing of `..."<NLD>"` expressions.
- [#478](https://github.com/NVIDIA-NeMo/Guardrails/pull/478) Fix #420 - evaluate not working with chat models.

## [0.8.3] - 2024-04-18

### Changed

- [#453](https://github.com/NVIDIA-NeMo/Guardrails/pull/453) Update documentation for NVIDIA API Catalog example.

### Fixed

- [#382](https://github.com/NVIDIA-NeMo/Guardrails/pull/382) Fix issue with `lowest_temperature` in self-check and hallucination rails.
- [#454](https://github.com/NVIDIA-NeMo/Guardrails/pull/454) Redo fix for #385.
- [#442](https://github.com/NVIDIA-NeMo/Guardrails/pull/442) Fix README type by @dileepbapat.

## [0.8.2] - 2024-04-01

### Added

- [#402](https://github.com/NVIDIA-NeMo/Guardrails/pull/402) Integrate Vertex AI Models into Guardrails by @aishwaryap.
- [#403](https://github.com/NVIDIA-NeMo/Guardrails/pull/403) Add support for NVIDIA AI Endpoints by @patriciapampanelli
- [#396](https://github.com/NVIDIA-NeMo/Guardrails/pull/396) Docs/examples nv ai foundation models.
- [#438](https://github.com/NVIDIA-NeMo/Guardrails/pull/438) Add research roadmap documentation.

### Changed

- [#389](https://github.com/NVIDIA-NeMo/Guardrails/pull/389) Expose the `verbose` parameter through `RunnableRails` by @d-mariano.
- [#415](https://github.com/NVIDIA-NeMo/Guardrails/pull/415) Enable `print(...)` and `log(...)`.
- [#389](https://github.com/NVIDIA-NeMo/Guardrails/pull/389) Expose verbose arg in RunnableRails by @d-mariano.
- [#414](https://github.com/NVIDIA-NeMo/Guardrails/pull/414) Feature/colang march release.
- [#416](https://github.com/NVIDIA-NeMo/Guardrails/pull/416) Refactor and improve the verbose/debug mode.
- [#418](https://github.com/NVIDIA-NeMo/Guardrails/pull/418) Feature/colang flow context sharing.
- [#425](https://github.com/NVIDIA-NeMo/Guardrails/pull/425) Feature/colang meta decorator.
- [#427](https://github.com/NVIDIA-NeMo/Guardrails/pull/427) Feature/colang single flow activation.
- [#426](https://github.com/NVIDIA-NeMo/Guardrails/pull/426) Feature/colang 2.0 tutorial.
- [#428](https://github.com/NVIDIA-NeMo/Guardrails/pull/428) Feature/Standard library and examples.
- [#431](https://github.com/NVIDIA-NeMo/Guardrails/pull/431) Feature/colang various improvements.
- [#433](https://github.com/NVIDIA-NeMo/Guardrails/pull/433) Feature/Colang 2.0 improvements: generate_async support, stateful API.

### Fixed

- [#412](https://github.com/NVIDIA-NeMo/Guardrails/pull/412) Fix #411 - explain rails not working for chat models.
- [#413](https://github.com/NVIDIA-NeMo/Guardrails/pull/413) Typo fix: Comment in llm_flows.co by @habanoz.
- [#420](https://github.com/NVIDIA-NeMo/Guardrails/pull/430) Fix typo for hallucination message.

## [0.8.1] - 2024-03-15

### Added

- [#377](https://github.com/NVIDIA-NeMo/Guardrails/pull/377) Add example for streaming from custom action.

### Changed

- [#380](https://github.com/NVIDIA-NeMo/Guardrails/pull/380) Update installation guide for OpenAI usage.
- [#401](https://github.com/NVIDIA-NeMo/Guardrails/pull/401) Replace YAML import with new import statement in multi-modal example.

### Fixed

- [#398](https://github.com/NVIDIA-NeMo/Guardrails/pull/398) Colang parser fixes and improvements.
- [#394](https://github.com/NVIDIA-NeMo/Guardrails/pull/394) Fixes and improvements for Colang 2.0 runtime.
- [#381](https://github.com/NVIDIA-NeMo/Guardrails/pull/381) Fix typo by @serhatgktp.
- [#379](https://github.com/NVIDIA-NeMo/Guardrails/pull/379) Fix missing prompt in verbose mode for chat models.
- [#400](https://github.com/NVIDIA-NeMo/Guardrails/pull/400) Fix Authorization header showing up in logs for NeMo LLM.

## [0.8.0] - 2024-02-28

### Added

- [#292](https://github.com/NVIDIA-NeMo/Guardrails/pull/292) [Jailbreak heuristics](./docs/getting-started/tutorials/jailbreak-detection-heuristics.mdx) by @erickgalinkin.
- [#256](https://github.com/NVIDIA-NeMo/Guardrails/pull/256) Support [generation options](./docs/run-rails/using-python-apis/generation-options.mdx).
- [#307](https://github.com/NVIDIA-NeMo/Guardrails/pull/307) Added support for multi-config api calls by @makeshn.
- [#293](https://github.com/NVIDIA-NeMo/Guardrails/pull/293) Adds configurable stop tokens by @zmackie.
- [#334](https://github.com/NVIDIA-NeMo/Guardrails/pull/334) Colang 2.0 - Preview by @schuellc.
- [#208](https://github.com/NVIDIA-NeMo/Guardrails/pull/208) Implement cache embeddings (resolves #200) by @Pouyanpi.
- [#331](https://github.com/NVIDIA-NeMo/Guardrails/pull/331) Huggingface pipeline streaming by @trebedea.

Documentation:

- [#311](https://github.com/NVIDIA-NeMo/Guardrails/pull/311) Update documentation to demonstrate the use of output rails when using a custom RAG by @niels-garve.
- [#347](https://github.com/NVIDIA-NeMo/Guardrails/pull/347) Add [detailed logging docs](./docs/observability/logging/index.mdx) by @erickgalinkin.
- [#354](https://github.com/NVIDIA-NeMo/Guardrails/pull/354) [Input and output rails only guide](./docs/run-rails/using-python-apis/check-messages.mdx) by @trebedea.
- [#359](https://github.com/NVIDIA-NeMo/Guardrails/pull/359) Added [user guide for jailbreak detection heuristics](./docs/getting-started/tutorials/jailbreak-detection-heuristics.mdx) by @makeshn.
- [#363](https://github.com/NVIDIA-NeMo/Guardrails/pull/363) Add [multi-config API call user guide](./docs/run-rails/using-fastapi-server/list-guardrail-configs.mdx).
- [#297](https://github.com/NVIDIA-NeMo/Guardrails/pull/297) Example configurations for using only the guardrails, without LLM generation.

### Changed

- [#309](https://github.com/NVIDIA-NeMo/Guardrails/pull/309) Change the paper citation from ArXiV to EMNLP 2023 by @manuelciosici
- [#319](https://github.com/NVIDIA-NeMo/Guardrails/pull/319) Enable embeddings model caching.
- [#267](https://github.com/NVIDIA-NeMo/Guardrails/pull/267) Make embeddings computing async and add support for batching.
- [#281](https://github.com/NVIDIA-NeMo/Guardrails/pull/281) Follow symlinks when building knowledge base by @piotrm0.
- [#280](https://github.com/NVIDIA-NeMo/Guardrails/pull/280) Add more information to results of `retrieve_relevant_chunks` by @piotrm0.
- [#332](https://github.com/NVIDIA-NeMo/Guardrails/pull/332) Update docs for batch embedding computations.
- [#244](https://github.com/NVIDIA-NeMo/Guardrails/pull/244) Docs/edit getting started by @DougAtNvidia.
- [#333](https://github.com/NVIDIA-NeMo/Guardrails/pull/333) Follow-up to PR 244.
- [#341](https://github.com/NVIDIA-NeMo/Guardrails/pull/341) Updated 'fastembed' version to 0.2.2 by @NirantK.

### Fixed

- [#286](https://github.com/NVIDIA-NeMo/Guardrails/pull/286) Fixed #285 - using the same evaluation set given a random seed for topical rails by @trebedea.
- [#336](https://github.com/NVIDIA-NeMo/Guardrails/pull/336) Fix #320. Reuse the asyncio loop between sync calls.
- [#337](https://github.com/NVIDIA-NeMo/Guardrails/pull/337) Fix stats gathering in a parallel async setup.
- [#342](https://github.com/NVIDIA-NeMo/Guardrails/pull/342) Fixes OpenAI embeddings support.
- [#346](https://github.com/NVIDIA-NeMo/Guardrails/pull/346) Fix issues with KB embeddings cache, bot intent detection and config ids validator logic.
- [#349](https://github.com/NVIDIA-NeMo/Guardrails/pull/349) Fix multi-config bug, asyncio loop issue and cache folder for embeddings.
- [#350](https://github.com/NVIDIA-NeMo/Guardrails/pull/350) Fix the incorrect logging of an extra dialog rail.
- [#358](https://github.com/NVIDIA-NeMo/Guardrails/pull/358) Fix Openai embeddings async support.
- [#362](https://github.com/NVIDIA-NeMo/Guardrails/pull/362) Fix the issue with the server being pointed to a folder with a single config.
- [#352](https://github.com/NVIDIA-NeMo/Guardrails/pull/352) Fix a few issues related to jailbreak detection heuristics.
- [#356](https://github.com/NVIDIA-NeMo/Guardrails/pull/356) Redo followlinks PR in new code by @piotrm0.

## [0.7.1] - 2024-02-01

### Changed

- [#288](https://github.com/NVIDIA-NeMo/Guardrails/pull/288) Replace SentenceTransformers with FastEmbed.

## [0.7.0] - 2024-01-31

### Added

- [#254](https://github.com/NVIDIA-NeMo/Guardrails/pull/254) Support for [Llama Guard input and output content moderation](./docs/configure-rails/guardrail-catalog/content-safety.mdx#llama-guard-based-content-moderation).
- [#253](https://github.com/NVIDIA-NeMo/Guardrails/pull/253) Support for [server-side threads](./docs/run-rails/using-fastapi-server/overview.mdx).
- [#235](https://github.com/NVIDIA-NeMo/Guardrails/pull/235) Improved [LangChain integration](./docs/integration/langchain/langchain-integration.mdx) through `RunnableRails`.
- [#190](https://github.com/NVIDIA-NeMo/Guardrails/pull/190) Add [example](./examples/notebooks/generate_events_and_streaming.ipynb) for using `generate_events_async` with streaming.
- Support for Python 3.11.

### Changed

- [#240](https://github.com/NVIDIA-NeMo/Guardrails/pull/240) Switch to pyproject.
- [#276](https://github.com/NVIDIA-NeMo/Guardrails/pull/276) Upgraded Typer to 0.9.

### Fixed

- [#286](https://github.com/NVIDIA-NeMo/Guardrails/pull/286) Fixed not having the same evaluation set given a random seed for topical rails.
- [#239](https://github.com/NVIDIA-NeMo/Guardrails/pull/239) Fixed logging issue where `verbose=true` flag did not trigger expected log output.
- [#228](https://github.com/NVIDIA-NeMo/Guardrails/pull/228) Fix docstrings for various functions.
- [#242](https://github.com/NVIDIA-NeMo/Guardrails/pull/242) Fix Azure LLM support.
- [#225](https://github.com/NVIDIA-NeMo/Guardrails/pull/225) Fix annoy import, to allow using without.
- [#209](https://github.com/NVIDIA-NeMo/Guardrails/pull/209) Fix user messages missing from prompt.
- [#261](https://github.com/NVIDIA-NeMo/Guardrails/pull/261) Fix small bug in `print_llm_calls_summary`.
- [#252](https://github.com/NVIDIA-NeMo/Guardrails/pull/252) Fixed duplicate loading for the default config.
- Fixed the dependencies pinning, allowing a wider range of dependencies versions.
- Fixed sever security issues related to uncontrolled data used in path expression and information exposure through an exception.

## [0.6.1] - 2023-12-20

### Added

- Support for `--version` flag in the CLI.

### Changed

- Upgraded `langchain` to `0.0.352`.
- Upgraded `httpx` to `0.24.1`.
- Replaced deprecated `text-davinci-003` model with `gpt-3.5-turbo-instruct`.

### Fixed

- [#191](https://github.com/NVIDIA-NeMo/Guardrails/pull/191): Fix chat generation chunk issue.

## [0.6.0] - 2023-12-13

### Added

- Support for [explicit definition](./docs/configure-rails/yaml-schema/guardrails-configuration.mdx) of input/output/retrieval rails.
- Support for [custom tasks and their prompts](./docs/configure-rails/yaml-schema/prompt-configuration.mdx).
- Support for fact-checking [using AlignScore](./docs/configure-rails/guardrail-catalog/community/alignscore.mdx).
- Support for [NeMo LLM Service](./docs/about/supported-llms.mdx) as an LLM provider.
- Support for making a single LLM call for both the guardrails process and generating the response (by setting `rails.dialog.single_call.enabled` to `True`).
- Support for [sensitive data detection](./docs/configure-rails/guardrail-catalog/community/presidio.mdx) guardrails using Presidio.
- [Example](./examples/configs/llm/hf_pipeline_llama2) using NeMo Guardrails with the LLaMa2-13B model.
- [Dockerfile](./Dockerfile) for building a Docker image.
- Support for [prompting modes](./docs/configure-rails/yaml-schema/prompt-configuration.mdx) using `prompting_mode`.
- Support for [TRT-LLM](./docs/about/supported-llms.mdx) as an LLM provider.
- Support for [streaming](./docs/run-rails/using-python-apis/streaming.mdx) the LLM responses when no output rails are used.
- [Integration](./docs/configure-rails/guardrail-catalog/community/active-fence.mdx) of ActiveFence ActiveScore API as an input rail.
- Support for `--prefix` and `--auto-reload` in the [guardrails server](./docs/run-rails/using-fastapi-server/overview.mdx).
- Example authentication dialog flow.
- Example [RAG using Pinecone](./examples/configs/rag/pinecone).
- Support for loading a configuration from dictionary, i.e. `RailsConfig.from_content(config=...)`.
- Guidance on [LLM support](./docs/about/supported-llms.mdx).
- Support for `LLMRails.explain()` (see the [Getting Started](./docs/getting-started/installation-guide.mdx) guide for sample usage).

### Changed

- Allow context data directly in the `/v1/chat/completion` using messages with the type `"role"`.
- Allow calling a subflow whose name is in a variable, e.g. `do $some_name`.
- Allow using actions which are not `async` functions.
- Disabled pretty exceptions in CLI.
- Upgraded dependencies.
- Updated the [Getting Started Guide](./docs/getting-started/installation-guide.mdx).
- Main [README](./README.md) now provides more details.
- Merged original examples into a single [ABC Bot](./examples/bots/abc) and removed the original ones.
- Documentation improvements.

### Fixed

- Fix going over the maximum prompt length using the `max_length` attribute in [Prompt Templates](./docs/configure-rails/yaml-schema/prompt-configuration.mdx).
- Fixed problem with `nest_asyncio` initialization.
- [#144](https://github.com/NVIDIA-NeMo/Guardrails/pull/144) Fixed TypeError in logging call.
- [#121](https://github.com/NVIDIA-NeMo/Guardrails/pull/109) Detect chat model using openai engine.
- [#109](https://github.com/NVIDIA-NeMo/Guardrails/pull/109) Fixed minor logging issue.
- Parallel flow support.
- Fix `HuggingFacePipeline` bug related to LangChain version upgrade.

## [0.5.0] - 2023-09-04

### Added

- Support for [custom configuration data](./docs/configure-rails/custom-initialization/custom-data.mdx).
- Example for using custom LLM and multiple KBs.
- Support for [`PROMPTS_DIR`](./docs/configure-rails/yaml-schema/prompt-configuration.mdx).
- [#101](https://github.com/NVIDIA-NeMo/Guardrails/pull/101) Support for [using OpenAI embeddings](./docs/configure-rails/custom-initialization/custom-embedding-providers.mdx) models in addition to SentenceTransformers.
- First set of end-to-end QA tests for the example configurations.
- Support for configurable [embedding search providers](./docs/configure-rails/other-configurations/embedding-search-providers.mdx)

### Changed

- Moved to using `nest_asyncio` for [implementing the blocking API](./docs/run-rails/using-python-apis/core-classes.mdx). Fixes [#3](https://github.com/NVIDIA-NeMo/Guardrails/issues/3) and [#32](https://github.com/NVIDIA-NeMo/Guardrails/issues/32).
- Improved event property validation in `new_event_dict`.
- Refactored imports to allow installing from source without Annoy/SentenceTransformers (would need a custom embedding search provider to work).

### Fixed

- Fixed when the `init` function from `config.py` is called to allow custom LLM providers to be registered inside.
- [#93](https://github.com/NVIDIA-NeMo/Guardrails/pull/93): Removed redundant `hasattr` check in `nemoguardrails/llm/params.py`.
- [#91](https://github.com/NVIDIA-NeMo/Guardrails/issues/91): Fixed how default context variables are initialized.

## [0.4.0] - 2023-08-03

### Added

- [Event-based API](./docs/run-rails/using-python-apis/event-based-api.mdx) for guardrails.
- Support for message with type "event" in [`LLMRails.generate_async`](/guardrails-python-sdk/nemoguardrails/rails/llm/llmrails#nemoguardrails-rails-llm-llmrails-LLMRails).
- Support for [bot message instructions](./docs/configure-rails/colang/usage-examples/bot-message-instructions.mdx).
- Support for [using variables inside bot message definitions](./docs/configure-rails/colang/colang-1/colang-language-syntax-guide.mdx#bot-messages-with-variables).
- Support for `vicuna-7b-v1.3` and `mpt-7b-instruct`.
- Topical evaluation results for `vicuna-7b-v1.3` and `mpt-7b-instruct`.
- Support to use different models for different LLM tasks.
- Support for [red-teaming](./docs/evaluation/llm-vulnerability-scanning.mdx) using challenges.
- Support to disable the Chat UI when running the server using `--disable-chat-ui`.
- Support for accessing the API request headers in server mode.
- Support to [enable CORS settings](./docs/run-rails/using-fastapi-server/overview.mdx) for the guardrails server.

### Changed

- Changed the naming of the internal events to align to the upcoming UMIM spec (Unified Multimodal Interaction Management).
- If there are no user message examples, the bot messages examples lookup is disabled as well.

### Fixed

- [#58](https://github.com/NVIDIA-NeMo/Guardrails/issues/58): Fix install on Mac OS 13.
- [#55](https://github.com/NVIDIA-NeMo/Guardrails/issues/55): Fix bug in example causing config.py to crash on computers with no CUDA-enabled GPUs.
- Fixed the model name initialization for LLMs that use the `model` kwarg.
- Fixed the Cohere prompt templates.
- [#55](https://github.com/NVIDIA-NeMo/Guardrails/issues/83): Fix bug related to LangChain callbacks initialization.
- Fixed generation of "..." on value generation.
- Fixed the parameters type conversion when invoking actions from Colang (previously everything was string).
- Fixed `model_kwargs` property for the `WrapperLLM`.
- Fixed bug when `stop` was used inside flows.
- Fixed Chat UI bug when an invalid guardrails configuration was used.

## [0.3.0] - 2023-06-30

### Added

- Support for defining [subflows](./docs/configure-rails/colang/colang-1/colang-language-syntax-guide.mdx#subflows).
- Improved support for [customizing LLM prompts](./docs/configure-rails/yaml-schema/prompt-configuration.mdx)
  - Support for using filters to change how variables are included in a prompt template.
  - Output parsers for prompt templates.
  - The `verbose_v1` formatter and output parser to be used for smaller models that don't understand Colang very well in a few-shot manner.
  - Support for including context variables in prompt templates.
  - Support for chat models i.e. prompting with a sequence of messages.
- Experimental support for allowing the LLM to generate [multi-step flows](./docs/configure-rails/yaml-schema/guardrails-configuration.mdx).
- Example of using Llama Index from a guardrails configuration (#40).
- [Example](examples/configs/llm/hf_endpoint) for using HuggingFace Endpoint LLMs with a guardrails configuration.
- [Example](examples/configs/llm/hf_pipeline_dolly) for using HuggingFace Pipeline LLMs with a guardrails configuration.
- Support to alter LLM parameters passed as `model_kwargs` in LangChain.
- CLI tool for running evaluations on the different steps (e.g., canonical form generation, next steps, bot message) and on existing rails implementation (e.g., moderation, jailbreak, fact-checking, and hallucination).
- [Initial evaluation](./docs/evaluation/evaluate-guardrails.mdx) results for `text-davinci-003` and `gpt-3.5-turbo`.
- The `lowest_temperature` can be set through the guardrails config (to be used for deterministic tasks).

### Changed

- The core templates now use Jinja2 as the rendering engines.
- Improved the internal prompting architecture, now using an LLM Task Manager.

### Fixed

- Fixed bug related to invoking a chain with multiple output keys.
- Fixed bug related to tracking the output stats.
- #51: Bug fix - avoid str concat with None when logging user_intent.
- #54: Fix UTF-8 encoding issue and add embedding model configuration.

## [0.2.0] - 2023-05-31

### Added

- Support to [connect any LLM](./docs/about/supported-llms.mdx) that implements the BaseLanguageModel interface from  LangChain.
- Support for [customizing the prompts](./docs/configure-rails/yaml-schema/prompt-configuration.mdx) for specific LLM models.
- Support for [custom initialization](./docs/configure-rails/custom-initialization/index.mdx) when loading a configuration through `config.py`.
- Support to extract [user-provided values](./docs/configure-rails/colang/usage-examples/extract-user-provided-values.mdx) from utterances.

### Changed

- Improved the logging output for Chat CLI (clear events stream, prompts, completion, timing information).
- Updated system actions to use temperature 0 where it makes sense, e.g., canonical form generation, next step generation, fact checking, etc.
- Excluded the default system flows from the "next step generation" prompt.
- Updated langchain to 0.0.167.

### Fixed

- Fixed initialization of LangChain tools.
- Fixed the overriding of general instructions [#7](https://github.com/NVIDIA-NeMo/Guardrails/issues/7).
- Fixed action parameters inspection bug [#2](https://github.com/NVIDIA-NeMo/Guardrails/issues/2).
- Fixed bug related to multi-turn flows [#13](https://github.com/NVIDIA-NeMo/Guardrails/issues/13).
- Fixed Wolfram Alpha error reporting in the sample execution rail.

## [0.1.0] - 2023-04-25

### Added

- First alpha release.



CONTRIBUTING.md

# Contributing Guidelines

Welcome to NeMo Guardrails. This guide explains the contribution workflow,
local setup, validation commands, and review expectations for this repository.

Coding agents should also read [AGENTS.md](./AGENTS.md). AI-assisted public
contributions must follow [AI_POLICY.md](./AI_POLICY.md).

## Before You Contribute

- Search existing [issues](https://github.com/NVIDIA-NeMo/Guardrails/issues)
  and [pull requests](https://github.com/NVIDIA-NeMo/Guardrails/pulls) before
  opening anything new.
- Use the GitHub issue templates for bugs, feature requests, and documentation
  issues. Blank issues are disabled.
- Use [Discussions](https://github.com/NVIDIA-NeMo/Guardrails/discussions) for
  support questions and "How do I...?" questions.
- Do not open a pull request before the related issue has been triaged and
  assigned to you.

Issues must be opened manually by a human using the GitHub issue templates. AI
tools may help draft or refine issue text, but agents must not open issues
directly through browser automation, the GitHub API, the `gh` CLI, or similar
tooling. The person opening the issue is responsible for reviewing, editing, and
owning the content.

## Issues and Proposals

Anyone is welcome to open an issue. Opening an issue does not mean you are
committing to implement it; it is fine to report a bug, propose an idea, or
share a design concern for someone else to pick up later.

If an issue author is not interested or available to implement the change,
another contributor may ask to take it over. Wait for maintainer assignment
before opening a PR.

Useful issue comments:

```text
I am opening this for tracking, but I am not planning to implement it.


I would like to work on this.
Proposed approach: <1-3 sentence summary>
Planned validation: <tests/docs/checks>


text

Is this still being worked on? If not, I would be happy to take it over.
Proposed approach: <1-3 sentence summary>


text

Refactors are maintainer-led and are not accepted as unsolicited PRs. If you

 

believe a refactor is needed, open a refactor proposal issue and wait for

 

maintainer feedback. Maintainers decide whether the refactor should happen, what

 

plan is acceptable, and who, if anyone, should be assigned to implement it.

For work in progress, experiments, or early ideas, share the branch name and

 

relevant files in the issue instead of opening a premature PR.

Pull Request Requirements

Pull requests must be linked to a triaged issue. The PR author must be assigned

 

to that issue before opening the PR. PRs without a linked issue, or opened by

 

someone who is not assigned to the linked issue, may be closed or redirected

 

without review.

Before opening a PR:

Fork the repository and create a branch from 

develop

.

Keep the PR cohesive and reviewable.

Avoid low-value mechanical PRs such as isolated formatting churn, broad

 

cleanup without a clear user benefit, or typo-only sweeps.

Use the pull request template and list the tests/checks you ran.

Use a clear 

Conventional Commit

https://www.conventionalcommits.org/

 

style PR title, for example 

fix: ...

, 

feat: ...

, 

docs: ...

,

 

test: ...

, 

refactor: ...

, 

perf: ...

, 

style: ...

, 

chore: ...

,

 

ci: ...

, or 

revert: ...

. Use scopes when helpful, for example

 

fix(server): ...

.

Do not update 

CHANGELOG.md

 or 

CHANGELOG-Colang.md

 manually. Changelog

 

entries are generated by the release workflow.

Review Readiness

Automated code review tools such as CodeRabbit and Greptile are part of the

 

pre-review workflow. A PR is ready for maintainer review only after the author

 

has addressed unresolved human and automated review comments.

Automated code review is gated on triage. A new PR opens as 

status: needs triage

 (a reopened PR keeps whatever triage label it already has); a maintainer

 

applies 

status: triaged

 after confirming the PR is linked to a triaged issue

 

assigned to the contributor. CodeRabbit and Greptile are configured to review

 

only PRs with 

status: triaged

.

Before requesting maintainer review:

Address every automated code review comment, or reply with a clear reason why

 

no change is needed.

When an automated review tool supports resolution confirmation, wait for the

 

tool to confirm that the issue is resolved. CodeRabbit may resolve

 

conversations itself; other tools, including Greptile, may require a follow-up

 

comment or rerun.

Address every human reviewer comment, or reply with a clear reason why no

 

change is needed.

Do not resolve human reviewer conversations unless you opened the

 

conversation, or the reviewer explicitly asks you to resolve it. Human review

 

conversations should normally be resolved by the reviewer who opened them.

The repository may use a 

status: ready for maintainer review

 label for PRs

 

that have completed this author-response step. Do not request or apply that

 

label while human or automated review comments still need author action.

AI-Assisted Contributions

AI-assisted contributions are welcome when they meet the same quality bar as any

 

other contribution. If AI tools helped create or substantially modify a

 

contribution:

Disclose the tool and extent of assistance in the PR description.

Review and edit AI-generated text before submitting it.

Make sure you understand every code change and can explain how it interacts

 

with the surrounding system.

Do not add AI tools as commit co-authors.

See 

AI_POLICY.md

./AI_POLICY.md

 for the full policy.

Development Setup

NeMo Guardrails supports Python 3.10 through 3.13. Install Git and uv. Follow the

 

uv installation instructions

https://docs.astral.sh/uv/getting-started/installation/

 

for your platform.

GitHub Actions uses the uv version pinned in

 

 

as the canonical version. Use that version when changing dependencies or

 

uv.lock

. If another project requires a different uv version, use a

 

directory-aware version manager or repository-scoped installation rather than

 

replacing a shared global executable.

When updating the canonical uv version, update

 

.github/actions/setup-uv/action.yml

, 

.gitlab-ci.yml

, and the uv image version

 

and digest in 

Dockerfile

 together.

Dependency resolution uses a seven-day cooldown, so newly uploaded distributions

 

are eligible only after seven days. To make an emergency package update without

 

waiting, use 

uv lock --upgrade-package <package> --exclude-newer-package <package>=false

.

Clone the repository and install development dependencies:

git clone https://github.com/NVIDIA-NeMo/Guardrails.git nemoguardrails
cd nemoguardrails
make install


bash

Documentation tooling requires Node.js 22. The Fern CLI version is pinned in

 

fern/fern.config.json

 and invoked through 

npx

; no separate Python docs

 

dependency group is required.

Valid optional extras are 

sdd

, 

eval

, 

gcp

, 

tracing

, 

jailbreak

,

 

multilingual

, 

server

, 

chat-ui

, and 

all

. For example:

uv sync --locked --extra server --extra tracing


bash

For temporary local investigation tools, use the uv-managed environment

 

without modifying project dependencies:

uv pip install <package-name>


bash

Do not commit environment-only dependency changes.

Validation

Run Python commands through uv.

Task

Command

Focused tests

make test TEST=path/to/test_file.py::test_name

Full test suite

make test

Pre-commit hooks

make pre-commit

Docs check

make docs-fern

Package coverage

make test-coverage

Run the smallest meaningful test set first, then broaden validation when the

 

change touches shared runtime behavior, public APIs, packaging, server behavior,

 

tracing, or docs.

Set up local pre-commit hooks if you want checks to run before every commit:

make pre-commit-install


bash

The pre-commit configuration runs Ruff, Ruff format, license-header insertion,

 

and ty.

Documentation and Notebooks

Update documentation when changing user-visible behavior, public APIs,

 

configuration syntax, examples, or installation requirements.

Documentation lives in 

docs/

 as MDX and is built with Fern. Edit the 

.mdx

 

files directly and check changes with 

make docs-fern

 (

make docs-fern-live

 

serves locally; 

make docs-fern-strict

 validates links). The Fern CLI version

 

is pinned in 

fern/fern.config.json

; do not run 

fern upgrade

 as part of normal

 

documentation changes.

For notebook documentation, place the notebook in its own folder and generate a

 

matching 

README.md

 with:

uv run python build_notebook_docs.py PATH/TO/SUBFOLDER


bash

Important: 

build_notebook_docs.py

 currently runs broad git staging and

 

pre-commit commands. Use a clean worktree before running it. Coding agents

 

should not run it unless explicitly asked.

Commit Signing

Public contributions must satisfy the Developer Certificate of Origin (DCO).

 

Use one of these options:

Submit GPG-signed commits.

Add a 

Signed-off-by

 line to commit messages.

PR titles and commit messages should follow the project commit convention

 

described above. A GPG-signed commit is accepted as a declaration that you agree

 

to the DCO terms. For details, see the

 

Developer Certificate of Origin

https://developercertificate.org/

 and

 

GitHub's signing commits documentation

https://docs.github.com/en/authentication/managing-commit-signature-verification/signing-commits

.

Community and Support

For general questions and discussion, use

 

GitHub Discussions

https://github.com/NVIDIA-NeMo/Guardrails/discussions

.

## LICENSE.md



SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.

 

SPDX-License-Identifier: Apache-2.0

Licensed under the Apache License, Version 2.0 (the "License");

 

you may not use this file except in compliance with the License.

 

You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software

 

distributed under the License is distributed on an "AS IS" BASIS,

 

WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

 

See the License for the specific language governing permissions and

 

limitations under the License.

## README.md



NVIDIA NeMo Guardrails Library

 

 

 

 

 

 

 

 

 

 

 

LATEST RELEASE / DEVELOPMENT VERSION

: The 

develop

https://github.com/NVIDIA-NeMo/Guardrails/tree/develop

 branch tracks the latest top of tree development. The latest released version is 

0.23.0

https://github.com/NVIDIA-NeMo/Guardrails/tree/v0.23.0

.

✨✨✨

📌 

The official NeMo Guardrails library documentation is available at 

docs.nvidia.com/nemo/guardrails

https://docs.nvidia.com/nemo/guardrails

.

✨✨✨

NVIDIA NeMo Guardrails library is an open-source toolkit for easily adding 

programmable guardrails

 to LLM-based conversational applications. Guardrails (or "rails" for short) are specific ways of controlling the output of a large language model, such as not talking about politics, responding in a particular way to specific user requests, following a predefined dialog path, using a particular language style, extracting structured data, and more.

This paper

https://arxiv.org/abs/2310.10501

 introduces the NeMo Guardrails library and contains a technical overview of the system and the current evaluation.

Requirements

Python 3.10, 3.11, 3.12 or 3.13.

Installation

To install using pip:

> pip install nemoguardrails


bash

For more detailed instructions, see the 

Installation Guide

https://docs.nvidia.com/nemo/guardrails/get-started/installation-guide

.

Overview

The NeMo Guardrails library enables developers building LLM-based applications to add 

programmable guardrails

 between the application code and the LLM.

Key benefits of adding 

programmable guardrails

 include:

Building Trustworthy, Safe, and Secure LLM-based Applications:

 you can define rails to guide and safeguard conversations; you can choose to define the behavior of your LLM-based application on specific topics and prevent it from engaging in discussions on unwanted topics.

Connecting models, chains, and other services securely:

 you can connect an LLM to other services (a.k.a. tools) seamlessly and securely.

Controllable dialog

: you can steer the LLM to follow pre-defined conversational paths, allowing you to design the interaction following conversation design best practices and enforce standard operating procedures (e.g., authentication, support).

Protecting against LLM Vulnerabilities

The NeMo Guardrails library provides several mechanisms for protecting an LLM-powered chat application against common LLM vulnerabilities, such as jailbreaks and prompt injections. Below is a sample overview of the protection offered by different guardrails configuration for the example 

ABC Bot

./examples/bots/abc

 included in this repository. For more details, please refer to the 

LLM Vulnerability Scanning

https://docs.nvidia.com/nemo/guardrails/evaluation/llm-vulnerability-scanning.html

 page.

Use Cases

You can use programmable guardrails in different types of use cases:

Question Answering

 over a set of documents (a.k.a. Retrieval Augmented Generation): Enforce fact-checking and output moderation.

Domain-specific Assistants

 (a.k.a. chatbots): Ensure the assistant stays on topic and follows the designed conversational flows.

LLM Endpoints

: Add guardrails to your custom LLM for safer customer interaction.

LangChain Chains

 (optional): If you use LangChain for any use case, you can add a guardrails layer around your chains. To enable this integration, set the 

NEMOGUARDRAILS_LLM_FRAMEWORK=langchain

 environment variable or call 

set_default_framework("langchain")

.

Usage

To add programmable guardrails to your application you can use the Python API or a guardrails server (see the 

Server Guide

https://docs.nvidia.com/nemo/guardrails/get-started/integrate-into-application

 for more details). Using the Python API is similar to using the LLM directly. Calling the guardrails layer instead of the LLM requires only minimal changes to the code base, and it involves two simple steps:

Loading a guardrails configuration and creating an 

LLMRails

 instance.

Making the calls to the LLM using the 

generate

/

generate_async

 methods.

from nemoguardrails import LLMRails, RailsConfig

# Load a guardrails configuration from the specified path.
config = RailsConfig.from_path("PATH/TO/CONFIG")
rails = LLMRails(config)

completion = rails.generate(
    messages=[{"role": "user", "content": "Hello world!"}]
)


python

Sample output:

{"role": "assistant", "content": "Hi! How can I help you?"}


json

The input and output format for the 

generate

 method is similar to the 

Chat Completions API

https://platform.openai.com/docs/guides/gpt/chat-completions-api

 from OpenAI.

Async API

The NeMo Guardrails library is an async-first toolkit as the core mechanics are implemented using the Python async model. The public methods have both a sync and an async version. For example: 

LLMRails.generate

 and 

LLMRails.generate_async

.

Supported LLMs

You can use NeMo Guardrails with multiple LLMs like OpenAI GPT-3.5, GPT-4, LLaMa-2, Falcon, Vicuna, or Mosaic. For more details, check out the 

Supported LLM Models

https://docs.nvidia.com/nemo/guardrails/about-nemo-guardrails-library/supported-llms

 section in the Configuration Guide.

Types of Guardrails

The NeMo Guardrails library supports five main types of guardrails:

Input rails

: applied to the input from the user; an input rail can reject the input, stopping any additional processing, or alter the input (e.g., to mask potentially sensitive data, to rephrase).

Dialog rails

: influence how the LLM is prompted; dialog rails operate on canonical form messages for details see 

Colang Guide

https://docs.nvidia.com/nemo/guardrails/configure-guardrails/colang

) and determine if an action should be executed, if the LLM should be invoked to generate the next step or a response, if a predefined response should be used instead, etc.

Retrieval rails

: applied to the retrieved chunks in the case of a RAG (Retrieval Augmented Generation) scenario; a retrieval rail can reject a chunk, preventing it from being used to prompt the LLM, or alter the relevant chunks (e.g., to mask potentially sensitive data).

Execution rails

: applied to input/output of the custom actions (a.k.a. tools), that need to be called by the LLM.

Output rails

: applied to the output generated by the LLM; an output rail can reject the output, preventing it from being returned to the user, or alter it (e.g., removing sensitive data).

Guardrails Configuration

A guardrails configuration defines the 

LLM(s)

 to be used and 

one or more guardrails

. A guardrails configuration can include any number of input/dialog/output/retrieval/execution rails. A configuration without any configured rails will essentially forward the requests to the LLM.

The standard structure for a guardrails configuration folder looks like this:

.
├── config
│   ├── actions.py
│   ├── config.py
│   ├── config.yml
│   ├── rails.co
│   ├── ...


The 

config.yml

 contains all the general configuration options, such as LLM models, active rails, and custom configuration data". The 

config.py

 file contains any custom initialization code and the 

actions.py

 contains any custom python actions. For a complete overview, see the 

Configuration Guide

https://docs.nvidia.com/nemo/guardrails/configure-guardrails/configure-rails

.

Below is an example 

config.yml

:

# config.yml
models:
  - type: main
    engine: openai
    model: gpt-3.5-turbo-instruct

rails:
  # Input rails are invoked when new input from the user is received.
  input:
    flows:
      - check jailbreak
      - mask sensitive data on input

  # Output rails are triggered after a bot message has been generated.
  output:
    flows:
      - self check facts
      - self check hallucination
      - activefence moderation on input

  config:
    # Configure the types of entities that should be masked on user input.
    sensitive_data_detection:
      input:
        entities:
          - PERSON
          - EMAIL_ADDRESS


yaml

The 

.co

 files included in a guardrails configuration contain the Colang definitions (see the next section for a quick overview of what Colang is) that define various types of rails. Below is an example 

greeting.co

 file which defines the dialog rails for greeting the user.

define user express greeting
  "Hello!"
  "Good afternoon!"

define flow
  user express greeting
  bot express greeting
  bot offer to help

define bot express greeting
  "Hello there!"

define bot offer to help
  "How can I help you today?"


colang

Below is an additional example of Colang definitions for a dialog rail against insults:

define user express insult
  "You are stupid"

define flow
  user express insult
  bot express calmly willingness to help


colang

Colang

To configure and implement various types of guardrails, this toolkit introduces 

Colang

, a modeling language specifically created for designing flexible, yet controllable, dialogue flows. Colang has a python-like syntax and is designed to be simple and intuitive, especially for developers.

Two versions of Colang, 1.0 and 2.0, are supported and Colang 1.0 is the default.


{note}

For a brief introduction to the Colang 1.0 syntax, see the 

Colang 1.0 Language Syntax Guide

https://docs.nvidia.com/nemo/guardrails/configure-guardrails/colang

.

To get started with Colang 2.0, see the 

Colang 2.0 Documentation

https://docs.nvidia.com/nemo/guardrails/colang-2/overview.html

.

Guardrails Library

NeMo Guardrails comes with a set of 

built-in guardrails

https://docs.nvidia.com/nemo/guardrails/user-guides/guardrails-library.html

.

The built-in guardrails may or may not be suitable for a given production use case. As always, developers should work with their internal application team to ensure guardrails meets requirements for the relevant industry and use case and address unforeseen product misuse.


{note}

The library includes guardrails for LLM self-checking (input/output moderation, fact-checking, hallucination detection), NVIDIA safety models (content safety, topic safety), jailbreak and injection detection, and integrations with community models and third-party APIs. For the complete list, see the 

Guardrails Library documentation

https://docs.nvidia.com/nemo/guardrails/user-guides/guardrails-library.html

.

CLI

The NeMo Guardrails library also comes with a built-in CLI.

$ nemoguardrails --help

Usage: nemoguardrails [OPTIONS] COMMAND [ARGS]...

actions-server    Start a NeMo Guardrails actions server.
chat              Start an interactive chat session.
evaluate          Run an evaluation task.
server            Start a NeMo Guardrails server.


bash

Guardrails Server

You can use the NeMo Guardrails library CLI to start a guardrails server. The server can load one or more configurations from the specified folder and expose and HTTP API for using them.

nemoguardrails server [--config PATH/TO/CONFIGS] [--port PORT]


For example, to get a chat completion for a 

sample

 config, you can use the 

/v1/chat/completions

 endpoint:

POST /v1/chat/completions


{
    "config_id": "sample",
    "messages": [{
      "role":"user",
      "content":"Hello! What can you do for me?"
    }]
}


json

Sample output:

{"role": "assistant", "content": "Hi! How can I help you?"}


json

Docker

To start a guardrails server, you can also use a Docker container. The NeMo Guardrails library provides a 

Dockerfile

./Dockerfile

 that you can use to build a 

nemoguardrails

 image. For further information, see the 

using Docker

https://docs.nvidia.com/nemo/guardrails/user-guides/advanced/using-docker.html

 section.

Integration with LangChain (Optional)

LangChain integration is opt-in. To enable it, set the 

NEMOGUARDRAILS_LLM_FRAMEWORK=langchain

 environment variable or call 

set_default_framework("langchain")

. Then install the LangChain packages your configuration requires. After you enable the integration, you can wrap a guardrails configuration around a LangChain chain (or any 

Runnable

), and you can call a LangChain chain from within a guardrails configuration. For more information, refer to the 

LangChain Integration Documentation

https://docs.nvidia.com/nemo/guardrails/user-guides/langchain/langchain-integration.html

.

Evaluation

Evaluating the safety of a LLM-based conversational application is a complex task and still an open research question. To support proper evaluation, the NeMo Guardrails library provides the following:

An 

evaluation tool

nemoguardrails/evaluate/README.md

, i.e. 

nemoguardrails evaluate

, with support for topical rails, fact-checking, moderation (jailbreak and output moderation) and hallucination.

Sample LLM Vulnerability Scanning Reports, e.g, 

ABC Bot - LLM Vulnerability Scan Results

https://docs.nvidia.com/nemo/guardrails/evaluation/llm-vulnerability-scanning.html

How is this different?

There are many ways guardrails can be added to an LLM-based conversational application. For example: explicit moderation endpoints (e.g., OpenAI, ActiveFence, PolicyAI), critique chains (e.g. constitutional chain), parsing the output (e.g. guardrails.ai), individual guardrails (e.g., LLM-Guard), hallucination detection for RAG applications (e.g., Got It AI, Patronus Lynx).

The NeMo Guardrails library aims to provide a flexible toolkit that can integrate all these complementary approaches into a cohesive LLM guardrails layer. For example, the toolkit provides out-of-the-box integration with ActiveFence, PolicyAI, AlignScore and LangChain chains.

To the best of our knowledge, the NeMo Guardrails library is the only guardrails toolkit that also offers a solution for modeling the dialog between the user and the LLM. This enables on one hand the ability to guide the dialog in a precise way. On the other hand it enables fine-grained control for when certain guardrails should be used, e.g., use fact-checking only for certain types of questions.

Learn More

Documentation

https://docs.nvidia.com/nemo/guardrails

Getting Started Guide

https://docs.nvidia.com/nemo/guardrails/getting-started

Examples

./examples

FAQs

https://docs.nvidia.com/nemo/guardrails/faqs.html

Security Guidelines

https://docs.nvidia.com/nemo/guardrails/security/guidelines.html

Telemetry and Privacy

The NVIDIA NeMo Guardrails library collects anonymous telemetry to help NVIDIA understand which deployment patterns and safety features are most used. The library emits one usage event when you instantiate 

LLMRails

, 

IORails

, or 

Guardrails

, then emits periodic heartbeats from a single daemon thread per process. This telemetry is separate from per-request 

tracing

https://docs.nvidia.com/nemo/guardrails/latest/observability/tracing/index.html

. You configure tracing in your guardrails config and send it to your own observability backend. Telemetry is a minimal anonymous ping to NVIDIA.

The telemetry includes:

Installed library version, Python version, operating system, and platform string

Colang configuration language version (1.0 or 2.x)

Names of configured LLM engine providers, such as 

openai

, 

nim

, or 

nvidia_ai_endpoints

, never model names or credentials

Counts of configured rail flows for input, output, retrieval, tool input, and tool output rails, plus which rail categories are active

Names of built-in library features that are active, such as 

jailbreak_detection

, 

content_safety

, or 

topic_safety

Count of user-defined Colang flows (count only, never flow names or contents)

Whether tracing, streaming, or a knowledge base is configured

How you deployed guardrails (

library

, 

api

, or 

cli

 server)

Which runtime rails engine is in use (

LLMRails

 or 

IORails

)

A random per-process UUID for correlating events from the same instance. The library generates it in memory and does not store it for reuse across restarts, but includes it in audit records and transmitted telemetry events

No user content is collected in the event payload. The payload does not include model names, API keys, endpoints, prompts, completions, token counts, per-request metrics, file paths, usernames, or IP addresses. NVIDIA uses the data in aggregate to prioritize engineering work and will share adoption trends with the community.

The library also attempts to write each event payload to a local audit file at 

~/.config/nemoguardrails/usage_stats.json

. The audit file stores the event JSONL, not the full NVIDIA telemetry envelope. Audit writes are best effort, and telemetry transmission still proceeds if local audit writing fails.

Set any one of the following options to disable telemetry:

export NEMO_GUARDRAILS_NO_USAGE_STATS=1
# or
export DO_NOT_TRACK=1
# or
mkdir -p ~/.config/nemoguardrails && touch ~/.config/nemoguardrails/do_not_track


bash

Set the opt-out before the NVIDIA NeMo Guardrails library starts. Changing environment variables or creating 

do_not_track

 after telemetry has started does not stop an already-running heartbeat thread.

Refer to 

docs/telemetry.md

https://docs.nvidia.com/nemo/guardrails/latest/telemetry.html

 for the full schema and field-by-field descriptions.

You may opt out of telemetry collection at any time. Opting out applies only to data collection by the NVIDIA NeMo Guardrails library itself.

Third-party endpoints have separate terms and privacy practices. The NVIDIA NeMo Guardrails library can use inference endpoints such as NVIDIA Build (

build.nvidia.com

). If you use NVIDIA Build or another third-party endpoint, that endpoint's terms of service and privacy practices apply independently of the library. Any telemetry opt-out in the NVIDIA NeMo Guardrails library does not extend to the endpoint you choose. NVIDIA Build is intended for evaluation and testing only and must not be used in production environments. Do not submit confidential information or personal data when using NVIDIA Build.

Inviting the community to contribute

The example rails residing in the repository are excellent starting points. We enthusiastically invite the community to contribute towards making the power of trustworthy, safe, and secure LLMs accessible to everyone. For guidance on setting up a development environment and how to contribute to the NeMo Guardrails library, see the 

contributing guidelines

./CONTRIBUTING.md

.

License

The NeMo Guardrails library is licensed under the 

Apache License, Version 2.0

http://www.apache.org/licenses/LICENSE-2.0

.

How to cite

If you use the NeMo Guardrails library, cite the 

EMNLP 2023 paper

https://aclanthology.org/2023.emnlp-demo.40

 that introduces it.

@inproceedings{rebedea-etal-2023-nemo,
    title = "{N}e{M}o Guardrails: A Toolkit for Controllable and Safe {LLM} Applications with Programmable Rails",
    author = "Rebedea, Traian  and
      Dinu, Razvan  and
      Sreedhar, Makesh Narsimhan  and
      Parisien, Christopher  and
      Cohen, Jonathan",
    editor = "Feng, Yansong  and
      Lefever, Els",
    booktitle = "Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing: System Demonstrations",
    month = dec,
    year = "2023",
    address = "Singapore",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2023.emnlp-demo.40",
    doi = "10.18653/v1/2023.emnlp-demo.40",
    pages = "431--445",
}


bibtex

## SECURITY.md



Security

NVIDIA is dedicated to the security and trust of our software products and services, including all source code repositories managed through our organization.

If you need to report a security issue, please use the appropriate contact points outlined below. 

Please do not report security vulnerabilities through GitHub.

Reporting Potential Security Vulnerability in an NVIDIA Product

To report a potential security vulnerability in any NVIDIA product:

Web: 

Security Vulnerability Submission Form

https://www.nvidia.com/object/submit-security-vulnerability.html

E-Mail: psirt@nvidia.com

We encourage you to use the following PGP key for secure email communication: 

NVIDIA public PGP Key for communication

https://www.nvidia.com/en-us/security/pgp-key

Please include the following information:

Product/Driver name and version/branch that contains the vulnerability

Type of vulnerability (code execution, denial of service, buffer overflow, etc.)

Instructions to reproduce the vulnerability

Proof-of-concept or exploit code

Potential impact of the vulnerability, including how an attacker could exploit the vulnerability

While NVIDIA currently does not have a bug bounty program, we do offer acknowledgement when an externally reported security issue is addressed under our coordinated vulnerability disclosure policy. Please visit our 

Product Security Incident Response Team (PSIRT)

https://www.nvidia.com/en-us/security/psirt-policies/

 policies page for more information.

NVIDIA Product Security

For all security-related concerns, please visit NVIDIA's Product Security portal at https://www.nvidia.com/en-us/security

## docs\.cursor\rules\product-names\RULE.mdc




--------------------------------------------------------------------------------


description: Referring to product names

alwaysApply: true

Refer to this package as "the NVIDIA NeMo Guardrails library" instead of "NVIDIA NeMo Guardrails" or "the NVIDIA NeMo Guardrails toolkit".

## docs\.cursor\rules\release-preparation\RULE.mdc




--------------------------------------------------------------------------------


alwaysApply: true

When a user asks you to prepare for a release of a new version v{version}, do the following:

Update the release version in docs/project.json and docs/versions1.json files.

Check the docs/about/release-notes.md file and remind the user to update the release notes for the new version, if not already done.

## docs\AGENTS.md



Documentation Agent Guide

You are a documentation engineer and writer for the NVIDIA NeMo Guardrails library.

 

Treat 

docs/

 as the source of truth for published product documentation and product-usage agent entry points.

Role

Write clear, accurate, task-oriented documentation for developers who use the NeMo Guardrails library.

Preserve the reader's workflow: explain what to do, when to do it, and how to verify it.

Prefer small, focused edits that match the structure of the current page.

Verify behavior against source code, tests, examples, or existing docs before documenting it.

Before Editing

Read the full target page before editing it.

Map behavior changes to existing pages before proposing a new page.

Update 

docs/index.yml

 when navigation, slugs, or page placement changes.

Do not hand-edit generated Python SDK reference output.

Do not run 

build_notebook_docs.py

 unless explicitly asked; it currently runs broad git staging and pre-commit commands.

Writing Rules

Refer to this package as "the NVIDIA NeMo Guardrails library".

Use active voice, second person, present tense, and direct language.

Use 

code

 formatting for commands, paths, flags, environment variables, file names, and literal values.

Avoid hype, rhetorical questions, emoji, em dashes, and unnecessary bold text.

Use Fern components such as 

<Tabs>

, 

<Tab>

, 

<Cards>

, 

<Card>

, 

<Badge>

, 

<Note>

, 

<Tip>

, and 

<Warning>

 consistently with nearby pages.

Do not duplicate the page title as a body H1 because Fern renders the title from frontmatter.

Agentic Documentation

Product-usage agent guidance must route to the canonical docs instead of duplicating full instructions.

Prefer docs MCP, 

llms.txt

, and clean per-page Markdown for AI agent entry points.

Keep starter prompts focused on bootstrapping an agent to the docs, not on restating all docs content.

Do not hardcode staging URLs in user-facing docs unless the page is explicitly about staging.

Document version-alignment behavior when telling agents how to use docs.

Product Names And Release Prep

Follow 

docs/.cursor/rules/product-names/RULE.mdc

 for product naming.

For release-preparation docs updates, follow 

docs/.cursor/rules/release-preparation/RULE.mdc

.

Never edit 

CHANGELOG.md

 or 

CHANGELOG-Colang.md

 manually.

Validation

Run 

make docs-fern

 when rendering, links, examples, or docs configuration may be affected.

Run 

make docs-fern-live

 only when an interactive local preview is useful.

Run 

make docs-fern-strict

 when link changes are broad or risky.

For docs-only changes, run 

uv run --locked pre-commit run --files <changed files>

 before handoff when practical.

Report any skipped validation clearly.

## docs\LIVE_DOCS.mdx




--------------------------------------------------------------------------------


SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.

SPDX-License-Identifier: Apache-2.0

title: "Fern Documentation Preview - Quick Reference"

This guide shows you how to preview the Fern documentation site while editing MDX pages.

Quick Start

Start the local Fern development server from the repository root:

make docs-fern-live


bash

For a branch preview that publishes to Fern, run:

make docs-fern-preview-watch


bash

Prerequisites

Fern is run through the pinned CLI version in 

fern/fern.config.json

. The commands use 

npx

 to fetch that version.

The Python SDK reference is generated automatically before the Fern checks and preview commands run.

Available Methods

Local Fern Server

make docs-fern-live


bash

Regenerates the Python SDK reference under 

docs/_static/python-sdk-reference

.

Normalizes the generated SDK tree to avoid duplicate sidebar entries.

Starts the Fern local development server.

Published Branch Preview

make docs-fern-preview-watch


bash

This watches local docs and 

fern/

 configuration changes and publishes a Fern preview for the current Git branch.

Check Only

make docs-fern-strict


bash

This regenerates the SDK reference, normalizes it, and runs 

fern check

.

CI Publishing

The docs build workflow checks Fern docs on documentation pull requests and publishes a Fern preview for same-repository branches. When a documentation pull request merges into 

develop

, the workflow publishes the Fern docs to the 

staging instance

https://nvidia-nemo-guardrails-staging.docs.buildwithfern.com/nemo/guardrails

.

After staging verification, maintainers with NVIDIA Fern admin access can publish the staged docs to the 

public instance

https://nvidia-nemo-guardrails.docs.buildwithfern.com/nemo/guardrails

:

make docs-fern-publish-public


bash

Direct Fern Command

make docs-fern-generate-sdk
cd fern
npx --yes fern-api@$(node -p "require('./fern.config.json').version") docs dev


bash

How It Works

SDK Reference Generation

: Fern generates Python library reference pages from the 

nemoguardrails

 package.

Normalization

: 

scripts/normalize-fern-sdk-reference.mjs

 removes duplicate generated sidebar entries.

Fern Dev Server

: Fern starts a local documentation server.

Live Reload

: Your browser refreshes as Fern rebuilds changed pages.

What Files Are Watched?

The Fern workflow watches:

MDX files in 

docs/

Fern configuration in 

fern/

Static assets referenced by the docs

Files ignored:

Generated SDK reference output (

docs/_static/python-sdk-reference/

)

Temporary files (

.swp

, 

*~

)

Git files (

.git/

)

Accessing the Documentation

Use the local URL printed by Fern in the terminal.

Stopping the Server

Press 

Ctrl+C

 in the terminal to stop the server.

Troubleshooting

Fern CLI Fails to Start

The Fern CLI is downloaded through 

npx

. If it fails to start, check network access and rerun:

make docs-fern-live


bash

Changes Not Reflecting

Regenerate the SDK reference and restart the local server:

make docs-fern-generate-sdk
make docs-fern-live


bash

Browser Not Auto-Refreshing

Make sure you're viewing the URL printed by Fern.

Some browser extensions may block live reload.

Try a different browser or incognito mode

Tips

Keep the terminal visible

: You'll see build progress and any errors

Check for errors

: Red text in the terminal indicates build warnings or errors

Generated files

: Do not edit files under 

docs/_static/python-sdk-reference/

; regenerate them.

Clean builds

: If things look wrong, stop the server and rerun 

make docs-fern-live

.

Advanced Configuration

The Make targets automatically:

Use the pinned Fern CLI version.

Regenerate and normalize Python SDK reference docs.

Run Fern check or the Fern development server.

To customize, edit:

Makefile

fern/docs.yml

Or run Fern directly from the 

fern/

 directory:

npx --yes fern-api@$(node -p "require('./fern.config.json').version") docs dev


bash

## docs\README.mdx




--------------------------------------------------------------------------------


SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.

SPDX-License-Identifier: Apache-2.0

title: "Documentation"

Product Documentation

Product documentation for the toolkit is available at

 

https://docs.nvidia.com/nemo/guardrails

https://docs.nvidia.com/nemo/guardrails

.

Building the Documentation

Make sure Node.js 22 is installed.

Build the documentation:

The Fern docs configuration is validated with the pinned Fern CLI.

Live Documentation Server

For local development with automatic rebuilding on file changes, use one of the following methods:

Option 1: Local Fern Server

make docs-fern-live


bash

The Fern development server starts locally and updates as you edit docs files.

Option 2: Published Branch Preview

make docs-fern-preview-watch


bash

This watches local docs and Fern configuration changes and publishes a preview for the current Git branch.

Option 3: Direct Fern Command

cd fern
npx --yes fern-api@$(node -p "require('./fern.config.json').version") docs dev


bash

Once the server is running:

Open the local URL printed by Fern

Edit documentation files or Fern configuration

Save the file

The browser will automatically refresh with the updated content

Press 

Ctrl+C

 to stop the server.

Publishing the Documentation

Tag the commit to publish with 

docs-v<semver>

.

 

Push the tag to GitHub.

To avoid publishing the documentation as the latest, ensure the commit has 

/not-latest

 on a single line, tag that commit, and push to GitHub.

## docs\_components\StarterPromptButton.tsx



/*

SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.

SPDX-License-Identifier: Apache-2.0

 

*/

declare const React: unknown;

const BUTTON_LABEL = "Copy Starter Prompt";

 

const STARTER_PROMPT = `# NVIDIA NeMo Guardrails Library Agent Instructions

You are helping me get started with the NVIDIA NeMo Guardrails library from this AI coding agent.

 

Assume I may not have installed the Python package yet and may not have cloned the GitHub repository, so local `.agents/skills/` and `AGENTS.md` files might not exist.

How to Help Me

Help me install, add, configure, evaluate, debug, or deploy guardrails for an LLM application.

Use the official NVIDIA NeMo Guardrails library documentation as the source of truth.

Prefer the docs MCP server if this agent supports MCP.

Otherwise, use the documentation index at `https://docs.nvidia.com/nemo/guardrails/llms.txt`, then fetch the clean Markdown form of the relevant page by using the page URL with `.md`.

Use Markdown documentation under `https://docs.nvidia.com/nemo/guardrails/` when loading information for agent context. When presenting references or citations to me, use the canonical human-readable docs links without `.md`.

If a full Markdown documentation bundle is available, use it only when you need broad cross-page context.

Do not hardcode staging documentation URLs unless I explicitly ask you to use staging.

Check my installed `nemoguardrails` version only after you confirm the package is installed. If it is not installed yet, use the current Installation docs first. If you cannot determine the version after installation, ask whether to use the latest docs.

If I am working from a cloned repository, you may also use local `docs/**/*.mdx`, `README.md`, `CONTRIBUTING.md`, and `AGENTS.md` files as context.

Identify My Role First

Before giving install or usage instructions, ask who I am:

Developer using the NVIDIA NeMo Guardrails library in an application.

Contributor changing the Guardrails repository.

If I choose developer, follow the Developer Path.

 

If I choose contributor, follow the Contributor Path.

Developer Path

Use this Markdown documentation page as the first source for installation and prerequisite handling:

`https://docs.nvidia.com/nemo/guardrails/latest/get-started/installation-guide.md`

Help me install the library based on that page.

 

Check whether prerequisites already exist before asking me to install anything:

Supported operating system: Windows, Linux, or macOS.

Python version: 3.10, 3.11, 3.12, or 3.13.

Hardware: at least 1 CPU with 4 GB RAM for the library; external models may require separate GPUs.

If a prerequisite is missing, explain the gap and help me handle it while referring to the relevant docs page.

 

Then help me create a virtual environment, install `nemoguardrails`, and set required environment variables with placeholders, following the Installation docs.

 

Never ask me to paste real API keys into chat.

 

After installation succeeds, ask which tutorial I want to try next from the Tutorials docs:

Check Harmful Content. If this is selected, load `https://docs.nvidia.com/nemo/guardrails/latest/get-started/tutorials/nemotron-safety-guard-deployment.md`

Content Safety Reasoning. If this is selected, load `https://docs.nvidia.com/nemo/guardrails/latest/get-started/tutorials/nemotron-content-safety-reasoning-deployment.md`

Restrict Topics. If this is selected, load `https://docs.nvidia.com/nemo/guardrails/latest/get-started/tutorials/nemoguard-topiccontrol-deployment.md`

Detect Jailbreak Attempts. If this is selected, load `https://docs.nvidia.com/nemo/guardrails/latest/get-started/tutorials/nemoguard-jailbreakdetect-deployment.md`

Jailbreak Heuristics. If this is selected, load `https://docs.nvidia.com/nemo/guardrails/latest/get-started/tutorials/jailbreak-detection-heuristics.md`

Add Multimodal Content Safety. If this is selected, load `https://docs.nvidia.com/nemo/guardrails/latest/get-started/tutorials/multimodal.md`

Contributor Path

Help me clone the Guardrails repository before assuming local repository instructions exist:

```bash

 

git clone https://github.com/NVIDIA-NeMo/Guardrails.git nemoguardrails

 

cd nemoguardrails

 

```

After the repository is available, help me navigate the implemented contributor guidance:

Start with `AGENTS.md` for root repository rules.

Follow `nemoguardrails/AGENTS.md` when changing package runtime code.

Follow `docs/AGENTS.md` when editing documentation.

Follow `CONTRIBUTING.md` and `AI_POLICY.md` for public contribution and AI-assistance policy.

Start by Understanding My Goal

Ask one focused question first: what am I trying to do?

 

Offer these choices when useful:

Help me install the library or verify my environment.

Add basic input/output guardrails to an app.

Choose which guardrail type or catalog item to use.

Write or debug Colang flows.

Integrate with Python, LangChain, LangGraph, or the Guardrails API server.

Add custom actions or a custom model/provider.

Evaluate guardrails or run vulnerability scanning.

Configure tracing, metrics, logging, Docker, or deployment.

Troubleshoot an error.

Security and Credentials

Never ask me to paste real API keys, tokens, passwords, or private credentials into chat.

Use placeholders such as `<NVIDIA_API_KEY>`, `<OPENAI_API_KEY>`, or `<YOUR_ENDPOINT>` in examples.

If a command needs a secret, explain where the secret should be set locally, then let me provide it through my shell, environment, secret manager, or local UI.

Do not print real secrets in commands, summaries, logs, or generated files.

Working Style

Keep answers task-oriented and concise.

Show the smallest working example first, then explain optional production hardening.

When writing code or configuration, prefer current documented patterns.

When using live model endpoints in examples, clearly state that unit tests should mock LLM/provider calls.

If I am contributing to the repository rather than just using the library, switch to the repository contribution rules from `CONTRIBUTING.md` and `AGENTS.md`.

Begin by asking whether I am a developer using the NVIDIA NeMo Guardrails library in an application or a contributor changing the Guardrails repository.`;

const resetCopyButtonTimers = new WeakMap<HTMLButtonElement, ReturnType

<typeof setTimeout>

>();

export function StarterPromptButton() {

 

return (

 

<button

 

aria-label="Copy NVIDIA NeMo Guardrails library starter prompt"

 

aria-live="polite"

 

onClick={handleCopyClick}

 

style={{

 

alignItems: "center",

 

background: "#76B900",

 

border: "0",

 

borderRadius: "8px",

 

color: "#111827",

 

cursor: "pointer",

 

display: "inline-flex",

 

fontSize: "0.95rem",

 

fontWeight: 700,

 

gap: "0.5rem",

 

margin: "0.5rem 0 1.5rem",

 

padding: "0.75rem 1rem",

 

transition: "background 180ms ease, box-shadow 180ms ease, transform 180ms ease",

 

willChange: "transform",

 

}}

 

type="button"

 

>

 

<svg

 

aria-hidden="true"

 

focusable="false"

 

height="18"

 

style={{ flexShrink: 0 }}

 

viewBox="0 0 24 24"

 

width="18"

 

>

 

<g data-starter-prompt-icon="prompt">

 

<rect
fill="none"
height="16"
rx="3"
stroke="currentColor"
strokeWidth="2"
width="20"
x="2"
y="4"
/>

 

<path d="M7 9l3 3-3 3" fill="none" stroke="currentColor" strokeWidth="2" />

 

<path d="M12 15h5" fill="none" stroke="currentColor" strokeWidth="2" />

 

</g>

 

<g data-starter-prompt-icon="check" style={{ display: "none" }}>

 

<circle cx="12" cy="12" fill="none" r="9" stroke="currentColor" strokeWidth="2" />

 

<path d="M8 12.5l2.5 2.5L16 9" fill="none" stroke="currentColor" strokeWidth="2" />

 

</g>

 

</svg>

 

<span data-starter-prompt-label>

{BUTTON_LABEL}

</span>

 

</button>

 

);

 

}

async function handleCopyClick(event: { currentTarget: HTMLButtonElement }) {

 

const button = event.currentTarget;

 

lockButtonWidth(button);

 

setCopyButtonState(button, "Copying...", "#8DD600", "Copying prompt");

const copied = await copyText(STARTER_PROMPT);

 

setCopyButtonState(

 

button,

 

copied ? "Copied to Clipboard" : "Copy Failed. Try Again",

 

copied ? "#8DD600" : "#F97316",

 

copied ? "Copied NVIDIA NeMo Guardrails library starter prompt" : "Could not copy starter prompt",

 

copied ? "check" : "prompt",

 

);

 

}

async function copyText(text: string): Promise

<boolean>

 {

 

if (typeof navigator !== "undefined" && navigator.clipboard) {

 

try {

 

await navigator.clipboard.writeText(text);

 

return true;

 

} catch {

 

// Fall through to the textarea fallback for browsers that block clipboard writes.

 

}

 

}

if (typeof document === "undefined") {

 

return false;

 

}

const textarea = document.createElement("textarea");

 

textarea.value = text;

 

textarea.setAttribute("readonly", "true");

 

textarea.style.position = "fixed";

 

textarea.style.top = "-1000px";

 

document.body.appendChild(textarea);

 

textarea.select();

 

try {

 

return document.execCommand("copy");

 

} finally {

 

document.body.removeChild(textarea);

 

}

 

}

function setCopyButtonState(

 

button: HTMLButtonElement,

 

label: string,

 

background: string,

 

ariaLabel: string,

 

icon: "prompt" | "check" = "prompt",

 

) {

 

const resetCopyButtonTimer = resetCopyButtonTimers.get(button);

 

if (resetCopyButtonTimer) {

 

clearTimeout(resetCopyButtonTimer);

 

}

setButtonLabel(button, label);

 

setButtonIcon(button, icon);

 

button.setAttribute("aria-label", ariaLabel);

 

button.style.background = background;

 

button.style.boxShadow = "0 0 0 4px rgb(118 185 0 / 20%)";

if (typeof button.animate === "function") {

 

button.animate(

 

[

 

{ transform: "scale(1)", offset: 0 },

 

{ transform: "scale(1.04)", offset: 0.45 },

 

{ transform: "scale(1)", offset: 1 },

 

],

 

{ duration: 360, easing: "ease-out" },

 

);

 

}

const timer = setTimeout(() => {

 

setButtonLabel(button, BUTTON_LABEL);

 

setButtonIcon(button, "prompt");

 

button.setAttribute("aria-label", "Copy NVIDIA NeMo Guardrails library starter prompt");

 

button.style.background = "#76B900";

 

button.style.boxShadow = "none";

 

button.style.width = "";

 

resetCopyButtonTimers.delete(button);

 

}, 2000);

 

resetCopyButtonTimers.set(button, timer);

 

}

function setButtonIcon(button: HTMLButtonElement, icon: "prompt" | "check") {

 

const promptIcon = button.querySelector

<SVGGElement>

("[data-starter-prompt-icon='prompt']");

 

const checkIcon = button.querySelector

<SVGGElement>

("[data-starter-prompt-icon='check']");

 

if (promptIcon) {

 

promptIcon.style.display = icon === "prompt" ? "" : "none";

 

}

 

if (checkIcon) {

 

checkIcon.style.display = icon === "check" ? "" : "none";

 

}

 

}

function setButtonLabel(button: HTMLButtonElement, label: string) {

 

const labelElement = button.querySelector

<HTMLElement>

("[data-starter-prompt-label]");

 

if (labelElement) {

 

labelElement.textContent = label;

 

}

 

}

function lockButtonWidth(button: HTMLButtonElement) {

 

if (!button.style.width) {

 

button.style.width = 

${button.offsetWidth}px

;

 

}

 

}

## docs\_static\css\custom.css



.swagger-ui code {

 

white-space: pre-wrap;

 

}

.microlight code {

 

color: white;

 

background: none;

 

border: none;

 

}

/* Equal height grid cards */

 

.sd-equal-height .sd-row {

 

display: flex;

 

flex-wrap: wrap;

 

}

.sd-equal-height .sd-col {

 

display: flex;

 

}

.sd-equal-height .sd-card {

 

height: 100%;

 

display: flex;

 

flex-direction: column;

 

}

.sd-equal-height .sd-card-body {

 

flex: 1;

 

}

.table-expand-button {

 

align-items: center;

 

background: #76b900;

 

border: 0;

 

border-radius: 4px;

 

color: #fff;

 

cursor: pointer;

 

display: inline-flex;

 

font-weight: 600;

 

gap: 0.4rem;

 

margin: 0.25rem 0 0.75rem;

 

padding: 0.45rem 0.75rem;

 

}

.table-expand-button:hover,

 

.table-expand-button:focus {

 

background: #5f9500;

 

}

.table-expand-button:focus {

 

outline: 2px solid #1a1a1a;

 

outline-offset: 2px;

 

}

.table-expander-modal {

 

background: rgba(0, 0, 0, 0.65);

 

display: none;

 

inset: 0;

 

padding: 2rem;

 

position: fixed;

 

z-index: 10000;

 

}

.table-expander-modal.is-open {

 

display: flex;

 

}

.table-expander-modal__dialog {

 

background: #fff;

 

border-radius: 6px;

 

box-shadow: 0 1rem 3rem rgba(0, 0, 0, 0.35);

 

display: flex;

 

flex-direction: column;

 

max-height: 90vh;

 

width: min(1200px, 96vw);

 

}

.table-expander-modal__header {

 

align-items: center;

 

border-bottom: 1px solid #d9d9d9;

 

display: flex;

 

justify-content: space-between;

 

padding: 1rem 1.25rem;

 

}

.table-expander-modal__title {

 

font-size: 1.2rem;

 

font-weight: 700;

 

margin: 0;

 

}

.table-expander-modal__close {

 

background: transparent;

 

border: 0;

 

cursor: pointer;

 

font-size: 1.8rem;

 

line-height: 1;

 

padding: 0.1rem 0.35rem;

 

}

.table-expander-modal__body {

 

overflow: auto;

 

padding: 1rem 1.25rem 1.25rem;

 

}

.table-expander-modal__body table {

 

margin: 0;

 

min-width: 1000px;

 

}

body.table-expander-modal-open {

 

overflow: hidden;

 

}

@media (max-width: 768px) {

 

.table-expander-modal {

 

padding: 0.75rem;

 

}

 

}

## docs\_static\html\abc_bare_llm.report.html



/* Style the buttons that are used to open and close the accordion panel */

 

.accordion {

 

//  background-color: #eee;

 

color: #444;

 

cursor: pointer;

 

padding: 18px;

 

width: 100%;

 

text-align: left;

 

border: none;

 

outline: none;

 

transition: 0.4s;

 

margin: 1pt;

 

}

/* Add a background color to the button if it is clicked on (add the .active class with JS), and when you move the mouse over it (hover) */

 

//.active, .accordion:hover {

 

//  background-color: #ccc;

 

//}

/* Style the accordion panel. Note: hidden by default */

 

.panel {

 

padding: 0 18px;

 

background-color: white;

 

display: none;

 

overflow: hidden;

 

}

 

</style>

for (i = 0; i < acc.length; i++) {

 

acc[i].addEventListener("click", function() {

 

/* Toggle between adding and removing the "active" class,

 

to highlight the button that controls the panel */

 

this.classList.toggle("active");

/* Toggle between hiding and showing the active panel */
var panel = this.nextElementSibling;
if (panel.style.display === "block") {
  panel.style.display = "none";
} else {
  panel.style.display = "block";
}


});

 

}

</script>

## docs\_static\html\abc_with_full_guardrails.report.html



/* Style the buttons that are used to open and close the accordion panel */

 

.accordion {

 

//  background-color: #eee;

 

color: #444;

 

cursor: pointer;

 

padding: 18px;

 

width: 100%;

 

text-align: left;

 

border: none;

 

outline: none;

 

transition: 0.4s;

 

margin: 1pt;

 

}

/* Add a background color to the button if it is clicked on (add the .active class with JS), and when you move the mouse over it (hover) */

 

//.active, .accordion:hover {

 

//  background-color: #ccc;

 

//}

/* Style the accordion panel. Note: hidden by default */

 

.panel {

 

padding: 0 18px;

 

background-color: white;

 

display: none;

 

overflow: hidden;

 

}

 

</style>

for (i = 0; i < acc.length; i++) {

 

acc[i].addEventListener("click", function() {

 

/* Toggle between adding and removing the "active" class,

 

to highlight the button that controls the panel */

 

this.classList.toggle("active");

/* Toggle between hiding and showing the active panel */
var panel = this.nextElementSibling;
if (panel.style.display === "block") {
  panel.style.display = "none";
} else {
  panel.style.display = "block";
}


});

 

}

</script>

## docs\_static\html\abc_with_general_instructions.report.html



/* Style the buttons that are used to open and close the accordion panel */

 

.accordion {

 

//  background-color: #eee;

 

color: #444;

 

cursor: pointer;

 

padding: 18px;

 

width: 100%;

 

text-align: left;

 

border: none;

 

outline: none;

 

transition: 0.4s;

 

margin: 1pt;

 

}

/* Add a background color to the button if it is clicked on (add the .active class with JS), and when you move the mouse over it (hover) */

 

//.active, .accordion:hover {

 

//  background-color: #ccc;

 

//}

/* Style the accordion panel. Note: hidden by default */

 

.panel {

 

padding: 0 18px;

 

background-color: white;

 

display: none;

 

overflow: hidden;

 

}

 

</style>

for (i = 0; i < acc.length; i++) {

 

acc[i].addEventListener("click", function() {

 

/* Toggle between adding and removing the "active" class,

 

to highlight the button that controls the panel */

 

this.classList.toggle("active");

/* Toggle between hiding and showing the active panel */
var panel = this.nextElementSibling;
if (panel.style.display === "block") {
  panel.style.display = "none";
} else {
  panel.style.display = "block";
}


});

 

}

</script>

## docs\_static\html\abc_with_general_instructions_and_dialog_rails.report.html



/* Style the buttons that are used to open and close the accordion panel */

 

.accordion {

 

//  background-color: #eee;

 

color: #444;

 

cursor: pointer;

 

padding: 18px;

 

width: 100%;

 

text-align: left;

 

border: none;

 

outline: none;

 

transition: 0.4s;

 

margin: 1pt;

 

}

/* Add a background color to the button if it is clicked on (add the .active class with JS), and when you move the mouse over it (hover) */

 

//.active, .accordion:hover {

 

//  background-color: #ccc;

 

//}

/* Style the accordion panel. Note: hidden by default */

 

.panel {

 

padding: 0 18px;

 

background-color: white;

 

display: none;

 

overflow: hidden;

 

}

 

</style>

for (i = 0; i < acc.length; i++) {

 

acc[i].addEventListener("click", function() {

 

/* Toggle between adding and removing the "active" class,

 

to highlight the button that controls the panel */

 

this.classList.toggle("active");

/* Toggle between hiding and showing the active panel */
var panel = this.nextElementSibling;
if (panel.style.display === "block") {
  panel.style.display = "none";
} else {
  panel.style.display = "block";
}


});

 

}

</script>

## docs\_static\images\abc-llm-vulnerability-scan-results.png



�PNG

 


