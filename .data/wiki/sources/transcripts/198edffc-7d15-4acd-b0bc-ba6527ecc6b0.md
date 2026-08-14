---
source_id: "198edffc-7d15-4acd-b0bc-ba6527ecc6b0"
title: "open-policy-agent-opa-part-3.md"
notebook_id: 29bbaa7b-965f-40b5-a404-76b4d2e7308c
url: null
type: generated_text
exported: 2026-07-27
---

# open-policy-agent-opa-part-3.md
open-policy-agent/opa — continued — docs

Branch:

 

main

  |  

Source:

 https://github.com/open-policy-agent/opa

File tree

file ADOPTERS.md

 

file AGENTS.md

 

file CHANGELOG.md

 

file CODE_OF_CONDUCT.md

 

file COMMUNITY_GUIDELINES.md

 

file CONTRIBUTING.md

 

file Dockerfile

 

file Dockerfile.rego

 

file GOVERNANCE.md

 

file LICENSE

 

file MAINTAINERS.md

 

file Makefile

 

file README.md

 

file SECURITY.md

 

file SECURITY_AUDIT.pdf

 

file buf.yaml

 

file builtin_metadata.json

 

file capabilities.json

 

file go.mod

 

file go.sum

 

file main.go

 

file main_windows.go

 

file netlify.toml

 

dir ast/

 

file annotations.go

 

file builtins.go

 

file capabilities.go

 

file check.go

 

file compare.go

 

file compile.go

 

file compile_test.go

 

file compilehelper.go

 

file compilehelper_test.go

 

file conflicts.go

 

file doc.go

 

file env.go

 

file errors.go

 

file index.go

 

file interning.go

 

file map.go

 

file parser.go

 

file parser_ext.go

 

file parser_ext_test.go

 

file parser_test.go

 

file policy.go

 

file policy_test.go

 

file pretty.go

 

file schema.go

 

file strings.go

 

file term.go

 

file transform.go

 

file unify.go

 

file varset.go

 

file visit.go

 

dir ast/json/

 

file doc.go

 

file json.go

 

dir ast/location/

 

file doc.go

 

file location.go

 

dir build/

 

file bench-comment.sh

 

file build-release.sh

 

py changelog.py

 

file check-working-copy.sh

 

file commit-cli-docs.sh

 

file commit-wasm-bins.sh

 

file gen-cli-docs.sh

 

file gen-deb.sh

 

file gen-dev-patch.sh

 

file gen-man.sh

 

file gen-release-patch.sh

 

file gen-run-go.sh

 

file gen-windows-versioninfo.sh

 

file get-build-hostname.sh

 

file get-build-version.sh

 

file github-release.sh

 

file latest-release-notes.sh

 

file regen-methodless-template.sh

 

file release-patcher-Dockerfile

 

file run-wasm-rego-tests.sh

 

file time-bound.sh

 

file update-version.sh

 

file utils.sh

 

dir build/generate-cli-docs/

 

file generate.go

 

dir build/generate-extended-cases/

 

file exceptions.yaml

 

file extended_cases.go

 

file extended_cases_test.go

 

dir build/generate-extended-cases/testdata/

 

file plus_sign_builtin_only.json

 

dir build/generate-man/

 

file generate.go

 

dir build/lychee/

 

file repo.toml

 

file website.toml

 

dir build/policy/files/

 

file files.rego

 

file files_test.rego

 

dir build/policy/pr-check/

 

file pr_check.rego

 

file pr_check_test.rego

 

dir build/policy/schema/

 

file files.json

 

dir build/tools/

 

file go.mod

 

file go.sum

 

dir bundle/

 

file bundle.go

 

file bundle_test.go

 

file doc.go

 

file file.go

 

file filefs.go

 

file hash.go

 

file keys.go

 

file sign.go

 

file store.go

 

file store_test.go

 

file verify.go

 

dir capabilities/

 

file capabilities.go

 

file doc.go

 

file v0.17.0.json

 

file v0.17.1.json

 

file v0.17.2.json

 

file v0.17.3.json

 

file v0.18.0.json

 

file v0.19.0-rc1.json

 

file v0.19.0.json

 

file v0.19.1.json

 

file v0.19.2.json

 

file v0.20.0.json

 

file v0.20.1.json

 

file v0.20.2.json

 

file v0.20.3.json

 

file v0.20.4.json

 

file v0.20.5.json

 

file v0.21.0.json

 

file v0.21.1.json

 

file v0.22.0.json

 

file v0.23.0.json

 

file v0.23.1.json

 

file v0.23.2.json

 

file v0.24.0.json

 

file v0.25.0-rc1.json

 

file v0.25.0-rc2.json

 

file v0.25.0-rc3.json

 

file v0.25.0-rc4.json

 

file v0.25.0.json

 

file v0.25.1.json

 

file v0.25.2.json

 

file v0.26.0.json

 

file v0.27.0.json

 

file v0.27.1.json

 

file v0.28.0.json

 

file v0.29.0.json

 

file v0.29.1.json

 

file v0.29.2.json

 

file v0.29.3.json

 

file v0.29.4.json

 

file v0.30.0.json

 

file v0.30.1.json

 

file v0.30.2.json

 

file v0.31.0.json

 

file v0.32.0.json

 

file v0.32.1.json

 

file v0.33.0.json

 

file v0.33.1.json

 

file v0.34.0.json

 

file v0.34.1.json

 

file v0.34.2.json

 

file v0.35.0.json

 

file v0.36.0.json

 

file v0.36.1.json

 

file v0.37.0.json

 

file v0.37.1.json

 

file v0.37.2.json

 

file v0.38.0.json

 

file v0.38.1.json

 

file v0.39.0.json

 

file v0.40.0.json

 

file v0.41.0.json

 

file v0.42.0.json

 

file v0.42.1.json

 

file v0.42.2.json

 

file v0.43.0.json

 

file v0.43.1.json

 

file v0.44.0.json

 

file v0.45.0.json

 

file v0.46.0.json

 

file v0.46.1.json

 

file v0.46.2.json

 

file v0.46.3.json

 

file v0.47.0.json

 

file v0.47.1.json

 

file v0.47.2.json

 

file v0.47.3.json

 

file v0.47.4.json

 

file v0.48.0.json

 

file v0.49.0.json

 

file v0.49.1.json

 

file v0.49.2.json

 

file v0.50.0.json

 

file v0.50.1.json

 

file v0.50.2.json

 

file v0.51.0.json

 

file v0.52.0.json

 

file v0.53.0.json

 

file v0.53.1.json

 

file v0.54.0.json

 

file v0.55.0.json

 

file v0.56.0.json

 

file v0.57.0.json

 

file v0.57.1.json

 

file v0.58.0.json

 

file v0.59.0.json

 

file v0.60.0.json

 

file v0.61.0.json

 

file v0.62.0.json

 

file v0.62.1.json

 

file v0.63.0.json

 

file v0.64.0.json

 

file v0.64.1.json

 

file v0.65.0.json

 

file v0.66.0.json

 

file v0.67.0.json

 

file v0.67.1.json

 

file v0.68.0.json

 

file v0.69.0.json

 

file v0.70.0.json

 

file v1.0.0.json

 

file v1.0.1.json

 

file v1.1.0.json

 

file v1.10.0.json

 

file v1.11.0.json

 

file v1.11.1.json

 

file v1.12.0.json

 

file v1.12.1.json

 

file v1.12.2.json

 

file v1.12.3.json

 

file v1.13.0.json

 

file v1.13.1.json

 

file v1.13.2.json

 

file v1.14.0.json

 

file v1.14.1.json

 

file v1.15.0.json

 

file v1.15.1.json

 

file v1.16.0.json

 

file v1.16.1.json

 

file v1.16.2.json

 

file v1.17.0.json

 

file v1.17.1.json

 

file v1.18.0.json

 

file v1.18.1.json

 

file v1.18.2.json

 

file v1.2.0.json

 

file v1.3.0.json

 

file v1.4.0.json

 

file v1.4.1.json

 

file v1.4.2.json

 

file v1.5.0.json

 

file v1.5.1.json

 

file v1.6.0.json

 

file v1.7.0.json

 

file v1.8.0.json

 

file v1.9.0.json

 

dir cmd/

 

file bench.go

 

file bench_test.go

 

file build.go

 

file build_test.go

 

file capabilities.go

 

file capabilities_test.go

 

file check.go

 

file check_test.go

 

file commands.go

 

file deps.go

 

file deps_test.go

 

file doc.go

 

file eval.go

 

file eval_test.go

 

file eval_wasmtarget_test.go

 

file exec.go

 

file exec_test.go

 

file features.go

 

file filters.go

 

file flags.go

 

file fmt.go

 

file fmt_test.go

 

file inspect.go

 

file inspect_test.go

 

file oracle.go

 

file oracle_test.go

 

file parse.go

 

file parse_test.go

 

file refactor.go

 

file refactor_test.go

 

file run.go

 

file run_test.go

 

file sign.go

 

file sign_test.go

 

file test.go

 

file test_test.go

 

file utils.go

 

file version.go

 

file version_test.go

 

dir cmd/formats/

 

file formats.go

 

dir cmd/internal/env/

 

file env.go

 

file env_test.go

 

dir cmd/internal/exec/

 

file exec.go

 

file exec_test.go

 

file json_reporter.go

 

file json_reporter_test.go

 

file params.go

 

file params_test.go

 

file parser.go

 

file parser_test.go

 

file std_in_reader.go

 

file std_in_reader_test.go

 

dir compile/

 

file compile.go

 

file compile_test.go

 

file doc.go

 

dir config/

 

file config.go

 

file doc.go

 

dir cover/

 

file cover.go

 

file doc.go

 

dir debug/

 

file breakpoint.go

 

file debugger.go

 

file doc.go

 

file event.go

 

file frame.go

 

file thread.go

 

file variable.go

 

dir dependencies/

 

file deps.go

 

file doc.go

 

dir docs/

 

file Makefile

 

file README.md

 

file docusaurus.config.js

 

file dprint.json

 

file eslint.config.mjs

 

file glossary.yaml

 

file imported.json

 

file package-lock.json

 

file package.json

 

dir docs/bin/

 

file build-latest.sh

 

file eval-examples.sh

 

file import-regal-docs.sh

 

file import-rego-cheat-sheet.sh

 

file import-rego-style-guide.sh

 

file smoke-test.sh

 

dir docs/config/OPA/

 

file WeOur.yml

 

dir docs/config/config/vocabularies/Vale/

 

file accept.txt

 

file reject.txt

 

dir docs/devel/

 

file DEVELOPMENT.md

 

file RELEASE.md

 

dir docs/docs/

 

file aws-cloudformation-hooks.md

 

file cheatsheet.md

 

file cli.md

 

file configuration.md

 

file contrib-adding-builtin-functions.md

 

file contrib-code.md

 

file contrib-development.md

 

file contrib-docs.md

 

file contributing.md

 

file docker-authorization.md

 

file editor-and-ide-support.md

 

file extensions.md

 

file faq.md

 

file graphql-api-authorization.md

 

file http-api-authorization.md

 

file index.md

 

file integration.md

 

file ir.md

 

file kafka-authorization.md

 

file management-decision-logs.md

 

file management-discovery.md

 

file management-status.md

 

file monitoring.md

 

file oauth-oidc.md

 

file operations.md

 

file policy-language.md

 

file policy-performance.md

 

file policy-testing.md

 

file privacy.md

 

file rest-api.md

 

file security.md

 

file ssh-and-sudo-authorization.md

 

file storage.md

 

file style-guide.md

 

file terraform.md

 

file v0-compatibility.md

 

file wasm.md

 

dir docs/docs/assets/

 

file OverviewDiagram.jsx

 

dir docs/docs/cicd/

 

file 

category

.yaml

 

file index.md

 

file pr-checks.md

 

dir docs/docs/comparisons/

 

file access-control-systems.md

 

dir docs/docs/comparisons/languages/

 

file ex1.js

 

file ex2.js

 

file ex3.js

 

file go.md

 

file index.mdx

 

file java.md

 

file python.md

 

dir docs/docs/debugging/

 

file index.md

 

dir docs/docs/deploy/

 

file index.mdx

 

dir docs/docs/deploy/aws/

 

file ec2.mdx

 

file ecs.mdx

 

file eks.mdx

 

file index.mdx

 

dir docs/docs/deploy/azure/

 

file aks.mdx

 

file container-apps.mdx

 

file index.mdx

 

file vm.mdx

 

dir docs/docs/deploy/docker/

 

file index.md

 

dir docs/docs/deploy/google-cloud/

 

file cloud-run.mdx

 

file gce.mdx

 

file gke.mdx

 

file index.mdx

 

dir docs/docs/deploy/k8s/

 

file index.mdx

 

dir docs/docs/envoy/

 

file 

category

.yaml

 

file debugging.md

 

file index.md

 

file performance.md

 

file primer.md

 

file tutorial-gloo-edge.md

 

file tutorial-istio.md

 

file tutorial-standalone-envoy.md

 

dir docs/docs/errors/

 

file index.md

 

dir docs/docs/errors/eval-conflict-error/

 

file complete-rules-must-not-produce-multiple-outputs.md

 

file object-keys-must-be-unique.md

 

dir docs/docs/errors/rego-compile-error/

 

file assigned-var-name-unused.md

 

dir docs/docs/errors/rego-parse-error/

 

file unexpected-assign-token.md

 

file unexpected-identifier-token.md

 

file unexpected-left-curly-token.md

 

file unexpected-name-keyword.md

 

file unexpected-right-curly-token.md

 

file unexpected-string-token.md

 

file var-cannot-be-used-for-rule-name.md

 

dir docs/docs/errors/rego-recursion-error/

 

file rule-name-is-recursive.md

 

dir docs/docs/errors/rego-type-error/

 

file arity-mismatch.md

 

file conflicting-rules-name-found.md

 

file function-has-arity-got-argument.md

 

file match-error.md

 

file multiple-default-rules-name-found.md

 

file multiple-default-rules.md

 

file unsafe-built-in-function-calls-in-expression-name.md

 

dir docs/docs/errors/rego-unsafe-var-error/

 

file var-name-is-unsafe.md

 

dir docs/docs/external-data/

 

file index.md

 

dir docs/docs/filtering/

 

file column-masks.md

 

file fragment.md

 

file index.md

 

file partial-evaluation.md

 

file tutorial-sql-filtering.md

 

file ucast-syntax.md

 

dir docs/docs/kubernetes/

 

file 

category

.yaml

 

file debugging.md

 

file index.md

 

file primer.md

 

file tutorial.md

 

dir docs/docs/management-bundles/

 

file index.md

 

dir docs/docs/management-introduction/

 

file index.md

 

dir docs/docs/management-introduction/assets/

 

file ControlPlaneDiagram.jsx

 

file DistributedDiagram.jsx

 

file HostLocalDiagram.jsx

 

dir docs/docs/ocp/

 

file api-reference.md

 

file authentication.md

 

file concepts.md

 

file configuration.md

 

file guide-deploy-as-a-service.md

 

file index.md

 

dir docs/docs/philosophy/

 

file index.md

 

dir docs/docs/policy-reference/

 

file index.md

 

dir docs/docs/policy-reference/_examples/aggregates/count/list_size/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/aggregates/sum/total_replicas/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/crypto/digest_verification/

 

file config.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/encoding/envoy_header_manipulation/

 

file config.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/glob/domain_matching/

 

file config.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/glob/image_matching/

 

file config.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/graphs/reachable/

 

file config.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/graphs/reachable_paths/

 

file config.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/io.jwt/decode_verify/cert/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/io.jwt/decode_verify/jwks/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/io.jwt/decode_verify/jwks_groups/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/io.jwt/decode_verify/jwks_time/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/io.jwt/decode_verify/symmetric/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/io.jwt/encode_sign/empty_json/

 

file config.json

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/io.jwt/encode_sign/hmac/

 

file config.json

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/io.jwt/encode_sign/rsa/

 

file config.json

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/io.jwt/encode_sign/sign/

 

file config.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/io.jwt/encode_sign_raw/sign_raw/

 

file config.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/io.jwt/verify_es256/cert/

 

file config.json

 

file intro.md

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/io.jwt/verify_es256/jwks/

 

file config.json

 

file intro.md

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/net/cidr_contains_array_string/

 

file config.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/net/cidr_contains_arrays/

 

file config.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/net/cidr_contains_objects/

 

file config.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/net/cidr_contains_strings/

 

file config.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/regex/find_all_string_submatch_n/email_plus_addressing/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/regex/find_all_string_submatch_n/scope_parsing/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/regex/globs_match/role_patterns/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/regex/match/case-insensitive/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file outro.md

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/regex/match/email/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/regex/match/names/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/regex/match/paths/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/regex/template_match/path_pattern/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/rego/rule_metadata/

 

file config.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/semver/isvalid/

 

file config.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/strings/contains/content-moderation/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/strings/contains/email-validation/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/time/clock/local_business_hours/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/time/format/local_time/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/time/now_ns/past/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/time/parse_ns/period/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/_examples/time/parse_ns/time_format/

 

file config.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/builtins/

 

file aggregates.mdx

 

file array.mdx

 

file bits.mdx

 

file comparison.mdx

 

file conversions.mdx

 

file crypto.mdx

 

file encoding.mdx

 

file glob.mdx

 

file graph.mdx

 

file graphql.mdx

 

file http.mdx

 

file index.mdx

 

file net.mdx

 

file numbers.mdx

 

file object.mdx

 

file opa.mdx

 

file providers.aws.mdx

 

file regex.mdx

 

file rego.mdx

 

file semver.mdx

 

file sets.mdx

 

file strings.mdx

 

file time.mdx

 

file tokens.go

 

file tokens.mdx

 

file tokensign.mdx

 

file tracing.mdx

 

file types.mdx

 

file units.mdx

 

file uuid.mdx

 

dir docs/docs/policy-reference/keywords/

 

file 

category

.json

 

file contains.md

 

file default.md

 

file every.md

 

file if.md

 

file import.md

 

file not.md

 

file some.md

 

dir docs/docs/policy-reference/keywords/_examples/contains/aggregated-validation/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/keywords/_examples/contains/error-codes/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/keywords/_examples/contains/object-validation/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/keywords/_examples/contains/todo-list/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/keywords/_examples/default/deny/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/keywords/_examples/default/overrides/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/keywords/_examples/every/feature-flags/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/keywords/_examples/every/internal-meetings/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/keywords/_examples/if/boolean/

 

file config.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/keywords/_examples/if/functions/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/keywords/_examples/if/multi-value/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/keywords/_examples/if/when-not/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/keywords/_examples/not/negation/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/keywords/_examples/not/undefined/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/keywords/_examples/some/some-in/

 

file data.json

 

file input.json

 

file intro.md

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/keywords/_examples/some/some-in-object/

 

file data.json

 

file input.json

 

file intro.md

 

file policy.rego

 

file title.txt

 

dir docs/docs/policy-reference/keywords/_examples/some/some-iteration/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/docs/v0-upgrade/

 

file index.md

 

dir docs/functions/

 

file badge.ts

 

file feedback.ts

 

file version-redirect.ts

 

dir docs/projects/regal/

 

file adopters.md

 

file architecture.md

 

file cicd.md

 

file cli.md

 

file debug-adapter.md

 

file editor-support.md

 

file fixing.md

 

file index.md

 

file integration.md

 

file language-server.md

 

file opa-one-dot-zero.md

 

file pre-commit-hooks.md

 

file remote-features.md

 

dir docs/projects/regal/configuration/

 

file capabilities.md

 

file ignore-rules.md

 

file index.md

 

file project-roots.md

 

file rego-version.md

 

dir docs/projects/regal/custom-rules/

 

file index.md

 

file roast.md

 

dir docs/projects/regal/rules/

 

file 

category

.json

 

file index.md

 

file index.md.yaml

 

dir docs/projects/regal/rules/bugs/

 

file annotation-without-metadata.md

 

file argument-always-wildcard.md

 

file constant-condition.md

 

file deprecated-builtin.md

 

file duplicate-rule.md

 

file if-empty-object.md

 

file if-object-literal.md

 

file import-shadows-rule.md

 

file impossible-not.md

 

file inconsistent-args.md

 

file index.md

 

file index.md.yaml

 

file internal-entrypoint.md

 

file invalid-metadata-attribute.md

 

file invalid-regexp.md

 

file leaked-internal-reference.md

 

file not-equals-in-loop.md

 

file redundant-existence-check.md

 

file redundant-loop-count.md

 

file rule-assigns-default.md

 

file rule-named-if.md

 

file rule-shadows-builtin.md

 

file sprintf-arguments-mismatch.md

 

file time-now-ns-twice.md

 

file top-level-iteration.md

 

file unassigned-return-value.md

 

file unused-output-variable.md

 

file unused-return-value.md

 

file var-shadows-builtin.md

 

file zero-arity-function.md

 

dir docs/projects/regal/rules/custom/

 

file chained-rule-body.md

 

file disallow-rego-v1.md

 

file forbidden-function-call.md

 

file index.md

 

file index.md.yaml

 

file missing-metadata.md

 

file naming-convention.md

 

file narrow-argument.md

 

file one-liner-rule.md

 

file prefer-value-in-head.md

 

dir docs/projects/regal/rules/idiomatic/

 

file ambiguous-scope.md

 

file boolean-assignment.md

 

file custom-has-key-construct.md

 

file custom-in-construct.md

 

file directory-package-mismatch.md

 

file equals-pattern-matching.md

 

file in-wildcard-key.md

 

file index.md

 

file index.md.yaml

 

file no-defined-entrypoint.md

 

file non-raw-regex-pattern.md

 

file prefer-equals-comparison.md

 

file prefer-set-or-object-rule.md

 

file single-item-in.md

 

file superfluous-object-get.md

 

file use-array-flatten.md

 

file use-contains.md

 

file use-if.md

 

file use-in-operator.md

 

file use-object-keys.md

 

file use-object-union-n.md

 

file use-some-for-output-vars.md

 

file use-strings-count.md

 

dir docs/projects/regal/rules/imports/

 

file avoid-importing-input.md

 

file circular-import.md

 

file confusing-alias.md

 

file ignored-import.md

 

file implicit-future-keywords.md

 

file import-after-rule.md

 

file import-shadows-builtin.md

 

file import-shadows-import.md

 

file index.md

 

file index.md.yaml

 

file pointless-import.md

 

file prefer-package-imports.md

 

file redundant-alias.md

 

file redundant-data-import.md

 

file unresolved-import.md

 

file unresolved-reference.md

 

file use-rego-v1.md

 

dir docs/projects/regal/rules/performance/

 

file defer-assignment.md

 

file equals-over-count.md

 

file index.md

 

file index.md.yaml

 

file non-loop-expression.md

 

file walk-no-path.md

 

file with-outside-test-context.md

 

dir docs/projects/regal/rules/style/

 

file avoid-get-and-list-prefix.md

 

file comprehension-term-assignment.md

 

file default-over-else.md

 

file default-over-not.md

 

file detached-metadata.md

 

file double-negative.md

 

file external-reference.md

 

file file-length.md

 

file function-arg-return.md

 

file index.md

 

file index.md.yaml

 

file line-length.md

 

file messy-rule.md

 

file mixed-iteration.md

 

file no-whitespace-comment.md

 

file opa-fmt.md

 

file pointless-reassignment.md

 

file prefer-snake-case.md

 

file prefer-some-in-iteration.md

 

file rule-length.md

 

file rule-name-repeats-package.md

 

file todo-comment.md

 

file trailing-default-rule.md

 

file unconditional-assignment.md

 

file unnecessary-some.md

 

file use-assignment-operator.md

 

file use-in-operator.md

 

file yoda-condition.md

 

dir docs/projects/regal/rules/testing/

 

file dubious-print-sprintf.md

 

file file-missing-test-suffix.md

 

file identically-named-tests.md

 

file index.md

 

file index.md.yaml

 

file metasyntactic-variable.md

 

file print-or-trace-call.md

 

file test-outside-test-package.md

 

file todo-test.md

 

dir docs/src/

 

file Archive.jsx

 

file EcosystemEntry.jsx

 

file EcosystemFeature.jsx

 

file EcosystemLanguage.jsx

 

file EventPage.jsx

 

file EventPage.module.css

 

dir docs/src/SurveyEvent/

 

file index.jsx

 

file styles.module.css

 

dir docs/src/components/BuiltinLegacyRedirect/

 

file index.jsx

 

dir docs/src/components/BuiltinSearch/

 

file index.jsx

 

file styles.module.css

 

dir docs/src/components/BuiltinTable/

 

file index.jsx

 

file styles.module.css

 

dir docs/src/components/Card/

 

file index.jsx

 

file styles.module.css

 

dir docs/src/components/CardGrid/

 

file index.jsx

 

file styles.module.css

 

dir docs/src/components/CommandDoc/

 

file index.jsx

 

file styles.module.css

 

dir docs/src/components/CommandList/

 

file index.jsx

 

file styles.module.css

 

dir docs/src/components/CopyPageMarkdown/

 

file index.jsx

 

file styles.module.css

 

dir docs/src/components/EcosystemEmbed/

 

file index.jsx

 

dir docs/src/components/EcosystemFeatureLink/

 

file index.jsx

 

dir docs/src/components/Event/AgendaItem/

 

file index.jsx

 

file styles.module.css

 

dir docs/src/components/Event/Countdown/

 

file index.jsx

 

file styles.module.css

 

dir docs/src/components/Event/SessionCard/

 

file index.jsx

 

file styles.module.css

 

dir docs/src/components/EvergreenCodeBlock/

 

file index.jsx

 

dir docs/src/components/FeedbackForm/

 

file index.jsx

 

file styles.module.css

 

dir docs/src/components/GlossaryTooltip/

 

file index.jsx

 

file styles.module.css

 

dir docs/src/components/InlineEditable/

 

file index.jsx

 

file styles.module.css

 

dir docs/src/components/NavbarItems/

 

file CurrentVersionNavbarItem.jsx

 

file KapaSearchNavbarItem.jsx

 

file KapaSearchNavbarItem.module.css

 

file styles.module.css

 

dir docs/src/components/ParamCodeBlock/

 

file index.jsx

 

file styles.module.css

 

dir docs/src/components/ParamContext/

 

file index.js

 

dir docs/src/components/ParamProvider/

 

file index.jsx

 

dir docs/src/components/PlaygroundExample/

 

file index.jsx

 

dir docs/src/components/QuestionComparison/

 

file index.jsx

 

file styles.module.css

 

dir docs/src/components/QuestionSingle/

 

file index.jsx

 

file styles.module.css

 

dir docs/src/components/RunSnippet/

 

file index.jsx

 

file styles.module.css

 

dir docs/src/components/SideBySide/

 

file Column.jsx

 

file Container.jsx

 

file styles.module.css

 

dir docs/src/components/SideBySideLanguageComparison/

 

file index.jsx

 

file styles.module.css

 

dir docs/src/components/SidebarTitle/

 

file index.js

 

dir docs/src/components/StandaloneLayout/

 

file index.jsx

 

file styles.module.css

 

dir docs/src/components/charts/

 

file index.js

 

dir docs/src/components/charts/BarChart/

 

file index.jsx

 

dir docs/src/components/charts/HorizontalBarChart/

 

file index.jsx

 

dir docs/src/components/charts/StackedBarChart/

 

file index.jsx

 

dir docs/src/components/charts/TextList/

 

file index.jsx

 

file styles.module.css

 

dir docs/src/components/projects/regal/Intro/

 

file index.jsx

 

file styles.module.css

 

dir docs/src/components/projects/regal/RulesTable/

 

file index.jsx

 

file styles.module.css

 

dir docs/src/css/

 

file custom.css

 

dir docs/src/data/

 

file cli.json

 

dir docs/src/data/ecosystem/entries/

 

file alfred.md

 

file alluxio.md

 

file antlr.md

 

file apache-apisix.md

 

file aserto.md

 

file atmos.md

 

file awesome-opa.md

 

file aws-api-gateway.md

 

file aws-cloudformation-hook.md

 

file backstage.md

 

file big-acl.md

 

file boomerang-bosun.md

 

file bottle.md

 

file carbonetes.md

 

file ceph.md

 

file chef-automate.md

 

file circleci.md

 

file clair-datasource.md

 

file clojure.md

 

file cloudflare-worker.md

 

file conforma.md

 

file conftest.md

 

file coredns-authz.md

 

file cosign.md

 

file custom-library-microservice-authorization.md

 

file dapr.md

 

file dart-authorization.md

 

file dependency-management-data.md

 

file digger.md

 

file docker-machine.md

 

file easegress.md

 

file elasticsearch-datafiltering.md

 

file emissary-ingress.md

 

file env0.md

 

file envoy-authorization.md

 

file eopa.md

 

file fairwinds-insights.md

 

file fiber.md

 

file fig.md

 

file flask-opa.md

 

file flipt.md

 

file gatekeeper.md

 

file ghostunnel.md

 

file github-action-opa-rego-test.md

 

file gloo-api-gateway.md

 

file google-calendar.md

 

file google-kubernetes-engine.md

 

file gradle-plugin.md

 

file graphql.md

 

file i2scim.md

 

file iptables.md

 

file jenkins-job-authorization.md

 

file kafka-authorization.md

 

file kong-authorization.md

 

file kopa.md

 

file kubernetes-authorization.md

 

file kubernetes-provisioning.md

 

file kubernetes-validating-admission.md

 

file kubescape.md

 

file kubeshield.md

 

file kubestellar-console.md

 

file legitify.md

 

file linux-pam.md

 

file lula.md

 

file magda.md

 

file minio.md

 

file moat.md

 

file nacp.md

 

file nginx.md

 

file nopa.md

 

file oauth2.md

 

file ocpr.md

 

file oidc.md

 

file opa-aspnetcore.md

 

file opa-csharp.md

 

file opa-dotnet-asp-core.md

 

file opa-dotnet.md

 

file opa-golang.md

 

file opa-java-client.md

 

file opa-java-wasm.md

 

file opa-java.md

 

file opa-mcp.md

 

file opa-nats.md

 

file opa-playground.md

 

file opa-python.md

 

file opa-springboot.md

 

file opa-typescript.md

 

file opa-wasm-dotnet.md

 

file opa-wasm-java.md

 

file opa-wasm-js.md

 

file opa-wasm-rust.md

 

file opa-wasm-zig.md

 

file opal.md

 

file open-service-mesh.md

 

file openfaas-function-authorization.md

 

file optoggles.md

 

file ossrisk.md

 

file permit.md

 

file php-authorization.md

 

file pomerium-authz.md

 

file pre-commit-hooks.md

 

file principled-evolution.md

 

file pulumi.md

 

file raygun.md

 

file regal.md

 

file rego-cheat-sheet.md

 

file rego-test-assertions.md

 

file regocpp.md

 

file regoround.md

 

file rekor.md

 

file reposaur.md

 

file rond.md

 

file sansshell.md

 

file scalr-iacp.md

 

file spacelift.md

 

file sphinx-rego.md

 

file spinnaker-pipeline.md

 

file spire.md

 

file springsecurity-api.md

 

file sql-datafiltering.md

 

file strimzi.md

 

file swift-opa.md

 

file sysdig-image-scanner.md

 

file tavoai.md

 

file terraform-cloud.md

 

file terraform.md

 

file topaz.md

 

file torque.md

 

file traefik-api-gateway.md

 

file trino.md

 

file vscode-opa.md

 

file vulnetix.md

 

file waltid.md

 

file wirelesssecuritylab.md

 

file zed-rego.md

 

dir docs/src/data/ecosystem/feature-categories/

 

file createwithopa.md

 

file production.md

 

file rego.md

 

file tool.md

 

dir docs/src/data/ecosystem/features/

 

file debugging-rego.md

 

file editors.md

 

file envoy.md

 

file external-data-realtime-push.md

 

file external-data-runtime.md

 

file external-data.md

 

file go-integration.md

 

file kubernetes.md

 

file learning-rego.md

 

file opa-bundles-discovery.md

 

file opa-bundles.md

 

file policy-testing.md

 

file rest-api-integration.md

 

file status-api.md

 

file terraform.md

 

file wasm-integration.md

 

dir docs/src/data/ecosystem/languages/

 

file clojure.md

 

file csharp.md

 

file golang.md

 

file java.md

 

file javascript.md

 

file php.md

 

file rust.md

 

file swift.md

 

file zig.md

 

dir docs/src/data/events/

 

file 2026-kubecon-eu.json

 

file 2026-kubecon-na.json

 

dir docs/src/data/surveys/events/2021/

 

file metadata.json

 

dir docs/src/data/surveys/events/2021/how-long-have-you-been-using-opa/

 

file data.json

 

dir docs/src/data/surveys/events/2021/how-many-opa-instances-do-you-have-deployed/

 

file data.json

 

dir docs/src/data/surveys/events/2021/what-stage-of-production-is-your-most-advanced-use/

 

file data.json

 

dir docs/src/data/surveys/events/2021/which-of-the-following-use-cases-do-you-have-for-o/

 

file data.json

 

dir docs/src/data/surveys/events/2022/

 

file metadata.json

 

dir docs/src/data/surveys/events/2022/how-long-have-you-been-using-opa/

 

file data.json

 

dir docs/src/data/surveys/events/2022/what-stage-of-production-is-your-most-advanced-use/

 

file data.json

 

dir docs/src/data/surveys/events/2025/

 

file metadata.json

 

dir docs/src/data/surveys/events/2025/any-missing-integrations-or-coverage-for-new-use-c/

 

file data.json

 

dir docs/src/data/surveys/events/2025/any-success-and-failures-with-generative-ai-toolin/

 

file data.json

 

dir docs/src/data/surveys/events/2025/community-project-use/

 

file data.json

 

dir docs/src/data/surveys/events/2025/company-size/

 

file data.json

 

dir docs/src/data/surveys/events/2025/country-of-residence/

 

file data.json

 

dir docs/src/data/surveys/events/2025/do-you-find-the-documentation-for-opa-envoy-to-be-/

 

file data.json

 

dir docs/src/data/surveys/events/2025/do-you-have-a-need-to-extend-or-replace-kubernetes/

 

file data.json

 

dir docs/src/data/surveys/events/2025/do-you-have-any-other-feedback-or-comments-to-shar/

 

file data.json

 

dir docs/src/data/surveys/events/2025/does-regal-help-you-find-bugs/

 

file data.json

 

dir docs/src/data/surveys/events/2025/does-regals-documentation-help-you-fix-the-bugs-yo/

 

file data.json

 

dir docs/src/data/surveys/events/2025/gatekeeper-performance-met-our-needs/

 

file data.json

 

dir docs/src/data/surveys/events/2025/how-did-you-first-find-out-about-opa/

 

file data.json

 

dir docs/src/data/surveys/events/2025/how-do-you-deploy-opa-envoy/

 

file data.json

 

dir docs/src/data/surveys/events/2025/how-do-you-manage-policy-for-opa-envoy/

 

file data.json

 

dir docs/src/data/surveys/events/2025/how-do-you-use-opa-for-genai-workloads/

 

file data.json

 

dir docs/src/data/surveys/events/2025/how-do-you-use-regal/

 

file data.json

 

dir docs/src/data/surveys/events/2025/how-does-your-organization-distribute-and-consume-/

 

file data.json

 

dir docs/src/data/surveys/events/2025/how-easy-or-difficult-was-it-to-deploy-and-configu/

 

file data.json

 

dir docs/src/data/surveys/events/2025/how-likely-are-you-to-recommend-opa-gatekeeper-to-/

 

file data.json

 

dir docs/src/data/surveys/events/2025/how-long-have-you-been-using-gatekeeper-for/

 

file data.json

 

dir docs/src/data/surveys/events/2025/how-long-have-you-been-using-opa/

 

file data.json

 

dir docs/src/data/surveys/events/2025/how-many-opa-instances-do-you-have-deployed/

 

file data.json

 

dir docs/src/data/surveys/events/2025/how-many-teams-use-opa-within-your-company/

 

file data.json

 

dir docs/src/data/surveys/events/2025/how-often-do-you-write-rego-code-in-your-team/

 

file data.json

 

dir docs/src/data/surveys/events/2025/how-satisfied-are-you-with-using-opa-gatekeeper/

 

file data.json

 

dir docs/src/data/surveys/events/2025/how-would-you-best-describe-your-current-use-of-op/

 

file data.json

 

dir docs/src/data/surveys/events/2025/how-would-you-describe-your-expertise-with-kuberne/

 

file data.json

 

dir docs/src/data/surveys/events/2025/how-would-you-describe-your-expertise-with-policy-/

 

file data.json

 

dir docs/src/data/surveys/events/2025/i-learned-rego-and-opa-using-the-following-resourc/

 

file data.json

 

dir docs/src/data/surveys/events/2025/i-make-use-of-the-following-management-api-feature/

 

file data.json

 

dir docs/src/data/surveys/events/2025/i-use-opa/

 

file data.json

 

dir docs/src/data/surveys/events/2025/i-wish-rego-was-more-like/

 

file data.json

 

dir docs/src/data/surveys/events/2025/if-you-havent-been-able-to-use-opa-for-a-project-o/

 

file data.json

 

dir docs/src/data/surveys/events/2025/if-you-want-to-but-havent-yet-whats-stopped-you-fr/

 

file data.json

 

dir docs/src/data/surveys/events/2025/main-programming-languages-used-at-my-workplace/

 

file data.json

 

dir docs/src/data/surveys/events/2025/my-use-case-for-opa-requires-the-response-latency-/

 

file data.json

 

dir docs/src/data/surveys/events/2025/personal-text-editor-or-ide-of-choice/

 

file data.json

 

dir docs/src/data/surveys/events/2025/stories-to-share-about-opa-adoption-in-your-team-a/

 

file data.json

 

dir docs/src/data/surveys/events/2025/tell-us-anything-else-youd-like-us-to-know-about-h/

 

file data.json

 

dir docs/src/data/surveys/events/2025/what-additional-integration-documentation-would-yo/

 

file data.json

 

dir docs/src/data/surveys/events/2025/what-challenges-have-you-encountered-when-adopting/

 

file data.json

 

dir docs/src/data/surveys/events/2025/what-changes-or-new-features-would-most-improve-yo/

 

file data.json

 

dir docs/src/data/surveys/events/2025/what-features-would-you-like-to-see-added-to-gk/

 

file data.json

 

dir docs/src/data/surveys/events/2025/what-features-would-you-like-to-see-added-to-opa-e/

 

file data.json

 

dir docs/src/data/surveys/events/2025/what-if-anything-do-you-dislike-about-using-opa-ga/

 

file data.json

 

dir docs/src/data/surveys/events/2025/what-if-anything-do-you-like-about-using-opa-gatek/

 

file data.json

 

dir docs/src/data/surveys/events/2025/what-stage-of-production-is-your-most-advanced-use/

 

file data.json

 

dir docs/src/data/surveys/events/2025/what-technologies-do-your-services-use-alongside-o/

 

file data.json

 

dir docs/src/data/surveys/events/2025/what-typical-latencies-do-you-observe-for-opa-resp/

 

file data.json

 

dir docs/src/data/surveys/events/2025/which-conftest-commands-does-your-organization-use/

 

file data.json

 

dir docs/src/data/surveys/events/2025/which-gatekeeper-features-do-you-currently-use/

 

file data.json

 

dir docs/src/data/surveys/events/2025/which-kubernetes-distributions-or-platforms-do-you/

 

file data.json

 

dir docs/src/data/surveys/events/2025/which-of-the-following-open-source-policy-librarie/

 

file data.json

 

dir docs/src/data/surveys/events/2025/which-of-the-following-use-cases-do-you-have-for-o/

 

file data.json

 

dir docs/src/data/surveys/events/2025/which-other-policy-management-tools-have-you-used-/

 

file data.json

 

dir docs/src/data/surveys/events/2025/which-types-of-policies-have-you-primarily-used-wi/

 

file data.json

 

dir docs/src/data/surveys/events/2025/years-of-professional-experience/

 

file data.json

 

dir docs/src/data/surveys/events/2025/your-roletitle/

 

file data.json

 

dir docs/src/data/surveys/questions/any-missing-integrations-or-coverage-for-new-use-c/

 

file data.json

 

dir docs/src/data/surveys/questions/any-success-and-failures-with-generative-ai-toolin/

 

file data.json

 

dir docs/src/data/surveys/questions/community-project-use/

 

file data.json

 

dir docs/src/data/surveys/questions/company-size/

 

file data.json

 

dir docs/src/data/surveys/questions/country-of-residence/

 

file data.json

 

dir docs/src/data/surveys/questions/do-you-find-the-documentation-for-opa-envoy-to-be-/

 

file data.json

 

dir docs/src/data/surveys/questions/do-you-have-a-need-to-extend-or-replace-kubernetes/

 

file data.json

 

dir docs/src/data/surveys/questions/do-you-have-any-other-feedback-or-comments-to-shar/

 

file data.json

 

dir docs/src/data/surveys/questions/does-regal-help-you-find-bugs/

 

file data.json

 

dir docs/src/data/surveys/questions/does-regals-documentation-help-you-fix-the-bugs-yo/

 

file data.json

 

dir docs/src/data/surveys/questions/gatekeeper-performance-met-our-needs/

 

file data.json

 

dir docs/src/data/surveys/questions/how-did-you-first-find-out-about-opa/

 

file data.json

 

dir docs/src/data/surveys/questions/how-do-you-deploy-opa-envoy/

 

file data.json

 

dir docs/src/data/surveys/questions/how-do-you-manage-policy-for-opa-envoy/

 

file data.json

 

dir docs/src/data/surveys/questions/how-do-you-use-opa-for-genai-workloads/

 

file data.json

 

dir docs/src/data/surveys/questions/how-do-you-use-regal/

 

file data.json

 

dir docs/src/data/surveys/questions/how-does-your-organization-distribute-and-consume-/

 

file data.json

 

dir docs/src/data/surveys/questions/how-easy-or-difficult-was-it-to-deploy-and-configu/

 

file data.json

 

dir docs/src/data/surveys/questions/how-likely-are-you-to-recommend-opa-gatekeeper-to-/

 

file data.json

 

dir docs/src/data/surveys/questions/how-long-have-you-been-using-gatekeeper-for/

 

file data.json

 

dir docs/src/data/surveys/questions/how-long-have-you-been-using-opa/

 

file data.json

 

dir docs/src/data/surveys/questions/how-many-opa-instances-do-you-have-deployed/

 

file data.json

 

dir docs/src/data/surveys/questions/how-many-teams-use-opa-within-your-company/

 

file data.json

 

dir docs/src/data/surveys/questions/how-often-do-you-write-rego-code-in-your-team/

 

file data.json

 

dir docs/src/data/surveys/questions/how-satisfied-are-you-with-using-opa-gatekeeper/

 

file data.json

 

dir docs/src/data/surveys/questions/how-would-you-best-describe-your-current-use-of-op/

 

file data.json

 

dir docs/src/data/surveys/questions/how-would-you-describe-your-expertise-with-kuberne/

 

file data.json

 

dir docs/src/data/surveys/questions/how-would-you-describe-your-expertise-with-policy-/

 

file data.json

 

dir docs/src/data/surveys/questions/i-learned-rego-and-opa-using-the-following-resourc/

 

file data.json

 

dir docs/src/data/surveys/questions/i-make-use-of-the-following-management-api-feature/

 

file data.json

 

dir docs/src/data/surveys/questions/i-use-opa/

 

file data.json

 

dir docs/src/data/surveys/questions/i-wish-rego-was-more-like/

 

file data.json

 

dir docs/src/data/surveys/questions/if-you-havent-been-able-to-use-opa-for-a-project-o/

 

file data.json

 

dir docs/src/data/surveys/questions/if-you-want-to-but-havent-yet-whats-stopped-you-fr/

 

file data.json

 

dir docs/src/data/surveys/questions/main-programming-languages-used-at-my-workplace/

 

file data.json

 

dir docs/src/data/surveys/questions/my-use-case-for-opa-requires-the-response-latency-/

 

file data.json

 

dir docs/src/data/surveys/questions/personal-text-editor-or-ide-of-choice/

 

file data.json

 

dir docs/src/data/surveys/questions/stories-to-share-about-opa-adoption-in-your-team-a/

 

file data.json

 

dir docs/src/data/surveys/questions/tell-us-anything-else-youd-like-us-to-know-about-h/

 

file data.json

 

dir docs/src/data/surveys/questions/what-additional-integration-documentation-would-yo/

 

file data.json

 

dir docs/src/data/surveys/questions/what-challenges-have-you-encountered-when-adopting/

 

file data.json

 

dir docs/src/data/surveys/questions/what-changes-or-new-features-would-most-improve-yo/

 

file data.json

 

dir docs/src/data/surveys/questions/what-features-would-you-like-to-see-added-to-gk/

 

file data.json

 

dir docs/src/data/surveys/questions/what-features-would-you-like-to-see-added-to-opa-e/

 

file data.json

 

dir docs/src/data/surveys/questions/what-if-anything-do-you-dislike-about-using-opa-ga/

 

file data.json

 

dir docs/src/data/surveys/questions/what-if-anything-do-you-like-about-using-opa-gatek/

 

file data.json

 

dir docs/src/data/surveys/questions/what-stage-of-production-is-your-most-advanced-use/

 

file data.json

 

dir docs/src/data/surveys/questions/what-technologies-do-your-services-use-alongside-o/

 

file data.json

 

dir docs/src/data/surveys/questions/what-typical-latencies-do-you-observe-for-opa-resp/

 

file data.json

 

dir docs/src/data/surveys/questions/which-conftest-commands-does-your-organization-use/

 

file data.json

 

dir docs/src/data/surveys/questions/which-gatekeeper-features-do-you-currently-use/

 

file data.json

 

dir docs/src/data/surveys/questions/which-kubernetes-distributions-or-platforms-do-you/

 

file data.json

 

dir docs/src/data/surveys/questions/which-of-the-following-open-source-policy-librarie/

 

file data.json

 

dir docs/src/data/surveys/questions/which-of-the-following-use-cases-do-you-have-for-o/

 

file data.json

 

dir docs/src/data/surveys/questions/which-other-policy-management-tools-have-you-used-/

 

file data.json

 

dir docs/src/data/surveys/questions/which-types-of-policies-have-you-primarily-used-wi/

 

file data.json

 

dir docs/src/data/surveys/questions/years-of-professional-experience/

 

file data.json

 

dir docs/src/data/surveys/questions/your-roletitle/

 

file data.json

 

dir docs/src/lib/

 

file kapa.js

 

file pageMarkdown.js

 

file playground.js

 

file sidebar-auto.js

 

file sidebars.js

 

dir docs/src/lib/ecosystem/

 

file getLogoAsset.js

 

file loadPages.js

 

file sortPagesByRank.js

 

dir docs/src/lib/events/

 

file loadEvents.js

 

dir docs/src/lib/plugins/

 

file markdownExport.js

 

dir docs/src/lib/projects/regal/

 

file loadRules.js

 

dir docs/src/lib/surveys/

 

file loadSurveyData.js

 

dir docs/src/pages/

 

file index.jsx

 

file index.module.css

 

file security.mdx

 

dir docs/src/pages/_examples/admin/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/src/pages/_examples/ai/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/src/pages/_examples/app/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/src/pages/_examples/envoy/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/src/pages/_examples/k8s/

 

file config.json

 

file data.json

 

file input.json

 

file intro.md

 

file output.json

 

file policy.rego

 

file title.txt

 

dir docs/src/pages/assets/

 

file README.md

 

dir docs/src/pages/assets/logos/

 

file allstate-dark.svg

 

file allstate-light.svg

 

file atlassian-dark.svg

 

file atlassian-light.svg

 

file bankdata-dark.svg

 

file bankdata-light.svg

 

file bloomberg-dark.svg

 

file bloomberg-light.svg

 

file bny-dark.svg

 

file bny-light.svg

 

file capital-one-dark.svg

 

file capital-one-light.svg

 

file cisco-dark.svg

 

file cisco-light.svg

 

file goldman-sachs-dark.svg

 

file goldman-sachs-light.svg

 

file intuit-dark.svg

 

file intuit-light.svg

 

file marsh-mclennan-dark.svg

 

file marsh-mclennan-light.svg

 

file pinterest-dark.svg

 

file pinterest-light.svg

 

file sugarcrm-dark.svg

 

file sugarcrm-light.svg

 

file t-mobile-dark.svg

 

file t-mobile-light.svg

 

file tripadvisor-dark.svg

 

file tripadvisor-light.svg

 

file vodafone-dark.svg

 

file vodafone-light.svg

 

file zalando-dark.svg

 

file zalando-light.svg

 

dir docs/src/pages/community/

 

file index.jsx

 

dir docs/src/pages/ecosystem/

 

file index.jsx

 

file styles.module.css

 

dir docs/src/pages/support/

 

file index.jsx

 

dir docs/src/pages/survey/

 

file index.jsx

 

dir docs/src/theme/

 

file MDXComponents.js

 

file prism-include-languages.js

 

file prism-rego.js

 

dir docs/src/theme/ColorModeToggle/

 

file index.jsx

 

file styles.module.css

 

dir docs/src/theme/DocItem/Content/

 

file index.jsx

 

dir docs/src/theme/NavbarItem/

 

file ComponentTypes.js

 

dir docs/src/theme/NotFound/

 

file index.jsx

 

dir docs/src/theme/NotFound/Content/

 

file index.jsx

 

dir docs/static/

 

file _redirects

 

file cheatsheet.pdf

 

file favicon.ico

 

file favicon.svg

 

file llms.txt

 

file netlify-forms.html

 

file robots.txt

 

file site.webmanifest

 

dir docs/static/external-resources/

 

file README.md

 

dir docs/static/external-resources/bundles/

 

file helm-kubernetes-quickstart

 

dir docs/static/external-resources/bundles/envoy/

 

file authz

 

dir docs/static/external-resources/bundles/istio/

 

file authz

 

dir docs/static/external-resources/bundles/kubernetes/

 

file admission

 

dir docs/static/img/ecosystem-entry-logos/

 

file aws-cloudformation-hook.svg

 

file backstage.svg

 

file easegress.svg

 

file enterprise-contract.svg

 

file kopa.svg

 

file kubestellar-console.svg

 

file lula.svg

 

file oauth2.svg

 

file ocpr.svg

 

file opa-wasm-zig.svg

 

file ossrisk.svg

 

file principled-evolution.svg

 

file regocpp.svg

 

file rekor.svg

 

file topaz.svg

 

dir docs/static/img/footer/

 

file cncf-dark.svg

 

file cncf-light.svg

 

dir docs/static/img/nav/

 

file github-dark.svg

 

file github-light.svg

 

file slack-dark.svg

 

file slack-light.svg

 

dir download/

 

file config.go

 

file doc.go

 

file download.go

 

file oci_download.go

 

file oci_downloader.go

 

dir e2e/

 

file README.md

 

file go.mod

 

file go.sum

 

dir e2e/api/compile/

 

file e2e_test.go

 

file logs_test.go

 

dir e2e/api/compile/prisma/

 

file README.md

 

file index.js

 

file package-lock.json

 

file package.json

 

file prisma.config.ts

 

dir e2e/api/compile/prisma/prisma/

 

file schema.prisma

 

dir e2e/cli/

 

file bundle_log.txtar

 

file file_logger.txtar

 

file main_test.go

 

file metadata.txtar

 

file print_log.txtar

 

file rule_labels_disk.txtar

 

file rule_labels_file_logger.txtar

 

file rule_metadata_dl.txtar

 

dir e2e/proto/

 

file manifest_test.go

 

file plan_test.go

 

dir e2e/proto/protoroundtrip/

 

file protoroundtrip.go

 

dir e2e/proto/protoschemacheck/

 

file protoschemacheck.go

 

dir features/

 

file doc.go

 

dir features/tracing/

 

file doc.go

 

file tracing.go

 

dir features/wasm/

 

file doc.go

 

file wasm.go

 

dir format/

 

file doc.go

 

file format.go

 

file format_test.go

 

dir hooks/

 

file doc.go

 

file hooks.go

 

dir internal/bundle/

 

file utils.go

 

dir internal/bundle/inspect/

 

file inspect.go

 

file inspect_test.go

 

dir internal/cidr/merge/

 

file merge.go

 

dir internal/cmd/genbuiltinmetadata/

 

file main.go

 

dir internal/cmd/genmanifestschema/

 

file main.go

 

file main_test.go

 

dir internal/cmd/genopacapabilities/

 

file main.go

 

dir internal/cmd/genplanschema/

 

file main.go

 

file main_test.go

 

dir internal/cmd/genversionindex/

 

file main.go

 

dir internal/compile/

 

file checks.go

 

file compile.go

 

file constraints.go

 

file ucast.go

 

dir internal/compiler/

 

file utils.go

 

file utils_test.go

 

dir internal/compiler/wasm/

 

file optimizations.go

 

file optimizations_test.go

 

file wasm.go

 

file wasm_test.go

 

dir internal/compiler/wasm/opa/

 

file callgraph.csv

 

file opa.go

 

file opa.wasm

 

dir internal/config/

 

file config.go

 

file config_test.go

 

dir internal/debug/

 

file debug.go

 

dir internal/deepcopy/

 

file deepcopy.go

 

file deepcopy_test.go

 

dir internal/distributedtracing/

 

file distributedtracing.go

 

file distributedtracing_test.go

 

dir internal/edittree/

 

file edittree.go

 

file edittree_test.go

 

dir internal/edittree/bitvector/

 

file README.md

 

file bitvector.go

 

file bitvector_test.go

 

file license.txt

 

dir internal/file/archive/

 

file tarball.go

 

dir internal/file/url/

 

file url.go

 

file url_test.go

 

dir internal/future/

 

file filter_imports.go

 

file parser_opts.go

 

dir internal/genjsonschema/

 

file genjsonschema.go

 

file genjsonschema_test.go

 

dir internal/gojsonschema/

 

file LICENSE-APACHE-2.0.txt

 

file README.md

 

file draft.go

 

file errors.go

 

file errors_dce_test.go

 

file format_checkers.go

 

file format_checkers_test.go

 

file internalLog.go

 

file jsonContext.go

 

file jsonLoader.go

 

file jsonschema_test.go

 

file locales.go

 

file result.go

 

file schema.go

 

file schemaLoader.go

 

file schemaLoader_test.go

 

file schemaPool.go

 

file schemaReferencePool.go

 

file schemaType.go

 

file schema_test.go

 

file subSchema.go

 

file types.go

 

file utils.go

 

file utils_test.go

 

file validation.go

 

dir internal/gojsonschema/testdata/draft4/

 

file additionalItems.json

 

file additionalProperties.json

 

file allOf.json

 

file anyOf.json

 

file default.json

 

file definitions.json

 

file dependencies.json

 

file enum.json

 

file format.json

 

file items.json

 

file maxItems.json

 

file maxLength.json

 

file maxProperties.json

 

file maximum.json

 

file minItems.json

 

file minLength.json

 

file minProperties.json

 

file minimum.json

 

file multipleOf.json

 

file not.json

 

file oneOf.json

 

file pattern.json

 

file patternProperties.json

 

file properties.json

 

file ref.json

 

file refRemote.json

 

file required.json

 

file type.json

 

file uniqueItems.json

 

dir internal/gojsonschema/testdata/draft4/optional/

 

file bignum.json

 

file ecmascript-regex.json

 

file format.json

 

file zeroTerminatedFloats.json

 

dir internal/gojsonschema/testdata/draft6/

 

file additionalItems.json

 

file additionalProperties.json

 

file allOf.json

 

file anyOf.json

 

file boolean_schema.json

 

file const.json

 

file contains.json

 

file default.json

 

file definitions.json

 

file dependencies.json

 

file enum.json

 

file exclusiveMaximum.json

 

file exclusiveMinimum.json

 

file format.json

 

file items.json

 

file maxItems.json

 

file maxLength.json

 

file maxProperties.json

 

file maximum.json

 

file minItems.json

 

file minLength.json

 

file minProperties.json

 

file minimum.json

 

file multipleOf.json

 

file not.json

 

file oneOf.json

 

file pattern.json

 

file patternProperties.json

 

file properties.json

 

file propertyNames.json

 

file ref.json

 

file refRemote.json

 

file required.json

 

file type.json

 

file uniqueItems.json

 

dir internal/gojsonschema/testdata/draft6/optional/

 

file bignum.json

 

file ecmascript-regex.json

 

file format.json

 

file zeroTerminatedFloats.json

 

dir internal/gojsonschema/testdata/draft7/

 

file additionalItems.json

 

file additionalProperties.json

 

file allOf.json

 

file anyOf.json

 

file boolean_schema.json

 

file const.json

 

file contains.json

 

file default.json

 

file definitions.json

 

file dependencies.json

 

file enum.json

 

file exclusiveMaximum.json

 

file exclusiveMinimum.json

 

file format.json

 

file if-then-else.json

 

file items.json

 

file maxItems.json

 

file maxLength.json

 

file maxProperties.json

 

file maximum.json

 

file minItems.json

 

file minLength.json

 

file minProperties.json

 

file minimum.json

 

file multipleOf.json

 

file not.json

 

file oneOf.json

 

file pattern.json

 

file patternProperties.json

 

file properties.json

 

file propertyNames.json

 

file ref.json

 

file refRemote.json

 

file required.json

 

file type.json

 

file uniqueItems.json

 

dir internal/gojsonschema/testdata/draft7/optional/

 

file bignum.json

 

file content.json

 

file ecmascript-regex.json

 

file zeroTerminatedFloats.json

 

dir internal/gojsonschema/testdata/draft7/optional/format/

 

file date-time.json

 

file date.json

 

file email.json

 

file hostname.json

 

file idn-email.json

 

file idn-hostname.json

 

file ipv4.json

 

file ipv6.json

 

file iri-reference.json

 

file iri.json

 

file json-pointer.json

 

file regex.json

 

file relative-json-pointer.json

 

file time.json

 

file uri-reference.json

 

file uri-template.json

 

file uri.json

 

dir internal/gojsonschema/testdata/extra/

 

file file with space.json

 

file fragment_schema.json

 

dir internal/gojsonschema/testdata/remotes/

 

file integer.json

 

file name.json

 

file subSchemas.json

 

dir internal/gojsonschema/testdata/remotes/folder/

 

file folderInteger.json

 

dir internal/json/patch/

 

file patch.go

 

file patch_test.go

 

dir internal/lcss/

 

file README.md

 

file lcss.go

 

file lcss_test.go

 

file qsufsort.go

 

dir internal/leb128/

 

file leb128.go

 

file leb128_test.go

 

dir internal/levenshtein/

 

file levenshtein.go

 

dir internal/logging/

 

file logging.go

 

file logging_test.go

 

dir internal/merge/

 

file merge.go

 

file merge_test.go

 

dir internal/methodlesstemplate/

 

file LICENSE

 

file README.md

 

file doc.go

 

file exec.go

 

file funcs.go

 

file option.go

 

file template.go

 

dir internal/methodlesstemplate/internal/fmtsort/

 

file sort.go

 

dir internal/metricsexport/

 

file metricsexport.go

 

file metricsexport_test.go

 

dir internal/pathwatcher/

 

file utils.go

 

file utils_test.go

 

dir internal/planner/

 

file determinism_test.go

 

file planner.go

 

file planner_test.go

 

file rules.go

 

file rules_test.go

 

file varstack.go

 

file varstack_test.go

 

dir internal/presentation/

 

file presentation.go

 

file presentation_test.go

 

dir internal/prometheus/

 

file prometheus.go

 

file prometheus_go1.17.go

 

file prometheus_test.go

 

dir internal/providers/aws/

 

file NOTICE.txt

 

file ecr.go

 

file ecr_test.go

 

file kms.go

 

file kms_test.go

 

file signing_v4.go

 

file signing_v4a.go

 

file util.go

 

dir internal/providers/aws/crypto/

 

file compare.go

 

file compare_test.go

 

file ecc.go

 

file ecc_test.go

 

dir internal/providers/aws/v4/

 

file const.go

 

file header_rules.go

 

file headers.go

 

file host.go

 

file util.go

 

file util_test.go

 

dir internal/ref/

 

file ref.go

 

dir internal/rego/opa/

 

file engine.go

 

file options.go

 

dir internal/runtime/init/

 

file init.go

 

file init_test.go

 

dir internal/semver/

 

file LICENSE

 

file semver.go

 

file semver_test.go

 

dir internal/storage/mock/

 

file mock.go

 

dir internal/strings/

 

file strings.go

 

dir internal/strvals/

 

file doc.go

 

file parser.go

 

file parser_test.go

 

dir internal/tlsutil/

 

file tlsutil.go

 

file tlsutil_test.go

 

dir internal/ucast/

 

file ucast.go

 

file ucast_test.go

 

dir internal/uuid/

 

file uuid.go

 

file uuid_test.go

 

dir internal/version/

 

file version.go

 

dir internal/versioncheck/

 

file versioncheck.go

 

file versioncheck_test.go

 

dir internal/wasm/constant/

 

file constant.go

 

dir internal/wasm/encoding/

 

file doc.go

 

file encoding_test.go

 

file reader.go

 

file writer.go

 

dir internal/wasm/encoding/testdata/

 

file test1.wasm

 

dir internal/wasm/instruction/

 

file control.go

 

file instruction.go

 

file memory.go

 

file numeric.go

 

file parametric.go

 

file variable.go

 

dir internal/wasm/module/

 

file module.go

 

file pretty.go

 

dir internal/wasm/opcode/

 

file opcode.go

 

dir internal/wasm/sdk/

 

file README.md

 

dir internal/wasm/sdk/examples/basic/

 

file README.md

 

file example-1.rego

 

file example-2.rego

 

file main.go

 

dir internal/wasm/sdk/examples/loaders/

 

file README.md

 

file example.rego

 

file main.go

 

dir internal/wasm/sdk/internal/wasm/

 

file bindings.go

 

file glue.go

 

file pool.go

 

file pool_test.go

 

file vm.go

 

dir internal/wasm/sdk/opa/

 

file config.go

 

file opa.go

 

file opa_bench_test.go

 

file opa_test.go

 

dir internal/wasm/sdk/opa/capabilities/

 

file capabilities.go

 

file capabilities_nowasm.go

 

dir internal/wasm/sdk/opa/errors/

 

file errors.go

 

dir internal/wasm/sdk/opa/loader/

 

file loader.go

 

dir internal/wasm/sdk/opa/loader/file/

 

file config.go

 

file loader.go

 

file loader_test.go

 

dir internal/wasm/sdk/opa/loader/http/

 

file config.go

 

file loader.go

 

file loader_test.go

 

file util.go

 

dir internal/wasm/sdk/test/e2e/

 

file exceptions.yaml

 

file external_test.go

 

dir internal/wasm/types/

 

file types.go

 

dir internal/wasm/util/

 

file util.go

 

dir ir/

 

file doc.go

 

file ir.go

 

file pretty.go

 

file walk.go

 

dir ir/encoding/

 

file doc.go

 

file encoding_test.go

 

dir keys/

 

file doc.go

 

file keys.go

 

dir loader/

 

file doc.go

 

file errors.go

 

file loader.go

 

file loader_test.go

 

dir loader/extension/

 

file doc.go

 

file extension.go

 

dir loader/filter/

 

file doc.go

 

file filter.go

 

dir logging/

 

file doc.go

 

file logging.go

 

dir logging/test/

 

file doc.go

 

file test.go

 

dir logo/

 

file logo.ico

 

file logo.svg

 

dir metrics/

 

file doc.go

 

file metrics.go

 

dir misc/syntax/sublime/

 

file rego.sublime-syntax

 

dir misc/syntax/textmate/

 

file Rego.tmLanguage

 

dir plugins/

 

file doc.go

 

file plugins.go

 

file plugins_test.go

 

dir plugins/bundle/

 

file config.go

 

file doc.go

 

file errors.go

 

file plugin.go

 

file status.go

 

dir plugins/discovery/

 

file config.go

 

file discovery.go

 

file doc.go

 

dir plugins/logs/

 

file doc.go

 

file plugin.go

 

dir plugins/logs/status/

 

file doc.go

 

file status.go

 

dir plugins/rest/

 

file auth.go

 

file doc.go

 

file gcp.go

 

file rest.go

 

dir plugins/server/

 

file doc.go

 

dir plugins/server/decoding/

 

file config.go

 

file doc.go

 

dir plugins/server/encoding/

 

file config.go

 

file doc.go

 

dir plugins/server/metrics/

 

file config.go

 

file doc.go

 

dir plugins/status/

 

file doc.go

 

file metrics.go

 

file plugin.go

 

dir profiler/

 

file doc.go

 

file profiler.go

 

dir proposals/attic/

 

file REGO_V2_PROPOSAL.md

 

dir refactor/

 

file doc.go

 

file refactor.go

 

dir rego/

 

file doc.go

 

file errors.go

 

file plugins.go

 

file rego.go

 

file rego_test.go

 

file resultset.go

 

dir repl/

 

file doc.go

 

file errors.go

 

file repl.go

 

file repl_test.go

 

dir resolver/

 

file doc.go

 

file interface.go

 

dir resolver/wasm/

 

file doc.go

 

file wasm.go

 

dir runtime/

 

file doc.go

 

file logging.go

 

file runtime.go

 

dir schemas/

 

file doc.go

 

file schemas.go

 

dir sdk/

 

file doc.go

 

file opa.go

 

file opa_test.go

 

dir sdk/test/

 

file doc.go

 

file test.go

 

dir server/

 

file buffer.go

 

file doc.go

 

file features.go

 

file server.go

 

dir server/authorizer/

 

file authorizer.go

 

file doc.go

 

dir server/handlers/

 

file compress.go

 

file decoding.go

 

file doc.go

 

dir server/identifier/

 

file certs.go

 

file doc.go

 

file identifier.go

 

file tls.go

 

file token.go

 

dir server/types/

 

file doc.go

 

file types.go

 

dir server/writer/

 

file doc.go

 

file writer.go

 

dir storage/

 

file doc.go

 

file errors.go

 

file interface.go

 

file path.go

 

file storage.go

 

dir storage/disk/

 

file config.go

 

file disk.go

 

file doc.go

 

dir storage/inmem/

 

file doc.go

 

file inmem.go

 

file opts.go

 

dir storage/inmem/test/

 

file doc.go

 

file testutil.go

 

dir test/authz/

 

file doc.go

 

file testing.go

 

dir test/cases/

 

file cases.go

 

file doc.go

 

dir test/e2e/

 

file doc.go

 

file testing.go

 

dir test/e2e/logs/

 

file doc.go

 

file utils.go

 

dir tester/

 

file doc.go

 

file reporter.go

 

file runner.go

 

file runner_test.go

 

dir topdown/

 

file builtins.go

 

file cache.go

 

file cancel.go

 

file doc.go

 

file errors.go

 

file http.go

 

file instrumentation.go

 

file print.go

 

file query.go

 

file trace.go

 

dir topdown/builtins/

 

file builtins.go

 

file doc.go

 

dir topdown/cache/

 

file cache.go

 

file doc.go

 

dir topdown/copypropagation/

 

file copypropagation.go

 

file doc.go

 

dir topdown/lineage/

 

file doc.go

 

file lineage.go

 

dir topdown/print/

 

file doc.go

 

file print.go

 

dir tracing/

 

file doc.go

 

file tracing.go

 

dir types/

 

file decode.go

 

file doc.go

 

file types.go

 

dir util/

 

file backoff.go

 

file close.go

 

file compare.go

 

file doc.go

 

file enumflag.go

 

file graph.go

 

file hashmap.go

 

file json.go

 

file maps.go

 

file queue.go

 

file read_gzip_body.go

 

file time.go

 

file wait.go

 

dir util/decoding/

 

file context.go

 

file doc.go

 

dir util/test/

 

file benchmark.go

 

file ci_skip.go

 

file ci_skip_darwin.go

 

file doc.go

 

file tempfs.go

 

file tempus.go

 

dir v1/

 

file doc.go

 

dir v1/ast/

 

file annotations.go

 

file annotations_test.go

 

file builtins.go

 

file builtins_test.go

 

file capabilities.go

 

file capabilities_test.go

 

file check.go

 

file check_test.go

 

file compare.go

 

file compare_test.go

 

file compile.go

 

file compile_bench_test.go

 

file compile_stage_test.go

 

file compile_test.go

 

file compilehelper.go

 

file compilehelper_test.go

 

file compilemetrics.go

 

file conflicts.go

 

file default_module_loader.go

 

file doc.go

 

file env.go

 

file env_test.go

 

file errors.go

 

file errors_test.go

 

file example_test.go

 

file external_source.go

 

file external_source_test.go

 

file fuzz_test.go

 

file index.go

 

file index_debug.go

 

file index_test.go

 

file interning.go

 

file interning_test.go

 

file map.go

 

file map_test.go

 

file marshal_test.go

 

file mermaid.go

 

file mermaid_test.go

 

file parser.go

 

file parser_bench_test.go

 

file parser_ext.go

 

file parser_ext_test.go

 

file parser_logical_test.go

 

file parser_test.go

 

file performance.go

 

file performance_test.go

 

file policy.go

 

file policy_appenders.go

 

file policy_appenders_test.go

 

file policy_bench_test.go

 

file policy_logical_test.go

 

file policy_test.go

 

file pretty.go

 

file pretty_test.go

 

file rego_compiler.go

 

file rego_v1.go

 

file schema.go

 

file schema_test.go

 

file slices.go

 

file string_length.go

 

file strings.go

 

file strings_bench_test.go

 

file syncpools.go

 

file term.go

 

file term_appenders.go

 

file term_appenders_test.go

 

file term_bench_test.go

 

file term_test.go

 

file transform.go

 

file transform_test.go

 

file treenode_dump.go

 

file unify.go

 

file unify_test.go

 

file varset.go

 

file version_index.json

 

file visit.go

 

file visit_bench_test.go

 

file visit_test.go

 

dir v1/ast/internal/scanner/

 

file scanner.go

 

file scanner_test.go

 

dir v1/ast/internal/tokens/

 

file tokens.go

 

dir v1/ast/json/

 

file json.go

 

dir v1/ast/location/

 

file location.go

 

file location_test.go

 

dir v1/ast/oracle/

 

file definition.go

 

file matcher.go

 

file oracle.go

 

file oracle_test.go

 

file stack.go

 

file target.go

 

file target_test.go

 

dir v1/ast/testdata/

 

file _definitions.json

 

dir v1/ast/testdata/fuzz/FuzzParseStatementsAndCompileModules/

 

file 00000.stmt

 

file 00001.stmt

 

file 00002.stmt

 

file 00003.stmt

 

file 00004.stmt

 

file 00005.stmt

 

file 00006.stmt

 

file 00007.stmt

 

file 00008.stmt

 

file 00009.stmt

 

file 00010.stmt

 

file 00011.stmt

 

file 00012.stmt

 

file 00013.stmt

 

file 00014.stmt

 

file 00015.stmt

 

file 00016.stmt

 

file 00017.stmt

 

file 00018.stmt

 

file 00019.stmt

 

file 00020.stmt

 

file 00021.stmt

 

file 00022.stmt

 

file 00023.stmt

 

file 00024.stmt

 

file 00025.stmt

 

file 00026.stmt

 

file 00027.stmt

 

file 00028.stmt

 

file 00029.stmt

 

file 00030.stmt

 

file 00031.stmt

 

file 00032.stmt

 

file 00033.stmt

 

file 00034.stmt

 

file 00035.stmt

 

file 00036.stmt

 

file 00037.stmt

 

file 00038.stmt

 

file 00039.stmt

 

file 00040.stmt

 

file 00041.stmt

 

file 00042.stmt

 

file 00043.stmt

 

file 00044.stmt

 

file 00045.stmt

 

file 00046.stmt

 

file 00047.stmt

 

file 00048.stmt

 

file 00049.stmt

 

file 00050.stmt

 

file 00051.stmt

 

file 00052.stmt

 

file 00053.stmt

 

file 00054.stmt

 

file 00055.stmt

 

file 00056.stmt

 

file 00057.stmt

 

file 00058.stmt

 

file 00059.stmt

 

file 00060.stmt

 

file 00061.stmt

 

file 00062.stmt

 

file 00063.stmt

 

file 00064.stmt

 

file 00065.stmt

 

file 00066.stmt

 

file 00067.stmt

 

file 00068.stmt

 

file 00069.stmt

 

file 00070.stmt

 

file 00071.stmt

 

file 00072.stmt

 

file 00073.stmt

 

file 00074.stmt

 

file 00075.stmt

 

file 00076.stmt

 

file 00077.stmt

 

file 00078.stmt

 

file 00079.stmt

 

file 00080.stmt

 

file 00081.stmt

 

file 00082.stmt

 

file 00083.stmt

 

file 00084.stmt

 

file 00085.stmt

 

file 00086.stmt

 

file 00087.stmt

 

file 00088.stmt

 

file 00089.stmt

 

file 00090.stmt

 

file 00091.stmt

 

file 00092.stmt

 

file 00093.stmt

 

file 00094.stmt

 

file 00095.stmt

 

file 00096.stmt

 

file 00097.stmt

 

file 00098.stmt

 

file 00099.stmt

 

file 00100.stmt

 

file 00101.stmt

 

file 00102.stmt

 

file 00103.stmt

 

file 00104.stmt

 

file 00105.stmt

 

file 00106.stmt

 

file 00107.stmt

 

file 00108.stmt

 

file 00109.stmt

 

file 00110.stmt

 

file 00111.stmt

 

file 00112.stmt

 

file 00113.stmt

 

file 00114.stmt

 

file 00115.stmt

 

file 00116.stmt

 

file 00117.stmt

 

file 00118.stmt

 

file 00119.stmt

 

file 00120.stmt

 

file 00121.stmt

 

file 00122.stmt

 

file 00123.stmt

 

file 00124.stmt

 

file 00125.stmt

 

file 00126.stmt

 

file 00127.stmt

 

file 00128.stmt

 

file 00129.stmt

 

file 00130.stmt

 

file 00131.stmt

 

file 00132.stmt

 

file 00133.stmt

 

file 00134.stmt

 

file 00135.stmt

 

file 00136.stmt

 

file 00137.stmt

 

file 00138.stmt

 

file 00139.stmt

 

file 00140.stmt

 

file 00141.stmt

 

file 00142.stmt

 

file 00143.stmt

 

file 00144.stmt

 

file 00145.stmt

 

file 00146.stmt

 

file 00147.stmt

 

file 00148.stmt

 

file 00149.stmt

 

file 00150.stmt

 

file 00151.stmt

 

file 00152.stmt

 

file 00153.stmt

 

file 00154.stmt

 

file 00155.stmt

 

file 00156.stmt

 

file 00157.stmt

 

file 00158.stmt

 

file 00159.stmt

 

file 00160.stmt

 

file 00161.stmt

 

file 00162.stmt

 

file 00163.stmt

 

file 00164.stmt

 

file 00165.stmt

 

file 00166.stmt

 

file 00167.stmt

 

file 00168.stmt

 

file 00169.stmt

 

file 00170.stmt

 

file 00171.stmt

 

file 00172.stmt

 

file 00173.stmt

 

file 00174.stmt

 

file 00175.stmt

 

file 00176.stmt

 

file 00177.stmt

 

file 00178.stmt

 

file 00179.stmt

 

file 00180.stmt

 

file 00181.stmt

 

file 00182.stmt

 

file 00183.stmt

 

file 00184.stmt

 

file 00185.stmt

 

file 00186.stmt

 

file 00187.stmt

 

file 00188.stmt

 

file 00189.stmt

 

file 00190.stmt

 

file 00191.stmt

 

file 00192.stmt

 

file 00193.stmt

 

file 00194.stmt

 

file 00195.stmt

 

file 00196.stmt

 

file 00197.stmt

 

file 00198.stmt

 

file 00199.stmt

 

file 00200.stmt

 

file 00201.stmt

 

file 00202.stmt

 

file 00203.stmt

 

file 00204.stmt

 

file 00205.stmt

 

file 00206.stmt

 

file 00207.stmt

 

file 00208.stmt

 

file 00209.stmt

 

file 00210.stmt

 

file 00211.stmt

 

file 00212.stmt

 

file 00213.stmt

 

file 00214.stmt

 

file 00215.stmt

 

file 00216.stmt

 

file 00217.stmt

 

file 00218.stmt

 

file 00219.stmt

 

file 00220.stmt

 

file 00221.stmt

 

file 00222.stmt

 

file 00223.stmt

 

file 00224.stmt

 

file 00225.stmt

 

file 00226.stmt

 

file 00227.stmt

 

file 00228.stmt

 

file 00229.stmt

 

file 00230.stmt

 

file 00231.stmt

 

file 00232.stmt

 

file 00233.stmt

 

file 00234.stmt

 

file 00235.stmt

 

file 00236.stmt

 

file 00237.stmt

 

file 00238.stmt

 

file 00239.stmt

 

file 00240.stmt

 

file 00241.stmt

 

file 00242.stmt

 

file 00243.stmt

 

file 00244.stmt

 

file 00245.stmt

 

file 00246.stmt

 

file 00247.stmt

 

file 00248.stmt

 

file 00249.stmt

 

file 00250.stmt

 

file 00251.stmt

 

file 00252.stmt

 

file 00253.stmt

 

file 00254.stmt

 

file 00255.stmt

 

file 00256.stmt

 

file 00257.stmt

 

file 00258.stmt

 

file 00259.stmt

 

file 00260.stmt

 

file 00261.stmt

 

file 00262.stmt

 

file 00263.stmt

 

file 00264.stmt

 

file 00265.stmt

 

file 00266.stmt

 

file 00267.stmt

 

file 00268.stmt

 

file 00269.stmt

 

file 00270.stmt

 

file 00271.stmt

 

file 00272.stmt

 

file 00273.stmt

 

file 00274.stmt

 

file 00275.stmt

 

file 00276.stmt

 

file 00277.stmt

 

file 00278.stmt

 

file 00279.stmt

 

file 00280.stmt

 

file 00281.stmt

 

file 00282.stmt

 

file 00283.stmt

 

file 00284.stmt

 

file 00285.stmt

 

file 00286.stmt

 

file 00287.stmt

 

file 00288.stmt

 

file 00289.stmt

 

file 00290.stmt

 

file 00291.stmt

 

file 00292.stmt

 

file 00293.stmt

 

file 00294.stmt

 

file 00295.stmt

 

file 00296.stmt

 

file 00297.stmt

 

file 00298.stmt

 

file 00299.stmt

 

file 00300.stmt

 

file 00301.stmt

 

file 00302.stmt

 

file 00303.stmt

 

file 00304.stmt

 

file 00305.stmt

 

file 00306.stmt

 

file 00307.stmt

 

file 00308.stmt

 

file 00309.stmt

 

file 00310.stmt

 

file 00311.stmt

 

file 00312.stmt

 

file 00313.stmt

 

file 00314.stmt

 

file 00315.stmt

 

file 00316.stmt

 

file 00317.stmt

 

file 00318.stmt

 

file 00319.stmt

 

file 00320.stmt

 

file 00321.stmt

 

file 00322.stmt

 

file 00323.stmt

 

file 00324.stmt

 

file 00325.stmt

 

file 00326.stmt

 

file 00327.stmt

 

file 00328.stmt

 

file 00329.stmt

 

file 00330.stmt

 

file 00331.stmt

 

file 00332.stmt

 

file 00333.stmt

 

file 00334.stmt

 

file 00335.stmt

 

file 00336.stmt

 

file 00337.stmt

 

file 00338.stmt

 

file 00339.stmt

 

file 00340.stmt

 

file 00341.stmt

 

file 00342.stmt

 

file 00343.stmt

 

file 00344.stmt

 

file 00345.stmt

 

file 00346.stmt

 

file 00347.stmt

 

file 00348.stmt

 

file 00349.stmt

 

file 00350.stmt

 

file 00351.stmt

 

file 00352.stmt

 

file 00353.stmt

 

file 00354.stmt

 

file 00355.stmt

 

file 00356.stmt

 

file 00357.stmt

 

file 00358.stmt

 

file 00359.stmt

 

file 00360.stmt

 

file 00361.stmt

 

file 00362.stmt

 

file 00363.stmt

 

file 00364.stmt

 

file 00365.stmt

 

file 00366.stmt

 

file 00367.stmt

 

file 00368.stmt

 

file 00369.stmt

 

file 00370.stmt

 

file 00371.stmt

 

file 00372.stmt

 

file 00373.stmt

 

file 00374.stmt

 

file 00375.stmt

 

file 00376.stmt

 

file 00377.stmt

 

file 00378.stmt

 

file 00379.stmt

 

file 00380.stmt

 

file 00381.stmt

 

file 00382.stmt

 

file 00383.stmt

 

file 00384.stmt

 

file 00385.stmt

 

file 00386.stmt

 

file 00387.stmt

 

file 00388.stmt

 

file 00389.stmt

 

file 00390.stmt

 

file 00391.stmt

 

file 00392.stmt

 

file 00393.stmt

 

file 00394.stmt

 

file 00395.stmt

 

file 00396.stmt

 

file 00397.stmt

 

file 00398.stmt

 

file 00399.stmt

 

file 00400.stmt

 

file 00401.stmt

 

file 00402.stmt

 

file 00403.stmt

 

file 00404.stmt

 

file 00405.stmt

 

file 00406.stmt

 

file 00407.stmt

 

file 00408.stmt

 

file 00409.stmt

 

file 00410.stmt

 

file 00411.stmt

 

file 00412.stmt

 

file 00413.stmt

 

file 00414.stmt

 

file 00415.stmt

 

file 00416.stmt

 

file 00417.stmt

 

file 00418.stmt

 

file 00419.stmt

 

file 00420.stmt

 

file 00421.stmt

 

file 00422.stmt

 

file 00423.stmt

 

file 00424.stmt

 

file 00425.stmt

 

file 00426.stmt

 

file 00427.stmt

 

file 00428.stmt

 

file 00429.stmt

 

file 00430.stmt

 

file 00431.stmt

 

file 00432.stmt

 

file 00433.stmt

 

file 00434.stmt

 

file 00435.stmt

 

file 00436.stmt

 

file 00437.stmt

 

file 00438.stmt

 

file 00439.stmt

 

file 00440.stmt

 

file 00441.stmt

 

file 00442.stmt

 

file 00443.stmt

 

file 00444.stmt

 

file 00445.stmt

 

file 00446.stmt

 

file 00447.stmt

 

file 00448.stmt

 

file 00449.stmt

 

file 00450.stmt

 

file 00451.stmt

 

file 00452.stmt

 

file 00453.stmt

 

file 00454.stmt

 

file 00455.stmt

 

file 00456.stmt

 

file 00457.stmt

 

file 00458.stmt

 

file 00459.stmt

 

file 00460.stmt

 

file 00461.stmt

 

file 00462.stmt

 

file 00463.stmt

 

file 00464.stmt

 

file 00465.stmt

 

file 00466.stmt

 

file 00467.stmt

 

file 00468.stmt

 

file 00469.stmt

 

file 00470.stmt

 

file 00471.stmt

 

file 00472.stmt

 

file 00473.stmt

 

file 00474.stmt

 

file 00475.stmt

 

file 00476.stmt

 

file 00477.stmt

 

file 00478.stmt

 

file 00479.stmt

 

file 00480.stmt

 

file 00481.stmt

 

file 00482.stmt

 

file 00483.stmt

 

file 00484.stmt

 

file 00485.stmt

 

file 00486.stmt

 

file 00487.stmt

 

file 00488.stmt

 

file 00489.stmt

 

file 00490.stmt

 

file 00491.stmt

 

file 00492.stmt

 

file 00493.stmt

 

file 00494.stmt

 

file 00495.stmt

 

file 00496.stmt

 

file 00497.stmt

 

file 00498.stmt

 

file 00499.stmt

 

file 00500.stmt

 

file 00501.stmt

 

file 00502.stmt

 

file 00503.stmt

 

file 00504.stmt

 

file 00505.stmt

 

file 00506.stmt

 

file 00507.stmt

 

file 00508.stmt

 

file 00509.stmt

 

file 00510.stmt

 

file 00511.stmt

 

file 00512.stmt

 

file 00513.stmt

 

file 00514.stmt

 

file 00515.stmt

 

file 00516.stmt

 

file 00517.stmt

 

file 00518.stmt

 

file 00519.stmt

 

file 00520.stmt

 

file 00521.stmt

 

file 00522.stmt

 

file 00523.stmt

 

file 00524.stmt

 

file 00525.stmt

 

file 00526.stmt

 

file 00527.stmt

 

file 00528.stmt

 

file 00529.stmt

 

file 00530.stmt

 

file 00531.stmt

 

file 00532.stmt

 

file 00533.stmt

 

file 00534.stmt

 

file 00535.stmt

 

file 00536.stmt

 

file 00537.stmt

 

file 00538.stmt

 

file 00539.stmt

 

file 00540.stmt

 

file 00541.stmt

 

file 00542.stmt

 

file 00543.stmt

 

file 00544.stmt

 

file 00545.stmt

 

file 00546.stmt

 

file 00547.stmt

 

file 00548.stmt

 

file 00549.stmt

 

file 00550.stmt

 

file 00551.stmt

 

file 00552.stmt

 

file 00553.stmt

 

file 00554.stmt

 

file 00555.stmt

 

file 00556.stmt

 

file 00557.stmt

 

file 00558.stmt

 

file 00559.stmt

 

file 00560.stmt

 

file 00561.stmt

 

file 00562.stmt

 

file 00563.stmt

 

file 00564.stmt

 

file 00565.stmt

 

file 00566.stmt

 

file 00567.stmt

 

file 00568.stmt

 

file 00569.stmt

 

file 00570.stmt

 

file 00571.stmt

 

file 00572.stmt

 

file 00573.stmt

 

file 00574.stmt

 

file 00575.stmt

 

file 00576.stmt

 

file 00577.stmt

 

file 00578.stmt

 

file 00579.stmt

 

file 00580.stmt

 

file 00581.stmt

 

file 00582.stmt

 

file 00583.stmt

 

file 00584.stmt

 

file 00585.stmt

 

file 00586.stmt

 

file 00587.stmt

 

file 00588.stmt

 

file 00589.stmt

 

file 00590.stmt

 

file 00591.stmt

 

file 00592.stmt

 

file 00593.stmt

 

file 00594.stmt

 

file 00595.stmt

 

file 00596.stmt

 

file 00597.stmt

 

file 00598.stmt

 

file 00599.stmt

 

file 00600.stmt

 

file 00601.stmt

 

file 00602.stmt

 

file 00603.stmt

 

file 00604.stmt

 

file 00605.stmt

 

file 00606.stmt

 

file 00607.stmt

 

file 00608.stmt

 

file 00609.stmt

 

file 00610.stmt

 

file 00611.stmt

 

file 00612.stmt

 

file 00613.stmt

 

file 00614.stmt

 

file 00615.stmt

 

file 00616.stmt

 

file 00617.stmt

 

file 00618.stmt

 

file 00619.stmt

 

file 00620.stmt

 

file 00621.stmt

 

file 00622.stmt

 

file 00623.stmt

 

file 00624.stmt

 

file 00625.stmt

 

file 00626.stmt

 

file 00627.stmt

 

file 00628.stmt

 

file 00629.stmt

 

file 00630.stmt

 

file 00631.stmt

 

file 00632.stmt

 

file 00633.stmt

 

file 00634.stmt

 

file 00635.stmt

 

file 00636.stmt

 

file 00637.stmt

 

file 00638.stmt

 

file 00639.stmt

 

file 00640.stmt

 

file 00641.stmt

 

file 00642.stmt

 

file 00643.stmt

 

file 00644.stmt

 

file 00645.stmt

 

file 00646.stmt

 

file 00647.stmt

 

file 00648.stmt

 

file 00649.stmt

 

file 00650.stmt

 

file 00651.stmt

 

file 00652.stmt

 

file 00653.stmt

 

file 00654.stmt

 

file 00655.stmt

 

file 00656.stmt

 

file 00657.stmt

 

file 00658.stmt

 

file 00659.stmt

 

file 00660.stmt

 

file 00661.stmt

 

file 00662.stmt

 

file 00663.stmt

 

file 00664.stmt

 

file 00665.stmt

 

file 00666.stmt

 

file 00667.stmt

 

file 00668.stmt

 

file 00669.stmt

 

file 00670.stmt

 

file 00671.stmt

 

file 00672.stmt

 

file 00673.stmt

 

file 00674.stmt

 

file 00675.stmt

 

file 00676.stmt

 

file 00677.stmt

 

file 00678.stmt

 

file 00679.stmt

 

file 00680.stmt

 

file 00681.stmt

 

file 00682.stmt

 

file 00683.stmt

 

file 00684.stmt

 

file 00685.stmt

 

file 00686.stmt

 

file 00687.stmt

 

file 00688.stmt

 

file 00689.stmt

 

file 00690.stmt

 

file 00691.stmt

 

file 00692.stmt

 

file 00693.stmt

 

file 00694.stmt

 

file 00695.stmt

 

file 00696.stmt

 

file 00697.stmt

 

file 00698.stmt

 

file 00699.stmt

 

file 00700.stmt

 

file 00701.stmt

 

file 00702.stmt

 

file 00703.stmt

 

file 00704.stmt

 

file 00705.stmt

 

file 00706.stmt

 

file 00707.stmt

 

file 00708.stmt

 

file 00709.stmt

 

file 00710.stmt

 

file 00711.stmt

 

file 00712.stmt

 

file 00713.stmt

 

file 00714.stmt

 

file 00715.stmt

 

file 00716.stmt

 

file 00717.stmt

 

file 00718.stmt

 

file 00719.stmt

 

file 00720.stmt

 

file 00721.stmt

 

file 00722.stmt

 

file 00723.stmt

 

file 00724.stmt

 

file 00725.stmt

 

file 00726.stmt

 

file 00727.stmt

 

file 00728.stmt

 

file 00729.stmt

 

file 00730.stmt

 

file 00731.stmt

 

file 00732.stmt

 

file 00733.stmt

 

file 00734.stmt

 

file 00735.stmt

 

file 00736.stmt

 

file 00737.stmt

 

file 00738.stmt

 

file 00739.stmt

 

file 00740.stmt

 

file 00741.stmt

 

file 00742.stmt

 

file 00743.stmt

 

file 00744.stmt

 

file 00745.stmt

 

file 00746.stmt

 

file 00747.stmt

 

file 00748.stmt

 

file 00749.stmt

 

file 00750.stmt

 

file 00751.stmt

 

file 00752.stmt

 

file 00753.stmt

 

file 00754.stmt

 

file 00755.stmt

 

file 00756.stmt

 

file 00757.stmt

 

file 00758.stmt

 

file 00759.stmt

 

file 00760.stmt

 

file 00761.stmt

 

file 00762.stmt

 

file 00763.stmt

 

file 00764.stmt

 

file 00765.stmt

 

file 00766.stmt

 

file 00767.stmt

 

file 00768.stmt

 

file 00769.stmt

 

file 00770.stmt

 

file 00771.stmt

 

file 00772.stmt

 

file 00773.stmt

 

file 00774.stmt

 

file 00775.stmt

 

file 00776.stmt

 

file 00777.stmt

 

file 00778.stmt

 

file 00779.stmt

 

file 00780.stmt

 

file 00781.stmt

 

file 00782.stmt

 

file 00783.stmt

 

file 00784.stmt

 

file 00785.stmt

 

file 00786.stmt

 

file 00787.stmt

 

file 00788.stmt

 

file 00789.stmt

 

file 00790.stmt

 

file 00791.stmt

 

file 00792.stmt

 

file 00793.stmt

 

file 00794.stmt

 

file 00795.stmt

 

file 00796.stmt

 

file 00797.stmt

 

file 00798.stmt

 

file 00799.stmt

 

file 00800.stmt

 

file 00801.stmt

 

file 00802.stmt

 

file 00803.stmt

 

file 00804.stmt

 

file 00805.stmt

 

file 00806.stmt

 

file 00807.stmt

 

file 00808.stmt

 

file 00809.stmt

 

file 00810.stmt

 

file 00811.stmt

 

file 00812.stmt

 

file 00813.stmt

 

file 00814.stmt

 

file 00815.stmt

 

file 00816.stmt

 

file 00817.stmt

 

file 00818.stmt

 

file 00819.stmt

 

file 00820.stmt

 

file 00821.stmt

 

file 00822.stmt

 

file 00823.stmt

 

file 00824.stmt

 

file 00825.stmt

 

file 00826.stmt

 

file 00827.stmt

 

file 00828.stmt

 

file 00829.stmt

 

file 00830.stmt

 

file 00831.stmt

 

file 00832.stmt

 

file 00833.stmt

 

file 00834.stmt

 

file 00835.stmt

 

file 00836.stmt

 

file 00837.stmt

 

file 00838.stmt

 

file 00839.stmt

 

file 00840.stmt

 

file 00841.stmt

 

file 00842.stmt

 

file 00843.stmt

 

file 00844.stmt

 

file 00845.stmt

 

file 00846.stmt

 

file 00847.stmt

 

file 00848.stmt

 

file 00849.stmt

 

file 00850.stmt

 

file 00851.stmt

 

file 00852.stmt

 

file 00853.stmt

 

file 00854.stmt

 

file 00855.stmt

 

file 00856.stmt

 

file 00857.stmt

 

file 00858.stmt

 

file 00859.stmt

 

file 00860.stmt

 

file 00861.stmt

 

file 00862.stmt

 

file 00863.stmt

 

file 00864.stmt

 

file 00865.stmt

 

file 00866.stmt

 

file 00867.stmt

 

file 00868.stmt

 

file 00869.stmt

 

file 00870.stmt

 

file 00871.stmt

 

file 00872.stmt

 

file 00873.stmt

 

file 00874.stmt

 

file 00875.stmt

 

file 00876.stmt

 

file 00877.stmt

 

file 00878.stmt

 

file 00879.stmt

 

file 00880.stmt

 

file 00881.stmt

 

file 00882.stmt

 

file 00883.stmt

 

file 00884.stmt

 

file 00885.stmt

 

file 00886.stmt

 

file 00887.stmt

 

file 00888.stmt

 

file 00889.stmt

 

file 00890.stmt

 

file 00891.stmt

 

file 00892.stmt

 

file 00893.stmt

 

file 00894.stmt

 

file 00895.stmt

 

file 00896.stmt

 

file 00897.stmt

 

file 00898.stmt

 

file 00899.stmt

 

file 00900.stmt

 

file 00901.stmt

 

file 00902.stmt

 

file 00903.stmt

 

file 00904.stmt

 

file 00905.stmt

 

file 00906.stmt

 

file 00907.stmt

 

file 00908.stmt

 

file 00909.stmt

 

file 00910.stmt

 

file 00911.stmt

 

file 00912.stmt

 

file 00913.stmt

 

file 00914.stmt

 

file 00915.stmt

 

file 00916.stmt

 

file 00917.stmt

 

file 00918.stmt

 

file 00919.stmt

 

file 00920.stmt

 

file 00921.stmt

 

file 00922.stmt

 

file 00923.stmt

 

file 00924.stmt

 

file 00925.stmt

 

file 00926.stmt

 

file 00927.stmt

 

file 00928.stmt

 

file 00929.stmt

 

file 00930.stmt

 

file 00931.stmt

 

file 00932.stmt

 

file 00933.stmt

 

file 00934.stmt

 

file 00935.stmt

 

file 00936.stmt

 

file 00937.stmt

 

file 00938.stmt

 

file 00939.stmt

 

file 00940.stmt

 

file 00941.stmt

 

file 00942.stmt

 

file 00943.stmt

 

file 00944.stmt

 

file 00945.stmt

 

file 00946.stmt

 

file 00947.stmt

 

file 00948.stmt

 

file 00949.stmt

 

file 00950.stmt

 

file 00951.stmt

 

file 00952.stmt

 

file 00953.stmt

 

file 00954.stmt

 

file 00955.stmt

 

file 00956.stmt

 

file 00957.stmt

 

file 00958.stmt

 

file 00959.stmt

 

file 00960.stmt

 

file 00961.stmt

 

file 00962.stmt

 

file 00963.stmt

 

file 00964.stmt

 

file 00965.stmt

 

file 00966.stmt

 

file 00967.stmt

 

file 00968.stmt

 

file 00969.stmt

 

file 00970.stmt

 

file 00971.stmt

 

file 00972.stmt

 

file 00973.stmt

 

file 00974.stmt

 

file 00975.stmt

 

file 00976.stmt

 

file 00977.stmt

 

file 00978.stmt

 

file 00979.stmt

 

file 00980.stmt

 

file 00981.stmt

 

file 00982.stmt

 

file 00983.stmt

 

file 00984.stmt

 

file 00985.stmt

 

file 00986.stmt

 

file 00987.stmt

 

file 00988.stmt

 

file 00989.stmt

 

file 00990.stmt

 

file 00991.stmt

 

file 00992.stmt

 

file 00993.stmt

 

file 00994.stmt

 

file 00995.stmt

 

file 00996.stmt

 

file 00997.stmt

 

file 00998.stmt

 

file 00999.stmt

 

file 01000.stmt

 

file 01001.stmt

 

file 01002.stmt

 

file 01003.stmt

 

file 01004.stmt

 

file 01005.stmt

 

file 01006.stmt

 

file 01007.stmt

 

file 01008.stmt

 

file 01009.stmt

 

file 01010.stmt

 

file 01011.stmt

 

file 01012.stmt

 

file 01013.stmt

 

file 01014.stmt

 

file 01015.stmt

 

file 01016.stmt

 

file 01017.stmt

 

file 01018.stmt

 

file 01019.stmt

 

file 01020.stmt

 

file 01021.stmt

 

file 01022.stmt

 

file 01023.stmt

 

file 01024.stmt

 

file 01025.stmt

 

file 01026.stmt

 

file 01027.stmt

 

file 01028.stmt

 

file 01029.stmt

 

file 01030.stmt

 

file 01031.stmt

 

file 01032.stmt

 

file 01033.stmt

 

file 01034.stmt

 

file 01035.stmt

 

file 01036.stmt

 

file 01037.stmt

 

file 01038.stmt

 

file 01039.stmt

 

file 01040.stmt

 

file 01041.stmt

 

file 01042.stmt

 

file 01043.stmt

 

file 01044.stmt

 

file 01045.stmt

 

file 01046.stmt

 

file 01047.stmt

 

file 01048.stmt

 

file 01049.stmt

 

file 01050.stmt

 

file 01051.stmt

 

file 01052.stmt

 

file 01053.stmt

 

file 01054.stmt

 

file 01055.stmt

 

file 01056.stmt

 

file 01057.stmt

 

file 01058.stmt

 

file 01059.stmt

 

file 01060.stmt

 

file 01061.stmt

 

file 01062.stmt

 

file 01063.stmt

 

file 01064.stmt

 

file 01065.stmt

 

file 01066.stmt

 

file 01067.stmt

 

file 01068.stmt

 

file 01069.stmt

 

file 01070.stmt

 

file 01071.stmt

 

file 01072.stmt

 

file 01073.stmt

 

file 01074.stmt

 

file 01075.stmt

 

file 01076.stmt

 

file 01077.stmt

 

file 01078.stmt

 

file 01079.stmt

 

file 01080.stmt

 

file 01081.stmt

 

file 01082.stmt

 

file 01083.stmt

 

file 01084.stmt

 

file 01085.stmt

 

file 01086.stmt

 

file 01087.stmt

 

file 01088.stmt

 

file 01089.stmt

 

file 01090.stmt

 

file 01091.stmt

 

file 01092.stmt

 

file 01093.stmt

 

file 01094.stmt

 

file 01095.stmt

 

file 01096.stmt

 

file 01097.stmt

 

file 01098.stmt

 

file 01099.stmt

 

file 01100.stmt

 

file 01101.stmt

 

file 01102.stmt

 

file 01103.stmt

 

file 01104.stmt

 

file 01105.stmt

 

file 01106.stmt

 

file 01107.stmt

 

file 01108.stmt

 

file 01109.stmt

 

file 01110.stmt

 

file 01111.stmt

 

file 01112.stmt

 

file 01113.stmt

 

file 01114.stmt

 

file 01115.stmt

 

file 01116.stmt

 

file 01117.stmt

 

file 01118.stmt

 

file 01119.stmt

 

file 01120.stmt

 

file 01121.stmt

 

file 01122.stmt

 

file 01123.stmt

 

file 01124.stmt

 

file 01125.stmt

 

file 01126.stmt

 

file 01127.stmt

 

file 01128.stmt

 

file 01129.stmt

 

file 01130.stmt

 

file 01131.stmt

 

file 01132.stmt

 

file 01133.stmt

 

file 01134.stmt

 

file 01135.stmt

 

file 01136.stmt

 

file 01137.stmt

 

file 01138.stmt

 

file 01139.stmt

 

file 01140.stmt

 

file 01141.stmt

 

file 01142.stmt

 

file 01143.stmt

 

file 01144.stmt

 

file 01145.stmt

 

file 01146.stmt

 

file 01147.stmt

 

file 01148.stmt

 

file 01149.stmt

 

file 01150.stmt

 

file 01151.stmt

 

file 01152.stmt

 

file 01153.stmt

 

file 01154.stmt

 

file 01155.stmt

 

file 01156.stmt

 

file 01157.stmt

 

file 01158.stmt

 

file 01159.stmt

 

file 01160.stmt

 

file 01161.stmt

 

file 01162.stmt

 

file 01163.stmt

 

file 01164.stmt

 

file 01165.stmt

 

file 01166.stmt

 

file 01167.stmt

 

file 01168.stmt

 

file 01169.stmt

 

file 01170.stmt

 

file 01171.stmt

 

file 01172.stmt

 

file 01173.stmt

 

file 01174.stmt

 

file 01175.stmt

 

file 01176.stmt

 

file 01177.stmt

 

file 01178.stmt

 

file 01179.stmt

 

file 01180.stmt

 

file 01181.stmt

 

file 01182.stmt

 

file 01183.stmt

 

file 01184.stmt

 

file 01185.stmt

 

file 01186.stmt

 

file 01187.stmt

 

file 01188.stmt

 

file 01189.stmt

 

file 01190.stmt

 

file 01191.stmt

 

file 01192.stmt

 

file 01193.stmt

 

file 01194.stmt

 

file 01195.stmt

 

file 01196.stmt

 

file 01197.stmt

 

file 01198.stmt

 

file 01199.stmt

 

file 01200.stmt

 

file 01201.stmt

 

file 01202.stmt

 

file 01203.stmt

 

file 01204.stmt

 

file 01205.stmt

 

file 01206.stmt

 

file 01207.stmt

 

file 01208.stmt

 

file 01209.stmt

 

file 01210.stmt

 

file 01211.stmt

 

file 01212.stmt

 

file 01213.stmt

 

file 01214.stmt

 

file 01215.stmt

 

file 01216.stmt

 

file 01217.stmt

 

file 01218.stmt

 

file 01219.stmt

 

file 01220.stmt

 

file 01221.stmt

 

file 01222.stmt

 

file 01223.stmt

 

file 01224.stmt

 

file 01225.stmt

 

file 01226.stmt

 

file 01227.stmt

 

file 01228.stmt

 

file 01229.stmt

 

file 01230.stmt

 

file 01231.stmt

 

file 01232.stmt

 

file 01233.stmt

 

file 01234.stmt

 

file 01235.stmt

 

file 01236.stmt

 

file 01237.stmt

 

file 01238.stmt

 

file 01239.stmt

 

file 01240.stmt

 

file 01241.stmt

 

file 01242.stmt

 

file 01243.stmt

 

file 01244.stmt

 

file 01245.stmt

 

file 01246.stmt

 

file 01247.stmt

 

file 01248.stmt

 

file 01249.stmt

 

file 01250.stmt

 

file 01251.stmt

 

file 01252.stmt

 

file 01253.stmt

 

file 01254.stmt

 

file 01255.stmt

 

file 01256.stmt

 

file 01257.stmt

 

file 01258.stmt

 

file 01259.stmt

 

file 01260.stmt

 

file 01261.stmt

 

file 01262.stmt

 

file 01263.stmt

 

file 01264.stmt

 

file 01265.stmt

 

file 01266.stmt

 

file 01267.stmt

 

file 01268.stmt

 

file 01269.stmt

 

file 01270.stmt

 

file 01271.stmt

 

file 01272.stmt

 

file 01273.stmt

 

file 01274.stmt

 

file 01275.stmt

 

file 01276.stmt

 

file 01277.stmt

 

file 01278.stmt

 

file 01279.stmt

 

file 01280.stmt

 

file 01281.stmt

 

file 01282.stmt

 

file 01283.stmt

 

file 01284.stmt

 

file 01285.stmt

 

file 01286.stmt

 

file 01287.stmt

 

file 01288.stmt

 

file 01289.stmt

 

file 01290.stmt

 

file 01291.stmt

 

file 01292.stmt

 

file 01293.stmt

 

file 01294.stmt

 

file 01295.stmt

 

file 01296.stmt

 

file 01297.stmt

 

file 01298.stmt

 

file 01299.stmt

 

file 01300.stmt

 

file 01301.stmt

 

file 01302.stmt

 

file 01303.stmt

 

file 01304.stmt

 

file 01305.stmt

 

file 01306.stmt

 

file 01307.stmt

 

file 01308.stmt

 

file 01309.stmt

 

file 01310.stmt

 

file 01311.stmt

 

file 01312.stmt

 

file 01313.stmt

 

file 01314.stmt

 

file 01315.stmt

 

file 01316.stmt

 

file 01317.stmt

 

file 01318.stmt

 

file 01319.stmt

 

file 01320.stmt

 

file 01321.stmt

 

file 01322.stmt

 

file 01323.stmt

 

file 01324.stmt

 

file 01325.stmt

 

file 01326.stmt

 

file 01327.stmt

 

file 01328.stmt

 

file 01329.stmt

 

file 01330.stmt

 

file 01331.stmt

 

file 01332.stmt

 

file 01333.stmt

 

file 01334.stmt

 

file 01335.stmt

 

file 01336.stmt

 

file 01337.stmt

 

file 01338.stmt

 

file 01339.stmt

 

file 01340.stmt

 

file 01341.stmt

 

file 01342.stmt

 

file 01343.stmt

 

file 01344.stmt

 

file 01345.stmt

 

file 01346.stmt

 

file 01347.stmt

 

file 01348.stmt

 

file 01349.stmt

 

file 01350.stmt

 

file 01351.stmt

 

file 01352.stmt

 

file 01353.stmt

 

file 01354.stmt

 

file 01355.stmt

 

file 01356.stmt

 

file 01357.stmt

 

file 01358.stmt

 

file 01359.stmt

 

file 01360.stmt

 

file 01361.stmt

 

file 01362.stmt

 

file 01363.stmt

 

file 01364.stmt

 

file 01365.stmt

 

file 01366.stmt

 

file 01367.stmt

 

file 01368.stmt

 

file 01369.stmt

 

file 01370.stmt

 

file 01371.stmt

 

file 01372.stmt

 

file 01373.stmt

 

file 01374.stmt

 

file 01375.stmt

 

file 01376.stmt

 

file 01377.stmt

 

file 01378.stmt

 

file 01379.stmt

 

file 01380.stmt

 

file 01381.stmt

 

file 01382.stmt

 

file 01383.stmt

 

file 01384.stmt

 

file 01385.stmt

 

file 01386.stmt

 

file 01387.stmt

 

file 01388.stmt

 

file 01389.stmt

 

file 01390.stmt

 

file 01391.stmt

 

file 01392.stmt

 

file 01393.stmt

 

file 01394.stmt

 

file 01395.stmt

 

file 01396.stmt

 

file 01397.stmt

 

file 01398.stmt

 

file 01399.stmt

 

file 01400.stmt

 

file 01401.stmt

 

file 01402.stmt

 

file 01403.stmt

 

file 01404.stmt

 

file 01405.stmt

 

file 01406.stmt

 

file 01407.stmt

 

file 01408.stmt

 

file 01409.stmt

 

file 01410.stmt

 

file 01411.stmt

 

file 01412.stmt

 

file 01413.stmt

 

file 01414.stmt

 

file 01415.stmt

 

file 01416.stmt

 

file 01417.stmt

 

file 01418.stmt

 

file 01419.stmt

 

file 01420.stmt

 

file 01421.stmt

 

file 01422.stmt

 

file 01423.stmt

 

file 01424.stmt

 

file 01425.stmt

 

file 01426.stmt

 

file 01427.stmt

 

file 01428.stmt

 

file 01429.stmt

 

file 01430.stmt

 

file 01431.stmt

 

file 01432.stmt

 

file 01433.stmt

 

file 01434.stmt

 

file 01435.stmt

 

file 01436.stmt

 

file 01437.stmt

 

file 01438.stmt

 

file 01439.stmt

 

file 01440.stmt

 

file 01441.stmt

 

file 01442.stmt

 

file 01443.stmt

 

file 01444.stmt

 

file 01445.stmt

 

file 01446.stmt

 

file 01447.stmt

 

file 01448.stmt

 

file 01449.stmt

 

file 01450.stmt

 

file 01451.stmt

 

file 01452.stmt

 

file 01453.stmt

 

file 01454.stmt

 

file 01455.stmt

 

file 01456.stmt

 

file 01457.stmt

 

file 01458.stmt

 

file 01459.stmt

 

file 01460.stmt

 

file 01461.stmt

 

file 01462.stmt

 

file 01463.stmt

 

file 01464.stmt

 

file 01465.stmt

 

file 01466.stmt

 

file 01467.stmt

 

file 01468.stmt

 

file 01469.stmt

 

file 01470.stmt

 

file 01471.stmt

 

file 01472.stmt

 

file 01473.stmt

 

file 01474.stmt

 

file 01475.stmt

 

file 01476.stmt

 

file 01477.stmt

 

file 01478.stmt

 

file 01479.stmt

 

file 01480.stmt

 

file 01481.stmt

 

file 01482.stmt

 

file 01483.stmt

 

file 01484.stmt

 

file 01485.stmt

 

file 01486.stmt

 

file 01487.stmt

 

file 01488.stmt

 

file 01489.stmt

 

file 01490.stmt

 

file 01491.stmt

 

file 01492.stmt

 

file 01493.stmt

 

file 01494.stmt

 

file 01495.stmt

 

file 01496.stmt

 

file 01497.stmt

 

file 01498.stmt

 

file 01499.stmt

 

file 01500.stmt

 

file 01501.stmt

 

file 01502.stmt

 

file 01503.stmt

 

file 01504.stmt

 

file 01505.stmt

 

file 01506.stmt

 

file 01507.stmt

 

file 01508.stmt

 

file 01509.stmt

 

file 01510.stmt

 

file 01511.stmt

 

file 01512.stmt

 

file 01513.stmt

 

file 01514.stmt

 

file 01515.stmt

 

file 01516.stmt

 

file 01517.stmt

 

file 01518.stmt

 

file 01519.stmt

 

file 01520.stmt

 

file 01521.stmt

 

file 01522.stmt

 

file 01523.stmt

 

file 01524.stmt

 

file 01525.stmt

 

file 01526.stmt

 

file 01527.stmt

 

file 01528.stmt

 

file 01529.stmt

 

file 01530.stmt

 

file 01531.stmt

 

file 01532.stmt

 

file 01533.stmt

 

file 01534.stmt

 

file 01535.stmt

 

file 01536.stmt

 

file 01537.stmt

 

file 01538.stmt

 

file 01539.stmt

 

file 01540.stmt

 

file 01541.stmt

 

file 01542.stmt

 

file 01543.stmt

 

file 01544.stmt

 

file 01545.stmt

 

file 01546.stmt

 

file 01547.stmt

 

file 01548.stmt

 

file 01549.stmt

 

file 01550.stmt

 

file 01551.stmt

 

file 01552.stmt

 

file 01553.stmt

 

file 01554.stmt

 

file 01555.stmt

 

file 01556.stmt

 

file 01557.stmt

 

file 01558.stmt

 

file 01559.stmt

 

file 01560.stmt

 

file 01561.stmt

 

file 01562.stmt

 

file 01563.stmt

 

file 01564.stmt

 

file 01565.stmt

 

file 01566.stmt

 

file 01567.stmt

 

file 01568.stmt

 

file 01569.stmt

 

file 01570.stmt

 

file 01571.stmt

 

file 01572.stmt

 

file 01573.stmt

 

file 01574.stmt

 

file 01575.stmt

 

file 01576.stmt

 

file 01577.stmt

 

file 01578.stmt

 

file 01579.stmt

 

file 01580.stmt

 

file 01581.stmt

 

file 01582.stmt

 

file 01583.stmt

 

file 01584.stmt

 

file 01585.stmt

 

file 01586.stmt

 

file 01587.stmt

 

file 01588.stmt

 

file 01589.stmt

 

file 01590.stmt

 

file 01591.stmt

 

file 01592.stmt

 

file 01593.stmt

 

file 01594.stmt

 

file 01595.stmt

 

file 01596.stmt

 

file 01597.stmt

 

file 01598.stmt

 

file 01599.stmt

 

file 01600.stmt

 

file 01601.stmt

 

file 01602.stmt

 

file 01603.stmt

 

file 01604.stmt

 

file 01605.stmt

 

file 01606.stmt

 

file 01607.stmt

 

file 01608.stmt

 

file 01609.stmt

 

file 01610.stmt

 

file 01611.stmt

 

file 01612.stmt

 

file 01613.stmt

 

file 01614.stmt

 

file 01615.stmt

 

file 01616.stmt

 

file 01617.stmt

 

file 01618.stmt

 

file 01619.stmt

 

file 01620.stmt

 

file 01621.stmt

 

file 01622.stmt

 

file 01623.stmt

 

file 01624.stmt

 

file 01625.stmt

 

file 01626.stmt

 

file 01627.stmt

 

file 01628.stmt

 

file 01629.stmt

 

file 01630.stmt

 

file 01631.stmt

 

file 01632.stmt

 

file 01633.stmt

 

file 01634.stmt

 

file 01635.stmt

 

file 01636.stmt

 

file 01637.stmt

 

file 01638.stmt

 

file 01639.stmt

 

file 01640.stmt

 

file 01641.stmt

 

file 01642.stmt

 

file 01643.stmt

 

file 01644.stmt

 

file 01645.stmt

 

file 01646.stmt

 

file 01647.stmt

 

file 01648.stmt

 

file 01649.stmt

 

file 01650.stmt

 

file 01651.stmt

 

file 01652.stmt

 

file 01653.stmt

 

file 01654.stmt

 

file 01655.stmt

 

file 01656.stmt

 

file 01657.stmt

 

file 01658.stmt

 

file 01659.stmt

 

file 01660.stmt

 

file 01661.stmt

 

file 01662.stmt

 

file 01663.stmt

 

file 01664.stmt

 

file 01665.stmt

 

file 01666.stmt

 

file 01667.stmt

 

file 01668.stmt

 

file 01669.stmt

 

file 01670.stmt

 

file 01671.stmt

 

file 01672.stmt

 

file 01673.stmt

 

file 01674.stmt

 

file 01675.stmt

 

file 01676.stmt

 

file 01677.stmt

 

file 01678.stmt

 

file 01679.stmt

 

file 01680.stmt

 

file 01681.stmt

 

file 01682.stmt

 

file 01683.stmt

 

file 01684.stmt

 

file 01685.stmt

 

file 01686.stmt

 

file 01687.stmt

 

file 01688.stmt

 

file 01689.stmt

 

file 01690.stmt

 

file 01691.stmt

 

file 01692.stmt

 

file 01693.stmt

 

file 01694.stmt

 

file 01695.stmt

 

file 01696.stmt

 

file 01697.stmt

 

file 01698.stmt

 

file 01699.stmt

 

file 01700.stmt

 

file 01701.stmt

 

file 01702.stmt

 

file 01703.stmt

 

file 01704.stmt

 

file 01705.stmt

 

file 01706.stmt

 

file 01707.stmt

 

file 01708.stmt

 

file 01709.stmt

 

file 01710.stmt

 

file 01711.stmt

 

file 01712.stmt

 

file 01713.stmt

 

file 01714.stmt

 

file 01715.stmt

 

file 01716.stmt

 

file 01717.stmt

 

file 01718.stmt

 

file 01719.stmt

 

file 01720.stmt

 

file 01721.stmt

 

file 01722.stmt

 

file 01723.stmt

 

file 01724.stmt

 

file 01725.stmt

 

file 01726.stmt

 

file 01727.stmt

 

file 01728.stmt

 

file 01729.stmt

 

file 01730.stmt

 

file 01731.stmt

 

file 01732.stmt

 

file 01733.stmt

 

file 01734.stmt

 

file 01735.stmt

 

file 01736.stmt

 

file 01737.stmt

 

file 01738.stmt

 

file 01739.stmt

 

file 01740.stmt

 

file 01741.stmt

 

file 01742.stmt

 

file 01743.stmt

 

file 01744.stmt

 

file 01745.stmt

 

file 01746.stmt

 

file 01747.stmt

 

file 01748.stmt

 

file 01749.stmt

 

file 01750.stmt

 

file 01751.stmt

 

file 01752.stmt

 

file 01753.stmt

 

file 01754.stmt

 

file 01755.stmt

 

file 01756.stmt

 

file 01757.stmt

 

file 01758.stmt

 

file 01759.stmt

 

file 01760.stmt

 

file 01761.stmt

 

file 01762.stmt

 

file 01763.stmt

 

file 01764.stmt

 

file 01765.stmt

 

file 01766.stmt

 

file 01767.stmt

 

file 01768.stmt

 

file 01769.stmt

 

file 01770.stmt

 

file 01771.stmt

 

file 01772.stmt

 

file 01773.stmt

 

file 01774.stmt

 

file 01775.stmt

 

file 01776.stmt

 

file 01777.stmt

 

file 01778.stmt

 

file 01779.stmt

 

file 01780.stmt

 

file 01781.stmt

 

file 01782.stmt

 

file 01783.stmt

 

file 01784.stmt

 

file 01785.stmt

 

file 01786.stmt

 

file 01787.stmt

 

file 01788.stmt

 

file 01789.stmt

 

file 01790.stmt

 

file 01791.stmt

 

file 01792.stmt

 

file 01793.stmt

 

file 01794.stmt

 

file 01795.stmt

 

file 01796.stmt

 

file 01797.stmt

 

file 01798.stmt

 

file 01799.stmt

 

file 01800.stmt

 

file 01801.stmt

 

file 01802.stmt

 

file 01803.stmt

 

file 01804.stmt

 

file 01805.stmt

 

file 01806.stmt

 

file 01807.stmt

 

file 01808.stmt

 

file 01809.stmt

 

file 01810.stmt

 

file 01811.stmt

 

file 01812.stmt

 

file 01813.stmt

 

file 01814.stmt

 

file 01815.stmt

 

file 01816.stmt

 

file 01817.stmt

 

file 01818.stmt

 

file 01819.stmt

 

file 01820.stmt

 

file 01821.stmt

 

file 01822.stmt

 

file 01823.stmt

 

file 01824.stmt

 

file 01825.stmt

 

file 01826.stmt

 

file 01827.stmt

 

file 01828.stmt

 

file 01829.stmt

 

file 01830.stmt

 

file 01831.stmt

 

file 01832.stmt

 

file 01833.stmt

 

file 01834.stmt

 

file 01835.stmt

 

file 01836.stmt

 

file 01837.stmt

 

file 01838.stmt

 

file 01839.stmt

 

file 01840.stmt

 

file 01841.stmt

 

file 01842.stmt

 

file 01843.stmt

 

file 01844.stmt

 

file 01845.stmt

 

file 01846.stmt

 

file 01847.stmt

 

file 01848.stmt

 

file 01849.stmt

 

file 01850.stmt

 

file 01851.stmt

 

file 01852.stmt

 

file 01853.stmt

 

file 01854.stmt

 

file 01855.stmt

 

file 01856.stmt

 

file 01857.stmt

 

file 01858.stmt

 

file 01859.stmt

 

file 01860.stmt

 

file 01861.stmt

 

file 01862.stmt

 

file 01863.stmt

 

file 01864.stmt

 

file 01865.stmt

 

file 01866.stmt

 

file 01867.stmt

 

file 01868.stmt

 

file 01869.stmt

 

file 01870.stmt

 

file 01871.stmt

 

file 01872.stmt

 

file 01873.stmt

 

file 01874.stmt

 

file 01875.stmt

 

file 01876.stmt

 

file 01877.stmt

 

file 01878.stmt

 

file 01879.stmt

 

file 01880.stmt

 

file 01881.stmt

 

file 01882.stmt

 

file 01883.stmt

 

file 01884.stmt

 

file 01885.stmt

 

file 01886.stmt

 

file 01887.stmt

 

file 01888.stmt

 

file 01889.stmt

 

file 01890.stmt

 

file 01891.stmt

 

file 01892.stmt

 

file 01893.stmt

 

file 01894.stmt

 

file 01895.stmt

 

file 01896.stmt

 

file 01897.stmt

 

file 01898.stmt

 

file 01899.stmt

 

file 01900.stmt

 

file 01901.stmt

 

file 01902.stmt

 

file 01903.stmt

 

file 01904.stmt

 

file 01905.stmt

 

file 01906.stmt

 

file 01907.stmt

 

file 01908.stmt

 

file 01909.stmt

 

file 01910.stmt

 

file 01911.stmt

 

file 01912.stmt

 

file 01913.stmt

 

dir v1/bundle/

 

file bundle.go

 

file bundle_ext_test.go

 

file bundle_test.go

 

file file.go

 

file file_bench_test.go

 

file file_test.go

 

file filefs.go

 

file filefs_test.go

 

file hash.go

 

file hash_test.go

 

file keys.go

 

file keys_test.go

 

file manifest.proto

 

file manifest.schema.json

 

file proto.go

 

file proto_test.go

 

file sign.go

 

file sign_test.go

 

file store.go

 

file store_bench_test.go

 

file store_test.go

 

file verify.go

 

file verify_test.go

 

dir v1/bundle/v1pb/

 

file manifest.pb.go

 

dir v1/capabilities/

 

file capabilities.go

 

file capabilities_test.go

 

dir v1/compile/

 

file compile.go

 

file compile_bench_test.go

 

file compile_test.go

 

dir v1/config/

 

file config.go

 

file config_test.go

 

file default.go

 

dir v1/cover/

 

file cover.go

 

file cover_bench_test.go

 

file cover_test.go

 

file file_report.go

 

file file_report_test.go

 

file range.go

 

file range_test.go

 

file threshold_error.go

 

dir v1/debug/

 

file README.md

 

file breakpoint.go

 

file debugger.go

 

file debugger_test.go

 

file event.go

 

file frame.go

 

file latch.go

 

file thread.go

 

file trace.go

 

file variable.go

 

dir v1/dependencies/

 

file deps.go

 

file deps_bench_test.go

 

file deps_test.go

 

file doc.go

 

dir v1/download/

 

file config.go

 

file config_test.go

 

file download.go

 

file download_test.go

 

file oci_download.go

 

file oci_download_test.go

 

file oci_download_unavailable.go

 

file oci_downloader.go

 

file oci_target_test.go

 

file testharness.go

 

dir v1/download/testdata/

 

file config.layer

 

file latest.manifest

 

file latest.tar.gz

 

file rego_v1.manifest

 

file rego_v1.tar.gz

 

file signed.manifest

 

file signed.tar.gz

 

dir v1/download/testdata/latest_bundle_data/

 

file data.json

 

dir v1/download/testdata/rego_v1_bundle_data/a/b/c/

 

file data.json

 

dir v1/download/testdata/rego_v1_bundle_data/http/policy/

 

file policy.rego

 

dir v1/download/testdata/signed_bundle_data/a/b/c/

 

file data.json

 

dir v1/download/testdata/signed_bundle_data/http/policy/

 

file policy.rego

 

dir v1/features/tracing/

 

file tracing.go

 

dir v1/features/wasm/

 

file wasm.go

 

dir v1/format/

 

file format.go

 

file format_test.go

 

dir v1/format/testdata/

 

file bench.rego

 

dir v1/format/testfiles/v0/

 

file test.rego

 

file test.rego.error

 

file test.rego.formatted

 

file test_assignments.rego

 

file test_assignments.rego.formatted

 

file test_contains.rego

 

file test_contains.rego.formatted

 

file test_contains.rego.formatted_no_keywords_in_refs

 

file test_contains_if.rego

 

file test_contains_if.rego.formatted

 

file test_end_of_rule_comment.rego

 

file test_end_of_rule_comment.rego.formatted

 

file test_every.rego

 

file test_every.rego.formatted

 

file test_every_with_key.rego

 

file test_every_with_key.rego.formatted

 

file test_fun_args_with_linebreaks.rego

 

file test_fun_args_with_linebreaks.rego.formatted

 

file test_functions.rego

 

file test_functions.rego.formatted

 

file test_if.rego

 

file test_if.rego.formatted

 

file test_if.rego.formatted_no_keywords_in_refs

 

file test_if_else.rego

 

file test_if_else.rego.formatted

 

file test_if_else.rego.formatted_no_keywords_in_refs

 

file test_in.rego

 

file test_in.rego.formatted

 

file test_in.rego.formatted_no_keywords_in_refs

 

file test_in_operator_with_all_keywords_import.rego

 

file test_in_operator_with_all_keywords_import.rego.formatted

 

file test_in_operator_with_parenthesis.rego

 

file test_in_operator_with_parenthesis.rego.formatted

 

file test_in_operator_without_import.rego

 

file test_in_operator_without_import.rego.formatted

 

file test_issue_1560.rego

 

file test_issue_1560.rego.formatted

 

file test_issue_2299.rego

 

file test_issue_2299.rego.formatted

 

file test_issue_2420.rego

 

file test_issue_2420.rego.formatted

 

file test_issue_3836.rego

 

file test_issue_3836.rego.formatted

 

file test_issue_3849.rego

 

file test_issue_3849.rego.formatted

 

file test_issue_4606.rego

 

file test_issue_4606.rego.formatted

 

file test_issue_5348.rego

 

file test_issue_5348.rego.formatted

 

file test_issue_5449.rego

 

file test_issue_5449.rego.formatted

 

file test_issue_5449_with_contains_ref_rule.rego

 

file test_issue_5449_with_contains_ref_rule.rego.formatted

 

file test_issue_5449_with_ref_rule.rego

 

file test_issue_5449_with_ref_rule.rego.formatted

 

file test_issue_5537_with_comprehension.rego

 

file test_issue_5537_with_comprehension.rego.formatted

 

file test_issue_5537_with_ref.rego

 

file test_issue_5537_with_ref.rego.formatted

 

file test_issue_5798.rego

 

file test_issue_5798.rego.formatted

 

file test_issue_6161.rego

 

file test_issue_6161.rego.formatted

 

file test_issue_6330.rego

 

file test_issue_6330.rego.formatted

 

file test_issue_6330_1.rego

 

file test_issue_6330_1.rego.formatted

 

file test_keywords_in_refs.rego

 

file test_keywords_in_refs.rego.formatted

 

file test_keywords_in_refs.rego.formatted_no_keywords_in_refs

 

file test_keywords_in_refs_keep_brackets.rego

 

file test_keywords_in_refs_keep_brackets.rego.formatted

 

file test_not_future_import.rego

 

file test_not_future_import.rego.formatted

 

file test_ref_heads.rego

 

file test_ref_heads.rego.formatted

 

file test_rego_v1.rego

 

file test_rego_v1.rego.formatted

 

file test_unicode.rego

 

file test_unicode.rego.formatted

 

file test_with.rego

 

file test_with.rego.formatted

 

dir v1/format/testfiles/v0_to_v1/

 

file constants.rego

 

file constants.rego.formatted

 

file deprecated_builtins.rego

 

file deprecated_builtins.rego.error

 

file duplicate_imports.rego

 

file duplicate_imports.rego.error

 

file functions.rego

 

file functions.rego.formatted

 

file keyword_errors.rego

 

file keyword_errors.rego.error

 

file keywords.rego

 

file keywords.rego.formatted

 

file multi_value.rego

 

file multi_value.rego.formatted

 

file multi_value_no_future_imports.rego

 

file multi_value_no_future_imports.rego.formatted

 

file shadowing.rego

 

file shadowing.rego.error

 

file single_value.rego

 

file single_value.rego.formatted

 

file single_value_no_future_imports.rego

 

file single_value_no_future_imports.rego.formatted

 

file test_not_future_import.rego

 

file test_not_future_import.rego.formatted

 

dir v1/format/testfiles/v1/

 

file test.rego

 

file test.rego.error

 

file test.rego.formatted

 

file test_assignments.rego

 

file test_assignments.rego.formatted

 

file test_contains.rego

 

file test_contains.rego.formatted

 

file test_contains_if.rego

 

file test_contains_if.rego.formatted

 

file test_else_strings.rego

 

file test_else_strings.rego.formatted

 

file test_end_of_rule_comment.rego

 

file test_end_of_rule_comment.rego.formatted

 

file test_every.rego

 

file test_every.rego.formatted

 

file test_every_with_key.rego

 

file test_every_with_key.rego.formatted

 

file test_fun_args_with_linebreaks.rego

 

file test_fun_args_with_linebreaks.rego.formatted

 

file test_functions.rego

 

file test_functions.rego.formatted

 

file test_future_kw_import.rego

 

file test_future_kw_import.rego.formatted

 

file test_grouping.rego

 

file test_grouping.rego.formatted

 

file test_if.rego

 

file test_if.rego.formatted

 

file test_if_else.rego

 

file test_if_else.rego.formatted

 

file test_in.rego

 

file test_in.rego.formatted

 

file test_in_operator_with_all_keywords_import.rego

 

file test_in_operator_with_all_keywords_import.rego.formatted

 

file test_in_operator_with_parenthesis.rego

 

file test_in_operator_with_parenthesis.rego.formatted

 

file test_in_operator_without_import.rego

 

file test_in_operator_without_import.rego.formatted

 

file test_issue_1560.rego

 

file test_issue_1560.rego.formatted

 

file test_issue_2299.rego

 

file test_issue_2299.rego.formatted

 

file test_issue_2420.rego

 

file test_issue_2420.rego.formatted

 

file test_issue_3836.rego

 

file test_issue_3836.rego.formatted

 

file test_issue_3849.rego

 

file test_issue_3849.rego.formatted

 

file test_issue_4606.rego

 

file test_issue_4606.rego.formatted

 

file test_issue_5348.rego

 

file test_issue_5348.rego.formatted

 

file test_issue_5449.rego

 

file test_issue_5449.rego.formatted

 

file test_issue_5449_with_contains_ref_rule.rego

 

file test_issue_5449_with_contains_ref_rule.rego.formatted

 

file test_issue_5449_with_ref_rule.rego

 

file test_issue_5449_with_ref_rule.rego.formatted

 

file test_issue_5537_with_comprehension.rego

 

file test_issue_5537_with_comprehension.rego.formatted

 

file test_issue_5537_with_ref.rego

 

file test_issue_5537_with_ref.rego.formatted

 

file test_issue_5798.rego

 

file test_issue_5798.rego.formatted

 

file test_issue_6161.rego

 

file test_issue_6161.rego.formatted

 

file test_issue_6330.rego

 

file test_issue_6330.rego.formatted

 

file test_issue_6330_1.rego

 

file test_issue_6330_1.rego.formatted

 

file test_issue_7565.rego

 

file test_issue_7565.rego.formatted

 

file test_issue_8557.rego

 

file test_issue_8557.rego.formatted

 

file test_issue_8765_with_after_object_comment.rego

 

file test_issue_8765_with_after_object_comment.rego.formatted

 

file test_issue_nested_comment.rego

 

file test_issue_nested_comment.rego.formatted

 

file test_issue_nukedcomment.rego

 

file test_issue_nukedcomment.rego.formatted

 

file test_keywords_in_refs.rego

 

file test_keywords_in_refs.rego.formatted

 

file test_keywords_in_refs.rego.formatted_no_keywords_in_refs

 

file test_keywords_in_refs_keep_brackets.rego

 

file test_keywords_in_refs_keep_brackets.rego.formatted

 

file test_metadata.rego

 

file test_metadata.rego.formatted

 

file test_metadata_already_separated.rego

 

file test_metadata_already_separated.rego.formatted

 

file test_metadata_comment_before.rego

 

file test_metadata_comment_before.rego.formatted

 

file test_metadata_single.rego

 

file test_metadata_single.rego.formatted

 

file test_not_future_import.rego

 

file test_not_future_import.rego.formatted

 

file test_ref_heads.rego

 

file test_ref_heads.rego.formatted

 

file test_rego_v1.rego

 

file test_rego_v1.rego.formatted

 

file test_template_strings.rego

 

file test_template_strings.rego.formatted

 

file test_unicode.rego

 

file test_unicode.rego.formatted

 

file test_with.rego

 

file test_with.rego.formatted

 

file test_with_indentation.rego

 

file test_with_indentation.rego.formatted

 

dir v1/hooks/

 

file hooks.go

 

dir v1/ir/

 

file ir.go

 

file marshal.go

 

file marshal_test.go

 

file plan.proto

 

file plan.schema.json

 

file pretty.go

 

file proto.go

 

file proto_test.go

 

file walk.go

 

dir v1/ir/encoding/

 

file encoding_test.go

 

dir v1/ir/v1pb/

 

file plan.pb.go

 

dir v1/keys/

 

file keys.go

 

file keys_test.go

 

dir v1/loader/

 

file errors.go

 

file loader.go

 

file loader_test.go

 

dir v1/loader/extension/

 

file extension.go

 

file extension_test.go

 

dir v1/loader/filter/

 

file filter.go

 

dir v1/loader/testdata/embedtest/

 

file foo.json

 

dir v1/loader/testdata/embedtest/bar/

 

file bar.rego

 

file bar.yaml

 

dir v1/loader/testdata/embedtest/baz/qux/

 

file qux.json

 

dir v1/logging/

 

file buffered_logger.go

 

file buffered_logger_test.go

 

file logging.go

 

file logging_test.go

 

dir v1/logging/test/

 

file test.go

 

dir v1/metrics/

 

file metrics.go

 

file metrics_bench_test.go

 

file metrics_test.go

 

dir v1/plugins/

 

file logger_integration_test.go

 

file plugins.go

 

file plugins_test.go

 

dir v1/plugins/bundle/

 

file config.go

 

file config_test.go

 

file errors.go

 

file errors_test.go

 

file plugin.go

 

file plugin_test.go

 

file status.go

 

dir v1/plugins/discovery/

 

file config.go

 

file config_test.go

 

file discovery.go

 

file discovery_test.go

 

dir v1/plugins/logger/file/

 

file plugin.go

 

file plugin_test.go

 

dir v1/plugins/logs/

 

file README.md

 

file buffer.go

 

file buffer_test.go

 

file encoder.go

 

file encoder_test.go

 

file eventBuffer.go

 

file eventBuffer_test.go

 

file logger_plugin_integration_test.go

 

file mask.go

 

file mask_test.go

 

file plugin.go

 

file plugin_benchmark_test.go

 

file plugin_test.go

 

file sizeBuffer.go

 

file sizeBuffer_test.go

 

dir v1/plugins/logs/status/

 

file status.go

 

dir v1/plugins/rest/

 

file auth.go

 

file auth_test.go

 

file auth_tls.go

 

file auth_tls_test.go

 

file aws.go

 

file aws_test.go

 

file azure.go

 

file azure_test.go

 

file gcp.go

 

file gcp_test.go

 

file rest.go

 

file rest_test.go

 

dir v1/plugins/server/decoding/

 

file config.go

 

file config_test.go

 

dir v1/plugins/server/encoding/

 

file config.go

 

file config_test.go

 

dir v1/plugins/server/metrics/

 

file config.go

 

file config_test.go

 

dir v1/plugins/status/

 

file metrics.go

 

file plugin.go

 

file plugin_test.go

 

dir v1/profiler/

 

file profiler.go

 

file profiler_bench_test.go

 

file profiler_test.go

 

dir v1/refactor/

 

file refactor.go

 

file refactor_test.go

 

dir v1/rego/

 

file errors.go

 

file example_test.go

 

file plugins.go

 

file plugins_test.go

 

file prepare_test.go

 

file rego.go

 

file rego_bench_test.go

 

file rego_external_source_test.go

 

file rego_metadata_test.go

 

file rego_test.go

 

file rego_wasm_bench_test.go

 

file rego_wasmtarget_test.go

 

file resultset.go

 

file resultset_test.go

 

dir v1/rego/compile/

 

file compile.go

 

file compile_test.go

 

dir v1/rego/testdata/

 

file ast.json

 

file bundle.tar.gz

 

dir v1/rego/testdata/aci/

 

file api.rego

 

file data.json

 

file framework.rego

 

file input.json

 

file policy.rego

 

dir v1/repl/

 

file errors.go

 

file example_test.go

 

file repl.go

 

file repl_test.go

 

file repl_wasmtarget_test.go

 

dir v1/resolver/

 

file interface.go

 

dir v1/resolver/wasm/

 

file wasm.go

 

dir v1/runtime/

 

file check_user_linux.go

 

file check_user_unix.go

 

file check_user_windows.go

 

file doc.go

 

file logging.go

 

file logging_test.go

 

file plugins_test.go

 

file runtime.go

 

file runtime_test.go

 

dir v1/runtime/info/

 

file info.go

 

dir v1/schemas/

 

file authorizationPolicy.json

 

file schemas.go

 

file schemas_test.go

 

dir v1/sdk/

 

file RawMapper.go

 

file opa.go

 

file opa_internal_test.go

 

file opa_test.go

 

file options.go

 

dir v1/sdk/test/

 

file test.go

 

dir v1/sdk/testdata/

 

file Makefile

 

file disco.tar.gz

 

file v1bundle.tar.gz

 

dir v1/sdk/testdata/bundle/

 

file data.json

 

dir v1/sdk/testdata/v1bundle/

 

file policy.rego

 

dir v1/server/

 

file buffer.go

 

file cache.go

 

file cache_test.go

 

file certs.go

 

file compile_handler.go

 

file compile_handler_bench_test.go

 

file compile_handler_checks_test.go

 

file compile_handler_test.go

 

file doc.go

 

file features.go

 

file server.go

 

file server_bench_test.go

 

file server_test.go

 

dir v1/server/authorizer/

 

file authorizer.go

 

file authorizer_test.go

 

dir v1/server/failtracer/

 

file failtracer.go

 

file hints_test.go

 

dir v1/server/handlers/

 

file compress.go

 

file compress_test.go

 

file decoding.go

 

file handlers.go

 

dir v1/server/identifier/

 

file certs.go

 

file identifier.go

 

file mock_test.go

 

file tls.go

 

file tls_test.go

 

file token.go

 

file token_test.go

 

dir v1/server/identifier/testdata/

 

file cn-cert.pem

 

file gencerts.sh

 

file key.pem

 

file ou-cert.pem

 

file spiffe-svid-cert.pem

 

file spiffe-svid-key.pem

 

dir v1/server/testdata/

 

file bench_filters.rego

 

file roles.json

 

dir v1/server/types/

 

file types.go

 

file types_extensible_test.go

 

dir v1/server/writer/

 

file writer.go

 

dir v1/storage/

 

file doc.go

 

file errors.go

 

file errors_test.go

 

file interface.go

 

file path.go

 

file path_test.go

 

file storage.go

 

file storage_test.go

 

dir v1/storage/disk/

 

file config.go

 

file config_test.go

 

file disk.go

 

file disk_test.go

 

file errors.go

 

file example_test.go

 

file metrics.go

 

file partition.go

 

file partition_test.go

 

file paths.go

 

file paths_test.go

 

file txn.go

 

file txn_test.go

 

dir v1/storage/inmem/

 

file ast.go

 

file ast_test.go

 

file example_test.go

 

file inmem.go

 

file inmem_bench_test.go

 

file inmem_test.go

 

file opts.go

 

file txn.go

 

dir v1/storage/inmem/test/

 

file testutil.go

 

dir v1/storage/internal/errors/

 

file errors.go

 

file errors_test.go

 

dir v1/storage/internal/ptr/

 

file ptr.go

 

file ptr_bench_test.go

 

dir v1/test/authz/

 

file authz_bench_test.go

 

file authz_test.go

 

file testing.go

 

dir v1/test/cases/

 

file cases.go

 

dir v1/test/cases/internal/fmtcases/

 

file main.go

 

dir v1/test/cases/internal/keywordrefs/

 

file main.go

 

file test-keywords-in-ref_v0.yaml.template

 

file test-keywords-in-ref_v1.yaml.template

 

dir v1/test/cases/testdata/

 

file testdata.go

 

dir v1/test/cases/testdata/v0/aggregates/

 

file test-aggregates-0001.yaml

 

file test-aggregates-0002.yaml

 

file test-aggregates-0003.yaml

 

file test-aggregates-0004.yaml

 

file test-aggregates-0005.yaml

 

file test-aggregates-0006.yaml

 

file test-aggregates-0007.yaml

 

file test-aggregates-0008.yaml

 

file test-aggregates-0009.yaml

 

file test-aggregates-0010.yaml

 

file test-aggregates-0011.yaml

 

file test-aggregates-0012.yaml

 

file test-aggregates-0013.yaml

 

file test-aggregates-0014.yaml

 

file test-aggregates-0015.yaml

 

file test-aggregates-0016.yaml

 

file test-aggregates-0017.yaml

 

file test-aggregates-0018.yaml

 

file test-aggregates-0019.yaml

 

file test-aggregates-0020.yaml

 

file test-aggregates-0021.yaml

 

file test-aggregates-0022.yaml

 

file test-aggregates-0023.yaml

 

file test-aggregates-0024.yaml

 

file test-aggregates-0025.yaml

 

file test-aggregates-0026.yaml

 

file test-aggregates-0027.yaml

 

file test-aggregates-0028.yaml

 

file test-aggregates-bad-utf8-runes.yaml

 

file test-membership.yaml

 

dir v1/test/cases/testdata/v0/all/

 

file test-all-0027.yaml

 

file test-all-0028.yaml

 

file test-all-0029.yaml

 

file test-all-0030.yaml

 

file test-all-0031.yaml

 

file test-all-0032.yaml

 

file test-all-0033.yaml

 

dir v1/test/cases/testdata/v0/any/

 

file test-any-0034.yaml

 

file test-any-0035.yaml

 

file test-any-0036.yaml

 

file test-any-0037.yaml

 

file test-any-0038.yaml

 

file test-any-0039.yaml

 

file test-any-0040.yaml

 

dir v1/test/cases/testdata/v0/arithmetic/

 

file test-arithmetic-0810.yaml

 

file test-arithmetic-0811.yaml

 

file test-arithmetic-0812.yaml

 

file test-arithmetic-0813.yaml

 

file test-arithmetic-0814.yaml

 

file test-arithmetic-0815.yaml

 

file test-arithmetic-0816.yaml

 

file test-arithmetic-0817.yaml

 

file test-arithmetic-0818.yaml

 

file test-arithmetic-0819.yaml

 

file test-arithmetic-0820.yaml

 

file test-arithmetic-0821.yaml

 

file test-arithmetic-0822.yaml

 

file test-arithmetic-0823.yaml

 

file test-arithmetic-0824.yaml

 

file test-arithmetic-0825.yaml

 

file test-arithmetic-ll-overflow.yaml

 

file test-arithmetic-minus-type-error.yaml

 

file test-big-int-0001.yaml

 

dir v1/test/cases/testdata/v0/array/

 

file flatten.yaml

 

file test-array-0041.yaml

 

file test-array-0042.yaml

 

file test-array-0043.yaml

 

file test-array-0044.yaml

 

file test-array-0045.yaml

 

file test-array-0046.yaml

 

file test-array-0047.yaml

 

file test-array-0048.yaml

 

file test-array-0049.yaml

 

file test-array-0050.yaml

 

file test-array-0051.yaml

 

file test-array-0052.yaml

 

dir v1/test/cases/testdata/v0/assignments/

 

file test-file-level-assignments.yaml

 

dir v1/test/cases/testdata/v0/base64builtins/

 

file test-base64builtins-0929.yaml

 

file test-base64builtins-0930.yaml

 

file test-base64builtins-0931.yaml

 

file test-base64builtins-0932.yaml

 

file test-base64builtins-0933.yaml

 

file test-base64builtins-0934.yaml

 

file test-base64builtins-0935.yaml

 

dir v1/test/cases/testdata/v0/base64urlbuiltins/

 

file test-base64urlbuiltins-0935.yaml

 

file test-base64urlbuiltins-0937.yaml

 

file test-base64urlbuiltins-0939.yaml

 

dir v1/test/cases/testdata/v0/baseandvirtualdocs/

 

file test-baseandvirtualdocs-0695.yaml

 

file test-baseandvirtualdocs-0696.yaml

 

file test-baseandvirtualdocs-0697.yaml

 

file test-baseandvirtualdocs-0698.yaml

 

file test-baseandvirtualdocs-0699.yaml

 

file test-baseandvirtualdocs-0700.yaml

 

file test-baseandvirtualdocs-0701.yaml

 

file test-baseandvirtualdocs-0702.yaml

 

file test-baseandvirtualdocs-0703.yaml

 

file test-baseandvirtualdocs-0704.yaml

 

file test-baseandvirtualdocs-0705.yaml

 

dir v1/test/cases/testdata/v0/bitsand/

 

file test-bitsand-0055.yaml

 

file test-bitsand-0056.yaml

 

file test-bitsand-0057.yaml

 

dir v1/test/cases/testdata/v0/bitsnegate/

 

file test-bitsnegate-0058.yaml

 

file test-bitsnegate-0059.yaml

 

dir v1/test/cases/testdata/v0/bitsor/

 

file test-bitsor-0052.yaml

 

file test-bitsor-0053.yaml

 

file test-bitsor-0054.yaml

 

dir v1/test/cases/testdata/v0/bitsshiftleft/

 

file test-bitsshiftleft-0063.yaml

 

file test-bitsshiftleft-0064.yaml

 

file test-bitsshiftleft-0065.yaml

 

file test-bitsshiftleft-0066.yaml

 

file test-bitsshiftleft-0067.yaml

 

dir v1/test/cases/testdata/v0/bitsshiftright/

 

file test-bitsshiftright-0068.yaml

 

file test-bitsshiftright-0069.yaml

 

file test-bitsshiftright-0070.yaml

 

dir v1/test/cases/testdata/v0/bitsxor/

 

file test-bitsxor-0060.yaml

 

file test-bitsxor-0061.yaml

 

file test-bitsxor-0062.yaml

 

dir v1/test/cases/testdata/v0/casts/

 

file test-casts-0077.yaml

 

file test-casts-0078.yaml

 

file test-casts-0079.yaml

 

file test-casts-0080.yaml

 

file test-casts-0081.yaml

 

file test-casts-0082.yaml

 

file test-casts-0083.yaml

 

file test-casts-0824.yaml

 

file test-casts-0825.yaml

 

file test-casts-0826.yaml

 

file test-casts-0827.yaml

 

dir v1/test/cases/testdata/v0/comparisonexpr/

 

file test-comparisonexpr-0608.yaml

 

file test-comparisonexpr-0609.yaml

 

file test-comparisonexpr-0610.yaml

 

file test-comparisonexpr-0611.yaml

 

file test-comparisonexpr-0612.yaml

 

file test-comparisonexpr-0613.yaml

 

file test-comparisonexpr-0614.yaml

 

file test-comparisonexpr-0615.yaml

 

file test-comparisonexpr-0616.yaml

 

file test-comparisonexpr-0617.yaml

 

file test-comparisonexpr-0618.yaml

 

file test-comparisonexpr-0619.yaml

 

file test-comparisonexpr-0620.yaml

 

dir v1/test/cases/testdata/v0/completedoc/

 

file test-completedoc-0495.yaml

 

file test-completedoc-0496.yaml

 

file test-completedoc-0497.yaml

 

file test-completedoc-0498.yaml

 

file test-completedoc-0499.yaml

 

file test-completedoc-0500.yaml

 

file test-completedoc-0501.yaml

 

file test-completedoc-0502.yaml

 

file test-completedoc-0503.yaml

 

file test-completedoc-0504.yaml

 

file test-completedoc-0505.yaml

 

file test-completedoc-0506.yaml

 

file test-completedoc-0507.yaml

 

file test-completedoc-0508.yaml

 

file test-completedoc-0509.yaml

 

file test-completedoc-0510.yaml

 

dir v1/test/cases/testdata/v0/compositebasedereference/

 

file test-compositebasedereference-1073.yaml

 

file test-compositebasedereference-1074.yaml

 

file test-compositebasedereference-1075.yaml

 

dir v1/test/cases/testdata/v0/compositereferences/

 

file test-compositereferences-0743.yaml

 

file test-compositereferences-0744.yaml

 

file test-compositereferences-0745.yaml

 

file test-compositereferences-0746.yaml

 

file test-compositereferences-0747.yaml

 

file test-compositereferences-0748.yaml

 

file test-compositereferences-0749.yaml

 

file test-compositereferences-0750.yaml

 

file test-compositereferences-0751.yaml

 

file test-compositereferences-0752.yaml

 

file test-compositereferences-0753.yaml

 

file test-compositereferences-0754.yaml

 

file test-compositereferences-0755.yaml

 

file test-compositereferences-0756.yaml

 

file test-compositereferences-0757.yaml

 

dir v1/test/cases/testdata/v0/comprehensions/

 

file test-comprehensions-0781.yaml

 

file test-comprehensions-0782.yaml

 

file test-comprehensions-0783.yaml

 

file test-comprehensions-0784.yaml

 

file test-comprehensions-0785.yaml

 

file test-comprehensions-0786.yaml

 

file test-comprehensions-0787.yaml

 

file test-comprehensions-0788.yaml

 

file test-comprehensions-0789.yaml

 

file test-comprehensions-0790.yaml

 

file test-comprehensions-0791.yaml

 

file test-comprehensions-0792.yaml

 

file test-comprehensions-0793.yaml

 

file test-comprehensions-0794.yaml

 

file test-comprehensions-0795.yaml

 

file test-comprehensions-0796.yaml

 

file test-comprehensions-0797.yaml

 

file test-comprehensions-0798.yaml

 

file test-comprehensions-0799.yaml

 

file test-comprehensions-0800.yaml

 

file test-comprehensions-0801.yaml

 

file test-comprehensions-0802.yaml

 

file test-comprehensions-0803.yaml

 

file test-comprehensions-and-vars.yaml

 

dir v1/test/cases/testdata/v0/containskeyword/

 

file test-contains-future-keyword.yaml

 

dir v1/test/cases/testdata/v0/cryptohmacequal/

 

file test-cryptohmacequal.yaml

 

dir v1/test/cases/testdata/v0/cryptohmacmd5/

 

file test-cryptohmacmd5.yaml

 

dir v1/test/cases/testdata/v0/cryptohmacsha1/

 

file test-cryptohmacsha1.yaml

 

dir v1/test/cases/testdata/v0/cryptohmacsha256/

 

file test-cryptohmacsha256.yaml

 

dir v1/test/cases/testdata/v0/cryptohmacsha512/

 

file test-cryptohmacsha512.yaml

 

dir v1/test/cases/testdata/v0/cryptomd5/

 

file test-cryptomd5-0130.yaml

 

dir v1/test/cases/testdata/v0/cryptoparsersaprivatekeys/

 

file test-cryptoparsersaprivatekey-1.yaml

 

dir v1/test/cases/testdata/v0/cryptosha1/

 

file test-cryptosha1-0131.yaml

 

dir v1/test/cases/testdata/v0/cryptosha256/

 

file test-cryptosha256-0132.yaml

 

dir v1/test/cases/testdata/v0/cryptox509parseandverifycertificates/

 

file test-cryptox509parseandverifycertificates.yaml

 

dir v1/test/cases/testdata/v0/cryptox509parsecertificaterequest/

 

file test-cryptox509parsecertificaterequest-0125.yaml

 

file test-cryptox509parsecertificaterequest-0126.yaml

 

file test-cryptox509parsecertificaterequest-0127.yaml

 

file test-cryptox509parsecertificaterequest-0128.yaml

 

file test-cryptox509parsecertificaterequest-0129.yaml

 

dir v1/test/cases/testdata/v0/cryptox509parsecertificates/

 

file test-cryptox509parsecertificates-0117.yaml

 

file test-cryptox509parsecertificates-0118.yaml

 

file test-cryptox509parsecertificates-0119.yaml

 

file test-cryptox509parsecertificates-0120.yaml

 

file test-cryptox509parsecertificates-0121.yaml

 

file test-cryptox509parsecertificates-0122.yaml

 

file test-cryptox509parsecertificates-0123.yaml

 

file test-cryptox509parsecertificates-0124.yaml

 

file test-cryptox509parsecertificates-raw-uris.yaml

 

dir v1/test/cases/testdata/v0/cryptox509parsekeypair/

 

file test-cryptox509parsekeypairs-0118.yaml

 

file test-cryptox509parsekeypairs-0119.yaml

 

dir v1/test/cases/testdata/v0/cryptox509parsersaprivatekey/

 

file test-cryptox509parsersaprivatekey-1.yaml

 

dir v1/test/cases/testdata/v0/dataderef/

 

file test-data-derefs.yaml

 

dir v1/test/cases/testdata/v0/defaultkeyword/

 

file test-default-functions.yaml

 

file test-defaultkeyword-0804.yaml

 

file test-defaultkeyword-0805.yaml

 

file test-defaultkeyword-0806.yaml

 

file test-defaultkeyword-0807.yaml

 

file test-defaultkeyword-0808.yaml

 

file test-defaultkeyword-0809.yaml

 

dir v1/test/cases/testdata/v0/disjunction/

 

file test-disjunction-0763.yaml

 

file test-disjunction-0764.yaml

 

file test-disjunction-0765.yaml

 

file test-disjunction-0766.yaml

 

file test-disjunction-0767.yaml

 

file test-disjunction-0768.yaml

 

file test-disjunction-0769.yaml

 

file test-disjunction-0770.yaml

 

file test-disjunction-0771.yaml

 

file test-disjunction-0772.yaml

 

file test-disjunction-0773.yaml

 

file test-disjunction-0774.yaml

 

file test-disjunction-0775.yaml

 

file test-disjunction-0776.yaml

 

dir v1/test/cases/testdata/v0/elsekeyword/

 

file test-elsekeyword-1054.yaml

 

file test-elsekeyword-1055.yaml

 

file test-elsekeyword-1056.yaml

 

file test-elsekeyword-1057.yaml

 

file test-elsekeyword-1058.yaml

 

file test-elsekeyword-1059.yaml

 

file test-elsekeyword-1060.yaml

 

file test-elsekeyword-1061.yaml

 

file test-elsekeyword-1062.yaml

 

file test-elsekeyword-1063.yaml

 

file test-elsekeyword-1064.yaml

 

file test-elsekeyword-1065.yaml

 

file test-elsekeyword-1066.yaml

 

file test-elsekeyword-1067.yaml

 

dir v1/test/cases/testdata/v0/embeddedvirtualdoc/

 

file test-embeddedvirtualdoc-0976.yaml

 

dir v1/test/cases/testdata/v0/eqexpr/

 

file test-eqexpr-0545.yaml

 

file test-eqexpr-0546.yaml

 

file test-eqexpr-0547.yaml

 

file test-eqexpr-0548.yaml

 

file test-eqexpr-0549.yaml

 

file test-eqexpr-0550.yaml

 

file test-eqexpr-0551.yaml

 

file test-eqexpr-0552.yaml

 

file test-eqexpr-0553.yaml

 

file test-eqexpr-0554.yaml

 

file test-eqexpr-0555.yaml

 

file test-eqexpr-0556.yaml

 

file test-eqexpr-0557.yaml

 

file test-eqexpr-0558.yaml

 

file test-eqexpr-0559.yaml

 

file test-eqexpr-0560.yaml

 

file test-eqexpr-0561.yaml

 

file test-eqexpr-0562.yaml

 

file test-eqexpr-0563.yaml

 

file test-eqexpr-0564.yaml

 

file test-eqexpr-0565.yaml

 

file test-eqexpr-0566.yaml

 

file test-eqexpr-0567.yaml

 

file test-eqexpr-0568.yaml

 

file test-eqexpr-0569.yaml

 

file test-eqexpr-0570.yaml

 

file test-eqexpr-0571.yaml

 

file test-eqexpr-0572.yaml

 

file test-eqexpr-0573.yaml

 

file test-eqexpr-0574.yaml

 

file test-eqexpr-0575.yaml

 

file test-eqexpr-0576.yaml

 

file test-eqexpr-0577.yaml

 

file test-eqexpr-0578.yaml

 

file test-eqexpr-0579.yaml

 

file test-eqexpr-0580.yaml

 

file test-eqexpr-0581.yaml

 

file test-eqexpr-0582.yaml

 

file test-eqexpr-0583.yaml

 

file test-eqexpr-0584.yaml

 

file test-eqexpr-0585.yaml

 

file test-eqexpr-0586.yaml

 

file test-eqexpr-0587.yaml

 

file test-eqexpr-0588.yaml

 

file test-eqexpr-0589.yaml

 

file test-eqexpr-0590.yaml

 

file test-eqexpr-0591.yaml

 

file test-eqexpr-0592.yaml

 

file test-eqexpr-0593.yaml

 

file test-eqexpr-0594.yaml

 

file test-eqexpr-0595.yaml

 

file test-eqexpr-0596.yaml

 

file test-eqexpr-0597.yaml

 

file test-eqexpr-0598.yaml

 

file test-eqexpr-0599.yaml

 

dir v1/test/cases/testdata/v0/evaltermexpr/

 

file test-evaltermexpr-0525.yaml

 

file test-evaltermexpr-0526.yaml

 

file test-evaltermexpr-0527.yaml

 

file test-evaltermexpr-0528.yaml

 

file test-evaltermexpr-0529.yaml

 

file test-evaltermexpr-0530.yaml

 

file test-evaltermexpr-0531.yaml

 

file test-evaltermexpr-0532.yaml

 

file test-evaltermexpr-0533.yaml

 

file test-evaltermexpr-0534.yaml

 

file test-evaltermexpr-0535.yaml

 

file test-evaltermexpr-0536.yaml

 

file test-evaltermexpr-0537.yaml

 

file test-evaltermexpr-0538.yaml

 

file test-evaltermexpr-0539.yaml

 

file test-evaltermexpr-0540.yaml

 

file test-evaltermexpr-0541.yaml

 

file test-evaltermexpr-0542.yaml

 

file test-evaltermexpr-0543.yaml

 

file test-evaltermexpr-0544.yaml

 

dir v1/test/cases/testdata/v0/every/

 

file every.yaml

 

file non_iterable_domain.yaml

 

file textbook.yaml

 

dir v1/test/cases/testdata/v0/example/

 

file test-example-1070.yaml

 

file test-example-1071.yaml

 

file test-example-1072.yaml

 

dir v1/test/cases/testdata/v0/fix1863/

 

file test-fix1863-0706.yaml

 

file test-fix1863-0707.yaml

 

file test-fix1863-0708.yaml

 

dir v1/test/cases/testdata/v0/functionerrors/

 

file test-conflicts.yaml

 

file test-functionerrors-1012.yaml

 

file test-functionerrors-1013.yaml

 

file test-functionerrors-1014.yaml

 

file test-functionerrors-undefined-builtin-result.yaml

 

dir v1/test/cases/testdata/v0/functions/

 

file test-functions-0990.yaml

 

file test-functions-0991.yaml

 

file test-functions-0992.yaml

 

file test-functions-0993.yaml

 

file test-functions-0994.yaml

 

file test-functions-0995.yaml

 

file test-functions-0996.yaml

 

file test-functions-0997.yaml

 

file test-functions-0998.yaml

 

file test-functions-0999.yaml

 

file test-functions-1000.yaml

 

file test-functions-1001.yaml

 

file test-functions-1002.yaml

 

file test-functions-1003.yaml

 

file test-functions-1004.yaml

 

file test-functions-1005.yaml

 

file test-functions-1006.yaml

 

file test-functions-1007.yaml

 

file test-functions-1008.yaml

 

file test-functions-1009.yaml

 

file test-functions-1010.yaml

 

file test-functions-1011.yaml

 

file test-functions-default.yaml

 

file test-functions-nested-with-early-exit.yaml

 

file test-functions-unused-arg.yaml

 

dir v1/test/cases/testdata/v0/globmatch/

 

file test-globmatch-0133.yaml

 

file test-globmatch-0134.yaml

 

file test-globmatch-0135.yaml

 

file test-globmatch-0136.yaml

 

file test-globmatch-0137.yaml

 

file test-globmatch-0138.yaml

 

file test-globmatch-0139.yaml

 

file test-globmatch-0140.yaml

 

file test-globmatch-0141.yaml

 

file test-globmatch-0142.yaml

 

file test-globmatch-0143.yaml

 

file test-globmatch-0144.yaml

 

file test-globmatch-0145.yaml

 

file test-globmatch-0146.yaml

 

file test-globmatch-0147.yaml

 

file test-globmatch-0148.yaml

 

file test-globmatch-0149.yaml

 

file test-globmatch-0150.yaml

 

file test-globmatch-0151.yaml

 

file test-globmatch-0152.yaml

 

file test-globmatch-0153.yaml

 

file test-globmatch-0154.yaml

 

file test-globmatch-0155.yaml

 

file test-globmatch-0156.yaml

 

file test-globmatch-0157.yaml

 

file test-globmatch-0158.yaml

 

file test-globmatch-0159.yaml

 

file test-globmatch-issue-5273.yaml

 

file test-globmatch-issue-5283.yaml

 

dir v1/test/cases/testdata/v0/globquotemeta/

 

file test-globquotemeta-0159.yaml

 

dir v1/test/cases/testdata/v0/globsmatch/

 

file test-globsmatch-0865.yaml

 

file test-globsmatch-0866.yaml

 

file test-globsmatch-0867.yaml

 

file test-globsmatch-0868.yaml

 

file test-globsmatch-0869.yaml

 

file test-globsmatch-0870.yaml

 

dir v1/test/cases/testdata/v0/graphql/

 

file test-graphql-basic-ast.yaml

 

file test-graphql-is-valid.yaml

 

file test-graphql-parse-and-verify.yaml

 

file test-graphql-parse-query.yaml

 

file test-graphql-parse-schema.yaml

 

file test-graphql-parse.yaml

 

file test-graphql-schema-is-valid.yaml

 

dir v1/test/cases/testdata/v0/helloworld/

 

file test-helloworld-1.yaml

 

dir v1/test/cases/testdata/v0/hexbuiltins/

 

file test-hexbuiltins-0939.yaml

 

file test-hexbuiltins-0940.yaml

 

file test-hexbuiltins-0941.yaml

 

dir v1/test/cases/testdata/v0/indexing/

 

file array-any.yaml

 

dir v1/test/cases/testdata/v0/indirectreferences/

 

file test-indirectreferences-0758.yaml

 

file test-indirectreferences-0759.yaml

 

file test-indirectreferences-0760.yaml

 

file test-indirectreferences-0761.yaml

 

file test-indirectreferences-0762.yaml

 

dir v1/test/cases/testdata/v0/inputvalues/

 

file test-inputvalues-0977.yaml

 

file test-inputvalues-0978.yaml

 

file test-inputvalues-0979.yaml

 

file test-inputvalues-0980.yaml

 

file test-inputvalues-0981.yaml

 

file test-inputvalues-0982.yaml

 

file test-inputvalues-0983.yaml

 

dir v1/test/cases/testdata/v0/intersection/

 

file test-intersection-0352.yaml

 

file test-intersection-0353.yaml

 

file test-intersection-0354.yaml

 

file test-intersection-0355.yaml

 

file test-intersection-0356.yaml

 

dir v1/test/cases/testdata/v0/invalidkeyerror/

 

file test-invalidkeyerror-0176.yaml

 

file test-invalidkeyerror-0177.yaml

 

dir v1/test/cases/testdata/v0/jsonbuiltins/

 

file test-is-valid.yaml

 

file test-json-marshal-with-options.yaml

 

file test-jsonbuiltins-0924.yaml

 

file test-jsonbuiltins-0925.yaml

 

file test-jsonbuiltins-0926.yaml

 

file test-jsonbuiltins-0927.yaml

 

file test-jsonbuiltins-0928.yaml

 

file test-marshal-large-ints.yaml

 

dir v1/test/cases/testdata/v0/jsonfilter/

 

file test-jsonfilter-0218.yaml

 

file test-jsonfilter-0219.yaml

 

file test-jsonfilter-0220.yaml

 

file test-jsonfilter-0221.yaml

 

file test-jsonfilter-0222.yaml

 

file test-jsonfilter-0223.yaml

 

file test-jsonfilter-0224.yaml

 

file test-jsonfilter-0225.yaml

 

file test-jsonfilter-0226.yaml

 

file test-jsonfilter-0227.yaml

 

file test-jsonfilter-0228.yaml

 

dir v1/test/cases/testdata/v0/jsonfilteridempotent/

 

file test-jsonfilteridempotent-0229.yaml

 

dir v1/test/cases/testdata/v0/jsonpatch/

 

file coverage.yaml

 

file json-patch-tests.yaml

 

file set.yaml

 

dir v1/test/cases/testdata/v0/jsonremove/

 

file test-jsonremove-0230.yaml

 

file test-jsonremove-0231.yaml

 

file test-jsonremove-0232.yaml

 

file test-jsonremove-0233.yaml

 

file test-jsonremove-0234.yaml

 

file test-jsonremove-0235.yaml

 

file test-jsonremove-0236.yaml

 

file test-jsonremove-0237.yaml

 

file test-jsonremove-0238.yaml

 

file test-jsonremove-0239.yaml

 

file test-jsonremove-0240.yaml

 

file test-jsonremove-0241.yaml

 

file test-jsonremove-0242.yaml

 

file test-jsonremove-0243.yaml

 

file test-jsonremove-0244.yaml

 

file test-jsonremove-0245.yaml

 

file test-jsonremove-0246.yaml

 

file test-jsonremove-0247.yaml

 

file test-jsonremove-0248.yaml

 

file test-jsonremove-0249.yaml

 

file test-jsonremove-0250.yaml

 

file test-jsonremove-0251.yaml

 

file test-jsonremove-0252.yaml

 

file test-jsonremove-0253.yaml

 

file test-jsonremove-0254.yaml

 

dir v1/test/cases/testdata/v0/jsonremoveidempotent/

 

file test-jsonremoveidempotent-0255.yaml

 

dir v1/test/cases/testdata/v0/jsonschema/

 

file test-json-match_schema.yaml

 

file test-json-verify_schema.yaml

 

dir v1/test/cases/testdata/v0/jwtbuiltins/

 

file test-jwtbuiltins-0389.yaml

 

file test-jwtbuiltins-0390.yaml

 

file test-jwtbuiltins-0391.yaml

 

file test-jwtbuiltins-0392.yaml

 

file test-jwtbuiltins-0393.yaml

 

file test-jwtbuiltins-0394.yaml

 

file test-jwtbuiltins-0395.yaml

 

file test-jwtbuiltins-0396.yaml

 

file test-jwtbuiltins-0397.yaml

 

file test-jwtbuiltins-0398.yaml

 

file test-jwtbuiltins-0399.yaml

 

file test-jwtbuiltins-0400.yaml

 

dir v1/test/cases/testdata/v0/jwtdecodeverify/

 

file test-jwtdecodeverify-0449.yaml

 

file test-jwtdecodeverify-0450.yaml

 

file test-jwtdecodeverify-0451.yaml

 

file test-jwtdecodeverify-0452.yaml

 

file test-jwtdecodeverify-0453.yaml

 

file test-jwtdecodeverify-0454.yaml

 

file test-jwtdecodeverify-0455.yaml

 

file test-jwtdecodeverify-0456.yaml

 

file test-jwtdecodeverify-0457.yaml

 

file test-jwtdecodeverify-0458.yaml

 

file test-jwtdecodeverify-0459.yaml

 

file test-jwtdecodeverify-0460.yaml

 

file test-jwtdecodeverify-0461.yaml

 

file test-jwtdecodeverify-0462.yaml

 

file test-jwtdecodeverify-0463.yaml

 

file test-jwtdecodeverify-0464.yaml

 

file test-jwtdecodeverify-0465.yaml

 

file test-jwtdecodeverify-0466.yaml

 

file test-jwtdecodeverify-0467.yaml

 

file test-jwtdecodeverify-0468.yaml

 

file test-jwtdecodeverify-0469.yaml

 

file test-jwtdecodeverify-0470.yaml

 

file test-jwtdecodeverify-0471.yaml

 

file test-jwtdecodeverify-0472.yaml

 

file test-jwtdecodeverify-0473.yaml

 

file test-jwtdecodeverify-0474.yaml

 

file test-jwtdecodeverify-0475.yaml

 

file test-jwtdecodeverify-0476.yaml

 

file test-jwtdecodeverify-0477.yaml

 

file test-jwtdecodeverify-0478.yaml

 

file test-jwtdecodeverify-0479.yaml

 

file test-jwtdecodeverify-0480.yaml

 

file test-jwtdecodeverify-0481.yaml

 

file test-jwtdecodeverify-0482.yaml

 

file test-jwtdecodeverify-0483.yaml

 

file test-jwtdecodeverify-0484.yaml

 

file test-jwtdecodeverify-0485.yaml

 

file test-jwtdecodeverify-0486.yaml

 

file test-jwtdecodeverify-0487.yaml

 

file test-jwtdecodeverify-0488.yaml

 

file test-jwtdecodeverify-0489.yaml

 

file test-jwtdecodeverify-0490.yaml

 

file test-jwtdecodeverify-0491.yaml

 

file test-jwtdecodeverify-eddsa.yaml

 

file test-jwtdecodeverify-invalid-exp-type.yaml

 

file test-jwtdecodeverify-invalid-nbf-type.yaml

 

file test-jwtdecodeverify-missing-iss-while-required.yaml

 

dir v1/test/cases/testdata/v0/jwtencodesign/

 

file test-jwtencodesign-0492.yaml

 

file test-jwtencodesign-0493.yaml

 

file test-jwtencodesign-0494.yaml

 

file test-jwtencodesign-eddsa.yaml

 

file test-jwtencodesign-integer-timestamps.yaml

 

file test-jwtencodesign-set-data.yaml

 

dir v1/test/cases/testdata/v0/jwtencodesignheadererrors/

 

file test-jwtencodesignheadererrors-0379.yaml

 

file test-jwtencodesignheadererrors-0380.yaml

 

file test-jwtencodesignheadererrors-0381.yaml

 

file test-jwtencodesignheadererrors-0382.yaml

 

file test-jwtencodesignheadererrors-0383.yaml

 

dir v1/test/cases/testdata/v0/jwtencodesignpayloaderrors/

 

file test-jwtencodesignpayloaderrors-0376.yaml

 

file test-jwtencodesignpayloaderrors-0377.yaml

 

file test-jwtencodesignpayloaderrors-0378.yaml

 

dir v1/test/cases/testdata/v0/jwtencodesignraw/

 

file test-jwtencodesignraw-0384.yaml

 

file test-jwtencodesignraw-0385.yaml

 

file test-jwtencodesignraw-0386.yaml

 

file test-jwtencodesignraw-0387.yaml

 

file test-jwtencodesignraw-0388.yaml

 

file test-jwtencodesignraw-eddsa.yaml

 

dir v1/test/cases/testdata/v0/jwtverifyeddsa/

 

file test-jwtverifyeddsa.yaml

 

dir v1/test/cases/testdata/v0/jwtverifyhs256/

 

file test-jwtverifyhs256-0440.yaml

 

file test-jwtverifyhs256-0441.yaml

 

file test-jwtverifyhs256-0442.yaml

 

dir v1/test/cases/testdata/v0/jwtverifyhs384/

 

file test-jwtverifyhs384-0443.yaml

 

file test-jwtverifyhs384-0444.yaml

 

file test-jwtverifyhs384-0445.yaml

 

dir v1/test/cases/testdata/v0/jwtverifyhs512/

 

file test-jwtverifyhs512-0446.yaml

 

file test-jwtverifyhs512-0447.yaml

 

file test-jwtverifyhs512-0448.yaml

 

dir v1/test/cases/testdata/v0/jwtverifyrsa/

 

file test-jwtverifyrsa-0401.yaml

 

file test-jwtverifyrsa-0402.yaml

 

file test-jwtverifyrsa-0403.yaml

 

file test-jwtverifyrsa-0404.yaml

 

file test-jwtverifyrsa-0405.yaml

 

file test-jwtverifyrsa-0406.yaml

 

file test-jwtverifyrsa-0407.yaml

 

file test-jwtverifyrsa-0408.yaml

 

file test-jwtverifyrsa-0409.yaml

 

file test-jwtverifyrsa-0410.yaml

 

file test-jwtverifyrsa-0411.yaml

 

file test-jwtverifyrsa-0412.yaml

 

file test-jwtverifyrsa-0413.yaml

 

file test-jwtverifyrsa-0414.yaml

 

file test-jwtverifyrsa-0415.yaml

 

file test-jwtverifyrsa-0416.yaml

 

file test-jwtverifyrsa-0417.yaml

 

file test-jwtverifyrsa-0418.yaml

 

file test-jwtverifyrsa-0419.yaml

 

file test-jwtverifyrsa-0420.yaml

 

file test-jwtverifyrsa-0421.yaml

 

file test-jwtverifyrsa-0422.yaml

 

file test-jwtverifyrsa-0423.yaml

 

file test-jwtverifyrsa-0424.yaml

 

file test-jwtverifyrsa-0425.yaml

 

file test-jwtverifyrsa-0426.yaml

 

file test-jwtverifyrsa-0427.yaml

 

file test-jwtverifyrsa-0428.yaml

 

file test-jwtverifyrsa-0429.yaml

 

file test-jwtverifyrsa-0430.yaml

 

file test-jwtverifyrsa-0431.yaml

 

file test-jwtverifyrsa-0432.yaml

 

file test-jwtverifyrsa-0433.yaml

 

file test-jwtverifyrsa-0434.yaml

 

file test-jwtverifyrsa-0435.yaml

 

file test-jwtverifyrsa-0436.yaml

 

file test-jwtverifyrsa-0437.yaml

 

file test-jwtverifyrsa-0438.yaml

 

file test-jwtverifyrsa-0439.yaml

 

dir v1/test/cases/testdata/v0/keywordrefs/

 

file test-keyword-as.yaml

 

file test-keyword-default.yaml

 

file test-keyword-else.yaml

 

file test-keyword-false.yaml

 

file test-keyword-import.yaml

 

file test-keyword-not.yaml

 

file test-keyword-null.yaml

 

file test-keyword-package.yaml

 

file test-keyword-some.yaml

 

file test-keyword-true.yaml

 

file test-keyword-with.yaml

 

dir v1/test/cases/testdata/v0/negation/

 

file test-negation-0777.yaml

 

file test-negation-0778.yaml

 

file test-negation-0779.yaml

 

file test-negation-0780.yaml

 

file test-negation-data-ref-with-var.yaml

 

dir v1/test/cases/testdata/v0/nestedreferences/

 

file test-nestedreferences-0709.yaml

 

file test-nestedreferences-0710.yaml

 

file test-nestedreferences-0711.yaml

 

file test-nestedreferences-0712.yaml

 

file test-nestedreferences-0713.yaml

 

file test-nestedreferences-0714.yaml

 

file test-nestedreferences-0715.yaml

 

file test-nestedreferences-0716.yaml

 

file test-nestedreferences-0717.yaml

 

file test-nestedreferences-0718.yaml

 

file test-nestedreferences-0719.yaml

 

file test-nestedreferences-0720.yaml

 

file test-nestedreferences-0721.yaml

 

file test-nestedreferences-0722.yaml

 

file test-nestedreferences-0723.yaml

 

file test-nestedreferences-0724.yaml

 

file test-nestedreferences-0725.yaml

 

dir v1/test/cases/testdata/v0/netcidrcontains/

 

file test-netcidrcontains-0092.yaml

 

file test-netcidrcontains-0093.yaml

 

file test-netcidrcontains-0094.yaml

 

file test-netcidrcontains-0095.yaml

 

file test-netcidrcontains-0096.yaml

 

file test-netcidrcontains-0097.yaml

 

file test-netcidrcontains-0098.yaml

 

file test-netcidrcontains-0099.yaml

 

file test-netcidrcontains-0100.yaml

 

file test-netcidrcontains-0101.yaml

 

file test-netcidrcontains-0102.yaml

 

file test-netcidrcontains-0103.yaml

 

dir v1/test/cases/testdata/v0/netcidrcontainsmatches/

 

file test-netcidrcontainsmatches-0104.yaml

 

file test-netcidrcontainsmatches-0105.yaml

 

file test-netcidrcontainsmatches-0106.yaml

 

file test-netcidrcontainsmatches-0107.yaml

 

file test-netcidrcontainsmatches-0108.yaml

 

file test-netcidrcontainsmatches-0109.yaml

 

file test-netcidrcontainsmatches-0110.yaml

 

file test-netcidrcontainsmatches-0111.yaml

 

file test-netcidrcontainsmatches-0112.yaml

 

dir v1/test/cases/testdata/v0/netcidrexpand/

 

file test-netcidrexpand-0113.yaml

 

file test-netcidrexpand-0114.yaml

 

file test-netcidrexpand-0115.yaml

 

file test-netcidrexpand-0116.yaml

 

dir v1/test/cases/testdata/v0/netcidrintersects/

 

file test-netcidrintersects-0086.yaml

 

file test-netcidrintersects-0087.yaml

 

file test-netcidrintersects-0088.yaml

 

file test-netcidrintersects-0089.yaml

 

file test-netcidrintersects-0090.yaml

 

file test-netcidrintersects-0091.yaml

 

dir v1/test/cases/testdata/v0/netcidrisvalid/

 

file test_netcidrisvalid-0001.yaml

 

dir v1/test/cases/testdata/v0/netcidrmerge/

 

file test-ipv6-with-and-without-prefix.yaml

 

file test-netcidrmerge0117.yaml

 

dir v1/test/cases/testdata/v0/netcidroverlap/

 

file test-netcidroverlap-0084.yaml

 

file test-netcidroverlap-0085.yaml

 

dir v1/test/cases/testdata/v0/netlookupipaddr/

 

file test-netlookupipaddr.yaml

 

dir v1/test/cases/testdata/v0/numbersrange/

 

file test-numbersrange-0256.yaml

 

file test-numbersrange-0257.yaml

 

file test-numbersrange-0258.yaml

 

file test-numbersrange-0259.yaml

 

file test-numbersrange-0260.yaml

 

file test-numbersrange-0261.yaml

 

dir v1/test/cases/testdata/v0/numbersrangestep/

 

file test-numbersrangestep.yaml

 

dir v1/test/cases/testdata/v0/objectfilter/

 

file test-objectfilter-0300.yaml

 

file test-objectfilter-0301.yaml

 

file test-objectfilter-0302.yaml

 

file test-objectfilter-0303.yaml

 

file test-objectfilter-0304.yaml

 

file test-objectfilter-0305.yaml

 

file test-objectfilter-0306.yaml

 

file test-objectfilter-0307.yaml

 

file test-objectfilter-0308.yaml

 

file test-objectfilter-0309.yaml

 

file test-objectfilter-0310.yaml

 

file test-objectfilter-0311.yaml

 

file test-objectfilter-0312.yaml

 

file test-objectfilter-0313.yaml

 

file test-objectfilter-0314.yaml

 

file test-objectfilter-0315.yaml

 

file test-objectfilter-0316.yaml

 

file test-objectfilter-0317.yaml

 

dir v1/test/cases/testdata/v0/objectfilteridempotent/

 

file test-objectfilteridempotent-0319.yaml

 

dir v1/test/cases/testdata/v0/objectfilternonstringkey/

 

file test-objectfilternonstringkey-0318.yaml

 

dir v1/test/cases/testdata/v0/objectget/

 

file test-objectget-0262.yaml

 

file test-objectget-0263.yaml

 

file test-objectget-0264.yaml

 

file test-objectget-0265.yaml

 

file test-objectget-0266.yaml

 

file test-objectget-0267.yaml

 

file test-objectget-path.yaml

 

dir v1/test/cases/testdata/v0/objectkeys/

 

file test-objectkeys.yaml

 

dir v1/test/cases/testdata/v0/objectremove/

 

file test-objectremove-0279.yaml

 

file test-objectremove-0280.yaml

 

file test-objectremove-0281.yaml

 

file test-objectremove-0282.yaml

 

file test-objectremove-0283.yaml

 

file test-objectremove-0284.yaml

 

file test-objectremove-0285.yaml

 

file test-objectremove-0286.yaml

 

file test-objectremove-0287.yaml

 

file test-objectremove-0288.yaml

 

file test-objectremove-0289.yaml

 

file test-objectremove-0290.yaml

 

file test-objectremove-0291.yaml

 

file test-objectremove-0292.yaml

 

file test-objectremove-0293.yaml

 

file test-objectremove-0294.yaml

 

file test-objectremove-0295.yaml

 

file test-objectremove-0296.yaml

 

file test-objectremove-0297.yaml

 

dir v1/test/cases/testdata/v0/objectremoveidempotent/

 

file test-objectremoveidempotent-0298.yaml

 

dir v1/test/cases/testdata/v0/objectremovenonstringkey/

 

file test-objectremovenonstringkey-0299.yaml

 

dir v1/test/cases/testdata/v0/objectunion/

 

file test-objectunion-0268.yaml

 

file test-objectunion-0269.yaml

 

file test-objectunion-0270.yaml

 

file test-objectunion-0271.yaml

 

file test-objectunion-0272.yaml

 

file test-objectunion-0273.yaml

 

file test-objectunion-0274.yaml

 

file test-objectunion-0275.yaml

 

file test-objectunion-0276.yaml

 

file test-objectunion-0277.yaml

 

file test-objectunion-0278.yaml

 

dir v1/test/cases/testdata/v0/objectunionn/

 

file test-objectunionn-0001.yaml

 

dir v1/test/cases/testdata/v0/partialdocconstants/

 

file test-partialdocconstants-0984.yaml

 

file test-partialdocconstants-0985.yaml

 

file test-partialdocconstants-0986.yaml

 

file test-partialdocconstants-0987.yaml

 

file test-partialdocconstants-0988.yaml

 

file test-partialdocconstants-0989.yaml

 

dir v1/test/cases/testdata/v0/partialiter/

 

file test-partialiter-001.yaml

 

dir v1/test/cases/testdata/v0/partialobjectdoc/

 

file test-partialobjectdoc-0519.yaml

 

file test-partialobjectdoc-0520.yaml

 

file test-partialobjectdoc-0521.yaml

 

file test-partialobjectdoc-0522.yaml

 

file test-partialobjectdoc-0523.yaml

 

file test-partialobjectdoc-0524.yaml

 

file test-partialobjectdoc-ref.yaml

 

file test-wasm-cases.yaml

 

dir v1/test/cases/testdata/v0/partialsetdoc/

 

file test-issue-3369.yaml

 

file test-issue-3376.yaml

 

file test-issue-3819.yaml

 

file test-partialsetdoc-0511.yaml

 

file test-partialsetdoc-0512.yaml

 

file test-partialsetdoc-0513.yaml

 

file test-partialsetdoc-0514.yaml

 

file test-partialsetdoc-0515.yaml

 

file test-partialsetdoc-0516.yaml

 

file test-partialsetdoc-0517.yaml

 

file test-partialsetdoc-0518.yaml

 

dir v1/test/cases/testdata/v0/planner-ir/

 

file test-array-ir-unify.yaml

 

file test-call-dynamic.yaml

 

dir v1/test/cases/testdata/v0/providers-aws/

 

file aws-sign_req-errors.yaml

 

file aws-sign_req.yaml

 

dir v1/test/cases/testdata/v0/rand/

 

file test-rand.intn.yaml

 

dir v1/test/cases/testdata/v0/reachable/

 

file test-reachable-0322.yaml

 

file test-reachable-0323.yaml

 

file test-reachable-0324.yaml

 

file test-reachable-0325.yaml

 

file test-reachable-0326.yaml

 

file test-reachable-0327.yaml

 

file test-reachable-0328.yaml

 

file test-reachable-paths-0422.yaml

 

file test-reachable-paths-1022.yaml

 

dir v1/test/cases/testdata/v0/refheads/

 

file test-generic-refs.yaml

 

file test-refs-as-rule-heads.yaml

 

file test-regressions.yaml

 

dir v1/test/cases/testdata/v0/regexfind/

 

file test-regexfind-0334.yaml

 

file test-regexfind-0335.yaml

 

file test-regexfind-0336.yaml

 

dir v1/test/cases/testdata/v0/regexfindallstringsubmatch/

 

file test-regexfindallstringsubmatch-0337.yaml

 

file test-regexfindallstringsubmatch-0338.yaml

 

file test-regexfindallstringsubmatch-0339.yaml

 

file test-regexfindallstringsubmatch-0340.yaml

 

file test-regexfindallstringsubmatch-0341.yaml

 

file test-regexfindallstringsubmatch-0342.yaml

 

file test-regexfindallstringsubmatch-0343.yaml

 

file test-regexfindallstringsubmatch-large-input.yaml

 

dir v1/test/cases/testdata/v0/regexisvalid/

 

file test-regexisvalid-0329.yaml

 

file test-regexisvalid-0330.yaml

 

file test-regexisvalid-0331.yaml

 

dir v1/test/cases/testdata/v0/regexmatch/

 

file test-regexmatch-0855.yaml

 

file test-regexmatch-0856.yaml

 

file test-regexmatch-0857.yaml

 

file test-regexmatch-0858.yaml

 

file test-regexmatch-0859.yaml

 

file test-regexmatch-0860.yaml

 

file test-regexmatch-0861.yaml

 

dir v1/test/cases/testdata/v0/regexmatchtemplate/

 

file test-regexmatchtemplate-0332.yaml

 

file test-regexmatchtemplate-0333.yaml

 

dir v1/test/cases/testdata/v0/regexreplace/

 

file test-regexreplace-0001.yaml

 

dir v1/test/cases/testdata/v0/regexsplit/

 

file test-regexsplit-0862.yaml

 

file test-regexsplit-0863.yaml

 

file test-regexsplit-0864.yaml

 

dir v1/test/cases/testdata/v0/regometadatachain/

 

file test-regometadatachain-1.yaml

 

dir v1/test/cases/testdata/v0/regometadatarule/

 

file test-regometadatarule-1.yaml

 

dir v1/test/cases/testdata/v0/regoparsemodule/

 

file test-regoparsemodule-0320.yaml

 

file test-regoparsemodule-0321.yaml

 

dir v1/test/cases/testdata/v0/rendertemplate/

 

file rendertemplate.yaml

 

dir v1/test/cases/testdata/v0/replacen/

 

file test-replacen-0374.yaml

 

file test-replacen-0375.yaml

 

file test-replacen-bad-operands.yaml

 

dir v1/test/cases/testdata/v0/semvercompare/

 

file test-semvercompare-0344.yaml

 

file test-semvercompare-0345.yaml

 

file test-semvercompare-0346.yaml

 

file test-semvercompare-0347.yaml

 

file test-semvercompare-0348.yaml

 

dir v1/test/cases/testdata/v0/semverisvalid/

 

file test-semverisvalid-0349.yaml

 

file test-semverisvalid-0350.yaml

 

file test-semverisvalid-0351.yaml

 

dir v1/test/cases/testdata/v0/sets/

 

file test-sets-0871.yaml

 

file test-sets-0872.yaml

 

file test-sets-0873.yaml

 

file test-sets-0874.yaml

 

file test-sets-0875.yaml

 

file test-sets-0876.yaml

 

dir v1/test/cases/testdata/v0/sprintf/

 

file test-sprintf.yaml

 

dir v1/test/cases/testdata/v0/strings/

 

file test-anyprefixmatch.yaml

 

file test-anysuffixmatch.yaml

 

file test-strings-0877.yaml

 

file test-strings-0878.yaml

 

file test-strings-0879.yaml

 

file test-strings-0880.yaml

 

file test-strings-0881.yaml

 

file test-strings-0882.yaml

 

file test-strings-0883.yaml

 

file test-strings-0884.yaml

 

file test-strings-0885.yaml

 

file test-strings-0886.yaml

 

file test-strings-0887.yaml

 

file test-strings-0888.yaml

 

file test-strings-0889.yaml

 

file test-strings-0890.yaml

 

file test-strings-0891.yaml

 

file test-strings-0892.yaml

 

file test-strings-0893.yaml

 

file test-strings-0894.yaml

 

file test-strings-0895.yaml

 

file test-strings-0896.yaml

 

file test-strings-0897.yaml

 

file test-strings-0898.yaml

 

file test-strings-0899.yaml

 

file test-strings-0900.yaml

 

file test-strings-0901.yaml

 

file test-strings-0902.yaml

 

file test-strings-0903.yaml

 

file test-strings-0904.yaml

 

file test-strings-0905.yaml

 

file test-strings-0906.yaml

 

file test-strings-0907.yaml

 

file test-strings-0908.yaml

 

file test-strings-0909.yaml

 

file test-strings-0910.yaml

 

file test-strings-0911.yaml

 

file test-strings-0912.yaml

 

file test-strings-0913.yaml

 

file test-strings-0914.yaml

 

file test-strings-0915.yaml

 

file test-strings-0916.yaml

 

file test-strings-0917.yaml

 

file test-strings-0918.yaml

 

file test-strings-0919.yaml

 

file test-strings-0920.yaml

 

file test-strings-0921.yaml

 

file test-strings-0922.yaml

 

file test-strings-0923.yaml

 

file test-strings-0924.yaml

 

file test-strings-0925.yaml

 

file test-strings-0926.yaml

 

file test-strings-indexof-unicode.yaml

 

dir v1/test/cases/testdata/v0/subset/

 

file test-subset.yaml

 

dir v1/test/cases/testdata/v0/time/

 

file test-time-0947.yaml

 

file test-time-0948.yaml

 

file test-time-0949.yaml

 

file test-time-0950.yaml

 

file test-time-0951.yaml

 

file test-time-0952.yaml

 

file test-time-0953.yaml

 

file test-time-0954.yaml

 

file test-time-0955.yaml

 

file test-time-0956.yaml

 

file test-time-0957.yaml

 

file test-time-0958.yaml

 

file test-time-0959.yaml

 

file test-time-0960.yaml

 

file test-time-0961.yaml

 

file test-time-0962.yaml

 

file test-time-0963.yaml

 

file test-time-0964.yaml

 

file test-time-0965.yaml

 

file test-time-0966.yaml

 

file test-time-0967.yaml

 

file test-time-0968.yaml

 

file test-time-0969.yaml

 

file test-time-0970.yaml

 

file test-time-0971.yaml

 

dir v1/test/cases/testdata/v0/toarray/

 

file test-toarray-0071.yaml

 

file test-toarray-0072.yaml

 

file test-toarray-0073.yaml

 

dir v1/test/cases/testdata/v0/topdowndynamicdispatch/

 

file test-topdowndynamicdispatch-1068.yaml

 

dir v1/test/cases/testdata/v0/toset/

 

file test-toset-0074.yaml

 

file test-toset-0075.yaml

 

file test-toset-0076.yaml

 

dir v1/test/cases/testdata/v0/trim/

 

file test-trim-0362.yaml

 

file test-trim-0363.yaml

 

dir v1/test/cases/testdata/v0/trimleft/

 

file test-trimleft-0364.yaml

 

file test-trimleft-0365.yaml

 

dir v1/test/cases/testdata/v0/trimprefix/

 

file test-trimprefix-0366.yaml

 

file test-trimprefix-0367.yaml

 

dir v1/test/cases/testdata/v0/trimright/

 

file test-trimright-0368.yaml

 

file test-trimright-0369.yaml

 

dir v1/test/cases/testdata/v0/trimspace/

 

file test-trimspace-0372.yaml

 

file test-trimspace-0373.yaml

 

dir v1/test/cases/testdata/v0/trimsuffix/

 

file test-trimsuffix-0370.yaml

 

file test-trimsuffix-0371.yaml

 

dir v1/test/cases/testdata/v0/type/

 

file test-regressions.yaml

 

dir v1/test/cases/testdata/v0/typebuiltin/

 

file test-typebuiltin-0828.yaml

 

file test-typebuiltin-0829.yaml

 

file test-typebuiltin-0830.yaml

 

file test-typebuiltin-0831.yaml

 

file test-typebuiltin-0832.yaml

 

file test-typebuiltin-0833.yaml

 

file test-typebuiltin-0834.yaml

 

file test-typebuiltin-0835.yaml

 

file test-typebuiltin-0836.yaml

 

file test-typebuiltin-0837.yaml

 

file test-typebuiltin-0838.yaml

 

file test-typebuiltin-0839.yaml

 

file test-typebuiltin-0840.yaml

 

file test-typebuiltin-0841.yaml

 

file test-typebuiltin-0842.yaml

 

file test-typebuiltin-0843.yaml

 

file test-typebuiltin-0844.yaml

 

file test-typebuiltin-0845.yaml

 

file test-typebuiltin-0846.yaml

 

file test-typebuiltin-0847.yaml

 

dir v1/test/cases/testdata/v0/typenamebuiltin/

 

file test-typenamebuiltin-0848.yaml

 

file test-typenamebuiltin-0849.yaml

 

file test-typenamebuiltin-0850.yaml

 

file test-typenamebuiltin-0851.yaml

 

file test-typenamebuiltin-0852.yaml

 

file test-typenamebuiltin-0853.yaml

 

file test-typenamebuiltin-0854.yaml

 

dir v1/test/cases/testdata/v0/undos/

 

file test-undos-0599.yaml

 

file test-undos-0600.yaml

 

file test-undos-0601.yaml

 

file test-undos-0602.yaml

 

file test-undos-0603.yaml

 

file test-undos-0604.yaml

 

file test-undos-0605.yaml

 

file test-undos-0606.yaml

 

file test-undos-0607.yaml

 

dir v1/test/cases/testdata/v0/union/

 

file test-union-0357.yaml

 

file test-union-0358.yaml

 

file test-union-0359.yaml

 

file test-union-0360.yaml

 

file test-union-0361.yaml

 

dir v1/test/cases/testdata/v0/units/

 

file test-issue-4856.yaml

 

file test-parse-bytes-comparisons.yaml

 

file test-parse-bytes-errors.yaml

 

file test-parse-bytes.yaml

 

file test-parse-units-comparisons.yaml

 

file test-parse-units-errors.yaml

 

file test-parse-units.yaml

 

file test-units-precision.yaml

 

dir v1/test/cases/testdata/v0/urlbuiltins/

 

file test-urlbuiltins-0939.yaml

 

file test-urlbuiltins-0940.yaml

 

file test-urlbuiltins-0941.yaml

 

file test-urlbuiltins-0942.yaml

 

file test-urlbuiltins-0943.yaml

 

file test-urlbuiltins-0944.yaml

 

file test-urlbuiltins-0945.yaml

 

file test-urlbuiltins-0946.yaml

 

file test-urlbuiltins-1076.yaml

 

dir v1/test/cases/testdata/v0/uuid/

 

file test-uuid-input-formats.yaml

 

file test-uuid-parse-rule.yaml

 

file test-uuid-parse.yaml

 

dir v1/test/cases/testdata/v0/varreferences/

 

file test-varreferences-0726.yaml

 

file test-varreferences-0727.yaml

 

file test-varreferences-0728.yaml

 

file test-varreferences-0729.yaml

 

file test-varreferences-0730.yaml

 

file test-varreferences-0731.yaml

 

file test-varreferences-0732.yaml

 

file test-varreferences-0733.yaml

 

file test-varreferences-0734.yaml

 

file test-varreferences-0735.yaml

 

file test-varreferences-0736.yaml

 

file test-varreferences-0737.yaml

 

file test-varreferences-0738.yaml

 

file test-varreferences-0739.yaml

 

file test-varreferences-0740.yaml

 

file test-varreferences-0741.yaml

 

file test-varreferences-0742.yaml

 

dir v1/test/cases/testdata/v0/virtualdocs/

 

file test-virtualdocs-0620.yaml

 

file test-virtualdocs-0621.yaml

 

file test-virtualdocs-0622.yaml

 

file test-virtualdocs-0623.yaml

 

file test-virtualdocs-0624.yaml

 

file test-virtualdocs-0625.yaml

 

file test-virtualdocs-0626.yaml

 

file test-virtualdocs-0627.yaml

 

file test-virtualdocs-0628.yaml

 

file test-virtualdocs-0629.yaml

 

file test-virtualdocs-0630.yaml

 

file test-virtualdocs-0631.yaml

 

file test-virtualdocs-0632.yaml

 

file test-virtualdocs-0633.yaml

 

file test-virtualdocs-0634.yaml

 

file test-virtualdocs-0635.yaml

 

file test-virtualdocs-0636.yaml

 

file test-virtualdocs-0637.yaml

 

file test-virtualdocs-0638.yaml

 

file test-virtualdocs-0639.yaml

 

file test-virtualdocs-0640.yaml

 

file test-virtualdocs-0641.yaml

 

file test-virtualdocs-0642.yaml

 

file test-virtualdocs-0643.yaml

 

file test-virtualdocs-0644.yaml

 

file test-virtualdocs-0645.yaml

 

file test-virtualdocs-0646.yaml

 

file test-virtualdocs-0647.yaml

 

file test-virtualdocs-0648.yaml

 

file test-virtualdocs-0649.yaml

 

file test-virtualdocs-0650.yaml

 

file test-virtualdocs-0651.yaml

 

file test-virtualdocs-0652.yaml

 

file test-virtualdocs-0653.yaml

 

file test-virtualdocs-0654.yaml

 

file test-virtualdocs-0655.yaml

 

file test-virtualdocs-0656.yaml

 

file test-virtualdocs-0657.yaml

 

file test-virtualdocs-0658.yaml

 

file test-virtualdocs-0659.yaml

 

file test-virtualdocs-0660.yaml

 

file test-virtualdocs-0661.yaml

 

file test-virtualdocs-0662.yaml

 

file test-virtualdocs-0663.yaml

 

file test-virtualdocs-0664.yaml

 

file test-virtualdocs-0665.yaml

 

file test-virtualdocs-0666.yaml

 

file test-virtualdocs-0667.yaml

 

file test-virtualdocs-0668.yaml

 

file test-virtualdocs-0669.yaml

 

file test-virtualdocs-0670.yaml

 

file test-virtualdocs-0671.yaml

 

file test-virtualdocs-0672.yaml

 

file test-virtualdocs-0673.yaml

 

file test-virtualdocs-0674.yaml

 

file test-virtualdocs-0675.yaml

 

file test-virtualdocs-0676.yaml

 

file test-virtualdocs-0677.yaml

 

file test-virtualdocs-0678.yaml

 

file test-virtualdocs-0679.yaml

 

file test-virtualdocs-0680.yaml

 

file test-virtualdocs-0681.yaml

 

file test-virtualdocs-0682.yaml

 

file test-virtualdocs-0683.yaml

 

file test-virtualdocs-0684.yaml

 

file test-virtualdocs-0685.yaml

 

file test-virtualdocs-0686.yaml

 

file test-virtualdocs-0687.yaml

 

file test-virtualdocs-0688.yaml

 

file test-virtualdocs-0689.yaml

 

file test-virtualdocs-0690.yaml

 

file test-virtualdocs-0691.yaml

 

file test-virtualdocs-0692.yaml

 

file test-virtualdocs-0693.yaml

 

file test-virtualdocs-0694.yaml

 

file test-virtualdocs-undefined.yaml

 

dir v1/test/cases/testdata/v0/walkbuiltin/

 

file test-walkbuiltin-0970.yaml

 

file test-walkbuiltin-0971.yaml

 

file test-walkbuiltin-0972.yaml

 

file test-walkbuiltin-0973.yaml

 

file test-walkbuiltin-0974.yaml

 

file test-walkbuiltin-0975.yaml

 

file test-walkbuiltin-wildcard-path.yaml

 

dir v1/test/cases/testdata/v0/withkeyword/

 

file test-with-and-ndbcache-issue.yaml

 

file test-with-builtin-mock.yaml

 

file test-with-function-mock.yaml

 

file test-with-function-mocks-issue-5299.yaml

 

file test-withkeyword-1015.yaml

 

file test-withkeyword-1016.yaml

 

file test-withkeyword-1017.yaml

 

file test-withkeyword-1018.yaml

 

file test-withkeyword-1019.yaml

 

file test-withkeyword-1020.yaml

 

file test-withkeyword-1021.yaml

 

file test-withkeyword-1022.yaml

 

file test-withkeyword-1023.yaml

 

file test-withkeyword-1024.yaml

 

file test-withkeyword-1025.yaml

 

file test-withkeyword-1026.yaml

 

file test-withkeyword-1027.yaml

 

file test-withkeyword-1028.yaml

 

file test-withkeyword-1029.yaml

 

file test-withkeyword-1030.yaml

 

file test-withkeyword-1031.yaml

 

file test-withkeyword-1032.yaml

 

file test-withkeyword-1033.yaml

 

file test-withkeyword-1034.yaml

 

file test-withkeyword-1035.yaml

 

file test-withkeyword-1036.yaml

 

file test-withkeyword-1037.yaml

 

file test-withkeyword-1038.yaml

 

file test-withkeyword-1039.yaml

 

file test-withkeyword-1040.yaml

 

file test-withkeyword-1041.yaml

 

file test-withkeyword-1042.yaml

 

file test-withkeyword-1043.yaml

 

file test-withkeyword-1044.yaml

 

file test-withkeyword-1045.yaml

 

file test-withkeyword-1046.yaml

 

file test-withkeyword-1047.yaml

 

file test-withkeyword-1048.yaml

 

file test-withkeyword-1049.yaml

 

file test-withkeyword-1050.yaml

 

file test-withkeyword-1051.yaml

 

file test-withkeyword-1052.yaml

 

file test-withkeyword-1053.yaml

 

file test-withkeyword-1054.yaml

 

dir v1/test/cases/testdata/v1/aggregates/

 

file test-aggregates-0001.yaml

 

file test-aggregates-0002.yaml

 

file test-aggregates-0003.yaml

 

file test-aggregates-0004.yaml

 

file test-aggregates-0005.yaml

 

file test-aggregates-0006.yaml

 

file test-aggregates-0007.yaml

 

file test-aggregates-0008.yaml

 

file test-aggregates-0009.yaml

 

file test-aggregates-0010.yaml

 

file test-aggregates-0011.yaml

 

file test-aggregates-0012.yaml

 

file test-aggregates-0013.yaml

 

file test-aggregates-0014.yaml

 

file test-aggregates-0015.yaml

 

file test-aggregates-0016.yaml

 

file test-aggregates-0017.yaml

 

file test-aggregates-0018.yaml

 

file test-aggregates-0019.yaml

 

file test-aggregates-0020.yaml

 

file test-aggregates-0021.yaml

 

file test-aggregates-0022.yaml

 

file test-aggregates-0023.yaml

 

file test-aggregates-0024.yaml

 

file test-aggregates-0025.yaml

 

file test-aggregates-0026.yaml

 

file test-aggregates-0027.yaml

 

file test-aggregates-0028.yaml

 

file test-aggregates-bad-utf8-runes.yaml

 

file test-membership.yaml

 

dir v1/test/cases/testdata/v1/arithmetic/

 

file test-arithmetic-0810.yaml

 

file test-arithmetic-0811.yaml

 

file test-arithmetic-0812.yaml

 

file test-arithmetic-0813.yaml

 

file test-arithmetic-0814.yaml

 

file test-arithmetic-0815.yaml

 

file test-arithmetic-0816.yaml

 

file test-arithmetic-0817.yaml

 

file test-arithmetic-0818.yaml

 

file test-arithmetic-0819.yaml

 

file test-arithmetic-0820.yaml

 

file test-arithmetic-0821.yaml

 

file test-arithmetic-0822.yaml

 

file test-arithmetic-0823.yaml

 

file test-arithmetic-0824.yaml

 

file test-arithmetic-0825.yaml

 

file test-arithmetic-minus-type-error.yaml

 

file test-big-int-0001.yaml

 

dir v1/test/cases/testdata/v1/array/

 

file flatten.yaml

 

file test-array-0041.yaml

 

file test-array-0042.yaml

 

file test-array-0043.yaml

 

file test-array-0044.yaml

 

file test-array-0045.yaml

 

file test-array-0046.yaml

 

file test-array-0047.yaml

 

file test-array-0048.yaml

 

file test-array-0049.yaml

 

file test-array-0050.yaml

 

file test-array-0051.yaml

 

file test-array-0052.yaml

 

dir v1/test/cases/testdata/v1/assignments/

 

file test-file-level-assignments.yaml

 

dir v1/test/cases/testdata/v1/base64builtins/

 

file test-base64builtins-0929.yaml

 

file test-base64builtins-0930.yaml

 

file test-base64builtins-0931.yaml

 

file test-base64builtins-0932.yaml

 

file test-base64builtins-0933.yaml

 

file test-base64builtins-0934.yaml

 

file test-base64builtins-0935.yaml

 

dir v1/test/cases/testdata/v1/base64urlbuiltins/

 

file test-base64urlbuiltins-0935.yaml

 

file test-base64urlbuiltins-0937.yaml

 

file test-base64urlbuiltins-0939.yaml

 

dir v1/test/cases/testdata/v1/baseandvirtualdocs/

 

file test-baseandvirtualdocs-0695.yaml

 

file test-baseandvirtualdocs-0696.yaml

 

file test-baseandvirtualdocs-0697.yaml

 

file test-baseandvirtualdocs-0698.yaml

 

file test-baseandvirtualdocs-0699.yaml

 

file test-baseandvirtualdocs-0700.yaml

 

file test-baseandvirtualdocs-0701.yaml

 

file test-baseandvirtualdocs-0702.yaml

 

file test-baseandvirtualdocs-0703.yaml

 

file test-baseandvirtualdocs-0704.yaml

 

file test-baseandvirtualdocs-0705.yaml

 

dir v1/test/cases/testdata/v1/bitsand/

 

file test-bitsand-0055.yaml

 

file test-bitsand-0056.yaml

 

file test-bitsand-0057.yaml

 

dir v1/test/cases/testdata/v1/bitsnegate/

 

file test-bitsnegate-0058.yaml

 

file test-bitsnegate-0059.yaml

 

dir v1/test/cases/testdata/v1/bitsor/

 

file test-bitsor-0052.yaml

 

file test-bitsor-0053.yaml

 

file test-bitsor-0054.yaml

 

dir v1/test/cases/testdata/v1/bitsshiftleft/

 

file test-bitsshiftleft-0063.yaml

 

file test-bitsshiftleft-0064.yaml

 

file test-bitsshiftleft-0065.yaml

 

file test-bitsshiftleft-0066.yaml

 

file test-bitsshiftleft-0067.yaml

 

dir v1/test/cases/testdata/v1/bitsshiftright/

 

file test-bitsshiftright-0068.yaml

 

file test-bitsshiftright-0069.yaml

 

file test-bitsshiftright-0070.yaml

 

dir v1/test/cases/testdata/v1/bitsxor/

 

file test-bitsxor-0060.yaml

 

file test-bitsxor-0061.yaml

 

file test-bitsxor-0062.yaml

 

dir v1/test/cases/testdata/v1/casts/

 

file test-casts-0824.yaml

 

file test-casts-0825.yaml

 

file test-casts-0826.yaml

 

file test-casts-0827.yaml

 

file test-casts-0828.yaml

 

dir v1/test/cases/testdata/v1/comparisonexpr/

 

file test-comparisonexpr-0608.yaml

 

file test-comparisonexpr-0609.yaml

 

file test-comparisonexpr-0610.yaml

 

file test-comparisonexpr-0611.yaml

 

file test-comparisonexpr-0612.yaml

 

file test-comparisonexpr-0613.yaml

 

file test-comparisonexpr-0614.yaml

 

file test-comparisonexpr-0615.yaml

 

file test-comparisonexpr-0616.yaml

 

file test-comparisonexpr-0617.yaml

 

file test-comparisonexpr-0618.yaml

 

file test-comparisonexpr-0619.yaml

 

file test-comparisonexpr-0620.yaml

 

dir v1/test/cases/testdata/v1/completedoc/

 

file test-completedoc-0495.yaml

 

file test-completedoc-0496.yaml

 

file test-completedoc-0497.yaml

 

file test-completedoc-0498.yaml

 

file test-completedoc-0499.yaml

 

file test-completedoc-0500.yaml

 

file test-completedoc-0501.yaml

 

file test-completedoc-0502.yaml

 

file test-completedoc-0503.yaml

 

file test-completedoc-0504.yaml

 

file test-completedoc-0505.yaml

 

file test-completedoc-0506.yaml

 

file test-completedoc-0507.yaml

 

file test-completedoc-0508.yaml

 

file test-completedoc-0509.yaml

 

file test-completedoc-0510.yaml

 

dir v1/test/cases/testdata/v1/compositebasedereference/

 

file test-compositebasedereference-1073.yaml

 

file test-compositebasedereference-1074.yaml

 

file test-compositebasedereference-1075.yaml

 

dir v1/test/cases/testdata/v1/compositereferences/

 

file test-compositereferences-0743.yaml

 

file test-compositereferences-0744.yaml

 

file test-compositereferences-0745.yaml

 

file test-compositereferences-0746.yaml

 

file test-compositereferences-0747.yaml

 

file test-compositereferences-0748.yaml

 

file test-compositereferences-0749.yaml

 

file test-compositereferences-0750.yaml

 

file test-compositereferences-0751.yaml

 

file test-compositereferences-0752.yaml

 

file test-compositereferences-0753.yaml

 

file test-compositereferences-0754.yaml

 

file test-compositereferences-0755.yaml

 

file test-compositereferences-0756.yaml

 

file test-compositereferences-0757.yaml

 

dir v1/test/cases/testdata/v1/comprehensions/

 

file test-comprehensions-0781.yaml

 

file test-comprehensions-0782.yaml

 

file test-comprehensions-0783.yaml

 

file test-comprehensions-0784.yaml

 

file test-comprehensions-0785.yaml

 

file test-comprehensions-0786.yaml

 

file test-comprehensions-0787.yaml

 

file test-comprehensions-0788.yaml

 

file test-comprehensions-0789.yaml

 

file test-comprehensions-0790.yaml

 

file test-comprehensions-0791.yaml

 

file test-comprehensions-0792.yaml

 

file test-comprehensions-0793.yaml

 

file test-comprehensions-0794.yaml

 

file test-comprehensions-0795.yaml

 

file test-comprehensions-0796.yaml

 

file test-comprehensions-0797.yaml

 

file test-comprehensions-0798.yaml

 

file test-comprehensions-0799.yaml

 

file test-comprehensions-0800.yaml

 

file test-comprehensions-0801.yaml

 

file test-comprehensions-0802.yaml

 

file test-comprehensions-0803.yaml

 

file test-comprehensions-and-vars.yaml

 

dir v1/test/cases/testdata/v1/containskeyword/

 

file test-contains-future-keyword.yaml

 

dir v1/test/cases/testdata/v1/cryptohmacequal/

 

file test-cryptohmacequal.yaml

 

dir v1/test/cases/testdata/v1/cryptohmacmd5/

 

file test-cryptohmacmd5.yaml

 

dir v1/test/cases/testdata/v1/cryptohmacsha1/

 

file test-cryptohmacsha1.yaml

 

dir v1/test/cases/testdata/v1/cryptohmacsha256/

 

file test-cryptohmacsha256.yaml

 

dir v1/test/cases/testdata/v1/cryptohmacsha512/

 

file test-cryptohmacsha512.yaml

 

dir v1/test/cases/testdata/v1/cryptomd5/

 

file test-cryptomd5-0130.yaml

 

dir v1/test/cases/testdata/v1/cryptoparsersaprivatekeys/

 

file test-cryptoparsersaprivatekey-1.yaml

 

dir v1/test/cases/testdata/v1/cryptosha1/

 

file test-cryptosha1-0131.yaml

 

dir v1/test/cases/testdata/v1/cryptosha256/

 

file test-cryptosha256-0132.yaml

 

dir v1/test/cases/testdata/v1/cryptox509parseandverifycertificates/

 

file test-cryptox509parseandverifycertificates.yaml

 

dir v1/test/cases/testdata/v1/cryptox509parsecertificaterequest/

 

file test-cryptox509parsecertificaterequest-0125.yaml

 

file test-cryptox509parsecertificaterequest-0126.yaml

 

file test-cryptox509parsecertificaterequest-0127.yaml

 

file test-cryptox509parsecertificaterequest-0128.yaml

 

file test-cryptox509parsecertificaterequest-0129.yaml

 

dir v1/test/cases/testdata/v1/cryptox509parsecertificates/

 

file test-cryptox509parsecertificates-0117.yaml

 

file test-cryptox509parsecertificates-0118.yaml

 

file test-cryptox509parsecertificates-0119.yaml

 

file test-cryptox509parsecertificates-0120.yaml

 

file test-cryptox509parsecertificates-0121.yaml

 

file test-cryptox509parsecertificates-0122.yaml

 

file test-cryptox509parsecertificates-0123.yaml

 

file test-cryptox509parsecertificates-0124.yaml

 

file test-cryptox509parsecertificates-raw-uris.yaml

 

dir v1/test/cases/testdata/v1/cryptox509parsekeypair/

 

file test-cryptox509parsekeypairs-0118.yaml

 

file test-cryptox509parsekeypairs-0119.yaml

 

dir v1/test/cases/testdata/v1/cryptox509parsersaprivatekey/

 

file test-cryptox509parsersaprivatekey-1.yaml

 

dir v1/test/cases/testdata/v1/dataderef/

 

file test-data-derefs.yaml

 

dir v1/test/cases/testdata/v1/defaultkeyword/

 

file test-default-functions.yaml

 

file test-defaultkeyword-0804.yaml

 

file test-defaultkeyword-0805.yaml

 

file test-defaultkeyword-0806.yaml

 

file test-defaultkeyword-0807.yaml

 

file test-defaultkeyword-0808.yaml

 

file test-defaultkeyword-0809.yaml

 

dir v1/test/cases/testdata/v1/disjunction/

 

file test-disjunction-0763.yaml

 

file test-disjunction-0764.yaml

 

file test-disjunction-0765.yaml

 

file test-disjunction-0766.yaml

 

file test-disjunction-0767.yaml

 

file test-disjunction-0768.yaml

 

file test-disjunction-0769.yaml

 

file test-disjunction-0770.yaml

 

file test-disjunction-0771.yaml

 

file test-disjunction-0772.yaml

 

file test-disjunction-0773.yaml

 

file test-disjunction-0774.yaml

 

file test-disjunction-0775.yaml

 

file test-disjunction-0776.yaml

 

dir v1/test/cases/testdata/v1/elsekeyword/

 

file test-elsekeyword-1054.yaml

 

file test-elsekeyword-1055.yaml

 

file test-elsekeyword-1056.yaml

 

file test-elsekeyword-1057.yaml

 

file test-elsekeyword-1058.yaml

 

file test-elsekeyword-1059.yaml

 

file test-elsekeyword-1060.yaml

 

file test-elsekeyword-1061.yaml

 

file test-elsekeyword-1062.yaml

 

file test-elsekeyword-1063.yaml

 

file test-elsekeyword-1064.yaml

 

file test-elsekeyword-1065.yaml

 

file test-elsekeyword-1066.yaml

 

file test-elsekeyword-1067.yaml

 

dir v1/test/cases/testdata/v1/embeddedvirtualdoc/

 

file test-embeddedvirtualdoc-0976.yaml

 

dir v1/test/cases/testdata/v1/eqexpr/

 

file test-eqexpr-0545.yaml

 

file test-eqexpr-0546.yaml

 

file test-eqexpr-0547.yaml

 

file test-eqexpr-0548.yaml

 

file test-eqexpr-0549.yaml

 

file test-eqexpr-0550.yaml

 

file test-eqexpr-0551.yaml

 

file test-eqexpr-0552.yaml

 

file test-eqexpr-0553.yaml

 

file test-eqexpr-0554.yaml

 

file test-eqexpr-0555.yaml

 

file test-eqexpr-0556.yaml

 

file test-eqexpr-0557.yaml

 

file test-eqexpr-0558.yaml

 

file test-eqexpr-0559.yaml

 

file test-eqexpr-0560.yaml

 

file test-eqexpr-0561.yaml

 

file test-eqexpr-0562.yaml

 

file test-eqexpr-0563.yaml

 

file test-eqexpr-0564.yaml

 

file test-eqexpr-0565.yaml

 

file test-eqexpr-0566.yaml

 

file test-eqexpr-0567.yaml

 

file test-eqexpr-0568.yaml

 

file test-eqexpr-0569.yaml

 

file test-eqexpr-0570.yaml

 

file test-eqexpr-0571.yaml

 

file test-eqexpr-0572.yaml

 

file test-eqexpr-0573.yaml

 

file test-eqexpr-0574.yaml

 

file test-eqexpr-0575.yaml

 

file test-eqexpr-0576.yaml

 

file test-eqexpr-0577.yaml

 

file test-eqexpr-0578.yaml

 

file test-eqexpr-0579.yaml

 

file test-eqexpr-0580.yaml

 

file test-eqexpr-0581.yaml

 

file test-eqexpr-0582.yaml

 

file test-eqexpr-0583.yaml

 

file test-eqexpr-0584.yaml

 

file test-eqexpr-0585.yaml

 

file test-eqexpr-0586.yaml

 

file test-eqexpr-0587.yaml

 

file test-eqexpr-0588.yaml

 

file test-eqexpr-0589.yaml

 

file test-eqexpr-0590.yaml

 

file test-eqexpr-0591.yaml

 

file test-eqexpr-0592.yaml

 

file test-eqexpr-0593.yaml

 

file test-eqexpr-0594.yaml

 

file test-eqexpr-0595.yaml

 

file test-eqexpr-0596.yaml

 

file test-eqexpr-0597.yaml

 

file test-eqexpr-0598.yaml

 

file test-eqexpr-0599.yaml

 

dir v1/test/cases/testdata/v1/evaltermexpr/

 

file test-evaltermexpr-0525.yaml

 

file test-evaltermexpr-0526.yaml

 

file test-evaltermexpr-0527.yaml

 

file test-evaltermexpr-0528.yaml

 

file test-evaltermexpr-0529.yaml

 

file test-evaltermexpr-0530.yaml

 

file test-evaltermexpr-0531.yaml

 

file test-evaltermexpr-0532.yaml

 

file test-evaltermexpr-0533.yaml

 

file test-evaltermexpr-0534.yaml

 

file test-evaltermexpr-0535.yaml

 

file test-evaltermexpr-0536.yaml

 

file test-evaltermexpr-0537.yaml

 

file test-evaltermexpr-0538.yaml

 

file test-evaltermexpr-0539.yaml

 

file test-evaltermexpr-0540.yaml

 

file test-evaltermexpr-0541.yaml

 

file test-evaltermexpr-0542.yaml

 

file test-evaltermexpr-0543.yaml

 

file test-evaltermexpr-0544.yaml

 

dir v1/test/cases/testdata/v1/every/

 

file every.yaml

 

file non_iterable_domain.yaml

 

file textbook.yaml

 

dir v1/test/cases/testdata/v1/example/

 

file test-example-1070.yaml

 

file test-example-1071.yaml

 

file test-example-1072.yaml

 

dir v1/test/cases/testdata/v1/fix1863/

 

file test-fix1863-0706.yaml

 

file test-fix1863-0707.yaml

 

file test-fix1863-0708.yaml

 

dir v1/test/cases/testdata/v1/functionerrors/

 

file test-conflicts.yaml

 

file test-functionerrors-1012.yaml

 

file test-functionerrors-1013.yaml

 

file test-functionerrors-1014.yaml

 

file test-functionerrors-undefined-builtin-result.yaml

 

dir v1/test/cases/testdata/v1/functions/

 

file test-functions-0990.yaml

 

file test-functions-0991.yaml

 

file test-functions-0992.yaml

 

file test-functions-0993.yaml

 

file test-functions-0994.yaml

 

file test-functions-0995.yaml

 

file test-functions-0996.yaml

 

file test-functions-0997.yaml

 

file test-functions-0998.yaml

 

file test-functions-0999.yaml

 

file test-functions-1000.yaml

 

file test-functions-1001.yaml

 

file test-functions-1002.yaml

 

file test-functions-1003.yaml

 

file test-functions-1004.yaml

 

file test-functions-1005.yaml

 

file test-functions-1006.yaml

 

file test-functions-1007.yaml

 

file test-functions-1008.yaml

 

file test-functions-1009.yaml

 

file test-functions-1010.yaml

 

file test-functions-1011.yaml

 

file test-functions-default.yaml

 

file test-functions-nested-with-early-exit.yaml

 

file test-functions-unused-arg.yaml

 

dir v1/test/cases/testdata/v1/globmatch/

 

file test-globmatch-0133.yaml

 

file test-globmatch-0134.yaml

 

file test-globmatch-0135.yaml

 

file test-globmatch-0136.yaml

 

file test-globmatch-0137.yaml

 

file test-globmatch-0138.yaml

 

file test-globmatch-0139.yaml

 

file test-globmatch-0140.yaml

 

file test-globmatch-0141.yaml

 

file test-globmatch-0142.yaml

 

file test-globmatch-0143.yaml

 

file test-globmatch-0144.yaml

 

file test-globmatch-0145.yaml

 

file test-globmatch-0146.yaml

 

file test-globmatch-0147.yaml

 

file test-globmatch-0148.yaml

 

file test-globmatch-0149.yaml

 

file test-globmatch-0150.yaml

 

file test-globmatch-0151.yaml

 

file test-globmatch-0152.yaml

 

file test-globmatch-0153.yaml

 

file test-globmatch-0154.yaml

 

file test-globmatch-0155.yaml

 

file test-globmatch-0156.yaml

 

file test-globmatch-0157.yaml

 

file test-globmatch-0158.yaml

 

file test-globmatch-0159.yaml

 

file test-globmatch-issue-5273.yaml

 

file test-globmatch-issue-5283.yaml

 

dir v1/test/cases/testdata/v1/globquotemeta/

 

file test-globquotemeta-0159.yaml

 

dir v1/test/cases/testdata/v1/globsmatch/

 

file test-globsmatch-0865.yaml

 

file test-globsmatch-0866.yaml

 

file test-globsmatch-0867.yaml

 

file test-globsmatch-0868.yaml

 

file test-globsmatch-0869.yaml

 

file test-globsmatch-0870.yaml

 

dir v1/test/cases/testdata/v1/graphql/

 

file test-graphql-basic-ast.yaml

 

file test-graphql-is-valid.yaml

 

file test-graphql-parse-and-verify.yaml

 

file test-graphql-parse-query.yaml

 

file test-graphql-parse-schema.yaml

 

file test-graphql-parse.yaml

 

file test-graphql-schema-is-valid.yaml

 

dir v1/test/cases/testdata/v1/helloworld/

 

file test-helloworld-1.yaml

 

dir v1/test/cases/testdata/v1/hexbuiltins/

 

file test-hexbuiltins-0939.yaml

 

file test-hexbuiltins-0940.yaml

 

file test-hexbuiltins-0941.yaml

 

dir v1/test/cases/testdata/v1/indexing/

 

file array-any.yaml

 

dir v1/test/cases/testdata/v1/indirectreferences/

 

file test-indirectreferences-0758.yaml

 

file test-indirectreferences-0759.yaml

 

file test-indirectreferences-0760.yaml

 

file test-indirectreferences-0761.yaml

 

file test-indirectreferences-0762.yaml

 

dir v1/test/cases/testdata/v1/inputvalues/

 

file test-inputvalues-0977.yaml

 

file test-inputvalues-0978.yaml

 

file test-inputvalues-0979.yaml

 

file test-inputvalues-0980.yaml

 

file test-inputvalues-0981.yaml

 

file test-inputvalues-0982.yaml

 

file test-inputvalues-0983.yaml

 

dir v1/test/cases/testdata/v1/intersection/

 

file test-intersection-0352.yaml

 

file test-intersection-0353.yaml

 

file test-intersection-0354.yaml

 

file test-intersection-0355.yaml

 

file test-intersection-0356.yaml

 

dir v1/test/cases/testdata/v1/invalidkeyerror/

 

file test-invalidkeyerror-0176.yaml

 

file test-invalidkeyerror-0177.yaml

 

dir v1/test/cases/testdata/v1/jsonbuiltins/

 

file test-is-valid.yaml

 

file test-json-marshal-with-options.yaml

 

file test-jsonbuiltins-0924.yaml

 

file test-jsonbuiltins-0925.yaml

 

file test-jsonbuiltins-0926.yaml

 

file test-jsonbuiltins-0927.yaml

 

file test-jsonbuiltins-0928.yaml

 

file test-marshal-large-ints.yaml

 

dir v1/test/cases/testdata/v1/jsonfilter/

 

file test-jsonfilter-0218.yaml

 

file test-jsonfilter-0219.yaml

 

file test-jsonfilter-0220.yaml

 

file test-jsonfilter-0221.yaml

 

file test-jsonfilter-0222.yaml

 

file test-jsonfilter-0223.yaml

 

file test-jsonfilter-0224.yaml

 

file test-jsonfilter-0225.yaml

 

file test-jsonfilter-0226.yaml

 

file test-jsonfilter-0227.yaml

 

file test-jsonfilter-0228.yaml

 

dir v1/test/cases/testdata/v1/jsonfilteridempotent/

 

file test-jsonfilteridempotent-0229.yaml

 

dir v1/test/cases/testdata/v1/jsonpatch/

 

file coverage.yaml

 

file json-patch-tests.yaml

 

file set.yaml

 

dir v1/test/cases/testdata/v1/jsonremove/

 

file test-jsonremove-0230.yaml

 

file test-jsonremove-0231.yaml

 

file test-jsonremove-0232.yaml

 

file test-jsonremove-0233.yaml

 

file test-jsonremove-0234.yaml

 

file test-jsonremove-0235.yaml

 

file test-jsonremove-0236.yaml

 

file test-jsonremove-0237.yaml

 

file test-jsonremove-0238.yaml

 

file test-jsonremove-0239.yaml

 

file test-jsonremove-0240.yaml

 

file test-jsonremove-0241.yaml

 

file test-jsonremove-0242.yaml

 

file test-jsonremove-0243.yaml

 

file test-jsonremove-0244.yaml

 

file test-jsonremove-0245.yaml

 

file test-jsonremove-0246.yaml

 

file test-jsonremove-0247.yaml

 

file test-jsonremove-0248.yaml

 

file test-jsonremove-0249.yaml

 

file test-jsonremove-0250.yaml

 

file test-jsonremove-0251.yaml

 

file test-jsonremove-0252.yaml

 

file test-jsonremove-0253.yaml

 

file test-jsonremove-0254.yaml

 

dir v1/test/cases/testdata/v1/jsonremoveidempotent/

 

file test-jsonremoveidempotent-0255.yaml

 

dir v1/test/cases/testdata/v1/jsonschema/

 

file test-json-match_schema.yaml

 

file test-json-verify_schema.yaml

 

dir v1/test/cases/testdata/v1/jwtbuiltins/

 

file test-jwtbuiltins-0389.yaml

 

file test-jwtbuiltins-0390.yaml

 

file test-jwtbuiltins-0391.yaml

 

file test-jwtbuiltins-0392.yaml

 

file test-jwtbuiltins-0393.yaml

 

file test-jwtbuiltins-0394.yaml

 

file test-jwtbuiltins-0395.yaml

 

file test-jwtbuiltins-0396.yaml

 

file test-jwtbuiltins-0397.yaml

 

file test-jwtbuiltins-0398.yaml

 

file test-jwtbuiltins-0399.yaml

 

file test-jwtbuiltins-0400.yaml

 

dir v1/test/cases/testdata/v1/jwtdecodeverify/

 

file test-jwtdecodeverify-0449.yaml

 

file test-jwtdecodeverify-0450.yaml

 

file test-jwtdecodeverify-0451.yaml

 

file test-jwtdecodeverify-0452.yaml

 

file test-jwtdecodeverify-0453.yaml

 

file test-jwtdecodeverify-0454.yaml

 

file test-jwtdecodeverify-0455.yaml

 

file test-jwtdecodeverify-0456.yaml

 

file test-jwtdecodeverify-0457.yaml

 

file test-jwtdecodeverify-0458.yaml

 

file test-jwtdecodeverify-0459.yaml

 

file test-jwtdecodeverify-0460.yaml

 

file test-jwtdecodeverify-0461.yaml

 

file test-jwtdecodeverify-0462.yaml

 

file test-jwtdecodeverify-0463.yaml

 

file test-jwtdecodeverify-0464.yaml

 

file test-jwtdecodeverify-0465.yaml

 

file test-jwtdecodeverify-0466.yaml

 

file test-jwtdecodeverify-0467.yaml

 

file test-jwtdecodeverify-0468.yaml

 

file test-jwtdecodeverify-0469.yaml

 

file test-jwtdecodeverify-0470.yaml

 

file test-jwtdecodeverify-0471.yaml

 

file test-jwtdecodeverify-0472.yaml

 

file test-jwtdecodeverify-0473.yaml

 

file test-jwtdecodeverify-0474.yaml

 

file test-jwtdecodeverify-0475.yaml

 

file test-jwtdecodeverify-0476.yaml

 

file test-jwtdecodeverify-0477.yaml

 

file test-jwtdecodeverify-0478.yaml

 

file test-jwtdecodeverify-0479.yaml

 

file test-jwtdecodeverify-0480.yaml

 

file test-jwtdecodeverify-0481.yaml

 

file test-jwtdecodeverify-0482.yaml

 

file test-jwtdecodeverify-0483.yaml

 

file test-jwtdecodeverify-0484.yaml

 

file test-jwtdecodeverify-0485.yaml

 

file test-jwtdecodeverify-0486.yaml

 

file test-jwtdecodeverify-0487.yaml

 

file test-jwtdecodeverify-0488.yaml

 

file test-jwtdecodeverify-0489.yaml

 

file test-jwtdecodeverify-0490.yaml

 

file test-jwtdecodeverify-0491.yaml

 

file test-jwtdecodeverify-eddsa.yaml

 

file test-jwtdecodeverify-invalid-exp-type.yaml

 

file test-jwtdecodeverify-invalid-nbf-type.yaml

 

file test-jwtdecodeverify-missing-iss-while-required.yaml

 

dir v1/test/cases/testdata/v1/jwtencodesign/

 

file test-jwtencodesign-0492.yaml

 

file test-jwtencodesign-0493.yaml

 

file test-jwtencodesign-0494.yaml

 

file test-jwtencodesign-eddsa.yaml

 

file test-jwtencodesign-integer-timestamps.yaml

 

file test-jwtencodesign-set-data.yaml

 

dir v1/test/cases/testdata/v1/jwtencodesignheadererrors/

 

file test-jwtencodesignheadererrors-0379.yaml

 

file test-jwtencodesignheadererrors-0380.yaml

 

file test-jwtencodesignheadererrors-0381.yaml

 

file test-jwtencodesignheadererrors-0382.yaml

 

file test-jwtencodesignheadererrors-0383.yaml

 

dir v1/test/cases/testdata/v1/jwtencodesignpayloaderrors/

 

file test-jwtencodesignpayloaderrors-0376.yaml

 

file test-jwtencodesignpayloaderrors-0377.yaml

 

file test-jwtencodesignpayloaderrors-0378.yaml

 

dir v1/test/cases/testdata/v1/jwtencodesignraw/

 

file test-jwtencodesignraw-0384.yaml

 

file test-jwtencodesignraw-0385.yaml

 

file test-jwtencodesignraw-0386.yaml

 

file test-jwtencodesignraw-0387.yaml

 

file test-jwtencodesignraw-0388.yaml

 

file test-jwtencodesignraw-eddsa.yaml

 

dir v1/test/cases/testdata/v1/jwtverifyeddsa/

 

file test-jwtverifyeddsa.yaml

 

dir v1/test/cases/testdata/v1/jwtverifyhs256/

 

file test-jwtverifyhs256-0440.yaml

 

file test-jwtverifyhs256-0441.yaml

 

file test-jwtverifyhs256-0442.yaml

 

dir v1/test/cases/testdata/v1/jwtverifyhs384/

 

file test-jwtverifyhs384-0443.yaml

 

file test-jwtverifyhs384-0444.yaml

 

file test-jwtverifyhs384-0445.yaml

 

dir v1/test/cases/testdata/v1/jwtverifyhs512/

 

file test-jwtverifyhs512-0446.yaml

 

file test-jwtverifyhs512-0447.yaml

 

file test-jwtverifyhs512-0448.yaml

 

dir v1/test/cases/testdata/v1/jwtverifyrsa/

 

file test-jwtverifyrsa-0401.yaml

 

file test-jwtverifyrsa-0402.yaml

 

file test-jwtverifyrsa-0403.yaml

 

file test-jwtverifyrsa-0404.yaml

 

file test-jwtverifyrsa-0405.yaml

 

file test-jwtverifyrsa-0406.yaml

 

file test-jwtverifyrsa-0407.yaml

 

file test-jwtverifyrsa-0408.yaml

 

file test-jwtverifyrsa-0409.yaml

 

file test-jwtverifyrsa-0410.yaml

 

file test-jwtverifyrsa-0411.yaml

 

file test-jwtverifyrsa-0412.yaml

 

file test-jwtverifyrsa-0413.yaml

 

file test-jwtverifyrsa-0414.yaml

 

file test-jwtverifyrsa-0415.yaml

 

file test-jwtverifyrsa-0416.yaml

 

file test-jwtverifyrsa-0417.yaml

 

file test-jwtverifyrsa-0418.yaml

 

file test-jwtverifyrsa-0419.yaml

 

file test-jwtverifyrsa-0420.yaml

 

file test-jwtverifyrsa-0421.yaml

 

file test-jwtverifyrsa-0422.yaml

 

file test-jwtverifyrsa-0423.yaml

 

file test-jwtverifyrsa-0424.yaml

 

file test-jwtverifyrsa-0425.yaml

 

file test-jwtverifyrsa-0426.yaml

 

file test-jwtverifyrsa-0427.yaml

 

file test-jwtverifyrsa-0428.yaml

 

file test-jwtverifyrsa-0429.yaml

 

file test-jwtverifyrsa-0430.yaml

 

file test-jwtverifyrsa-0431.yaml

 

file test-jwtverifyrsa-0432.yaml

 

file test-jwtverifyrsa-0433.yaml

 

file test-jwtverifyrsa-0434.yaml

 

file test-jwtverifyrsa-0435.yaml

 

file test-jwtverifyrsa-0436.yaml

 

file test-jwtverifyrsa-0437.yaml

 

file test-jwtverifyrsa-0438.yaml

 

file test-jwtverifyrsa-0439.yaml

 

dir v1/test/cases/testdata/v1/keywordrefs/

 

file test-keyword-as.yaml

 

file test-keyword-contains.yaml

 

file test-keyword-default.yaml

 

file test-keyword-else.yaml

 

file test-keyword-every.yaml

 

file test-keyword-false.yaml

 

file test-keyword-if.yaml

 

file test-keyword-import.yaml

 

file test-keyword-in.yaml

 

file test-keyword-not.yaml

 

file test-keyword-null.yaml

 

file test-keyword-package.yaml

 

file test-keyword-some.yaml

 

file test-keyword-true.yaml

 

file test-keyword-with.yaml

 

dir v1/test/cases/testdata/v1/logic_operators/

 

file and_basic.yaml

 

file and_explicit_body.yaml

 

file and_short_circuit.yaml

 

file builtin_calls.yaml

 

file chained.yaml

 

file comprehension.yaml

 

file default_and_else.yaml

 

file every.yaml

 

file iteration.yaml

 

file local_collision.yaml

 

file negation.yaml

 

file nesting.yaml

 

file or_basic.yaml

 

file or_explicit_body.yaml

 

file or_short_circuit.yaml

 

file or_single_result.yaml

 

file precedence.yaml

 

file rule_head.yaml

 

file with_modifier.yaml

 

dir v1/test/cases/testdata/v1/negation/

 

file test-negation-0777.yaml

 

file test-negation-0778.yaml

 

file test-negation-0779.yaml

 

file test-negation-0780.yaml

 

file test-negation-data-ref-with-var.yaml

 

file test-not-body.yaml

 

dir v1/test/cases/testdata/v1/nestedreferences/

 

file test-nestedreferences-0709.yaml

 

file test-nestedreferences-0710.yaml

 

file test-nestedreferences-0711.yaml

 

file test-nestedreferences-0712.yaml

 

file test-nestedreferences-0713.yaml

 

file test-nestedreferences-0714.yaml

 

file test-nestedreferences-0715.yaml

 

file test-nestedreferences-0716.yaml

 

file test-nestedreferences-0717.yaml

 

file test-nestedreferences-0718.yaml

 

file test-nestedreferences-0719.yaml

 

file test-nestedreferences-0720.yaml

 

file test-nestedreferences-0721.yaml

 

file test-nestedreferences-0722.yaml

 

file test-nestedreferences-0723.yaml

 

file test-nestedreferences-0724.yaml

 

file test-nestedreferences-0725.yaml

 

dir v1/test/cases/testdata/v1/netcidrcontains/

 

file test-netcidrcontains-0092.yaml

 

file test-netcidrcontains-0093.yaml

 

file test-netcidrcontains-0094.yaml

 

file test-netcidrcontains-0095.yaml

 

file test-netcidrcontains-0096.yaml

 

file test-netcidrcontains-0097.yaml

 

file test-netcidrcontains-0098.yaml

 

file test-netcidrcontains-0099.yaml

 

file test-netcidrcontains-0100.yaml

 

file test-netcidrcontains-0101.yaml

 

file test-netcidrcontains-0102.yaml

 

file test-netcidrcontains-0103.yaml

 

dir v1/test/cases/testdata/v1/netcidrcontainsmatches/

 

file test-netcidrcontainsmatches-0104.yaml

 

file test-netcidrcontainsmatches-0105.yaml

 

file test-netcidrcontainsmatches-0106.yaml

 

file test-netcidrcontainsmatches-0107.yaml

 

file test-netcidrcontainsmatches-0108.yaml

 

file test-netcidrcontainsmatches-0109.yaml

 

file test-netcidrcontainsmatches-0110.yaml

 

file test-netcidrcontainsmatches-0111.yaml

 

file test-netcidrcontainsmatches-0112.yaml

 

dir v1/test/cases/testdata/v1/netcidrexpand/

 

file test-netcidrexpand-0113.yaml

 

file test-netcidrexpand-0114.yaml

 

file test-netcidrexpand-0115.yaml

 

file test-netcidrexpand-0116.yaml

 

dir v1/test/cases/testdata/v1/netcidrintersects/

 

file test-netcidrintersects-0086.yaml

 

file test-netcidrintersects-0087.yaml

 

file test-netcidrintersects-0088.yaml

 

file test-netcidrintersects-0089.yaml

 

file test-netcidrintersects-0090.yaml

 

file test-netcidrintersects-0091.yaml

 

dir v1/test/cases/testdata/v1/netcidrisvalid/

 

file test_netcidrisvalid-0001.yaml

 

dir v1/test/cases/testdata/v1/netcidrmerge/

 

file test-ipv6-with-and-without-prefix.yaml

 

file test-netcidrmerge0117.yaml

 

dir v1/test/cases/testdata/v1/netlookupipaddr/

 

file test-netlookupipaddr.yaml

 

dir v1/test/cases/testdata/v1/numbersrange/

 

file test-numbersrange-0256.yaml

 

file test-numbersrange-0257.yaml

 

file test-numbersrange-0258.yaml

 

file test-numbersrange-0259.yaml

 

file test-numbersrange-0260.yaml

 

file test-numbersrange-0261.yaml

 

file test-numbersrange-issue-7269.yaml

 

dir v1/test/cases/testdata/v1/numbersrangestep/

 

file test-numbersrangestep.yaml

 

dir v1/test/cases/testdata/v1/objectfilter/

 

file test-objectfilter-0300.yaml

 

file test-objectfilter-0301.yaml

 

file test-objectfilter-0302.yaml

 

file test-objectfilter-0303.yaml

 

file test-objectfilter-0304.yaml

 

file test-objectfilter-0305.yaml

 

file test-objectfilter-0306.yaml

 

file test-objectfilter-0307.yaml

 

file test-objectfilter-0308.yaml

 

file test-objectfilter-0309.yaml

 

file test-objectfilter-0310.yaml

 

file test-objectfilter-0311.yaml

 

file test-objectfilter-0312.yaml

 

file test-objectfilter-0313.yaml

 

file test-objectfilter-0314.yaml

 

file test-objectfilter-0315.yaml

 

file test-objectfilter-0316.yaml

 

file test-objectfilter-0317.yaml

 

dir v1/test/cases/testdata/v1/objectfilteridempotent/

 

file test-objectfilteridempotent-0319.yaml

 

dir v1/test/cases/testdata/v1/objectfilternonstringkey/

 

file test-objectfilternonstringkey-0318.yaml

 

dir v1/test/cases/testdata/v1/objectget/

 

file test-objectget-0262.yaml

 

file test-objectget-0263.yaml

 

file test-objectget-0264.yaml

 

file test-objectget-0265.yaml

 

file test-objectget-0266.yaml

 

file test-objectget-0267.yaml

 

file test-objectget-path.yaml

 

dir v1/test/cases/testdata/v1/objectkeys/

 

file test-objectkeys.yaml

 

dir v1/test/cases/testdata/v1/objectremove/

 

file test-objectremove-0279.yaml

 

file test-objectremove-0280.yaml

 

file test-objectremove-0281.yaml

 

file test-objectremove-0282.yaml

 

file test-objectremove-0283.yaml

 

file test-objectremove-0284.yaml

 

file test-objectremove-0285.yaml

 

file test-objectremove-0286.yaml

 

file test-objectremove-0287.yaml

 

file test-objectremove-0288.yaml

 

file test-objectremove-0289.yaml

 

file test-objectremove-0290.yaml

 

file test-objectremove-0291.yaml

 

file test-objectremove-0292.yaml

 

file test-objectremove-0293.yaml

 

file test-objectremove-0294.yaml

 

file test-objectremove-0295.yaml

 

file test-objectremove-0296.yaml

 

file test-objectremove-0297.yaml

 

dir v1/test/cases/testdata/v1/objectremoveidempotent/

 

file test-objectremoveidempotent-0298.yaml

 

dir v1/test/cases/testdata/v1/objectremovenonstringkey/

 

file test-objectremovenonstringkey-0299.yaml

 

dir v1/test/cases/testdata/v1/objectunion/

 

file test-objectunion-0268.yaml

 

file test-objectunion-0269.yaml

 

file test-objectunion-0270.yaml

 

file test-objectunion-0271.yaml

 

file test-objectunion-0272.yaml

 

file test-objectunion-0273.yaml

 

file test-objectunion-0274.yaml

 

file test-objectunion-0275.yaml

 

file test-objectunion-0276.yaml

 

file test-objectunion-0277.yaml

 

file test-objectunion-0278.yaml

 

dir v1/test/cases/testdata/v1/objectunionn/

 

file test-objectunionn-0001.yaml

 

dir v1/test/cases/testdata/v1/partialdocconstants/

 

file test-partialdocconstants-0984.yaml

 

file test-partialdocconstants-0985.yaml

 

file test-partialdocconstants-0986.yaml

 

file test-partialdocconstants-0987.yaml

 

file test-partialdocconstants-0988.yaml

 

file test-partialdocconstants-0989.yaml

 

dir v1/test/cases/testdata/v1/partialiter/

 

file test-partialiter-001.yaml

 

dir v1/test/cases/testdata/v1/partialobjectdoc/

 

file test-partialobjectdoc-0519.yaml

 

file test-partialobjectdoc-0520.yaml

 

file test-partialobjectdoc-0521.yaml

 

file test-partialobjectdoc-0522.yaml

 

file test-partialobjectdoc-0523.yaml

 

file test-partialobjectdoc-0524.yaml

 

file test-partialobjectdoc-ref.yaml

 

file test-wasm-cases.yaml

 

dir v1/test/cases/testdata/v1/partialsetdoc/

 

file test-issue-3369.yaml

 

file test-issue-3376.yaml

 

file test-issue-3819.yaml

 

file test-partialsetdoc-0511.yaml

 

file test-partialsetdoc-0512.yaml

 

file test-partialsetdoc-0513.yaml

 

file test-partialsetdoc-0514.yaml

 

file test-partialsetdoc-0515.yaml

 

file test-partialsetdoc-0516.yaml

 

file test-partialsetdoc-0517.yaml

 

file test-partialsetdoc-0518.yaml

 

dir v1/test/cases/testdata/v1/planner-ir/

 

file test-array-ir-unify.yaml

 

file test-call-dynamic.yaml

 

dir v1/test/cases/testdata/v1/providers-aws/

 

file aws-sign_req-errors.yaml

 

file aws-sign_req.yaml

 

dir v1/test/cases/testdata/v1/rand/

 

file test-rand.intn.yaml

 

dir v1/test/cases/testdata/v1/reachable/

 

file test-reachable-0322.yaml

 

file test-reachable-0323.yaml

 

file test-reachable-0324.yaml

 

file test-reachable-0325.yaml

 

file test-reachable-0326.yaml

 

file test-reachable-0327.yaml

 

file test-reachable-0328.yaml

 

file test-reachable-paths-0422.yaml

 

file test-reachable-paths-1022.yaml

 

dir v1/test/cases/testdata/v1/refheads/

 

file test-generic-refs.yaml

 

file test-refs-as-rule-heads.yaml

 

file test-regressions.yaml

 

dir v1/test/cases/testdata/v1/regexfind/

 

file test-regexfind-0334.yaml

 

file test-regexfind-0335.yaml

 

file test-regexfind-0336.yaml

 

dir v1/test/cases/testdata/v1/regexfindallstringsubmatch/

 

file test-regexfindallstringsubmatch-0337.yaml

 

file test-regexfindallstringsubmatch-0338.yaml

 

file test-regexfindallstringsubmatch-0339.yaml

 

file test-regexfindallstringsubmatch-0340.yaml

 

file test-regexfindallstringsubmatch-0341.yaml

 

file test-regexfindallstringsubmatch-0342.yaml

 

file test-regexfindallstringsubmatch-0343.yaml

 

file test-regexfindallstringsubmatch-large-input.yaml

 

dir v1/test/cases/testdata/v1/regexisvalid/

 

file test-regexisvalid-0329.yaml

 

file test-regexisvalid-0330.yaml

 

file test-regexisvalid-0331.yaml

 

dir v1/test/cases/testdata/v1/regexmatch/

 

file test-regexmatch-0861.yaml

 

dir v1/test/cases/testdata/v1/regexmatchtemplate/

 

file test-regexmatchtemplate-0332.yaml

 

file test-regexmatchtemplate-0333.yaml

 

dir v1/test/cases/testdata/v1/regexreplace/

 

file test-regexreplace-0001.yaml

 

dir v1/test/cases/testdata/v1/regexsplit/

 

file test-regexsplit-0862.yaml

 

file test-regexsplit-0863.yaml

 

file test-regexsplit-0864.yaml

 

dir v1/test/cases/testdata/v1/regometadatachain/

 

file test-regometadatachain-1.yaml

 

dir v1/test/cases/testdata/v1/regometadatarule/

 

file test-regometadatarule-1.yaml

 

dir v1/test/cases/testdata/v1/regoparsemodule/

 

file test-regoparsemodule-0320.yaml

 

file test-regoparsemodule-0321.yaml

 

dir v1/test/cases/testdata/v1/rendertemplate/

 

file rendertemplate.yaml

 

dir v1/test/cases/testdata/v1/replacen/

 

file test-replacen-0374.yaml

 

file test-replacen-0375.yaml

 

file test-replacen-bad-operands.yaml

 

dir v1/test/cases/testdata/v1/semvercompare/

 

file test-semvercompare-0344.yaml

 

file test-semvercompare-0345.yaml

 

file test-semvercompare-0346.yaml

 

file test-semvercompare-0347.yaml

 

file test-semvercompare-0348.yaml

 

dir v1/test/cases/testdata/v1/semverisvalid/

 

file test-semverisvalid-0349.yaml

 

file test-semverisvalid-0350.yaml

 

file test-semverisvalid-0351.yaml

 

dir v1/test/cases/testdata/v1/sets/

 

file test-sets-0871.yaml

 

file test-sets-0872.yaml

 

file test-sets-0873.yaml

 

file test-sets-0874.yaml

 

file test-sets-0875.yaml

 

file test-sets-0876.yaml

 

dir v1/test/cases/testdata/v1/sprintf/

 

file test-sprintf.yaml

 

dir v1/test/cases/testdata/v1/stringinterpolation/

 

file test-string_interpolation.yaml

 

file test-string_interpolation_multi-line.yaml

 

file test-string_interpolation_queries.yaml

 

dir v1/test/cases/testdata/v1/strings/

 

file test-anyprefixmatch.yaml

 

file test-anysuffixmatch.yaml

 

file test-strings-0877.yaml

 

file test-strings-0878.yaml

 

file test-strings-0879.yaml

 

file test-strings-0880.yaml

 

file test-strings-0881.yaml

 

file test-strings-0882.yaml

 

file test-strings-0883.yaml

 

file test-strings-0884.yaml

 

file test-strings-0885.yaml

 

file test-strings-0886.yaml

 

file test-strings-0887.yaml

 

file test-strings-0888.yaml

 

file test-strings-0889.yaml

 

file test-strings-0890.yaml

 

file test-strings-0891.yaml

 

file test-strings-0892.yaml

 

file test-strings-0893.yaml

 

file test-strings-0894.yaml

 

file test-strings-0895.yaml

 

file test-strings-0896.yaml

 

file test-strings-0897.yaml

 

file test-strings-0898.yaml

 

file test-strings-0899.yaml

 

file test-strings-0900.yaml

 

file test-strings-0901.yaml

 

file test-strings-0902.yaml

 

file test-strings-0903.yaml

 

file test-strings-0904.yaml

 

file test-strings-0905.yaml

 

file test-strings-0906.yaml

 

file test-strings-0907.yaml

 

file test-strings-0908.yaml

 

file test-strings-0909.yaml

 

file test-strings-0910.yaml

 

file test-strings-0911.yaml

 

file test-strings-0912.yaml

 

file test-strings-0913.yaml

 

file test-strings-0914.yaml

 

file test-strings-0915.yaml

 

file test-strings-0916.yaml

 

file test-strings-0917.yaml

 

file test-strings-0918.yaml

 

file test-strings-0919.yaml

 

file test-strings-0920.yaml

 

file test-strings-0921.yaml

 

file test-strings-0922.yaml

 

file test-strings-0923.yaml

 

file test-strings-0924.yaml

 

file test-strings-0925.yaml

 

file test-strings-0926.yaml

 

file test-strings-format-int-bignum.yaml

 

file test-strings-indexof-unicode.yaml

 

dir v1/test/cases/testdata/v1/subset/

 

file test-subset.yaml

 

dir v1/test/cases/testdata/v1/time/

 

file test-time-0947.yaml

 

file test-time-0948.yaml

 

file test-time-0949.yaml

 

file test-time-0950.yaml

 

file test-time-0951.yaml

 

file test-time-0952.yaml

 

file test-time-0953.yaml

 

file test-time-0954.yaml

 

file test-time-0955.yaml

 

file test-time-0956.yaml

 

file test-time-0957.yaml

 

file test-time-0958.yaml

 

file test-time-0959.yaml

 

file test-time-0960.yaml

 

file test-time-0961.yaml

 

file test-time-0962.yaml

 

file test-time-0963.yaml

 

file test-time-0964.yaml

 

file test-time-0965.yaml

 

file test-time-0966.yaml

 

file test-time-0967.yaml

 

file test-time-0968.yaml

 

file test-time-0969.yaml

 

file test-time-0970.yaml

 

file test-time-0971.yaml

 

file test-time-0972.yaml

 

dir v1/test/cases/testdata/v1/topdowndynamicdispatch/

 

file test-topdowndynamicdispatch-1068.yaml

 

dir v1/test/cases/testdata/v1/trim/

 

file test-trim-0362.yaml

 

file test-trim-0363.yaml

 

dir v1/test/cases/testdata/v1/trimleft/

 

file test-trimleft-0364.yaml

 

file test-trimleft-0365.yaml

 

dir v1/test/cases/testdata/v1/trimprefix/

 

file test-trimprefix-0366.yaml

 

file test-trimprefix-0367.yaml

 

dir v1/test/cases/testdata/v1/trimright/

 

file test-trimright-0368.yaml

 

file test-trimright-0369.yaml

 

dir v1/test/cases/testdata/v1/trimspace/

 

file test-trimspace-0372.yaml

 

file test-trimspace-0373.yaml

 

dir v1/test/cases/testdata/v1/trimsuffix/

 

file test-trimsuffix-0370.yaml

 

file test-trimsuffix-0371.yaml

 

dir v1/test/cases/testdata/v1/type/

 

file test-regressions.yaml

 

dir v1/test/cases/testdata/v1/typebuiltin/

 

file test-typebuiltin-0828.yaml

 

file test-typebuiltin-0829.yaml

 

file test-typebuiltin-0830.yaml

 

file test-typebuiltin-0831.yaml

 

file test-typebuiltin-0832.yaml

 

file test-typebuiltin-0833.yaml

 

file test-typebuiltin-0834.yaml

 

file test-typebuiltin-0835.yaml

 

file test-typebuiltin-0836.yaml

 

file test-typebuiltin-0837.yaml

 

file test-typebuiltin-0838.yaml

 

file test-typebuiltin-0839.yaml

 

file test-typebuiltin-0840.yaml

 

file test-typebuiltin-0841.yaml

 

file test-typebuiltin-0842.yaml

 

file test-typebuiltin-0843.yaml

 

file test-typebuiltin-0844.yaml

 

file test-typebuiltin-0845.yaml

 

file test-typebuiltin-0846.yaml

 

file test-typebuiltin-0847.yaml

 

dir v1/test/cases/testdata/v1/typenamebuiltin/

 

file test-typenamebuiltin-0848.yaml

 

file test-typenamebuiltin-0849.yaml

 

file test-typenamebuiltin-0850.yaml

 

file test-typenamebuiltin-0851.yaml

 

file test-typenamebuiltin-0852.yaml

 

file test-typenamebuiltin-0853.yaml

 

file test-typenamebuiltin-0854.yaml

 

dir v1/test/cases/testdata/v1/undos/

 

file test-undos-0599.yaml

 

file test-undos-0600.yaml

 

file test-undos-0601.yaml

 

file test-undos-0602.yaml

 

file test-undos-0603.yaml

 

file test-undos-0604.yaml

 

file test-undos-0605.yaml

 

file test-undos-0606.yaml

 

file test-undos-0607.yaml

 

dir v1/test/cases/testdata/v1/union/

 

file test-union-0357.yaml

 

file test-union-0358.yaml

 

file test-union-0359.yaml

 

file test-union-0360.yaml

 

file test-union-0361.yaml

 

dir v1/test/cases/testdata/v1/units/

 

file test-issue-4856.yaml

 

file test-parse-bytes-comparisons.yaml

 

file test-parse-bytes-errors.yaml

 

file test-parse-bytes.yaml

 

file test-parse-units-comparisons.yaml

 

file test-parse-units-errors.yaml

 

file test-parse-units.yaml

 

file test-units-precision.yaml

 

dir v1/test/cases/testdata/v1/uribuiltins/

 

file test-uribuiltins-0001.yaml

 

file test-uribuiltins-0002.yaml

 

dir v1/test/cases/testdata/v1/urlbuiltins/

 

file test-urlbuiltins-0939.yaml

 

file test-urlbuiltins-0940.yaml

 

file test-urlbuiltins-0941.yaml

 

file test-urlbuiltins-0942.yaml

 

file test-urlbuiltins-0943.yaml

 

file test-urlbuiltins-0944.yaml

 

file test-urlbuiltins-0945.yaml

 

file test-urlbuiltins-0946.yaml

 

file test-urlbuiltins-1076.yaml

 

dir v1/test/cases/testdata/v1/uuid/

 

file test-uuid-input-formats.yaml

 

file test-uuid-parse-rule.yaml

 

file test-uuid-parse.yaml

 

file test-uuid-rfc4122.yaml

 

dir v1/test/cases/testdata/v1/varreferences/

 

file test-varreferences-0726.yaml

 

file test-varreferences-0727.yaml

 

file test-varreferences-0728.yaml

 

file test-varreferences-0729.yaml

 

file test-varreferences-0730.yaml

 

file test-varreferences-0731.yaml

 

file test-varreferences-0732.yaml

 

file test-varreferences-0733.yaml

 

file test-varreferences-0734.yaml

 

file test-varreferences-0735.yaml

 

file test-varreferences-0736.yaml

 

file test-varreferences-0737.yaml

 

file test-varreferences-0738.yaml

 

file test-varreferences-0739.yaml

 

file test-varreferences-0740.yaml

 

file test-varreferences-0741.yaml

 

file test-varreferences-0742.yaml

 

dir v1/test/cases/testdata/v1/virtualdocs/

 

file test-virtualdocs-0620.yaml

 

file test-virtualdocs-0621.yaml

 

file test-virtualdocs-0622.yaml

 

file test-virtualdocs-0623.yaml

 

file test-virtualdocs-0624.yaml

 

file test-virtualdocs-0625.yaml

 

file test-virtualdocs-0626.yaml

 

file test-virtualdocs-0627.yaml

 

file test-virtualdocs-0628.yaml

 

file test-virtualdocs-0629.yaml

 

file test-virtualdocs-0630.yaml

 

file test-virtualdocs-0631.yaml

 

file test-virtualdocs-0632.yaml

 

file test-virtualdocs-0633.yaml

 

file test-virtualdocs-0634.yaml

 

file test-virtualdocs-0635.yaml

 

file test-virtualdocs-0636.yaml

 

file test-virtualdocs-0637.yaml

 

file test-virtualdocs-0638.yaml

 

file test-virtualdocs-0639.yaml

 

file test-virtualdocs-0640.yaml

 

file test-virtualdocs-0641.yaml

 

file test-virtualdocs-0642.yaml

 

file test-virtualdocs-0643.yaml

 

file test-virtualdocs-0644.yaml

 

file test-virtualdocs-0645.yaml

 

file test-virtualdocs-0646.yaml

 

file test-virtualdocs-0647.yaml

 

file test-virtualdocs-0648.yaml

 

file test-virtualdocs-0649.yaml

 

file test-virtualdocs-0650.yaml

 

file test-virtualdocs-0651.yaml

 

file test-virtualdocs-0652.yaml

 

file test-virtualdocs-0653.yaml

 

file test-virtualdocs-0654.yaml

 

file test-virtualdocs-0655.yaml

 

file test-virtualdocs-0656.yaml

 

file test-virtualdocs-0657.yaml

 

file test-virtualdocs-0658.yaml

 

file test-virtualdocs-0659.yaml

 

file test-virtualdocs-0660.yaml

 

file test-virtualdocs-0661.yaml

 

file test-virtualdocs-0662.yaml

 

file test-virtualdocs-0663.yaml

 

file test-virtualdocs-0664.yaml

 

file test-virtualdocs-0665.yaml

 

file test-virtualdocs-0666.yaml

 

file test-virtualdocs-0667.yaml

 

file test-virtualdocs-0668.yaml

 

file test-virtualdocs-0669.yaml

 

file test-virtualdocs-0670.yaml

 

file test-virtualdocs-0671.yaml

 

file test-virtualdocs-0672.yaml

 

file test-virtualdocs-0673.yaml

 

file test-virtualdocs-0674.yaml

 

file test-virtualdocs-0675.yaml

 

file test-virtualdocs-0676.yaml

 

file test-virtualdocs-0677.yaml

 

file test-virtualdocs-0678.yaml

 

file test-virtualdocs-0679.yaml

 

file test-virtualdocs-0680.yaml

 

file test-virtualdocs-0681.yaml

 

file test-virtualdocs-0682.yaml

 

file test-virtualdocs-0683.yaml

 

file test-virtualdocs-0684.yaml

 

file test-virtualdocs-0685.yaml

 

file test-virtualdocs-0686.yaml

 

file test-virtualdocs-0687.yaml

 

file test-virtualdocs-0688.yaml

 

file test-virtualdocs-0689.yaml

 

file test-virtualdocs-0690.yaml

 

file test-virtualdocs-0691.yaml

 

file test-virtualdocs-0692.yaml

 

file test-virtualdocs-0693.yaml

 

file test-virtualdocs-0694.yaml

 

file test-virtualdocs-undefined.yaml

 

dir v1/test/cases/testdata/v1/walkbuiltin/

 

file test-walkbuiltin-0970.yaml

 

file test-walkbuiltin-0971.yaml

 

file test-walkbuiltin-0972.yaml

 

file test-walkbuiltin-0973.yaml

 

file test-walkbuiltin-0974.yaml

 

file test-walkbuiltin-0975.yaml

 

file test-walkbuiltin-issue-7656.yaml

 

file test-walkbuiltin-wildcard-path.yaml

 

dir v1/test/cases/testdata/v1/withkeyword/

 

file test-with-and-ndbcache-issue.yaml

 

file test-with-builtin-mock.yaml

 

file test-with-function-mock.yaml

 

file test-with-function-mocks-issue-5299.yaml

 

file test-withkeyword-1015.yaml

 

file test-withkeyword-1016.yaml

 

file test-withkeyword-1017.yaml

 

file test-withkeyword-1018.yaml

 

file test-withkeyword-1019.yaml

 

file test-withkeyword-1020.yaml

 

file test-withkeyword-1021.yaml

 

file test-withkeyword-1022.yaml

 

file test-withkeyword-1023.yaml

 

file test-withkeyword-1024.yaml

 

file test-withkeyword-1025.yaml

 

file test-withkeyword-1026.yaml

 

file test-withkeyword-1027.yaml

 

file test-withkeyword-1028.yaml

 

file test-withkeyword-1029.yaml

 

file test-withkeyword-1030.yaml

 

file test-withkeyword-1031.yaml

 

file test-withkeyword-1032.yaml

 

file test-withkeyword-1033.yaml

 

file test-withkeyword-1034.yaml

 

file test-withkeyword-1035.yaml

 

file test-withkeyword-1036.yaml

 

file test-withkeyword-1037.yaml

 

file test-withkeyword-1038.yaml

 

file test-withkeyword-1039.yaml

 

file test-withkeyword-1040.yaml

 

file test-withkeyword-1041.yaml

 

file test-withkeyword-1042.yaml

 

file test-withkeyword-1043.yaml

 

file test-withkeyword-1044.yaml

 

file test-withkeyword-1045.yaml

 

file test-withkeyword-1046.yaml

 

file test-withkeyword-1047.yaml

 

file test-withkeyword-1048.yaml

 

file test-withkeyword-1049.yaml

 

file test-withkeyword-1050.yaml

 

file test-withkeyword-1051.yaml

 

file test-withkeyword-1052.yaml

 

file test-withkeyword-1053.yaml

 

file test-withkeyword-1054.yaml

 

dir v1/test/cli/script/

 

file bundle_files.txtar

 

file eval_bundle_input.txtar

 

file exec.txtar

 

file inspect_data.txtar

 

file smoke.txtar

 

dir v1/test/e2e/

 

file testing.go

 

dir v1/test/e2e/authz/

 

file authz_bench_integration_test.go

 

file disk.go

 

file nodisk.go

 

dir v1/test/e2e/certrefresh/

 

file certrefresh_test.go

 

dir v1/test/e2e/certrefresh/testdata/

 

file ca.pem

 

file gencerts.sh

 

file server-cert-new.pem

 

file server-cert.pem

 

file server-key-new.pem

 

file server-key.pem

 

dir v1/test/e2e/concurrency/

 

file concurrency_test.go

 

dir v1/test/e2e/diagnostics/

 

file diagnostics_test.go

 

dir v1/test/e2e/distributedtracing/

 

file distributedtracing_test.go

 

dir v1/test/e2e/h2c/

 

file h2c_test.go

 

dir v1/test/e2e/http/

 

file http_test.go

 

dir v1/test/e2e/logs/

 

file utils.go

 

dir v1/test/e2e/logs/console/

 

file console_decision_logger_benchmark_test.go

 

file console_decision_logger_test.go

 

dir v1/test/e2e/logs/remote/

 

file remote_decision_logger_benchmark_test.go

 

dir v1/test/e2e/metrics/

 

file metrics_test.go

 

dir v1/test/e2e/metricsexport/

 

file otlpmetrics_grpc_test.go

 

file otlpmetrics_http_test.go

 

dir v1/test/e2e/oci/

 

file oci_test.go

 

dir v1/test/e2e/print/

 

file print_test.go

 

dir v1/test/e2e/shutdown/

 

file shutdown_test.go

 

dir v1/test/e2e/tls/

 

file tls_test.go

 

dir v1/test/e2e/tls/testdata/

 

file ca.pem

 

file client-cert-2.pem

 

file client-cert.pem

 

file client-key-2.pem

 

file client-key.pem

 

file gencerts.sh

 

file server-cert.pem

 

file server-key.pem

 

dir v1/test/e2e/wasm/authz/

 

file authz_bench_integration_test.go

 

file disk.go

 

file nodisk.go

 

dir v1/test/scheduler/

 

file scheduler_bench_test.go

 

file scheduler_test.go

 

dir v1/test/scheduler/testdata/

 

file data_10nodes_30pods.json

 

dir v1/test/wasm/assets/

 

file 001_eq.yaml

 

file 002_iteration.yaml

 

file 003_comparison.yaml

 

file 004_negation.yaml

 

file 005_references.yaml

 

file 006_pattern_matching.yaml

 

file 007_complete.yaml

 

file 008_functions.yaml

 

file 009_default.yaml

 

file 010_else.yaml

 

file 011_partialsets.yaml

 

file 012_partialobjects.yaml

 

file 013_virtual.yaml

 

file 014_comprehensions.yaml

 

file 015_results.yaml

 

file 016_with.yaml

 

file 017_strings.yaml

 

file 018_builtins.yaml

 

file 019_call_indirect_optimization.yaml

 

file test.js

 

dir v1/test/wasm/cmd/wasm-rego-testgen/

 

file main.go

 

dir v1/tester/

 

file fixture_test.go

 

file reporter.go

 

file reporter_test.go

 

file runer_compile_test.go

 

file runner.go

 

file runner_test.go

 

file test_tracer.go

 

dir v1/tester/testdata/

 

file JSONReporter.json

 

file JSONReporter_sorted.json

 

dir v1/topdown/

 

file aggregates.go

 

file aggregates_bench_test.go

 

file arithmetic.go

 

file array.go

 

file binary.go

 

file bindings.go

 

file bindings_alloc_bench_test.go

 

file bindings_test.go

 

file bits.go

 

file builtins.go

 

file builtins_test.go

 

file cache.go

 

file cache_bench_test.go

 

file cache_test.go

 

file cancel.go

 

file casts.go

 

file cidr.go

 

file cidr_test.go

 

file comparison.go

 

file comprehension_bindings_bench_test.go

 

file comprehension_comparison_bench_test.go

 

file crypto.go

 

file crypto_test.go

 

file doc.go

 

file encoding.go

 

file encoding_bench_test.go

 

file enumerate_bench_test.go

 

file errors.go

 

file errors_test.go

 

file eval.go

 

file eval_bench_test.go

 

file eval_test.go

 

file evaluated.go

 

file evaluated_test.go

 

file example_test.go

 

file exported_test.go

 

file external_source_test.go

 

file glob.go

 

file glob_bench_test.go

 

file glob_test.go

 

file graphql.go

 

file graphql_bench_test.go

 

file graphql_test.go

 

file http.go

 

file http_fixup.go

 

file http_fixup_darwin.go

 

file http_slow_test.go

 

file http_test.go

 

file input.go

 

file input_test.go

 

file instrumentation.go

 

file json.go

 

file json_bench_test.go

 

file json_test.go

 

file jsonschema.go

 

file jsonschema_test.go

 

file net.go

 

file net_test.go

 

file numbers.go

 

file numbers_bench_test.go

 

file numbers_test.go

 

file object.go

 

file object_bench_test.go

 

file object_test.go

 

file parse.go

 

file parse_bytes.go

 

file parse_units.go

 

file print.go

 

file print_test.go

 

file providers.go

 

file query.go

 

file query_test.go

 

file reachable.go

 

file regex.go

 

file regex_bench_test.go

 

file regex_template.go

 

file regex_template_test.go

 

file regex_test.go

 

file resolver.go

 

file rules_bindings_bench_test.go

 

file runtime.go

 

file runtime_test.go

 

file save.go

 

file save_test.go

 

file semver.go

 

file sets.go

 

file sets_bench_test.go

 

file sets_test.go

 

file sink.go

 

file strings.go

 

file strings_bench_test.go

 

file subset.go

 

file template.go

 

file template_dce_test.go

 

file template_string.go

 

file template_string_test.go

 

file test.go

 

file time.go

 

file time_test.go

 

file tokens.go

 

file tokens_bench_test.go

 

file tokens_test.go

 

file topdown_bench_test.go

 

file topdown_logical_test.go

 

file topdown_partial_bench_test.go

 

file topdown_partial_test.go

 

file topdown_test.go

 

file trace.go

 

file trace_test.go

 

file type.go

 

file type_name.go

 

file uri.go

 

file uuid.go

 

file uuid_test.go

 

file walk.go

 

dir v1/topdown/builtins/

 

file builtins.go

 

dir v1/topdown/cache/

 

file cache.go

 

file cache_test.go

 

dir v1/topdown/copypropagation/

 

file copypropagation.go

 

file unionfind.go

 

file unionfind_test.go

 

dir v1/topdown/durationparser/

 

file duration.peg

 

file duration_parser.go

 

file types.go

 

dir v1/topdown/lineage/

 

file lineage.go

 

file lineage_test.go

 

dir v1/topdown/print/

 

file print.go

 

dir v1/topdown/testdata/

 

file ca.pem

 

file client-cert-2.pem

 

file client-cert.pem

 

file client-key-2.pem

 

file client-key.pem

 

file gencerts.sh

 

file server-cert.pem

 

file server-key.pem

 

dir v1/topdown/testdata/cases/

 

file test-systemdocument-1069.yaml

 

dir v1/tracing/

 

file tracing.go

 

dir v1/types/

 

file decode.go

 

file types.go

 

file types_bench_test.go

 

file types_test.go

 

dir v1/util/

 

file backoff.go

 

file channel.go

 

file close.go

 

file compare.go

 

file compare_test.go

 

file doc.go

 

file enumflag.go

 

file enumflag_test.go

 

file graph.go

 

file graph_test.go

 

file hashmap.go

 

file hashmap_test.go

 

file json.go

 

file json_test.go

 

file maps.go

 

file maps_test.go

 

file performance.go

 

file performance_test.go

 

file queue.go

 

file queue_test.go

 

file read_gzip_body.go

 

file read_gzip_body_test.go

 

file slices.go

 

file strings.go

 

file time.go

 

file wait.go

 

file wait_test.go

 

dir v1/util/decoding/

 

file context.go

 

dir v1/util/test/

 

file benchmark.go

 

file ci_skip.go

 

file ci_skip_darwin.go

 

file doc.go

 

file populate.go

 

file tempfs.go

 

file tempus.go

 

file zeroreader.go

 

dir v1/util/testdata/

 

file atoi.txt

 

dir v1/version/

 

file version.go

 

file wasm.go

 

dir version/

 

file doc.go

 

file version.go

 

file wasm.go

 

dir wasm/

 

file Dockerfile

 

file Makefile

 

file README.md

 

file test.js

 

dir wasm/build/

 

file gen-wasm-callgraph.sh

 

dir wasm/src/

 

file aggregates.c

 

file aggregates.h

 

file arithmetic.c

 

file arithmetic.h

 

file array.c

 

file array.h

 

file bits-builtins.c

 

file bits-builtins.h

 

file cidr.c

 

file cidr.h

 

file comparisons.c

 

file comparisons.h

 

file context.c

 

file context.h

 

file conversions.c

 

file conversions.h

 

file encoding.c

 

file encoding.h

 

file error.c

 

file error.h

 

file glob-compiler.cc

 

file glob-compiler.h

 

file glob-lexer.cc

 

file glob-lexer.h

 

file glob-parser.cc

 

file glob-parser.h

 

file glob.cc

 

file glob.h

 

file graphs.c

 

file graphs.h

 

file json.c

 

file json.h

 

file malloc.c

 

file malloc.h

 

file memoize.c

 

file memoize.h

 

file mpd.c

 

file mpd.h

 

file numbers.c

 

file numbers.h

 

file object.c

 

file object.h

 

file regex.cc

 

file regex.h

 

file set.c

 

file set.h

 

file std.h

 

file str.c

 

file str.h

 

file strings.c

 

file strings.h

 

file template-string.c

 

file template-string.h

 

file types.c

 

file types.h

 

file undefined.symbols

 

file unicode.c

 

file unicode.h

 

file value.c

 

file value.h

 

dir wasm/src/lib/

 

file assert.h

 

file bits.h

 

file ctype.c

 

file ctype.h

 

file errno.c

 

file errno.h

 

file inttypes.h

 

file locale.c

 

file locale.h

 

file math.c

 

file math.h

 

file printf.c

 

file printf.h

 

file signal.h

 

file stdio.c

 

file stdio.h

 

file stdlib.c

 

file stdlib.h

 

file string.c

 

file string.h

 

file time.h

 

file unistd.h

 

file wchar.c

 

file wchar.h

 

file wctype.h

 

dir wasm/src/libc++/

 

file __config_site

 

file __threading_support

 

file hash.cc

 

file minimal.cc

 

file mutex

 

file mutex.cc

 

dir wasm/src/libmpdec/

 

file basearith.c

 

file basearith.h

 

file bits.h

 

file constants.c

 

file constants.h

 

file context.c

 

file convolute.c

 

file convolute.h

 

file crt.c

 

file crt.h

 

file difradix2.c

 

file difradix2.h

 

file fnt.c

 

file fnt.h

 

file fourstep.c

 

file fourstep.h

 

file io.c

 

file io.h

 

file memory.c

 

file memory.h

 

file mpdecimal.c

 

file mpdecimal.h

 

file numbertheory.c

 

file numbertheory.h

 

file sixstep.c

 

file sixstep.h

 

file transpose.c

 

file transpose.h

 

file typearith.h

 

file umodarith.h

 

dir wasm/src/re2/re2/

 

file bitmap256.h

 

file bitstate.cc

 

file compile.cc

 

file dfa.cc

 

file nfa.cc

 

file onepass.cc

 

file parse.cc

 

file perl_groups.cc

 

file pod_array.h

 

file prog.cc

 

file prog.h

 

file re2.cc

 

file re2.h

 

file regexp.cc

 

file regexp.h

 

file simplify.cc

 

file sparse_array.h

 

file sparse_set.h

 

file stringpiece.cc

 

file stringpiece.h

 

file tostring.cc

 

file unicode_casefold.cc

 

file unicode_casefold.h

 

file unicode_groups.cc

 

file unicode_groups.h

 

file walker-inl.h

 

dir wasm/src/re2/util/

 

file logging.h

 

file mix.h

 

file mutex.h

 

file rune.cc

 

file strutil.cc

 

file strutil.h

 

file utf.h

 

file util.h

 

dir wasm/tests/

 

file test-glob.cc

 

file test-regex.cc

 

file test.c

 

file test.h

 

file undefined.symbols

============================================================

Documentation

============================================================

ADOPTERS.md

# Adopters

<!-- Hello! If you are using OPA and contributing to this file, thank you! -->
<!-- Please keep lines shorter than 80 characters (or so.) Links can go long. -->

This is a list of organizations that have spoken publicly about their adoption or
production users that have added themselves (in alphabetical order):

* [2U, Inc](https://2u.com) has incorporated OPA into their SDLC for both Terraform and Kubernetes deployments.
  Shift left!

* [APIwiz](https://www.apiwiz.io) has implemented OPA as a centralized service to enforce consistent
  and secure authorization decisions across all internal APIs. By delegating authorization logic to OPA,
  APIwiz streamlines access control, ensuring robust security throughout the platform. Furthermore, OPA
  has been seamlessly integrated into APIwiz's API Builder, enabling users to embed policy-driven workflows.
  This integration provides precise control over workflows, enhancing both the security and efficiency of
  the platform's operations.

* [Appsflyer](https://www.appsflyer.com/) uses OPA to make consistent
  authorization decisions by hundreds of microservices for UI and API data
  access. All authorization decisions are delegated to OPA that is deployed as a
  central service. The decisions are driven by flexible policy rules that take
  into consideration data privacy regulations and policies, data consents and
  application level access permissions. For more information, see the [Appsflyer
  Engineering Blog post](https://medium.com/appsflyer/authorization-solution-for-microservices-architecture-a2ac0c3c510b).

* [Atlassian](https://www.atlassian.com/) uses OPA in a heterogeneous cloud
  environment for microservice API authorization. OPA is deployed per-host and
  inside of their Slauth (AAA) system. Policies are tagged and categorized
  (e.g., platform, service, etc.) and distributed via S3. Custom log infrastructure
  consumes decision logs.

* Bisnode (Dun & Bradstreet) uses OPA for a wide range of use cases,
  including microservice authorization, fine grained kubernetes authorization,
  validating and mutating admission control and CI/CD pipeline testing. Built
  and maintains some OPA related tools and libraries, primarily to help
  integrate OPA in the Java/JVM ecosystem, [see `github.com/Bisnode`](https://github.com/Bisnode).

* [bol.com](https://www.bol.com/) uses OPA for a mix of
  validating and mutating admission control use cases in their
  Kubernetes clusters. Use cases include patching image pull secrets,
  load balancer properties, and tolerations based on contextual
  information stored on namespaces. OPA is deployed on multiple
  clusters with ~100 nodes and ~300 namespaces total.

* [BNY Mellon](https://www.bny.com/corporate/global/en.html) uses OPA as a sidecar to enforce access
  control over applications based on external context coming from AD and other
  internal services. For more information see this talk from [QCon 2019](https://www.infoq.com/presentations/opa-spring-boot-hocon/).

* [Capital One](https://www.capitalone.com/) uses OPA to enforce a variety of
  admission control policies across their Kubernetes clusters including image
  registry allowlisting, label requirements, resource requirements, container
  privileges, etc. For more information see this talk from [KubeCon US 2018](https://www.youtube.com/watch?v=CDDsjMOtJ-c&t=6m35s).

* [Chef](https://www.chef.io/) integrates OPA to implement IAM-style
  access control and enumerate user->resource permissions in Chef
  Automate V2. The integration utilizes OPA's Partial Evaluation
  feature to reduce evaluation time (in exchange for higher update
  latency.) A high-level description can be found [in this blog
  post](https://blog.chef.io/2019/01/24/introducing-the-chef-automate-identity-access-management-version-two-iam-v2-beta/),
  and the code is Open Source, [see
  `github.com/chef/automate`](https://github.com/chef/automate/tree/master/components/authz-service).

* [cluetec.de](https://cluetec-audit.de/) primarily uses OPA to enforce fine-grained authorization
  and data-filtering policies in its Spring-based microservices and multi-tenant SaaS. Policies
  are mapped to tenant-specific domains and used to enrich the database queries without any code
  modifications. OPA is also used to enforce admission control policies and RBAC in multi-tenant
  Kubernetes clusters.

* [Cloudflare](https://www.cloudflare.com/) uses OPA as a validating
  admission controller to prevent conflicting Ingresses in their
  Kubernetes clusters that host a mix of production and test
  workloads.

* [Cloudsmith](https://www.cloudsmith.com/) uses OPA to allow organizations to define, enforce,
  and monitor policies across the artifact lifecycle. Cloudsmith users can leverage EPSS-based logic
  in their Rego policies for more granular, data-informed decisions around vulnerability management.
  For more information on how Cloudsmith uses Exploit Prediction Scoring System (EPSS) in OPA policies,
  check out the [Cloudsmith Blog](https://cloudsmith.com/blog/cloudsmith-introduces-epss-scoring-in-enterprise-policy-management-epm).

* [ControlPlane](https://control-plane.io) uses OPA to enforce enterprise-friendly
  policy for safe adoption of Kubernetes, Istio, and cloud services. OPA policies
  are validated and tested individually and en masse with unit tests and conftest.
  This enables developers to validate local changes against production policies,
  minimise engineering feedback loops, and reduce CI cycle time. Policies are
  tested as "SDLC guardrails", then re-validated at deployment time by a range of
  OPA-based admission controllers, covering single-tenant environments and hard
  multi-tenancy configurations.

* [Elastic](https://www.elastic.co/) uses OPA in its Cloud Security offering to enable CSPM and KSPM solutions, helping customers adhere to best practices
  defined in CIS benchmarks by tracking misconfigurations on AWS, GCP and Azure. the code is Open Source, see [Security Policies](https://github.com/elastic/cloudbeat/tree/main/security-policies).

* [Facets.cloud](https://www.facets.cloud/) is a DevOps platform designed to streamline software development and deployment processes.
  The integration of Open Policy Agent (OPA) has been a key factor in developing our [Guardrails Policy](https://readme.facets.cloud/docs/guardrail-policy) feature.
  Managed using OPA, this feature enables our customers to set rules that align their software blueprints(detailed architectural designs of their software) - with established standards.
  The Guardrails Policy feature has optimized resource management, minimized redundancy in policy definitions, and ensured comprehensive adherence to organizations’ best practices.

* [Fugue](https://snyk.io/platform/) was a cloud security SaaS that uses OPA to
  classify compliance violations and security risks in AWS and Azure
  accounts and generate compliance reports and notifications. Now part of
  [Snyk](https://snyk.io/).

* [Goldman Sachs](https://www.goldmansachs.com/) uses OPA to enforce admission control
  policies in their multi-tenant Kubernetes clusters as well as for _provisioning_
  RBAC, PV, and Quota resources that are central to the security and operation of
  these clusters. For more information see this talk from [KubeCon US 2019](https://www.youtube.com/watch?v=lYHr_UaHsYQ).

* [Google Cloud](https://cloud.google.com/) uses OPA to validate Google Cloud
  product's configurations in several products and tools, including
  [Config Controller](https://docs.cloud.google.com/kubernetes-engine/policy-controller/docs/overview),
  [GKE Policy Automation](https://github.com/google/gke-policy-automation) or
  [Config Validator](https://github.com/GoogleCloudPlatform/policy-library). See
  [Creating policy-compliant Google Cloud resources article](https://docs.cloud.google.com/kubernetes-engine/policy-controller/docs/how-to/creating-policy-controller-constraints)
  for example use cases.

* [Infracost](https://www.infracost.io/) shows cloud cost estimates for Terraform.
  It uses OPA to enable users to create cost policies, and setup guardrails such
  as "this change puts the monthly costs above $10K, which is the budget for this
  product. Consider asking the team lead to review it". See [the docs](https://www.infracost.io/docs/features/cost_policies/) for details.

* [Intuit](https://www.intuit.com/company/) uses OPA as a validating
  and mutating admission controller to implement various security,
  multi-tenancy, and risk management policies across approximately 50
  clusters and 1,000 namespaces. For more information on how Intuit
  uses OPA see [this talk from KubeCon Seattle 2018](https://youtu.be/CDDsjMOtJ-c?t=980).

* [Jetstack](https://www.cyberark.com/services-support/cloud-native-consulting/) uses OPA on customer projects to validate
  resources deployed to Kubernetes environments are conformant with
  organization rules. This has involved both validating and mutating resources
  as well as the following related projects: conftest, konstraint, and
  Gatekeeper. Jetstack also uses OPA via the Golang API in _Jetstack Secure_ to
  automate the checking of resources against our best practice recommendations.

* [Marsh McLennan](https://www.marshmclennan.com) uses OPA Gatekeeper in their
  Kubernetes clusters, and OPA as an authorization decision point by many
  applications for ingress traffic. Some applications also use OPA as a rules
  engine.

* [Medallia](https://www.medallia.com/) uses OPA to audit AWS
  resources for compliance violations. The policies search across
  state from Terraform and AWS APIs to identify security violations
  and identify high-risk configurations. The policies ingest 1,000s of
  AWS resources to generate the final report.

* [Mercari](https://www.mercari.com/) uses OPA to enforce admission control
  policies in their multi-tenant Kubernetes clusters. It helps maintain
  the governance of the cluster, checking that developers are following
  the best practices in the admission controller. They also use [confest](https://github.com/open-policy-agent/conftest) to
  enforce policies in their CI/CD pipeline.

* [Mia-Platform](https://mia-platform.eu/) uses OPA to run RBAC authorization policies
  distributed within the application microservices. They built [Rönd](https://github.com/rond-authz/rond)
  sidecar to intercept API invocation in the kubernetes ecosystem and created an extensible
  RBAC solution that protects the application with little-to-none changes to the existing codebase.

* [Netflix](https://www.netflix.com) uses OPA as a method of enforcing
  access control in microservices across a variety of languages and
  frameworks for thousands of instances in their cloud
  infrastructure. Netflix takes advantage of OPA's ability to bring in
  contextual information and data from remote resources in order to
  evaluate policies in a flexible and consistent manner. For a
  description of how Netflix has architected access control with OPA
  check out [this talk from KubeCon Austin 2017](https://www.youtube.com/watch?v=R6tUNpRpdnY).

* [Pinterest](https://www.pinterest.com/) uses OPA to solve multiple policy-related use cases
  including access control in Kafka, Envoy, and Jenkins! At peak, their Kafka-OPA
  integration handles ~400K QPS without caching. With caching the system
  handles ~8.5M QPS.

* [Pix4D](https://www.pix4d.com/) uses OPA to run and define RBAC authorization policies for
  the users of its cloud platform. Defining the policies in OPA ensures a single source of
  controls and a consistent policy enforcement for any microservices. It operates as a
  sidecar to a Django application exposing access roles of users over resources.

* [Plex Systems](https://plex.rockwellautomation.com/en-us.html) uses OPA to enforce policy throughout
  their entire release process; from local development to continuous production
  audits. The CI/CD pipelines at Plex leverage [conftest](https://github.com/open-policy-agent/conftest),
  a policy enforcement tool that relies on OPA, to automatically reject changes that do not adhere
  to defined policies. Plex also uses
  [Gatekeeper](https://github.com/open-policy-agent/gatekeeper), a Kubernetes policy controller, as
  a means to enforce policies within their Kubernetes clusters. The general-purpose nature of OPA
  has enabled Plex to have a consistent means of policy enforcement,
  no matter the environment.

* [Splash](https://splashthat.com) uses OPA to handle fine-grained authorization
  across its entire platform, implemented as both a sidecar in Kubernetes and a separate
  container on bare instances. Policies and datasets are recompiled and updated based
  on changes to users' roles and permissions.

* [SAP/InfraBox](https://github.com/SAP/Infrabox) integrates OPA to
  implement authorization over HTTP API resources. OPA policies
  evaluate user and permission data replicated from Postgres to make
  access control decisions over projects, collaborators, jobs,
  etc. SAP/Infrabox is used in production within SAP and has several
  external users.

* [Terminus Software](https://demandscience.com/?utm_campaign=terminus-redirect) uses OPA for microservice authorization.

* [T-Mobile](https://www.t-mobile.com) uses OPA as a core component for their
  [MagTape](https://github.com/tmobile/magtape/) project that enforces best
  practices and secure configurations across their fleet of Kubernetes
  clusters (more info in [this blog post](https://www.t-mobile.com/)).
  T-Mobile also leverages OPA to enforce authorization workflows within their
  Corporate Delivery Platform (CI/CD).

* [Tremolo Security](https://www.tremolo.io/) uses OPA at a
  London-based financial services company to inject annotations and
  volume mount parameters into Kubernetes Pods so that workloads can
  connect to off-cluster CIFS drives and SQL Server
  instances. Policies are based on external context sourced from
  OpenUnison. Ability to validate policies offline is a huge win
  because the clusters are air-gapped. For more information on how
  Tremolo Security uses OPA see [this blog post](https://www.tremolo.io/post/beyond-rbac-in-openshift-open-policy-agent).

* [Tripadvisor](https://tripadvisor.com/) uses OPA to enforce
  admission control policies in Kubernetes. In the process of rolling out OPA,
  they created an integration testing framework that verifies clusters are accepting
  and rejecting the right objects when OPA is deployed.

* [Very Good Security (VGS)](https://www.vgs.io/) integrates OPA to
  implement a fine-grained permission system and enumerate
  user->resource permissions in their product. The backend is
  architected as a collection of (polyglot) microservices running on
  Kubernetes that offload policy decisions to OPA sidecars. VGS has
  implemented a synchronization protocol on top of the Bundle and
  Status APIs so that the system can determine when permission updates
  have propagated. For more details on the VGS use case see this
  [blog post](https://www.verygoodsecurity.com/blog/posts/building-a-fine-grained-permission-system-in-a-distributed-environment).

* [VNG Cloud](https://www.vngcloud.vn/en/home) [Identity and Access Management (IAM)](https://iam.console.vngcloud.vn/)
  use OPA as a policy-based decision engine for authorization. IAM provides administrators with fine-grained 
  access control to VNG Cloud resources and help centralize and manage permissions to access resources. 
  Specifically, OPA is integrated to evaluate policies to make the decision about denying or allowing incoming requests.
  
* [Wiz](https://www.wiz.io/) helps every organization rapidly remove the most critical
  risks in their cloud estate. It simply connects in minutes, requires zero agents, and
  automatically correlates the entire security stack to uncover the most pressing issues.
  Wiz policies leverage Open Policy Agent (OPA) for a unified framework across the
  cloud-native stack. Whether for configurations, compliance, IaC, and more, OPA enables
  teams to move faster in the cloud. For more information on how Wiz uses OPA, [contact Wiz](https://www.wiz.io/contact).

* [Xenit AB](https://xenit.se/) uses OPA to implement fine-grained control
  over resource formulation in its managed Kubernetes service as well as several
  customer-specific implementations. For more information, see the Kubernetes Terraform library
  [OPA Gatekeeper module](https://github.com/XenitAB/terraform-modules/tree/main/modules/kubernetes/gatekeeper) and
  [OPA Gatekeeper policy library](https://github.com/XenitAB/gatekeeper-library).

* [Yelp](https://www.yelp.com/) use OPA and Envoy to enforce authorization policies
  across a fleet of microservices that evolved out of a monolithic architecture.
  For more information see this talk from [KubeCon US 2019](https://www.youtube.com/watch?v=Z6aN3Smt-9M).
  
In addition, there are several production adopters that prefer to
remain anonymous.

* **A Fortune 100 company** uses OPA to implement validating admission
  control and fine-grained authorization policies on ~10 Kubernetes
  clusters with ~1,000 nodes. They also integrate OPA into their PKI
  as part of a Certificate RA that serves these clusters.

This is a list of adopters in early stages of production or
pre-production (in alphabetical order):

* [Aserto](https://www.aserto.com/) is a venture-backed developer API company
  that helps developers easily build permissions and roles into their SaaS
  applications. Aserto uses OPA as its core engine, and has contributed projects
  such as [Open Policy Containers](https://openpolicycontainers.com/) and
  [OPA Runtime](https://github.com/aserto-dev/runtime) that make it easier for
  developers to incorporate OPA policies and the OPA engine into their applications.

* [Cyral](https://www.varonis.com/platform/database-activity-monitoring) is a venture-funded data security
  company. Still in stealth mode but using OPA to manage and enforce
  fine-grained authorization policies.

* [Permit.io](https://www.permit.io/) Uses a combination of OPA and OPAL
  to power fine-grained authorization policies at the core of the Permit.io platform.
  Permit.io leverages the power of OPA's Rego language,
  generating new Rego code on the fly from its UI policy editor.
  The team behind Permit.io contributes to the OPA ecosystem - creating opens-source projects like
  [OPAL- making OPA event-driven)](https://github.com/permitio/opal)
  and [OPToggles - sync Frontend with open-policy](https://github.com/permitio/OPToggles).

* [Scalr](https://scalr.com/) is a remote operations backend for Terraform
  that helps users scale their Terraform usage through automation and collaboration.
  [Scalr uses OPA](https://docs.scalr.io/docs/introduction) to validate Terraform
  code against organization standards and allows for approvals prior to a Terraform apply.

* [Spacelift](https://spacelift.io) is a specialized CI/CD platform
  for infrastructure-as-code. Spacelift is [using OPA](https://docs.spacelift.io/concepts/policy) to provide flexible,
  fine-grained controls at various application decision points, including
  automated code review, defining access levels or blocking execution of
  unwanted code.

* [Magda](https://github.com/magda-io/magda) is a federated, Kubernetes-based, open-source data catalog system. Working as Magda's central authorisation policy engine, OPA helps not only the API endpoint authorisation. Magda also uses its partial evaluation feature to translate datasets authorisation decisions to other database-specific DSLs (e.g. SQL or Elasticsearch DSL) and use them for dataset authorisation enforcement in different databases.

* [VodafoneZiggo](https://www.vodafoneziggo.nl/) Is a Dutch telecommunications company that uses OPA to power authorisation decisions in our internal developer platform based on Backstage, it is also used as a way to enforce and validate component metadata that is onboarded as software components into the Backstage software catalog.

Other adopters that have gone into production or various stages of
testing include:

* [Cisco](https://www.cisco.com/)
* [Nefeli Networks](https://www.cloudflare.com/press/press-releases/2024/cloudflare-enters-multicloud-networking-market-unlocks-simple-secure/)
* [SolarWinds](https://www.solarwinds.com/) via [Lee Calcote](https://github.com/leecalcote)
* [State Street Corporation](https://www.statestreet.com/us/en)
* [PITS Global Data Recovery Services](https://www.pitsdatarecovery.com/)

If you have adopted OPA and would like to be included in this list,
feel free to submit a PR updating this file or
[open an issue](https://github.com/login?return_to=https%3A%2F%2Fgithub.com%2Fopen-policy-agent%2Fopa%2Fissues%2Fnew%3Fassignees%3D%26labels%3Dadopt-opa%26template%3Dadopt-opa.yaml%26title%3Dorganization_name%2Bhas%2Badopted%2BOPA).



CHANGELOG.md

# Change Log

All notable changes to this project will be documented in this file. This
project adheres to [Semantic Versioning](http://semver.org/).

## Unreleased

## 1.18.2

This release includes a bug fix for a `opa fmt` regression introduced in v1.18.0.

The original fix for #8557 had the formatter enforce newlines in single-item
collections (arrays, objects, sets) rather than merely honoring existing ones.
As a result, running `opa fmt` on already-formatted policies could introduce
a large number of unwanted changes. This patch release restores the intended
behavior: only newlines already present in the source determine whether a
single-item collection is formatted on one line or across multiple lines.

### Fixes

- Fix regression in fix of #8557 (#8845) (authored by @anderseknert)

## 1.18.1

This release fixes a memory leak introduced in OPA v1.17.0.
It is advised to update if you notice excess memory usage when running OPA server.

### Fixes

- ast: fix AnnotationSet memory leak via runtime.AddCleanup cycle ([#8817](https://github.com/open-policy-agent/opa/issues/8817)) authored by @srenatus reported by @keydon and @gorsr01

## 1.18.0

This release contains a mix of bugfixes and small features. Notably:

- A breaking fix to the outbound `User-Agent` header so it conforms to RFC 9110 (see below)
- Container-aware resource limits: automatic `GOMAXPROCS` is restored and automatic `GOMEMLIMIT` is now supported
- Several `opa fmt` correctness fixes
- Improvements to `opa test --coverage` (ranges in report, inline rule head tracking, conjunction-expression coverage)

### Breaking: Fix User-Agent according to RFC9110 ([#8792](https://github.com/open-policy-agent/opa/issues/8792))

OPA's outbound HTTP requests (bundle, discovery, decision log, status, `http.send`, AWS KMS/ECR)
previously sent `User-Agent: Open Policy Agent/<version> (<os>, <arch>)`, which is not a valid
RFC 9110 `User-Agent` value because the `product` token cannot contain spaces. The header is now
`Open-Policy-Agent/<version> (<os>, <arch>)`. Server-side log filters or WAF rules that
exact-match the old string will need to be updated.

Authored by @sspaink, reported by @SpecLad

### Runtime, SDK, Tooling

- bundle: fix per-module rego version lookup ([#8797](https://github.com/open-policy-agent/opa/issues/8797)) authored by @sspaink, reported by @xubinzheng
- bundle: improve determinism of `file_rego_versions` patterns with overlap ([#8733](https://github.com/open-policy-agent/opa/pull/8733)) authored by @philipaconrad
- cover: Track inline rule head in post trace walk ([#6531](https://github.com/open-policy-agent/opa/issues/6531)) authored by @charlieegan3, reported by @anderseknert
- cover: Update report to include ranges ([#8748](https://github.com/open-policy-agent/opa/issues/8748)) reported and authored by @charlieegan3
- cover: Add support for coverage of conjunction exprs ([#8809](https://github.com/open-policy-agent/opa/pull/8809)) authored by @charlieegan3
- download/oci: Set Accept headers ([#8720](https://github.com/open-policy-agent/opa/pull/8720)) authored by @charlieegan3
- fmt: preserve the multiline but single entry iterables ([#8557](https://github.com/open-policy-agent/opa/issues/8557)) authored by @unichronic, reported by @anderseknert
- format: Fix dropped with-clause after comment in object value ([#8765](https://github.com/open-policy-agent/opa/issues/8765)) authored by @sspaink, reported by @srabraham
- format: keep lone `with` on the closing-bracket line of multi-line expressions ([#8804](https://github.com/open-policy-agent/opa/issues/8804)) authored by @anneheartrecord, reported by @burnster
- oracle: Fix find-definition on expressions inside `ast.Not` nodes ([#8731](https://github.com/open-policy-agent/opa/pull/8731)) authored by @johanfylling
- runtime: Restore goautomaxprocs, add automemlimit ([#8784](https://github.com/open-policy-agent/opa/pull/8784)) authored by @charlieegan3

### Compiler, Topdown and Rego

- ast: Apply location to inner `ast.Not` expressions ([#8717](https://github.com/open-policy-agent/opa/issues/8717)) authored by @johanfylling, reported by @anderseknert
- ast: Clean up code for value comparisons ([#8737](https://github.com/open-policy-agent/opa/pull/8737)) authored by @anderseknert
- ast: Fix PE regression for `future.keywords.not` negation inside `every` ([#8781](https://github.com/open-policy-agent/opa/pull/8781)) authored by @johanfylling
- internal/edittree: Add recursive tree node recycling ([#8693](https://github.com/open-policy-agent/opa/pull/8693)) authored by @philipaconrad
- internal: compile,planner: improve determinism of `plan`/`wasm` bundle builds ([#8732](https://github.com/open-policy-agent/opa/pull/8732)) authored by @philipaconrad
- perf: avoid allocations in `object.get` ([#8729](https://github.com/open-policy-agent/opa/pull/8729)) authored by @anderseknert
- topdown: Fix PE not namespacing vars in comprehensions nested inside `every` ([#8816](https://github.com/open-policy-agent/opa/pull/8816)) authored by @johanfylling
- topdown: remove `dst.Compare(src)` shortcut ([#8739](https://github.com/open-policy-agent/opa/pull/8739)) authored by @srenatus
- topdown: skip strconv.ParseInt in format_int base-10 fast path ([#8801](https://github.com/open-policy-agent/opa/pull/8801)) authored by @srenatus

### Docs, Website, Ecosystem

- docs/chore: Remove broken links ([#8714](https://github.com/open-policy-agent/opa/issues/8714)) authored by @charlieegan3, reported by @github-actions
- docs: PoC for kapa.ai ([#8125](https://github.com/open-policy-agent/opa/issues/8125)) reported and authored by @charlieegan3
- docs(ecosystem): update OPA MCP entry with video, blog, and distribution links ([#8712](https://github.com/open-policy-agent/opa/pull/8712)) authored by @OrygnsCode
- docs/contributing: add formatting ([#8740](https://github.com/open-policy-agent/opa/pull/8740)) authored by @mmzzuu
- docs: Add SDK references for evaluating IR plans ([#8783](https://github.com/open-policy-agent/opa/pull/8783)) authored by @charlieegan3
- docs: Add depkeep to enterprise support ([#8685](https://github.com/open-policy-agent/opa/pull/8685)) authored by @pkuzco
- docs: Add notes about use of GOMEMLIMIT ([#8771](https://github.com/open-policy-agent/opa/pull/8771)) authored by @charlieegan3
- docs: Add we/our/us check to spell check ([#8787](https://github.com/open-policy-agent/opa/pull/8787)) authored by @charlieegan3
- docs: Update built-in index page titles ([#8728](https://github.com/open-policy-agent/opa/pull/8728)) authored by @charlieegan3
- docs: Update documentation to be more consistent and sound more like reference docs ([#8786](https://github.com/open-policy-agent/opa/pull/8786)) authored by @charlieegan3
- docs: Update regal docs for 0.41.1 release ([#8730](https://github.com/open-policy-agent/opa/pull/8730)) authored by @charlieegan3
- docs: Update to agents.md regarding security dependences 'fixes' ([#8754](https://github.com/open-policy-agent/opa/pull/8754)) authored by @charlieegan3
- docs: clarify environment variable substitution behaviour ([#8713](https://github.com/open-policy-agent/opa/pull/8713)) authored by @taurelius
- docs: remove duplicated word in Rego style guide ([#8800](https://github.com/open-policy-agent/opa/pull/8800)) authored by @s3onghyun
- website: Add .md alternate content types for llms ([#8725](https://github.com/open-policy-agent/opa/pull/8725)) authored by @charlieegan3
- website: Add support page disclaimer and sort by date added ([#8736](https://github.com/open-policy-agent/opa/pull/8736)) authored by @charlieegan3
- website: Fix build from missing dateAdded ([#8764](https://github.com/open-policy-agent/opa/pull/8764)) authored by @charlieegan3
- website: Update docusaurus ([#8756](https://github.com/open-policy-agent/opa/pull/8756)) authored by @charlieegan3
- website: Update homepage AI example to tool calls ([#8755](https://github.com/open-policy-agent/opa/pull/8755)) authored by @charlieegan3
- website: Various updates to node and website deps ([#8768](https://github.com/open-policy-agent/opa/pull/8768)) authored by @charlieegan3
- website: add ossrisk to ecosystem ([#8780](https://github.com/open-policy-agent/opa/pull/8780)) authored by @pkuzco

### Miscellaneous

- benchmarks: smaller tweaks ([#8759](https://github.com/open-policy-agent/opa/pull/8759)) authored by @srenatus
- benchmarks: split off script, emit markdown table ([#8812](https://github.com/open-policy-agent/opa/pull/8812)) authored by @srenatus
- benchmarks: use details+summary comments for benchlab results ([#8811](https://github.com/open-policy-agent/opa/pull/8811)) authored by @srenatus
- capabilities: Integrate 1.17.1 patch release ([#8798](https://github.com/open-policy-agent/opa/pull/8798)) authored by @sspaink
- chore: tidy go.mod to remove untagged versions ([#8791](https://github.com/open-policy-agent/opa/pull/8791)) authored by @thaJeztah
- e2e: Add proto schemas for the IR plan and bundle manifest ([#8766](https://github.com/open-policy-agent/opa/issues/8766)) reported and authored by @sspaink
- gha: deduplicate change-detection output in pr CI checks ([#8808](https://github.com/open-policy-agent/opa/pull/8808)) authored by @sspaink
- nightly: use regal@main ([#8735](https://github.com/open-policy-agent/opa/pull/8735)) authored by @srenatus
- workflow: remove tests from docker (edge) image build ([#8721](https://github.com/open-policy-agent/opa/pull/8721)) authored by @srenatus
- workflows: bring back docker edge tags for post-merge ([#8718](https://github.com/open-policy-agent/opa/pull/8718)) authored by @srenatus
- workflows: use `go-version-file` with `actions/setup-go` ([#8751](https://github.com/open-policy-agent/opa/pull/8751)) authored by @srenatus
- Dependency updates; notably:
    - build(deps): Add github.com/KimMachineGun/automemlimit v0.7.5
    - build(deps): Add go.uber.org/automaxprocs v1.6.0
    - build(deps): Bump github.com/dgraph-io/badger/v4 from v4.9.1 to v4.9.2
    - build(deps): Bump github.com/vektah/gqlparser/v2 from v2.5.33 to v2.5.34
    - build(deps): Bump go.opentelemetry.io/contrib/bridges/prometheus from v0.68.0 to v0.69.0
    - build(deps): Bump go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp from v0.68.0 to v0.69.0
    - build(deps): Bump go.opentelemetry.io/otel from v1.43.0 to v1.44.0
    - build(deps): Bump go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetricgrpc from v1.43.0 to v1.44.0
    - build(deps): Bump go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetrichttp from v1.43.0 to v1.44.0
    - build(deps): Bump go.opentelemetry.io/otel/exporters/otlp/otlptrace from v1.43.0 to v1.44.0
    - build(deps): Bump go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc from v1.43.0 to v1.44.0
    - build(deps): Bump go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp from v1.43.0 to v1.44.0
    - build(deps): Bump go.opentelemetry.io/otel/sdk from v1.43.0 to v1.44.0
    - build(deps): Bump go.opentelemetry.io/otel/sdk/metric from v1.43.0 to v1.44.0
    - build(deps): Bump go.opentelemetry.io/otel/trace from v1.43.0 to v1.44.0
    - build(deps): Bump golang.org/x/sync from v0.20.0 to v0.21.0
    - build(deps): Bump golang.org/x/text from v0.37.0 to v0.38.0
    - build(deps): Bump google.golang.org/grpc from v1.81.0 to v1.81.1
    - build(deps): Bump gopkg.in/ini.v1 from v1.67.2 to v1.67.3
    - build(deps): Bump oras.land/oras-go/v2 from v2.6.0 to v2.6.1
    - build(deps): bump golang.org/x/crypto to v0.52.0 and golang.org/x/net to v0.55.0 ([#8745](https://github.com/open-policy-agent/opa/pull/8745)) authored by @BGebken
    - build: bump go 1.26.3 -> 1.26.4 ([#8726](https://github.com/open-policy-agent/opa/pull/8726)) authored by @srenatus

### WebAssembly runtime: wasmtime-go replaced with wazero

OPA's WebAssembly runtime — used by the `wasm` evaluation target and the WASM SDK — now runs on
the pure-Go [wazero](https://wazero.io/) runtime instead of `bytecodealliance/wasmtime-go`. This
removes the cgo dependency from this path, so `wasm`-enabled builds no longer need a C toolchain.

Compiled policy modules are now cached process-wide, so repeated VM creation for the same policy
skips recompilation. On an Apple M4 Max this makes wasm cold start (compile + instantiate + first
eval) about 73% faster, and warm evaluation about 29% faster with ~28% fewer allocations.

One side effect worth noting: wasm linear memory is now allocated on the Go heap rather than in C,
so memory profiles and `B/op` figures for wasm evaluations account for it (it was previously
invisible to Go's allocator).

## 1.17.1

This release uses the latest version of Go (1.26.4) to build OPA, fixing stdlib vulnerabilities in
code that OPA's HTTP handler and crypto builtins use:

- https://pkg.go.dev/vuln/GO-2026-5039
- https://pkg.go.dev/vuln/GO-2026-5037

It is otherwise the same code as v1.17.0.

Note that users building their own OPA binaries and images already control the Golang
version, so this is not relevant for them.

### Miscellaneous

- build: bump go 1.26.3 -> 1.26.4 (authored by @srenatus)

## 1.17.0

This release contains a mix of new features, performance improvements, and bugfixes.  Notably:

- A new `future.keywords.not` import that adds improved semantics to the `not` keyword.
- Rule Labels in Decision Logs
- Published json schema for IR and bundle manifest
- Dropped automaxprocs and x/net dependencies

### Improved Negation Semantics ([#8387](https://github.com/open-policy-agent/opa/issues/8387))

This OPA release introduces a new [`future.keywords.not` import](https://www.openpolicyagent.org/docs/policy-reference/keywords/not#improved-negation-semantics)
that fixes a long-standing semantic issue with negation in Rego.

Without the import, the compiler expands a negated composite expression like
`not f(g(input.x))` into a series of sub-expressions evaluated *before* the
`not`:



local0

 = input.x

 

g(

local0

, 

local1

)

 

not f(

local1

)


If any sub-expression fails — for example, `input.x` is undefined or `g`
produces an undefined result — the entire rule fails rather than the `not` succeeding.
This is unintuitive: the user's intent is "the condition does not hold," but
an undefined intermediate value causes a silent failure instead of the expected
`not` result.

With `import future.keywords.not`, composite-expression negation wraps the full compiler
expansion in an implicit body:



not { 

local0

 = input.x; g(

local0

, 

local1

); f(

local1

) }


Now, if *any* sub-expression is undefined or fails, the body is unsatisfiable
and the `not` expression succeeds; matching the intuition that "the condition does not hold."

> **_NOTE:_**
>
> Users are recommended to import `future.keywords.not` whenever the `not` keyword is used in a policy.
 
Authored by @johanfylling

### Rule Labels in Decision Logs ([#2089](https://github.com/open-policy-agent/opa/issues/2089))

Rule annotations now support a `labels` field. Labels from all successfully evaluated
rules are collected and included in each decision log entry as a top-level `rule_labels`
array. Each element is the merged label map for one successfully evaluated rule, with
inner-scope-wins precedence across the rule's annotation chain
(`subpackages` < `package` < `document` < `rule`). Merged maps are deduplicated
across rules so that identical label sets collapse to a single entry.

```rego
# METADATA
# scope: package
# labels:
#   service: authz
#   severity: info
package myapp

# METADATA
# labels:
#   severity: low
#   team: platform
allow if input.role == "admin"


The resulting decision log entry will contain:

{"rule_labels": [{"service": "authz", "severity": "low", "team": "platform"}]}


json

Note how 

severity: info

 from the package scope is overridden by 

severity: low

 from

 

the rule scope. Queries against 

rule_labels

 can now rely on each entry carrying the

 

full label context for a single rule, rather than one entry per contributing scope.

Both the runtime and the Go SDK now process metadata annotations by default.

Authored by @srenatus, reported by @tsandall

Runtime, SDK, Tooling

ast: Allow 

$ref

 in 

allOf

 in JSON schemas (

#6523

https://github.com/open-policy-agent/opa/issues/6523

) authored by @deeglaze reported by @mosiac1

bundle: Update bundle roots conflict detection algorithm. (

#8664

https://github.com/open-policy-agent/opa/pull/8664

) authored by @philipaconrad

download: Use oras, not containerd (

#8639

https://github.com/open-policy-agent/opa/pull/8639

) authored by @srenatus

server: Remove dead code (s.partials) (

#8708

https://github.com/open-policy-agent/opa/pull/8708

) authored by @srenatus

server: Wire in response/request metadata for compile handler (

#8650

https://github.com/open-policy-agent/opa/pull/8650

) authored by @srenatus

server/types: generalize request/response metadata (

#8650

https://github.com/open-policy-agent/opa/pull/8650

) authored by @srenatus

Compiler, Topdown and Rego

builtins: Enable pattern validation in 

json.verify_schema

 and 

json.match_schema

 built-in functions (

#6089

https://github.com/open-policy-agent/opa/issues/6089

) authored by @sspaink reported by @ewout8

ir: Don't capitalize 

index

 field in 

MakeNumberRefStmt

 IR statement (

#6266

https://github.com/open-policy-agent/opa/issues/6266

) authored by @sspaink reported by @johanfylling

perf: Avoid allocating in binary and/or operators when possible (

#8689

https://github.com/open-policy-agent/opa/pull/8689

) authored by @anderseknert

rego: Allow per-eval 

GenerateJSON

 function (

#8690

https://github.com/open-policy-agent/opa/pull/8690

) authored by @anderseknert

Docs, Website, Ecosystem

ecosystem: add OPA MCP (

#8618

https://github.com/open-policy-agent/opa/pull/8618

) authored by @OrygnsCode

docs: Add explicit address binding to examples (

#8688

https://github.com/open-policy-agent/opa/pull/8688

) authored by @charlieegan3

docs: Add titles to code blocks in policy-testing (

#8649

https://github.com/open-policy-agent/opa/pull/8649

) authored by @charlieegan3

docs: Correct OCP SSH key docs (

#8675

https://github.com/open-policy-agent/opa/pull/8675

) authored by @taurelius

docs: Update diagram to match index examples (

#8667

https://github.com/open-policy-agent/opa/pull/8667

) authored by @charlieegan3

Miscellaneous

ast,storage/inmem: Add 

inmem.NewFromASTObject

 and add missing string case to 

ast.InternedValue

  (

#8707

https://github.com/open-policy-agent/opa/pull/8707

) authored by @anderseknert

build: 

go install

 -> 

go install tool

 to control checksums (

#8646

https://github.com/open-policy-agent/opa/pull/8646

) authored by @srenatus

build: Push edge binaries to bucket (

#8668

https://github.com/open-policy-agent/opa/pull/8668

) authored by @charlieegan3

workflows: Fix benchmarks workflow (replace action, avoid stackoverflow) (

#8655

https://github.com/open-policy-agent/opa/pull/8655

) authored by @srenatus

workflows: Note improvements in benchmark comments (

#8673

https://github.com/open-policy-agent/opa/pull/8673

) authored by @srenatus

Generate a JSON Schema for the IR plan (

#8662

https://github.com/open-policy-agent/opa/issues/8662

) authored by @sspaink reported by @kroekle

Generate a JSON Schema for the bundle manifest (

#8661

https://github.com/open-policy-agent/opa/issues/8661

) authored by @sspaink reported by @kroekle

Dependency updates; notably:

build(deps): Remove automaxprocs dependency (

#8696

https://github.com/open-policy-agent/opa/pull/8696

) authored by @anderseknert

build(deps): Remove direct x/net dependency (

#8697

https://github.com/open-policy-agent/opa/pull/8697

) authored by @anderseknert

build(deps): Bump github.com/bytecodealliance/wasmtime-go from 43.0.2 to 44.0.0 (

8652

https://github.com/open-policy-agent/opa/pull/8652

) authored by @srenatus

build(deps): Bump github.com/fsnotify/fsnotify from 1.9.0 to 1.10.1

build(deps): Bump github.com/huandu/go-sqlbuilder from 1.40.2 to 1.41.0

build(deps): Bump github.com/lestrrat-go/jwx/v3 from 3.1.0 to 3.1.1

build(deps): Bump github.com/vektah/gqlparser/v2 from 2.5.32 to 2.5.33

build(deps): Bump google.golang.org/grpc from 1.80.0 to 1.81.0

build(deps): Bump gopkg.in/ini.v1 from 1.67.1 to 1.67.2

1.16.2

This release updates the version of Go used to build the OPA binaries and images to 1.26.3;

 

addressing 

a number of vulnerabilities

https://groups.google.com/g/golang-announce/c/qcCIEXso47M

.

1.16.1

This is a patch release addressing a regression (

#8590

https://github.com/open-policy-agent/opa/pull/8590

) in the plugin manager that may cause the service to hang on shutdown.

1.16.0

This release contains a mix of new features, performance improvements, and bugfixes. Notably:

New 

uri.parse

 and 

uri.is_valid

 built-in functions

Data API Request/Response Metadata

Prometheus metrics exported via OTLP

Formatter improvements

NOTE:

In v1.15.x, OPA was dropping logs for bundle downloads, 

print()

 calls and other plugin-originated logs.

 

Users are advised to update, v1.16.0 fixes this bug in (

#8544

https://github.com/open-policy-agent/opa/pull/8544

).

New 

uri.parse

 and 

uri.is_valid

 built-in functions (

)

Two new 

built-in functions

https://www.openpolicyagent.org/docs/policy-reference/builtins

 have been added: 

uri.parse

 for parsing a given URI, and 

uri.is_valid

 for verifying the structure of a given URI.

uri.parse

Parses a URI and returns an object containing its components according to 

RFC 3986

https://www.rfc-editor.org/rfc/rfc3986.html

. Empty components are omitted.

package example

test_uri if {
	uri.parse("https://example.com:8080/api?q=1#top") == {
		"scheme": "https",
		"hostname": "example.com",
		"port": "8080",
		"path": "/api",
		"raw_path": "/api",
		"raw_query": "q=1",
		"fragment": "top",
	}
}


rego

uri.is_valid

Returns 

true

 if the input can be parsed as a URI, 

false

 otherwise.

package example

deny contains "invalid URI" if {
    not uri.is_valid("http://[invalid")
}


rego

Authored by @charlieegan3 reported by @anivar

Data API Request/Response Metadata (

)

Wrapping projects can now attach custom metadata to 

Data API

https://www.openpolicyagent.org/docs/rest-api#data-api

 requests and have evaluation produce response metadata.

Two distinct metadata paths are introduced:

Request metadata

: parsed from extra top-level keys in the request body, made available to builtins via 

BuiltinContext.RequestMetadata

. Logged in the decision log under 

Custom["request_metadata"]

.

Response metadata

: a separate map (

BuiltinContext.ResponseMetadata

) that builtins can populate during evaluation. Only included in the API response and decision log if non-empty.

In vanilla OPA, no builtins write response metadata, so responses are unchanged. The request metadata map is only allocated when the request carries extra fields; the response map is one empty map per request.

To avoid conflicts with future OPA top-level keys, callers should use a namespaced key: 

{"input": {...}, "com.example.opa/md": {...}}

.

Request with metadata:

curl -H 'Content-Type: application/json' \
  -d '{"input": {"user": "alice"}, "com.example.opa/metadata": {"corp-id": "acme-42"}}' \
  http://localhost:8181/v1/data/example/allow


bash

Response

 (response metadata included if, for example, set by a custom builtin):

{
  "decision_id": "04789f85-de5a-477b-8aa5-6d59d7742135",
  "result": true,
  "com.example.opa/response": {
    "snapshot_version": "v3"
  }
}


json

Decision log entry:

{
  "custom": {
    "request_metadata": {
      "com.example.opa/metadata": {
        "corp-id": "acme-42"
      }
    },
    "response_metadata": {
      "com.example.opa/response": {
        "snapshot_version": "v3"
      }
    }
  },
  "decision_id": "04789f85-de5a-477b-8aa5-6d59d7742135",
  "input": { "user": "alice" },
  "msg": "Decision Log",
  "path": "example/allow",
  "result": true
}


json

Authored by @srenatus

Runtime, SDK, Tooling

distributedtracing: Export Prometheus metrics via OTLP (

#7591

https://github.com/open-policy-agent/opa/issues/7591

) reported and authored by @Munken

cmd,tester: Update opa test to stream test case results (

#3676

https://github.com/open-policy-agent/opa/issues/3676

) authored by @sspaink reported by @tsandall

cmd,tester: Show full errors when test fails and using 

--coverage

 (

#8438

https://github.com/open-policy-agent/opa/pull/8438

) authored by @grosser

format: Add new line between METADATA blocks (

#8483

https://github.com/open-policy-agent/opa/pull/8483

) authored by @sspaink

format: Allow indenting all 

with

s in expression (

#8508

https://github.com/open-policy-agent/opa/pull/8508

) authored by @anderseknert

format: Fix dropping comments after handling unexpectedCommentError (

#8553

https://github.com/open-policy-agent/opa/pull/8553

) authored by @sspaink

format: Preserve location of trailing comments inside 

every

 body (

#8558

https://github.com/open-policy-agent/opa/issues/8558

) authored by @johanfylling

format: Prevent 

opa fmt

 from formatting single attribute objects with comments (

#7565

https://github.com/open-policy-agent/opa/issues/7565

) authored by @sspaink reported by @anderseknert

logging: Keep forwarding from BufferedLogger after Flush() (

#8544

https://github.com/open-policy-agent/opa/pull/8544

) authored by @srenatus reported by @annieyhuang

plugins/logs: Fix logBuffer eviction loop only dropping one element (

#8543

https://github.com/open-policy-agent/opa/pull/8543

) authored by @sspaink

plugins/logs: Fix out-of-order plugin status notifications (

#8009

https://github.com/open-policy-agent/opa/issues/8009

) authored by @sspaink reported by @Pushpalanka

plugins/rest: Carry over all of 

*tls.Config

 (

#8473

https://github.com/open-policy-agent/opa/issues/8473

) authored by @srenatus reported by @ashu2496

server: Drop HTML index page query form (

#8477

https://github.com/open-policy-agent/opa/issues/8477

) authored by @johanfylling reported by @srenatus and @r0binak

server: Skip chmod for abstract Unix domain sockets (

#8536

https://github.com/open-policy-agent/opa/pull/8536

) authored by @bakayolo

storage/inmem: Avoid allocations from Read() in MakeDir() (

#8561

https://github.com/open-policy-agent/opa/pull/8561

) authored by @srenatus

tester: Add method to match tests by ref prefixes (

#6696

https://github.com/open-policy-agent/opa/issues/6696

) authored by @anderseknert




Note: Experimental.

Compiler, Topdown and Rego

ast: Allow Back-to-back metadata blocks (

#8482

https://github.com/open-policy-agent/opa/issues/6409

) authored by @sspaink reported by @johanfylling

ast: Catch functions in dynamic extent of ref head rule (

#8461

https://github.com/open-policy-agent/opa/issues/8461

) authored by @srenatus reported by @johanfylling

ast: Fix parenthesis in String() of {obj,arr,set} comprehensions (

#8511

https://github.com/open-policy-agent/opa/pull/8511

) authored by @srenatus

ast: Fix parsing of unary 

-

 in front of a ref (

#5014

https://github.com/open-policy-agent/opa/issues/5014

) authored by @mmzzuu reported by @philipaconrad

ast: Fix type checker match error for objects with set keys (

#6260

https://github.com/open-policy-agent/opa/issues/6260

) authored by @sspaink reported by @tsandall

ast: Fix type checker to recognize numeric index in generated map (

#6736

https://github.com/open-policy-agent/opa/issues/6736

) authored by @sspaink reported by @anderseknert

ast: Handle underdetermined function args (

#5234

https://github.com/open-policy-agent/opa/issues/5234

) authored by @sspaink reported by @obataku

ast: Identify compatible type from reference in type checker (

#7273

https://github.com/open-policy-agent/opa/issues/7273

) authored by @sspaink reported by @anderseknert

ast: Support recursive JSON Schemas (

#6099

https://github.com/open-policy-agent/opa/issues/6099

) authored by @sspaink reported by @anderseknert

builtins: Add support for days, weeks and years in 

time.parse_duration_ns

 built-in function (

#2719

https://github.com/open-policy-agent/opa/issues/2719

) authored by @sspaink reported by @freeseacher

builtins: Fix 

graph.reachable_paths

 to return all reachable paths (

#5871

https://github.com/open-policy-agent/opa/issues/5871

) authored by @davidmarne-wf reported by @ericjkao

builtins: Limit exponent size in 

units.parse_bytes

 built-in function to prevent timeout bypass (

#8326

https://github.com/open-policy-agent/opa/issues/8326

) authored by @isaiahvita reported by @anderseknert

perf: Add CopyNonGround() methods for Array, Set, and Object (

#8323

https://github.com/open-policy-agent/opa/pull/8323

) authored by @alex60217101990

resolver/wasm: Add NewWithContext to allow passing context (

#8499

https://github.com/open-policy-agent/opa/pull/8499

) authored by @dominikschulz

Docs, Website, Ecosystem

docs: Add aggregates examples for 

count

 and 

sum

 built-in functions (

#8566

https://github.com/open-policy-agent/opa/pull/8566

) authored by @alliasgher reported by @srenatus

docs: Add generated output.jsons for docs examples (

#8535

https://github.com/open-policy-agent/opa/pull/8535

) authored by @charlieegan3

docs: Add spec for OCP bundle status tracking API (

#8502

https://github.com/open-policy-agent/opa/pull/8502

) authored by @ashutosh-narkar

docs: Add the latest videos to the README presentations section (

#8523

https://github.com/open-policy-agent/opa/pull/8523

) authored by @sspaink

docs: Add Windows development notes to dev reference guide (

#8422

https://github.com/open-policy-agent/opa/pull/8422

) authored by @raajheshkannaa

docs: Fix input value type in 

not

 undefined example (

#8580

https://github.com/open-policy-agent/opa/pull/8580

) authored by @menma1234

docs: Update Regal docs to v0.40.0 (

#8538

https://github.com/open-policy-agent/opa/pull/8538

) authored by @charlieegan3

docs: Updated roadmap link (

#8501

https://github.com/open-policy-agent/opa/pull/8501

) authored by @johanfylling

docs: Various typo fixes (

#8529

https://github.com/open-policy-agent/opa/pull/8529

) authored by @sspaink

ecosystem: Add vulnetix ecosystem entry (

#8532

https://github.com/open-policy-agent/opa/pull/8532

) authored by @0x73746F66

ecosystem: Add KubeStellar Console (

#8560

https://github.com/open-policy-agent/opa/pull/8560

) authored by @clubanderson

website: Add banner to show when event has passed (

#8493

https://github.com/open-policy-agent/opa/pull/8493

) authored by @charlieegan3

website: Add copy-as-markdown button to doc pages (

#8540

https://github.com/open-policy-agent/opa/pull/8540

) authored by @charlieegan3

website: Copy button improvements (

#8577

https://github.com/open-policy-agent/opa/pull/8577

) authored by @charlieegan3

website: Remove old redirects, add new management redirect (

#8424

https://github.com/open-policy-agent/opa/issues/8424

) authored by @charlieegan3 reported by @narainar

website: Update intro video on homepage (

#8547

https://github.com/open-policy-agent/opa/pull/8547

) authored by @charlieegan3

Miscellaneous

build: Exclude domains that cause false positives (#8533) (

#8495

https://github.com/open-policy-agent/opa/issues/8495

) authored by @charlieegan3

e2e/cli: Add test for debug 

print()

 logging (

#8567

https://github.com/open-policy-agent/opa/pull/8567

) authored by @srenatus

e2e/cli: Start CLI E2E tests (

#8545

https://github.com/open-policy-agent/opa/pull/8545

) authored by @srenatus

github: declare formatted rego as rego (

#8564

https://github.com/open-policy-agent/opa/pull/8564

) authored by @srenatus

Security policy update (

#8479

https://github.com/open-policy-agent/opa/pull/8479

) authored by @anderseknert

Dependency updates; notably:

build: bump go 1.26.2 (

#8497

https://github.com/open-policy-agent/opa/pull/8497

) authored by @sspaink

build(deps): bump wasmtime-go from v39.0.1 to v43.0.2

build(deps): bump go.opentelemetry.io deps from 1.40.0/0.65.0 to 1.43.0/0.68.0

build(deps): bump github.com/containerd/containerd/v2 from 2.2.1 to 2.2.3

build(deps): bump ithub.com/huandu/go-sqlbuilder from 1.39.1 to 1.40.2

build(deps): bump golang.org/x/net from 0.51.0 to 0.53.0

build(deps): bump golang.org/x/text from 0.34.0 to 0.36.0

1.15.1

This patch release fixes a backwards-incompatible change in the v1/logging.Logger interface that inadvertently made it

 

into Release v1.15.0. When using OPA as Go module, and when providing custom Logger implementations, this change would

 

break your build.

Users of the binaries or Docker images can ignore this, the code is otherwise the same as v1.15.0.

 

Miscellaneous

logging: make WithContext() optional (authored by @srenatus)


1.15.0

This release contains a mix of new features, performance improvements, and bugfixes. Notably:

Add logger plugin interface and file logger implementation with log rotation

Custom HTTPAuthPlugin behavior change, all per-request authentication logic must be moved from 

NewClient()

 to

 

Prepare()

AWS signing supports for web identity for assume role credentials

Logger Plugin Support (#8434) (authored by @srenatus)

OPA now supports pluggable logging implementations via the logger plugin interface, which is based on Go's standard 

log/slog.Handler

 interface. This allows any 

slog.Handler

 implementation to be used as a logger plugin. Loggers can be configured via the 

server.logger_plugin

 configuration option and used for both runtime logging and decision logs. OPA includes a built-in file logger plugin (

file_logger

) that writes structured JSON logs with rotation support using lumberjack. Users can also implement and register custom logger plugins when building OPA.

Example configuration for server logging:

server:
  logger_plugin: file_logger

plugins:
  file_logger:
    path: /var/log/opa/server.log
    max_size_mb: 100
    max_age_days: 28
    max_backups: 3
    compress: true
    level: info


yaml

Example configuration for decision logs using the same plugin:

server:
  logger_plugin: file_logger

decision_logs:
  plugin: file_logger

plugins:
  file_logger:
    path: /var/log/opa/server.log
    max_size_mb: 100
    max_age_days: 28
    max_backups: 3
    compress: true
    level: info


yaml

Custom HTTPAuthPlugin behavior change (#8376) (authored by @srenatus)

The 

HTTPAuthPlugin.NewClient()

 method is now called once per 

Client

 instance and cached rather than being called for

 

every request. Custom plugins that performed per-request operations in 

NewClient()

 (such as request counters,

 

per-request transport wrapping, or logging/metrics side effects) will now only execute those operations once. All

 

per-request authentication logic must be moved from 

NewClient()

 to 

Prepare()

. All plugins included in OPA have been

 

updated and are unaffected by this change.

Runtime, SDK, Tooling

plugins/logger: Add logger plugin interface and file logger implementation with log rotation (#8434) (authored by

 

@srenatus)

plugins/logs: Decision logs can now use logger plugins for output (#8434) (authored by @srenatus)

logging: Add BufferedLogger to capture early startup logs before plugins are initialized (#8434) (authored by

 

@srenatus)

plugins/rest: Configurable re-read interval for TLS client certificates via 

cert_reread_interval_seconds

 field.

 

Defaults to re-reading on every request for backwards compatibility.

 

The implementation also uses content hashing to detect changes and avoid re-parsing unchanged TLS certificates and

 

keys. (#8376) (authored by @srenatus)

plugins/rest: All TLS configurations now inherit the minimum version and TLS ciphersuites as configured for the

 

server. (#8376) (authored by @srenatus)

internal/providers/aws: Refactor deprecated crypto/elliptic APIs to crypto/ecdh (#8395) (authored by @kanywst)

plugins/rest: AWS Signing - Allow Service Account (Web Identity) credentials for Assume Role Credentials (#8386) (

 

authored by @tiagogviegas)

Compiler, Topdown and Rego

ast: fix overlapping array and scalar pattern in rule index (authored by @srenatus)

Bundles

optimized bundles: filter metadata comments properly (

 

#8388) (

#6529

https://github.com/open-policy-agent/opa/issues/6529

) authored by @srenatus

Docs, Website, Ecosystem

docs(ecosystem): add Kopa ecosystem entry (#8405) (authored by @sfreet)

docs: Update KubeCon event listing (#8439) (authored by @charlieegan3)

docs: fix input of partial-evaluation example (#8430) (authored by @edobrb)

ecosystem: add Big ACL (#8389) (authored by @francois-eckert)

Regal v0.39.0 doc updates (#8383) (authored by @anderseknert)

Miscellaneous

build/generate-extended-cases: Fix testcase loader to use json.Number. (#8429) (authored by @philipaconrad)

Filter compliance test cases using capabilities file (#8418) (authored by @sspaink)

Fix intermittent plugins manager deadlock on opa.configure (#8407) (authored by @sspaink)

Linter configuration cleanup (#8397) (authored by @anderseknert)

fix nightly.yaml by moving secret to env (#8381) (authored by @sspaink)

fix release-vulnerability-check.yaml (authored by @sspaink)

nightly+release-vuln-check: add links to slack msg payloads (authored by @srenatus)

Dependency updates; notably:

build: bump go 1.26.1 (#8409) (authored by @srenatus)

gha: bump trivy-action (authored by @srenatus)

build(deps): bump google.golang.org/grpc from 1.79.1 to 1.79.3 (#8428) (authored by @dependabot[bot])

build(deps): bump github.com/vektah/gqlparser/v2 from 2.5.31 to 2.5.32 (#8399) (authored by @dependabot[bot])

build(deps): bump modernc.org/sqlite from 1.45.0 to 1.46.1 (#8399) (authored by @dependabot[bot])

build(deps): bump golang.org/x/net from 0.50.0 to 0.51.0 (#8412) (authored by @dependabot[bot])

build(deps): bump golang.org/x/sync from 0.19.0 to 0.20.0 (#8412) (authored by @dependabot[bot])

build(deps): bump golang.org/x/time from 0.14.0 to 0.15.0 (#8412) (authored by @dependabot[bot])

build(deps): bump github.com/microsoft/go-mssqldb from 1.9.6 to 1.9.7(#8412) (authored by @dependabot[bot])

1.14.1

This is a patch release collecting two bug fixes and various dependency updates for Golang standard library and common package vulnerabilities.

These bug fixes include a revert of the rule indexer tweaks shipped in 1.14.0, which had caused unexpected lookup failures for some users. (We expect to properly fix the issue in 1.15.0, but for now, a revert is the quicker choice.)

Changes

Fix intermittent plugins manager  deadlock on opa.configure (#8407)

Revert "ast: make rule index track var assignments and 

x in {...}

 (#8341)" (#8410)

build: bump deps (go.mod from main)

build: bump go 1.26.1 (#8409)

1.14.0

This release contains a mix of new features, performance improvements, and bugfixes. Notably:

Improved rule indexing of variable assignments and 

x in {...}

 expressions

Support for 

--h2c

 with unix domain socket for 

opa run

A new glossary tooltip for technical terms in the docs

Fixes published in the v1.13.1 and v1.13.2 releases

Improved rule indexing of variable assignments and 

x in {...}

 expressions (

)

With this change, the rule indexer will index expressions like:

allow if input.role in {"admin", "user"}


rego

On lookup, the rule body will only be returned if 

input.role

 is either one of 

"admin"

 or 

"user"

.

The reverse case is also indexed:

allow if "admin" in input.roles


rego

in which the searched collection is 

unknown

.

Authored by @srenatus reported by @nischalsheth

Runtime, SDK, Tooling

cmd,run: Support 

--h2c

 with unix domain socket (UDS) (

#8282

https://github.com/open-policy-agent/opa/issues/8282

) authored by @srenatus reported by @theJC

cmd,tester: Add line number next to test file in pretty format (

#8328

https://github.com/open-policy-agent/opa/issues/8328

) authored by @sspaink reported by @anderseknert

plugins: Fix race accessing 

registeredTriggers

 (

#8363

https://github.com/open-policy-agent/opa/issues/8363

) reported and authored by @szuecs

rego: Add 

ResultValue[T]()

 helper method (

#8320

https://github.com/open-policy-agent/opa/pull/8320

) authored by @srenatus

runtime: Add custom storage backend registration API (

#8277

https://github.com/open-policy-agent/opa/issues/8277

) authored and reported by @alex60217101990

topdown: Add config option to disable named inter-query built-in cache (

#7519

https://github.com/open-policy-agent/opa/issues/7519

) authored by @sspaink reported by @johanfylling

Compiler, Topdown and Rego

ast: Add index else == nil test, fix it (

#8348

https://github.com/open-policy-agent/opa/pull/8348

) authored by @srenatus

ast: Add scaffolding to introspect and skip compiler stages (#8304) (authored by @srenatus)

ast: Ensure term values implement 

ast.StringLengther

 (

#8374

https://github.com/open-policy-agent/opa/pull/8374

) authored by @charlieegan3

ast: Fix double-fix for refs["with-a"].dash as package (

#8286

https://github.com/open-policy-agent/opa/pull/8286

) authored by @srenatus

ast: Optimized template-expression handling of values known to be defined (

#8310

https://github.com/open-policy-agent/opa/pull/8310

) authored by @anderseknert

ast: Put rule indices into rule tree, change Values to 

[]*Rule

 (

#8298

https://github.com/open-policy-agent/opa/pull/8298

) authored by @srenatus

ast: Replace 

true

 expr when appending to empty body (

#8299

https://github.com/open-policy-agent/opa/pull/8299

) authored by @anderseknert

ast: Return correct location of unsafe var in object (

#7935

https://github.com/open-policy-agent/opa/issues/7935

) authored by @sspaink reported by @anderseknert

ast: Use 

StageID

 in 

WithStageAfterID

, also for 

QueryCompiler

 (follow-up) (

#8306

https://github.com/open-policy-agent/opa/pull/8306

) authored by @srenatus

compile: Add StringLength to lazy object (

#8369

https://github.com/open-policy-agent/opa/issues/8369

) authored by @charlieegan3 reported by @robmyersrobmyers

parser: Add test to verify filename interning in Location (

#8322

https://github.com/open-policy-agent/opa/pull/8322

) authored by @anderseknert

perf: Allocate less in array unification (

#8351

https://github.com/open-policy-agent/opa/pull/8351

) authored by @anderseknert

perf: Various minor eval performance tweaks (

#8290

https://github.com/open-policy-agent/opa/pull/8290

) authored by @anderseknert

perf: 

json.patch

 + interning improvements (

#8289

https://github.com/open-policy-agent/opa/pull/8289

) authored by @anderseknert

topdown: Optimize bindings allocation with dynamic pre-sizing (

#7266

https://github.com/open-policy-agent/opa/issues/7266

) authored by @alex60217101990

topdown: Preserve original package name with special characters in optimized builds (

#8284

https://github.com/open-policy-agent/opa/issues/8284

) authored by @sspaink reported by @at50989

wasm: Updates (LLVM+tools) (

#8295

https://github.com/open-policy-agent/opa/pull/8295

) authored by @srenatus

Docs, Website, Ecosystem

docs: Add examples to 

glob.match

 built-in documentation (

#8252

https://github.com/open-policy-agent/opa/issues/8209

) authored by @sibasispadhi reported by @anderseknert

docs: Add workflow to auto update Regal docs (

#8318

https://github.com/open-policy-agent/opa/pull/8318

) authored by @charlieegan3

docs: Document metrics for 

http.send

, 

regex

, and 

glob

 built-ins (

#6730

https://github.com/open-policy-agent/opa/issues/6730

) authored by @anivar reported by @rudrakhp

docs: Fix 

json.patch

 target description (

#8271

https://github.com/open-policy-agent/opa/pull/8271

) authored by @anderseknert

docs: Update broken links (

#8285

https://github.com/open-policy-agent/opa/pull/8285

) authored by @charlieegan3

docs: Update bundle signing docs to clarify key config (

#8307

https://github.com/open-policy-agent/opa/pull/8307

) authored by @charlieegan3

docs: Update faulty example using bundle optimize (

#5379

https://github.com/open-policy-agent/opa/issues/5379

) authored by @sspaink reported by @bluebrown

docs: Update 

interface{}

 -> 

any

 in golang snippets (

#8373

https://github.com/open-policy-agent/opa/pull/8373

) authored by @srenatus

docs/website: Add a new KubeCon event page (

#8311

https://github.com/open-policy-agent/opa/pull/8311

) authored by @charlieegan3

docs/website: Add formatting and linting checks (

#8288

https://github.com/open-policy-agent/opa/pull/8288

) authored by @charlieegan3

docs/website: Allow Regal import to use local dir (

#8312

https://github.com/open-policy-agent/opa/pull/8312

) authored by @charlieegan3

docs/website: Implement new GlossaryTooltip component (

#8367

https://github.com/open-policy-agent/opa/pull/8367

) authored by @charlieegan3

docs/website: Markdown linting and spell checking for documentation (

#8292

https://github.com/open-policy-agent/opa/pull/8292

) authored by @charlieegan3

docs/website: Redirect /docs/latest/ecosystem (

#8315

https://github.com/open-policy-agent/opa/issues/8315

) authored by @charlieegan3 reported by @tweekSun1

Miscellaneous

maintainers: Moving nilekhc to emeritus, and renew maintainer terms (

#8276

https://github.com/open-policy-agent/opa/pull/8276

) authored by @JaydipGabani

ast: Add public method to extend the compliance test cases with IR plans (

#7556

https://github.com/open-policy-agent/opa/issues/7556

) authored by @sspaink reported by @shomron

ast: Tiny nitpicky cleanup (

#8309

https://github.com/open-policy-agent/opa/pull/8309

) authored by @srenatus

chore: Clean up bundle storage tests (

#8267

https://github.com/open-policy-agent/opa/pull/8267

) authored by @anderseknert

chore: Remove unnecessary comment from bundle JWT verification impl (

#8354

https://github.com/open-policy-agent/opa/pull/8354

) authored by @johanfylling

ci: Bump golangci-lint (v2.9.0), fix issues (

#8314

https://github.com/open-policy-agent/opa/pull/8314

) authored by @srenatus

ci: Harden and update all GH Actions workflows (

#8356

https://github.com/open-policy-agent/opa/pull/8356

, 

#8377

https://github.com/open-policy-agent/opa/pull/8377

, 

#8368

https://github.com/open-policy-agent/opa/pull/8368

 authored by @philipaconrad and @srenatus

go: Cleanup old build flags (

#8314

https://github.com/open-policy-agent/opa/pull/8314

) authored by @srenatus

rego: Remove superfluous package import of plugins (

#6754

https://github.com/open-policy-agent/opa/issues/6754

) authored by @srenatus reported by @oxisto

tests: Extract runtime Info to new package (

#8362

https://github.com/open-policy-agent/opa/pull/8362

) authored by @charlieegan3

tests: Fix 

BenchmarkFunctionArgumentCounts

 query (

#8327

https://github.com/open-policy-agent/opa/pull/8327

) authored by @alex60217101990

tests: Disable rule indexing for benchmark (

#8375

https://github.com/open-policy-agent/opa/pull/8375

) authored by @srenatus

workflows: Add nightly vuln checks for released versions/images (

#8336

https://github.com/open-policy-agent/opa/pull/8336

 

#8339

https://github.com/open-policy-agent/opa/pull/8339

) authored by @srenatus

Dependency updates; notably:

build: bump golang from 1.25.6 to 1.26.0

build(deps): build(deps): bump go.opentelemetry.io deps from 1.39.0/0.64.0 to 1.40.0/0.65.0




Applying fix for 

GHSA-9h8m-3fm2-qjrq

https://github.com/advisories/GHSA-9h8m-3fm2-qjrq

build(deps): bump github.com/dgraph-io/badger/v4 from 4.9.0 to 4.9.1

build(deps): bump github.com/huandu/go-sqlbuilder from 1.39.0 to 1.39.1

build(deps): bump golang.org/x/net from 0.49.0 to 0.50.0

build(deps): bump golang.org/x/text from 0.33.0 to 0.34.0

build(deps): bump google.golang.org/grpc from 1.78.0 to 1.79.1

build(deps): bump go.opentelemetry.io deps from 1.39.0/0.64.0 to 1.40.0/0.65.0

1.13.2

This release updates the version of Go used to build the OPA binaries and images to 1.25.7.

 

That version of the Go standard library contains a fix for 

GO-2026-4337

https://pkg.go.dev/vuln/GO-2026-4337

.

1.13.1

This bug fix release addresses an issue found in the new 

array.flatten

 built-in function

Fix issue in 

array.flatten

 handling of single item arrays (

 

#8273) (

#8272

https://github.com/open-policy-agent/opa/issues/8272

) authored by @anderseknert

1.13.0

This release contains a mix of new features, performance improvements, and bugfixes. Notably:

A new 

immediate

 upload trigger mode

A new 

array.flatten

 built-in function

Numerous performance improvements

Immediate Upload Trigger Mode in Decision Logger (

)

An 

immediate

 trigger mode has been added to the Decision Logger; enabled by setting the 

decision_logs.reporting.trigger

 

configuration option

https://www.openpolicyagent.org/docs/configuration#decision-logs

 to 

immediate

.

 

When enabled, log events are pushed to the log service as soon as the configured upload chunk size criteria is met; or, at latest, when the configured upload delay is reached.

Authored by @sspaink

Runtime, SDK, Tooling

cmd/fmt: Do not overwrite file on 

fmt

 without changes (

#8222

https://github.com/open-policy-agent/opa/issues/8222

) authored by @Loic-R

cmd/test: Enable sorting JSON test results by duration (

#7444

https://github.com/open-policy-agent/opa/issues/7444

) authored by @sspaink

profiler: 

nil

 

*Profiler

 should not report 

Enabled()

 (

#8256

https://github.com/open-policy-agent/opa/pull/8256

) authored by @anderseknert

rego: Add Data function to simplify adding data from map (

#5961

https://github.com/open-policy-agent/opa/issues/5961

) authored by @majiayu000 reported by @anderseknert

runtime: Correct naming & docs for version checking (

#8191

https://github.com/open-policy-agent/opa/pull/8191

) authored by @charlieegan3

Compiler, Topdown and Rego

ast: 

Body.String()

 doesn't panic on empty body (

#8244

https://github.com/open-policy-agent/opa/pull/8244

) authored by @srenatus

ast: Improve type error message when referencing functions (

#6840

https://github.com/open-policy-agent/opa/issues/6840

) authored by @sspaink

ast: Type Checker recognizes when a variable has multiple assignments but is an undefined function (

#7463

https://github.com/open-policy-agent/opa/issues/7463

) authored by @sspaink reported by @anderseknert

ast/parser: Avoid duplicate loc copies (

#8142

https://github.com/open-policy-agent/opa/pull/8142

) authored by @srenatus

topdown: Add 

array.flatten

 built-in function (

#8226

https://github.com/open-policy-agent/opa/issues/8226

) authored by @anderseknert

topdown: Fix issue where 

numbers.range_step

 built-in could erroneously return 

undefined

 value (

#8194

https://github.com/open-policy-agent/opa/pull/8194

) authored by @thevilledev

topdown: Remove hard-coded missing key error in 

strings.render_template

 built-in (

#7931

https://github.com/open-policy-agent/opa/issues/7931

) authored by @colinjlacy reported by @anderseknert

topdown: Re-introduce cancellation-awareness for 

regex.replace

 built-in (

#8179

https://github.com/open-policy-agent/opa/pull/8179

) authored by @srenatus




from having been reverted in v1.12.1

topdown: Support arrays as input for 

json.match_schema

 (

#6615

https://github.com/open-policy-agent/opa/issues/6615

) authored by @sspaink reported by @mscudlik

Performance

ast: Improved annotations parsing (

#8210

https://github.com/open-policy-agent/opa/pull/8210

) authored by @anderseknert

ast: Reinstate zero-alloc paths in 

Ref.String()

 (

#8202

https://github.com/open-policy-agent/opa/pull/8202

) authored by @anderseknert

ast: Replace regex implementation in 

IsVarCompatibleString

 (

#8164

https://github.com/open-policy-agent/opa/pull/8164

) authored by @anderseknert

ast: Optimize 

Set.Intersect

 and 

Set.Diff

 (

#8167

https://github.com/open-policy-agent/opa/pull/8167

) authored by @thevilledev

ast: Optimize 

Set.Union

 (

#8172

https://github.com/open-policy-agent/opa/pull/8172

) authored by @thevilledev

ast: Reduce allocations in 

Expr.MarshalJSON

 (

#8204

https://github.com/open-policy-agent/opa/pull/8204

) authored by @thevilledev

ast: Reduce allocations in 

Rule.MarshalJSON

 (

#8205

https://github.com/open-policy-agent/opa/pull/8205

) authored by @thevilledev

ast: Reduce allocations in 

Term.MarshalJSON

 (

#8200

https://github.com/open-policy-agent/opa/pull/8200

) authored by @thevilledev

ast: Reduce allocations in 

With.MarshalJSON

 (

#8206

https://github.com/open-policy-agent/opa/pull/8206

) authored by @thevilledev

perf: 

String()

 implementations using appenders (

#8192

https://github.com/open-policy-agent/opa/pull/8192

) authored by @anderseknert

topdown: Avoid redundancy in builtinTrim (

#8237

https://github.com/open-policy-agent/opa/pull/8237

) authored by @thevilledev

topdown: Eliminate closure allocations in Set and virtual doc enumeration (

#8242

https://github.com/open-policy-agent/opa/pull/8242

) authored by @alex60217101990

topdown: Fast paths for 

array.reverse

 (

#8177

https://github.com/open-policy-agent/opa/pull/8177

) authored by @thevilledev

topdown: Optimize 

json.remove

 and 

json.filter

 (

#8193

https://github.com/open-policy-agent/opa/pull/8193

) authored by @thevilledev

topdown: Optimize 

object

 built-ins (

#8175

https://github.com/open-policy-agent/opa/pull/8175

) authored by @thevilledev

topdown: Optimize 

union

 built-in (

#8173

https://github.com/open-policy-agent/opa/pull/8173

) authored by @thevilledev

topdown: Pre-alloc in various built-ins (

#8198

https://github.com/open-policy-agent/opa/pull/8198

) authored by @thevilledev

topdown: Reduce allocs in float sum/product (

#8235

https://github.com/open-policy-agent/opa/pull/8235

) authored by @thevilledev

topdown: Skip set copy in 

getObjectKeysParam

 (

#8176

https://github.com/open-policy-agent/opa/pull/8176

) authored by @thevilledev

Docs, Website, Ecosystem

docs: Add authz-spring-boot-starter to Spring Security API ecosystem entry (

#8234

https://github.com/open-policy-agent/opa/pull/8234

) authored by @francois-eckert

docs: Add header for crypto example to make (

#8259

https://github.com/open-policy-agent/opa/pull/8259

) authored by @charlieegan3

docs: Add notes for automated agents (

#8147

https://github.com/open-policy-agent/opa/pull/8147

, 

#8203

https://github.com/open-policy-agent/opa/pull/8203

) authored by @charlieegan3

docs: Add opa-wasm-zig to the ecosystem (

#8163

https://github.com/open-policy-agent/opa/pull/8163

) authored by @burdzwastaken

docs: Add scripts to import docs from source (

#8148

https://github.com/open-policy-agent/opa/pull/8148

) authored by @charlieegan3

docs: Explain how to use the SDK without a initialising a server (

#8248

https://github.com/open-policy-agent/opa/pull/8248

) authored by @andrewcameronsims

docs: Fix a number of redirecting links (

#8165

https://github.com/open-policy-agent/opa/issues/8165

 authored by @charlieegan3

docs: Fix template-expression examples (

#8199

https://github.com/open-policy-agent/opa/pull/8199

) authored by @johanfylling

docs/ocp: Mention source prefix/path options (

#8238

https://github.com/open-policy-agent/opa/pull/8238

) authored by @srenatus

website: Add redirect section for immutable referrers (

#8262

https://github.com/open-policy-agent/opa/issues/8262

) authored by @charlieegan3 reported by @KraLeoD

website: Display 2025 survey results on the website (

#8258

https://github.com/open-policy-agent/opa/pull/8258

) authored by @charlieegan3

website: Show breadcrumbs in search results (

#8207

https://github.com/open-policy-agent/opa/pull/8207

) authored by @charlieegan3

Miscellaneous

Decoupled the Rego job check from the Go job checks in the Github PR workflow (

#8203

https://github.com/open-policy-agent/opa/pull/8203

) authored by @SeanLedford

build: Format 

pr_check.rego

 with 

opa fmt

 (

#8201

https://github.com/open-policy-agent/opa/pull/8201

) authored by @thevilledev

build: Migrate PR check to OPA policy (

#8183

https://github.com/open-policy-agent/opa/pull/8183

) authored by @SeanLedford

build: Run 

go get

 against 

main

 to spot redacted (

#8146

https://github.com/open-policy-agent/opa/pull/8146

) authored by @charlieegan3

deps: Switch to maintained 

go.yaml.in/yaml/v3

 yaml library (

#8182

https://github.com/open-policy-agent/opa/pull/8182

) authored by @mrueg

test/cases: Increase yaml test coverage for some regex and string builtins (

#8152

https://github.com/open-policy-agent/opa/pull/8152

) authored by @srenatus

Dependency updates; notably:

build: bump golang from 1.25.5 to 1.25.6 (

#8224

https://github.com/open-policy-agent/opa/pull/8224

) authored by @srenatus

build(deps): bump go.opentelemetry.io deps from 1.38.0/0.63.0 to 1.39.0/0.64.0

build(deps): bump klauspost/compress from v1.18.1 to v1.18.2 (

#8184

https://github.com/open-policy-agent/opa/pull/8184

) authored by @srenatus




because of redaction warning

build(deps): bump github.com/go-ini/ini from v1.67.0 to gopkg.in/ini.v1 v1.67.1 (

#8208

https://github.com/open-policy-agent/opa/issues/8208

) authored by @gabrpt

1.12.3

This is a bug fix release addressing two issues:

Bundle polling is being misconfigured when discovery bundle is updated (

)

This is an issue where the polling interval for discovery (

discovery.polling.min_delay_seconds

 and

 

discovery.polling.max_delay_seconds

) were misinterpreted on reconfiguration, causing extremely long update intervals.

Reported by @loganmiller-chime, authored by @sspaink

Decision log 

size

 buffer

buffer_size_limit_bytes

 misconfigured during reconfiguration (

#8213

https://github.com/open-policy-agent/opa/pull/8213

)

This is a regression in the decision log, where the 

decision_logs.reporting.buffer_size_limit_bytes

 was mistakenly

 

assigned the value of 

decision_logs.reporting.upload_size_limit_bytes

 during reconfiguration.

 

This issue is only present when 

decision_logs.reporting.buffer_type

 is set to 

size

, which is the default value.

Authored by @sspaink

1.12.2

This bug fix release address issues found in the new string interpolation feature

Add (*TemplateString).Copy() method (#8159) authored by @anderseknert

Fix template string not serialized with escaped { (#8161) authored by @anderseknert

fix(ast): skip template string vars in ref safety (#8174) authored by @thevilledev

fix(ast): use original var names in template error (#8180) authored by @thevilledev

1.12.1

This bug fix release reverts a change to 

regex.replace

 that unintentionally changed its behaviour for anchored regular expressions.

Revert "topdown: make 

regex.replace

 respect cancellation" (authored by @srenatus)

1.12.0

This release contains a mix of new features, performance improvements, and bugfixes. Notably:

Support for string interpolation in the Rego language

Faster compilation and runtime

Fixes published in the v1.11.1 release

String Interpolation (

)

The Rego language has been extended to support 

String Interpolation

https://www.openpolicyagent.org/docs/policy-language#string-interpolation

,

 

which provides a readable means to compose strings containing dynamic values determined at evaluation time.

An interpolated string is composed of a template-string containing zero or more template-expressions that evaluates to a value at evaluation time.

 

The 

$

 character prefix identifies a template-string, and template-expressions are declared by being enclosed in curly-braces (

{

, 

}

).

Additionally, 

undefined

 template-expression values don't halt evaluation; instead, 

<undefined>

 will be injected into the generated string.

package interpolation

allowed_roles := ["admin", "employee"]

default role := "guest"
role := input.role

deny contains $"User {input.username}'s role was '{role}', but must be one of {allowed_roles}" if {
  not role in allowed_roles
}


rego

{
  "deny": [
    "User <undefined>'s role was 'guest', but must be one of [\"admin\", \"employee\"]"
  ],
}


String interpolation is a more readable and less error-prone substitute for the 

sprintf

 built-in function.

Authored by @johanfylling reported by @anderseknert

Help us out!

New Rego language features are exciting, and we want to maximize their usefulness. If you come across tools and integrations in the community where string interpolation isn't properly handled, such as syntax highlighting, please 

reach out

https://www.openpolicyagent.org/community

 and let us know.

Runtime, SDK, Tooling

oracle: Refactor Oracle better support 

some

 and 

every

 (

#8105

https://github.com/open-policy-agent/opa/pull/8105

, 

#8131

https://github.com/open-policy-agent/opa/pull/8131

, 

#8138

https://github.com/open-policy-agent/opa/pull/8138

) authored by @charlieegan3

plugins/bundle: Prevent ns-level polling by validating intervals (

#8082

https://github.com/open-policy-agent/opa/pull/8082

) authored by @jjhwan-h

plugins/discovery: Initialize plugins before downloading (

#8071

https://github.com/open-policy-agent/opa/pull/8071

) authored by @jt28828

topdown: Introduce sink for context cancellation

topdown: Make 

regex.replace

 respect cancellation (

#8089

https://github.com/open-policy-agent/opa/pull/8089

) authored by @srenatus

topdown: Make 

replace

 and 

strings.replace_n

 respect cancellation (

#8089

https://github.com/open-policy-agent/opa/pull/8089

) authored by @srenatus

topdown: Use sink for 

concat

 (

#8090

https://github.com/open-policy-agent/opa/pull/8090

) authored by @srenatus

perf: Avoid extra allocation in sink if no cancel (

#8104

https://github.com/open-policy-agent/opa/pull/8104

) authored by @anderseknert

Compiler, Topdown and Rego

ast/compile: Deal with error limit without panic/defer (

#8087

https://github.com/open-policy-agent/opa/pull/8087

) authored by @srenatus

ast/parser: Check if we need to unescape at all (

#8135

https://github.com/open-policy-agent/opa/pull/8135

) authored by @srenatus

perf: Improved visitor implementation (10% faster compilation) (

#8078

https://github.com/open-policy-agent/opa/pull/8078

) authored by @anderseknert

perf: Reduce allocations handling terms (

#8116

https://github.com/open-policy-agent/opa/pull/8116

) authored by @anderseknert

perf: Type-checker performance improvements (

#8143

https://github.com/open-policy-agent/opa/pull/8143

) authored by @anderseknert

Docs, Website, Ecosystem

website: Add support for rego string interpolation syntax highlighting (

#8092

https://github.com/open-policy-agent/opa/pull/8092

) authored by @charlieegan3

docs/ocp: Update "concepts" for v0.3.0 (

#8117

https://github.com/open-policy-agent/opa/pull/8117

) authored by @srenatus

website: Show playground errors (

#8141

https://github.com/open-policy-agent/opa/pull/8141

) authored by @charlieegan3

website: Update a number of links to their new location (

#8100

https://github.com/open-policy-agent/opa/pull/8100

) authored by @charlieegan3

docs: Remove link to feedback form (

#8101

https://github.com/open-policy-agent/opa/pull/8101

) authored by @charlieegan3

website: Remove survey bar (

#8136

https://github.com/open-policy-agent/opa/pull/8136

) authored by @charlieegan3

docs: Update community contacts (

#8108

https://github.com/open-policy-agent/opa/pull/8108

) authored by @charlieegan3

Miscellaneous

ast/checks_test: Fix flaky tests (

#8111

https://github.com/open-policy-agent/opa/pull/8111

) authored by @srenatus

benchmarks: Install node v24 (

#8122

https://github.com/open-policy-agent/opa/pull/8122

) authored by @srenatus

download: Fix when compiling with tag opa_no_oci (

#8070

https://github.com/open-policy-agent/opa/issues/8070

) authored by @srenatus reported by @mg0083

tests: Race in TestStatusUpdateBuffer (

#8133

https://github.com/open-policy-agent/opa/pull/8133

) authored by @thevilledev

workflow: Integrate benchmarks notebook (

#8121

https://github.com/open-policy-agent/opa/pull/8121

) authored by @srenatus

workflows: Skip all tests in benchmarks run (

#8086

https://github.com/open-policy-agent/opa/pull/8086

) authored by @srenatus

Dependency updates; notably:

build: Bump golang from 1.25.4 to 1.25.5 (

#8107

https://github.com/open-policy-agent/opa/pull/8107

) authored by @srenatus

build(deps): Bump google.golang.org/grpc from 1.76.0 to 1.77.0

1.11.1

This is a bugfix release:

Memory exhaustion via forged gzip header

A crafted HTTP request any of OPA's HTTP endpoints would lead OPA to use a large amount of memory, triggering

 

an out-of-memory process exit.

This weakness in OPA's HTTP API gzip handling is as old as the gzip handling itself.

 

A configurable limit was introduced in v0.67.0

https://github.com/open-policy-agent/opa/blob/v0.67.0/CHANGELOG.md#request-body-size-limits

, but it has been shown that this security measure wasn't sufficient to avoid running out of memory in memory-constrained setups.

 

Thanks to @thevilledev for reporting and fixing this issue.

It only applies to OPA running as server (as a binary or in a container, as "sidecar").

 

To trigger an OOM process exit using this weakness, an adversary must be able to send an HTTP request directly to OPA.

 

This would be the case if they are in the same network, there is no proxy in front of OPA, or if OPA was exposed to the internet, which is advised against.

By the nature of HTTP encodings, this would be effective 

before

 

token-based authentication

 and 

authorization policies

, so these measures do not protect against the attack vector.

 

If all OPA endpoints are using 

TLS-based authentication

https://www.openpolicyagent.org/docs/security#tls-based-authentication-example

 (mutual TLS, "mTLS"), then an adversary cannot do harm with this method.

Please note that while we're taking all of these issues seriously, OPA isn't designed for adversary environments.

 

It's strongly advised not to expose any of its endpoints to the public internet.

 

Furthermore, available security measures should be applied 

regardless

, for a defense in depth approach.

 

See the documentation for the available means of authentication and authorization in OPA.

https://www.openpolicyagent.org/docs/security

Please also check out our 

Security Policy

https://www.openpolicyagent.org/security

 for reporting critical issues and bugs.

Decision Logs dropped (introduced in OPA v1.9.0)

When the decision logs buffer was uploaded, the buffer limit inadvertently got reset to the default upload limit (32kb).

 

This causes logs to be dropped that shouldn't have been dropped.

This default is overridden by the configuration value 

decision_logs.reporting.upload_size_limit_bytes

, see 

the docs on decision logs

https://www.openpolicyagent.org/docs/configuration#decision-logs

.

There's a Prometheus metric for dropped events, 

counter_decision_logs_dropped_buffer_size_limit_bytes_exceeded

,

 

and you can check that for unexpectedly high counts.

Reported by @johanneslarsson 

#8123

https://github.com/open-policy-agent/opa/issues/8123

, fixed by @sspaink.

The release is otherwise identical to v1.11.0.

1.11.0

This release contains a mix of new features, performance improvements, and bugfixes. Notably:

More efficient connection management in the 

http.send

 built-in function

More performant loading of large bundles containing multiple Rego files

Immutable Releases

Starting with this release, OPA releases are 

immutable

https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/immutable-releases

 for increased security.

Runtime, SDK, Tooling

v1/ast: Fix Call parsing Text attribute including an extra character (

#7989

https://github.com/open-policy-agent/opa/issues/7989

) authored by @schmitd

ast: Export built-in deprecated field (

#7912

https://github.com/open-policy-agent/opa/issues/7912

) authored by @colinjlacy

ast: Intern common var values + some parser improvements (

#8028

https://github.com/open-policy-agent/opa/pull/8028

) authored by @anderseknert

ast: Support custom builtins in CompileModulesWithOpt (

#8061

https://github.com/open-policy-agent/opa/issues/5580

) authored by @sspaink

bundle: Concurrent Rego parsing in bundle loader (

#8067

https://github.com/open-policy-agent/opa/pull/8067

) authored by @anderseknert

cmd: Support 

--ignore

 in 

eval

 cmd when using bundle flag (

--bundle

) (

#8062

https://github.com/open-policy-agent/opa/pull/8048

) authored by @sspaink

storage/inmem: Allow passing triggers (AST) data without conversion (

#7958

https://github.com/open-policy-agent/opa/issues/7958

) authored by @anderseknert

Compiler, Topdown and Rego

topdown: Avoid unnecessary use of custom 

http.Transport

 in 

http.send

 built-in (

#7927

https://github.com/open-policy-agent/opa/pull/7927

) authored by @sykesm

topdown: New custom SemVer implementation (

#8010

https://github.com/open-policy-agent/opa/pull/8010

) authored by @anderseknert

topdown: Use 

sync.Pool

 for eval func objects (

#8054

https://github.com/open-policy-agent/opa/pull/8054

) authored by @anderseknert

Docs, Website, Ecosystem

docs: Add example for Compile API's table mapping (

#8017

https://github.com/open-policy-agent/opa/pull/8017

) authored by @srenatus

docs: Address pages with similar titles (

#8046

https://github.com/open-policy-agent/opa/pull/8046

) authored by @charlieegan3

docs: Address some broken links (

#8022

https://github.com/open-policy-agent/opa/pull/8022

) authored by @charlieegan3

docs: Bump glob dep (CVE-2025-64756) (

#8056

https://github.com/open-policy-agent/opa/pull/8056

) authored by @srenatus

docs: Improve ground value and assignment docs (

#8047

https://github.com/open-policy-agent/opa/pull/8047

) authored by @charlieegan3

docs: Make iteration content flow better (

#8064

https://github.com/open-policy-agent/opa/pull/8064

) authored by @charlieegan3

docs: Note package repos are community maintained (

#8053

https://github.com/open-policy-agent/opa/pull/8053

) authored by @charlieegan3

docs: Update terraform guide with notes about plan (

#8043

https://github.com/open-policy-agent/opa/pull/8043

) authored by @charlieegan3

docs: Update the archive to have an edge link (

#8011

https://github.com/open-policy-agent/opa/pull/8011

) authored by @charlieegan3

docs: Update the policy language intro (

#8050

https://github.com/open-policy-agent/opa/pull/8050

) authored by @charlieegan3

docs/ocp: Datasource example uses wrong AWS S3 URL (

#8039

https://github.com/open-policy-agent/opa/pull/8039

) authored by @SuchSkill

docs/regal: Replicate sidebar fixes (

#8036

https://github.com/open-policy-agent/opa/pull/8036

) authored by @charlieegan3

website: Various fixes and improvements by @charlieegan3

Miscellaneous

Bump golangci-lint, more gocritic linters (

#8052

https://github.com/open-policy-agent/opa/pull/8052

) authored by @anderseknert

Tidy up and unify sync pool handling (

#8068

https://github.com/open-policy-agent/opa/pull/8068

) authored by @anderseknert

builtins: Add 

StringOperandByteSlice

 helper (

#8048

https://github.com/open-policy-agent/opa/pull/8048

) authored by @anderseknert

test: Add test cases for consistent cache behavior (

#8015

https://github.com/open-policy-agent/opa/pull/8015

) authored by @DFrenkel

util/performance: Remove math.Log10, remove unused KeysCount (

#8041

https://github.com/open-policy-agent/opa/pull/8041

) authored by @srenatus

workflow: Add 

Benchmarks

 workflow (

#8072

https://github.com/open-policy-agent/opa/pull/8072

) authored by @srenatus

workflows/pull-request: Update macos versions (

#8030

https://github.com/open-policy-agent/opa/pull/8030

) authored by @srenatus

Dependency updates; notably:

build: golang 1.25.3 -> 1.25.4 (

#8051

https://github.com/open-policy-agent/opa/pull/8051

) authored by @srenatus

build(deps): Bump github.com/bytecodealliance/wasmtime-go from v37.0.0 to v39.0.1 (

#8075

https://github.com/open-policy-agent/opa/pull/8075

) authored by @srenatus

build(deps): Bump github.com/containerd/containerd/v2 from 2.1.4 to 2.2.0

build(deps): Bump github.com/huandu/go-sqlbuilder from 1.37.0 to 1.38.1

build(deps): Bump github.com/lestrrat-go/jwx/v3 from 3.0.11 to 3.0.12

build(deps): Bump github.com/vektah/gqlparser/v2 from 2.5.30 to 2.5.31 (

#8027

https://github.com/open-policy-agent/opa/pull/8027

) authored by @johanfylling

build(deps): Bump golang.org/x/crypto from 0.43.0 to 0.45.0

build(deps): Bump golang.org/x/net from 0.44.0 to 0.45.0

build(deps): Bump golang.org/x/time from 0.13.0 to 0.14.0

build(deps): Bump google.golang.org/grpc from 1.75.1 to 1.76.0

build(deps): Bump google.golang.org/protobuf from 1.36.9 to 1.36.10

1.10.1

This is a bugfix release for the 

split

 builtin: In v1.10.0, it was looping infinitely when used with an empty-string delimiter (

#8018

https://github.com/open-policy-agent/opa/issues/8018

).

Reported by @SignalRichard, authored by @srenatus

The release is otherwise identical to v1.10.0.

1.10.0

This release contains a mix of new features, performance improvements, and bugfixes. Notably:

Non-static arm64 executables for linux and darwin

Performance improvements to the formatter, compiler, and runtime

A new 

--fail-on-empty

 flag for 

opa test

Support for 

IS NOT NULL

 query statements in the Compile API

Non-static OPA binaries for linux/arm64 and darwin/arm64

Starting with this release, OPA will ship non-static arm64 executables for linux and darwin.

 

Furthermore, the openpolicyagent/opa:latest docker image is a multi-platform image with arm64 support.

Runtime, Tooling

cmd: Add 

opa test --fail-on-empty

 to allow making bad 

-r

 or empty folders fail (

#7943

https://github.com/open-policy-agent/opa/issues/7943

) reported and authored by @grosser

format: Performance improvements in formatter (

#7967

https://github.com/open-policy-agent/opa/pull/7967

) authored by @anderseknert

repl: Check usage of 

with

 keyword (

#7942

https://github.com/open-policy-agent/opa/pull/7942

) authored by @sspaink

server/failtracer: don't assume only being fed two-elem calls (

#7995

https://github.com/open-policy-agent/opa/pull/7995

) authored by @srenatus

storage: Improve performance of storage operations (

#7957

https://github.com/open-policy-agent/opa/pull/7957

) authored by @anderseknert

storage: Some small improvements to inmem storage (

#7944

https://github.com/open-policy-agent/opa/pull/7944

) authored by @anderseknert

util: Fix race condition in 

ReadMaybeCompressedBody

 (

#7966

https://github.com/open-policy-agent/opa/pull/7966

) authored by @anderseknert

Compiler, Topdown and Rego

ast: Fix 

undeclared

 error when printing nested comprehension (

#7647

https://github.com/open-policy-agent/opa/issues/7647

) authored by @schmitd reported by @charlesdaniels

ast: Raise parse error on infix operator in rule name (

#7433

https://github.com/open-policy-agent/opa/issues/7433

) authored by @mmzzuu

ast: Refactor hash key equality function (

#7969

https://github.com/open-policy-agent/opa/pull/7969

) authored by @anderseknert

ast,topdown: Ref String() and greatly improved builtin lookup cost (

#7961

https://github.com/open-policy-agent/opa/pull/7961

) authored by @anderseknert

compile: Add support for "any value at all", as IS NOT NULL (

#7998

https://github.com/open-policy-agent/opa/pull/7998

) authored by @srenatus

eval: Lazy init of 

eval.Time

 term (

#7968

https://github.com/open-policy-agent/opa/pull/7968

) authored by @anderseknert

perf: Zero alloc AST store lookups of interned path terms (

#7979

https://github.com/open-policy-agent/opa/pull/7979

) authored by @anderseknert

perf: Cheaper 

split

 built-in calls (

#7962

https://github.com/open-policy-agent/opa/pull/7962

) authored by @anderseknert

Docs, Website, Ecosystem

docs: Add Compile API data filtering docs (

#7939

https://github.com/open-policy-agent/opa/pull/7939

) authored by @srenatus

docs: Add ecosystem project Moat (

#7963

https://github.com/open-policy-agent/opa/pull/7963

) authored by @jcoenraadts

docs: Address broken anchors (

#8000

https://github.com/open-policy-agent/opa/pull/8000

) authored by @charlieegan3

docs: Correction in OCP docs information regarding supported datasources (

#7964

https://github.com/open-policy-agent/opa/pull/7964

) authored by @irodzik

docs: Moving 

CLI Reference

 to 

Operations

 in TOC (

#8001

https://github.com/open-policy-agent/opa/pull/8001

) authored by @johanfylling

docs: OCP HTTP API updates (

#7951

https://github.com/open-policy-agent/opa/pull/7951

) authored by @srenatus

docs: Remove k8s primer line numbers comments (

#7946

https://github.com/open-policy-agent/opa/pull/7946

) authored by @charlieegan3

docs: Update based on Slack feedback (

#7990

https://github.com/open-policy-agent/opa/pull/7990

) authored by @charlieegan3

docs: Update link checker config (

#7949

https://github.com/open-policy-agent/opa/pull/7949

) authored by @charlieegan3

docs: Updated AI guidelines (

#7945

https://github.com/open-policy-agent/opa/pull/7945

) authored by @charlieegan3

docs/ocp/deployment: Add segment on database migrations (

#7952

https://github.com/open-policy-agent/opa/pull/7952

) authored by @srenatus

website: Fix build issues (

#7999

https://github.com/open-policy-agent/opa/pull/7999

) authored by @charlieegan3

website: FOUC squashing on the homepage (

#7948

https://github.com/open-policy-agent/opa/pull/7948

) authored by @charlieegan3

website: Show latest release rather than edge (

#7988

https://github.com/open-policy-agent/opa/pull/7988

) authored by @charlieegan3

website: Update docusaurus (

#7947

https://github.com/open-policy-agent/opa/pull/7947

) authored by @charlieegan3

Miscellaneous

ast/capabilities: Remove stale comment (

#7994

https://github.com/open-policy-agent/opa/pull/7994

) authored by @srenatus

build: Non-static images for linux/arm64 (

#7977

https://github.com/open-policy-agent/opa/pull/7977

) authored by @srenatus

ci: Add zig to post-merge github action (

#7983

https://github.com/open-policy-agent/opa/pull/7983

) authored by @sspaink

e2e/authz,topdown: Fix benchmarks (

#7980

https://github.com/open-policy-agent/opa/pull/7980

) authored by @srenatus

runtime: Fixing tests by closing watcher & set default 

GracefulShutdownPeriod

 (

#7991

https://github.com/open-policy-agent/opa/pull/7991

) authored by @rMaxiQp

test/e2e: move 

http.DefaultTransport

 fix to 

init()

 (

#7955

https://github.com/open-policy-agent/opa/pull/7955

) authored by @srenatus

Remove 

vendor/

 (

#7975

https://github.com/open-policy-agent/opa/pull/7975

) authored by @srenatus

Modernize analyzer fixes (

#7965

https://github.com/open-policy-agent/opa/pull/7965

) authored by @anderseknert

Dependency updates; notably:

build: bump golang 1.25.1 -> 1.25.3 authored by @srenatus

build(deps): Bump github.com/olekukonko/tablewriter from 0.0.5 to 1.1.0 (

#7937

https://github.com/open-policy-agent/opa/pull/7937

) authored by @jh125486




This is a major version update containing breaking API changes. If you're affected by this, please consult the 

tablewriter migration guide

https://github.com/olekukonko/tablewriter/blob/master/MIGRATION.md

.

deps(build): Bump github.com/bytecodealliance/wasmtime-go from v3.0.2 to v37.0.0 authored by @srenatus

Optionally fail when 

opa test

 did not run any tests

With the new 

--fail-on-empty

 flag, accidentally running 

opa test

 in a directory without any tests or

 

with a 

-r

 that did not match any test names, can be caught by making the test fail instead.

1.9.0

This release contains a mix of new features, performance improvements, and bugfixes. Notably:

Compile API extensions ported from EOPA

Improved rule indexing

Compile Rego Queries Into SQL Filters (

)

Compile API extensions with support for SQL filter generation previously exclusive to EOPA has been ported into OPA.

Example

With OPA running with this policy, we'll compile the query 

data.filters.include

 into SQL filters:

package filters

# METADATA
# scope: document
# compile:
#   unknowns: [input.fruits]
include if input.fruits.name == input.favorite


rego

Example Request

POST /v1/compile/filters/include HTTP/1.1
Content-Type: application/json
Accept: application/vnd.opa.sql.postgresql+json


{
  "input": {
    "favorite": "pineapple"
  }
}


json

Example Response

HTTP/1.1 200 OK
Content-Type: application/vnd.opa.sql.postgresql+json


{
  "result": {
    "query": "WHERE fruits.name = E'pineapple'"
  }
}


json

See the 

documentation

https://www.openpolicyagent.org/docs/rest-api#compling-a-rego-policy-and-query-into-data-filters

 for more details.

Authored by @srenatus and @philipaconrad

Improved Rule Indexing For "Naked" Refs (

)

OPA's 

rule indexer

https://blog.openpolicyagent.org/optimizing-opa-rule-indexing-59f03f17caf3

 is a means by which OPA can optimize evaluation performance.

 

Briefly, the indexer can in some cases determine that a rule won't successfully evaluate 

before

 it's evaluated based on the query input.

 

The indexer previously only considered terms in certain compound expressions, ignoring single terms; e.g. an expression containing a sole "naked" ref. This has now changed!

Example

Given a policy with an 

allow

 rule containing two "naked" refs: 

input.foo

 and 

input.bar

:

package example

allow if {
    input.foo
    input.bar
}


rego

and the input document:

{
    "foo": 1
}


json

before this improvement, when evaluating the query 

data.example.allow

, we get the trace log:

query:1           Enter data.example.allow = _
query:1           | Eval data.example.allow = _
query:1           | Index data.example.allow (matched 1 rule, early exit)
policy.rego:3     | Enter data.example.allow
policy.rego:5     | | Eval input.foo
policy.rego:6     | | Eval input.bar
policy.rego:6     | | Fail input.bar
policy.rego:5     | | Redo input.foo
query:1           | Fail data.example.allow = _


Here, we can see that the 

allow

 rule is evaluated, but fails on the 

input.bar

 expression, as it's referencing an 

undefined

 value.

With the improvement to the indexer, we instead get:

query:1     Enter data.example.allow = _
query:1     | Eval data.example.allow = _
query:1     | Index data.example.allow (matched 0 rules, early exit)
query:1     | Fail data.example.allow = _


Where we can see that the 

allow

 rule was never evaluated, since the input doesn't meet the conditions established by the indexer; i.e. both 

input.foo

 and 

input.bar

 must have 

defined

 values.

Authored by @srenatus

Runtime, Tooling

cmd: Print eval errors to stderr (

#6749

https://github.com/open-policy-agent/opa/issues/6749

) authored by @sspaink reported by @janorn

plugin/decision: Encoder immediately returns when event same size as limit (

#7928

https://github.com/open-policy-agent/opa/pull/7928

) authored by @sspaink

plugin/decision: Refactor size buffer into its own type (

#7884

https://github.com/open-policy-agent/opa/pull/7884

) authored by @sspaink

plugins/bundle: Return callback error for manually triggered bundle downloads through the SDK (

#7869

https://github.com/open-policy-agent/opa/issues/7869

) authored by @sspaink reported by @victoraugustolls

runtime: Fix possible panic in 

opa run

 when loading bundles in watch-mode (

--watch

) (

#7870

https://github.com/open-policy-agent/opa/issues/7870

) authored by @sspaink reported by @johanfylling

Compiler, Topdown and Rego

perf: Don't invoke future parser for Rego v1 (

#7909

https://github.com/open-policy-agent/opa/pull/7909

) authored by @anderseknert

topdown: Add counter metric for http.send network requests (

#7851

https://github.com/open-policy-agent/opa/pull/7851

) authored by @anivar

topdown: Update 

numbers.range_step

 built-in error message (

#7882

https://github.com/open-policy-agent/opa/pull/7882

) authored by @charlieegan3

Docs, Website

docs: Add 

every

 and 

not

 examples (

#7901

https://github.com/open-policy-agent/opa/pull/7901

) authored by @charlieegan3

docs: Add examples for 

io.jwt

 and 

time

 built-ins (

#7892

https://github.com/open-policy-agent/opa/pull/7892

) authored by @charlieegan3

docs: Add examples for 

regex

 and 

string

 built-ins (

#7890

https://github.com/open-policy-agent/opa/pull/7890

) authored by @charlieegan3

docs: Add guide for common Rego errors (

#7896

https://github.com/open-policy-agent/opa/pull/7896

) authored by @charlieegan3

docs: Add missing anchors and example data (

#6205

https://github.com/open-policy-agent/opa/issues/6205

) authored by @mmzzuu reported by @johanfylling

docs: Add Rego keyword examples (

#7889

https://github.com/open-policy-agent/opa/pull/7889

) authored by @charlieegan3

docs: Add Rego language comparison pages (

#7893

https://github.com/open-policy-agent/opa/pull/7893

) authored by @charlieegan3

docs: Add Style Guide to policy authoring docs (

#7932

https://github.com/open-policy-agent/opa/pull/7932

) authored by @charlieegan3

docs: Generative AI policy example fix (

#7885

https://github.com/open-policy-agent/opa/pull/7885

) authored by @msorens

docs: Remove integration from build-security (

#7899

https://github.com/open-policy-agent/opa/pull/7899

) authored by @ieugen

docs: Update Envoy tutorial for new versions and images (

#7911

https://github.com/open-policy-agent/opa/pull/7911

) authored by @CharlieTLe

docs: Update references to cheat sheet and awesome-opa (

#7930

https://github.com/open-policy-agent/opa/pull/7930

) authored by @charlieegan3

docs: Add OCP docs (

#7875

https://github.com/open-policy-agent/opa/pull/7875

) authored by @charlieegan3

docs/ocp: Update docs on Azure object storage (

#7921

https://github.com/open-policy-agent/opa/pull/7921

) authored by @minajevs

docs/ocp: Fix inline-transform example (

#7913

https://github.com/open-policy-agent/opa/pull/7913

) authored by @srenatus

docs/ocp: Fix wrong example on concepts page (

#7907

https://github.com/open-policy-agent/opa/pull/7907

) authored by @srenatus

docs/ocp: Update API reference (

#7906

https://github.com/open-policy-agent/opa/pull/7906

) authored by @srenatus

docs/ocp: Update OCP api-key (

#7904

https://github.com/open-policy-agent/opa/pull/7904

) authored by @charlieegan3

docs/ocp: Update OCP install instructions (

#7910

https://github.com/open-policy-agent/opa/pull/7910

) authored by @ashutosh-narkar

docs: Add Regal docs to OPA site (

#7874

https://github.com/open-policy-agent/opa/pull/7874

) authored by @charlieegan3

docs/regal: Update docs following 0.36.0 (

#7891

https://github.com/open-policy-agent/opa/pull/7891

) authored by @charlieegan3

docs/deploy: Add OPA deployment docs (

#7898

https://github.com/open-policy-agent/opa/pull/7898

) authored by @charlieegan3

docs/website: Update references to Styra (

#7877

https://github.com/open-policy-agent/opa/pull/7877

) authored by @charlieegan3

Miscellaneous

Bump golangci-lint to v2.4.0 (

#7878

https://github.com/open-policy-agent/opa/pull/7878

) authored by @sspaink

Community Guidelines: update email list (

#7900

https://github.com/open-policy-agent/opa/pull/7900

) authored by @srenatus

ci: port binary tests to testscript (

#7865

https://github.com/open-policy-agent/opa/pull/7865

) authored by @srenatus

dependabot: Updating e2e go deps together with core OPA deps (

#7923

https://github.com/open-policy-agent/opa/pull/7923

) authored by @johanfylling

github_actions: Add working directory in arguments for Link Checker (

#7883

https://github.com/open-policy-agent/opa/pull/7883

) authored by @sspaink

rego: Add comprehensive WASM performance benchmarks (

#7841

https://github.com/open-policy-agent/opa/pull/7841

) authored by @anivar

Dependency updates; notably:

build: Bump go to 1.25.1

build(deps): Add github.com/huandu/go-sqlbuilder 1.37.0

build(deps): Bump github.com/lestrrat-go/jwx/v3 from 3.0.10 to 3.0.11

build(deps): Bump github.com/prometheus/client_golang from 1.23.0 to 1.23.2

build(deps): Bump golang.org/x/net from 0.43.0 to 0.44.0

build(deps): Bump golang.org/x/time from 0.12.0 to 0.13.0

build(deps): Bump google.golang.org/grpc from 1.75.0 to 1.75.1

build(deps): Bump google.golang.org/protobuf from 1.36.8 to 1.36.9

build(deps): bump go.opentelemetry.io deps from 1.37.0/0.62.0 to 1.38.0/0.63.0

1.8.0

This release contains a mix of new features, performance improvements, and bugfixes. Notably:

Support for EdDSA signatures in 

io.jwt

 built-ins, including a new 

io.jwt.verify_eddsa

 built-in.

EdDSA Support in built-ins (

)

Support for the EdDSA signing algorithm has been added to built-in functions in the 

io.jwt

 namespace.

This introduces the new 

io.jwt.verify_eddsa

https://www.openpolicyagent.org/docs/policy-reference/builtins/tokens#builtin-tokens-iojwtverify_eddsa

 built-in function, and adds EdDSA support for the following built-ins:

io.jwt.decode_verify

https://www.openpolicyagent.org/docs/policy-reference/builtins/tokens#builtin-tokens-iojwtdecode_verify

io.jwt.encode_sign

https://www.openpolicyagent.org/docs/policy-reference/builtins/tokensign#builtin-tokensign-iojwtencode_sign

io.jwt.encode_sign_raw

https://www.openpolicyagent.org/docs/policy-reference/builtins/tokensign#builtin-tokensign-iojwtencode_sign_raw

This feature benefited greatly from the groundwork laid by @lestrrat in (

#7638

https://github.com/open-policy-agent/opa/issues/7638

). 👏 🎉 🥳

Authored by @johanfylling reported by @aromeyer

Runtime

cmd: Add back default 

cmd.RootCommand

 definition. (

#7811

https://github.com/open-policy-agent/opa/pull/7811

) authored by @philipaconrad




Fixing a breaking change to the go API introduced in OPA v1.7.0.

cmd: Fix 

opa exec

 parameters (

#7850

https://github.com/open-policy-agent/opa/issues/7850

, 

#7840

https://github.com/open-policy-agent/opa/issues/7840

) authored by @srenatus




Fixing regressions introduced in OPA v1.7.0, where the 

--fail-non-empty

 and 

--stdin-input

 flags were dropped.

config: accept env vars set to 

""

, discern from unset (

#7831

https://github.com/open-policy-agent/opa/issues/7831

) authored by @srenatus reported by @ManuelNowackConfinale

handlers: Add thread-safe initialization for gzipPool (

#7828

https://github.com/open-policy-agent/opa/pull/7828

) authored by @charlieegan3

plugins: Address race in config access (

#7825

https://github.com/open-policy-agent/opa/pull/7825

) authored by @charlieegan3

plugin/bundle: Correct bundle delay behavior (

#7812

https://github.com/open-policy-agent/opa/pull/7812

) authored by @charlieegan3

runtime: Update server init check (

#7818

https://github.com/open-policy-agent/opa/pull/7818

) authored by @charlieegan3

Topdown

perf: Performance greatly improved for 

Object.Insert

 on existing key (

#7820

https://github.com/open-policy-agent/opa/pull/7820

) authored by @anderseknert

topdown,bundle,plugins: Upgrade interned jwx (0.9.x) with 

github.com/lestrrat-go/jwx/v3

 (

#7638

https://github.com/open-policy-agent/opa/issues/7638

) authored by @lestrrat

Docs, Website

Update website to build from tip of main (

#7848

https://github.com/open-policy-agent/opa/pull/7848

) authored by @tsandall

ast/builtins: Remove space from 

count

 description (

#7836

https://github.com/open-policy-agent/opa/pull/7836

) authored by @charlieegan3

docs: Add link to logic-or/and on docs index (

#7826

https://github.com/open-policy-agent/opa/pull/7826

) authored by @charlieegan3

docs: Add note on using LLM in PR discussions (

#7859

https://github.com/open-policy-agent/opa/pull/7859

) authored by @anderseknert

docs: Fix broken anchor links in annotations (

#7827

https://github.com/open-policy-agent/opa/pull/7827

) authored by @charlieegan3

docs: Use set in the Python code example for consistence (

#7860

https://github.com/open-policy-agent/opa/pull/7860

) authored by @durnik-ivo

docs: Update frontpage (

#7847

https://github.com/open-policy-agent/opa/pull/7847

) authored by @tsandall

docs/rest-api: Add notes about policy IDs (

#7837

https://github.com/open-policy-agent/opa/pull/7837

) authored by @charlieegan3

website: Use latest release rather than edge (

#7781

https://github.com/open-policy-agent/opa/pull/7781

) authored by @charlieegan3

Miscellaneous

Update organization affiliations (

#7842

https://github.com/open-policy-agent/opa/pull/7842

) authored by @tsandall

test/e2e: Avoid port exhaustion in concurrent tests (

#7862

https://github.com/open-policy-agent/opa/pull/7862

) authored by @anderseknert

server: Make 

TestCertReloading

 less verbose (

#7823

https://github.com/open-policy-agent/opa/pull/7823

) authored by @charlieegan3

cmd: Exec test wait for bundle server to start (

#7821

https://github.com/open-policy-agent/opa/pull/7821

) authored by @charlieegan3

cmd: Update tests to run sync when ready (

#7835

https://github.com/open-policy-agent/opa/pull/7835

) authored by @charlieegan3

cmd: Move accidental pkg var to local var (

#7813

https://github.com/open-policy-agent/opa/pull/7813

) authored by @philipaconrad

internal/report: Allow overriding GitHub repo (

#7867

https://github.com/open-policy-agent/opa/pull/7867

) authored by @srenatus

release: Adding Dockerfile for image used in 

*-patch

 build targets (

#7864

https://github.com/open-policy-agent/opa/pull/7864

) authored by @johanfylling

Dependency updates; notably:

build: Bump go to 1.24.6 (

#7834

https://github.com/open-policy-agent/opa/pull/7834

, 

#7839

https://github.com/open-policy-agent/opa/pull/7839

) authored by @johanfylling and @thevilledev

build(deps): Bump go-viper/mapstructure/v2 from v2.3.0 to v2.4.0 (

#7857

https://github.com/open-policy-agent/opa/pull/7857

) authored by @deeglaze

build(deps): Bump github.com/containerd/containerd/v2 from 2.1.3 to 2.1.4

build(deps): Bump github.com/prometheus/client_golang from 1.22.0 to 1.23.0

1.7.1

This is a bug fix release addressing two issues for users that include OPA's CLI in their own application's CLI:

A missing symbol in the 

cmd

 package (

cmd.RootCommand

)

A possible panic in the 

opa parse

 command

1.7.0

This release contains a mix of new features, performance improvements, and bugfixes. Notably:

Improved OPA SDK/API for better extensibility

SDK Improvements

The OPA SDK/API has been improved to provide better extensibility an more points of integration for developers.

ast: Add 

DefaultModuleLoader

 (

#7794

https://github.com/open-policy-agent/opa/pull/7794

) authored by @srenatus

ast: Add feature registration from the outside (

#7782

https://github.com/open-policy-agent/opa/pull/7782

) authored by @srenatus

bundle: Add support for bundle store and activation plugins (

#7771

https://github.com/open-policy-agent/opa/pull/7771

) authored by @philipaconrad

cmd: Allow branding (

#7797

https://github.com/open-policy-agent/opa/pull/7797

) authored by @srenatus

decisionlogs: Add custom fields grab bag (

#7793

https://github.com/open-policy-agent/opa/pull/7793

) authored by @srenatus

plugins: allow registering handlerfuncs with name+path (

#7769

https://github.com/open-policy-agent/opa/pull/7769

) authored by @srenatus

rego: Expose 

QueryTracers

, 

tracing.Options

 and 

Cancel

 from 

QueryContext

 (

#7767

https://github.com/open-policy-agent/opa/pull/7767

) authored by @philipaconrad

rego: Pass along 

TracingOpts

 into 

EvalContext

 (

#7778

https://github.com/open-policy-agent/opa/pull/7778

) authored by @srenatus

runtime: add 

ExtraDiscoveryOpts

 to 

runtime.Params

 (

#7766

https://github.com/open-policy-agent/opa/pull/7766

) authored by @srenatus

sdk: Allow for setting default options for all instances (

#7760

https://github.com/open-policy-agent/opa/pull/7760

) authored by @srenatus

server: Add hooks wiring + new hooks for inter-query caches (

#7775

https://github.com/open-policy-agent/opa/pull/7775

) authored by @srenatus

server: Ensure that wrapped middlewares all support 

http.Flusher

 (

#7772

https://github.com/open-policy-agent/opa/pull/7772

) authored by @srenatus

server/authorizer: Allow adding paths to validator (

#7792

https://github.com/open-policy-agent/opa/pull/7792

) authored by @philipaconrad

server+plugins: Allow plugins to inject http handler middlewares (

#7789

https://github.com/open-policy-agent/opa/pull/7789

) authored by @srenatus reported by @deeglaze

store+runtime: Extension points for custom stores (

#7779

https://github.com/open-policy-agent/opa/pull/7779

) authored by @srenatus

test+eval: Add helper to smuggle compiler through context (

#7790

https://github.com/open-policy-agent/opa/pull/7790

) authored by @srenatus

tester: Support 

uint64

 and 

float64

 metrics in 

runBenchmark

 (

#7761

https://github.com/open-policy-agent/opa/pull/7761

) authored by @srenatus

Runtime, Tooling

build: Show a warning when .manifest is ignored (

#7807

https://github.com/open-policy-agent/opa/pull/7807

) authored by @charlieegan3

cli: Avoid os.Exit() in Run() funcs (

#7788

https://github.com/open-policy-agent/opa/pull/7788

) authored by @srenatus

config: Keep unknown env replacements (

#7786

https://github.com/open-policy-agent/opa/pull/7786

) authored by @srenatus

format: Not bracketing keywords in imports (

#7742

https://github.com/open-policy-agent/opa/issues/7742

) authored by @johanfylling

loader: Add bundle lazy loading mode across the runtime. (

#7768

https://github.com/open-policy-agent/opa/pull/7768

) authored by @philipaconrad

loader: Pass bundle name in 

AsBundle()

 (

#7798

https://github.com/open-policy-agent/opa/pull/7798

) authored by @srenatus

opa exec: stop plugins before exit (

#7760

https://github.com/open-policy-agent/opa/pull/7760

) authored by @srenatus

plugins/discovery: Make 

Factories()

 merge the factories (

#7777

https://github.com/open-policy-agent/opa/pull/7777

) authored by @srenatus

plugins/discovery: Replace environment variables after evaluation (

#7787

https://github.com/open-policy-agent/opa/pull/7787

) authored by @philipaconrad

plugins/logs: Add experimental intermediate results field (

#7796

https://github.com/open-policy-agent/opa/pull/7796

) authored by @philipaconrad

report: Fetching latest OPA release version from GitHub (

#7756

https://github.com/open-policy-agent/opa/pull/7756

) authored by @johanfylling




OPA will no longer send telemetry data when fetching the latest release version.

runtime: Allow enabling NDBCache by default (

#7780

https://github.com/open-policy-agent/opa/pull/7780

) authored by @srenatus

server+logging: Add 

BatchDecisionID

 field to Decision Logs (

#7791

https://github.com/open-policy-agent/opa/pull/7791

) authored by @philipaconrad

store: Improve conflicting root error message (

#7806

https://github.com/open-policy-agent/opa/issues/7806

) authored by @charlieegan3

Compiler, Topdown and Rego

perf: AST compiler optimizations (

#7740

https://github.com/open-policy-agent/opa/pull/7740

) authored by @anderseknert

Docs, Website

Note:

 While we have been working on the new website we have been showing

 

the edge documentation contents (as contents and framework changes often must

 

go hand in hand). Now that the website development pace has slowed and the

 

functionality is more stable, we will be returning to showing the documentation

 

content from the latest release instead. Please use the

 

edge documentation site

https://edge--opa-docs.netlify.app/

 

to review new changes. PR previews are also based on the latest branch commit.

 

This change will be made to show the v1.7.0 release shortly after publishing.

docs: Add examples for crypto.sha256 and base64.encode built-in functions (

#7762

https://github.com/open-policy-agent/opa/pull/7762

) authored by @ToluGIT

docs: Break out the built-in categories in policy ref (

#7722

https://github.com/open-policy-agent/opa/pull/7722

) authored by @sky3n3t

docs: Correctly spell NetBSD (

#7738

https://github.com/open-policy-agent/opa/pull/7738

) authored by @iamleot

docs: Fix a number of minor docs typos (

#7799

https://github.com/open-policy-agent/opa/pull/7799

) authored by @charlieegan3

docs: Fix 

/docs/envoy-authorization/

 

404

 (

#7755

https://github.com/open-policy-agent/opa/issues/7755

 authored by @charlieegan3

docs: Remove link to OPA playground share (

#7750

https://github.com/open-policy-agent/opa/pull/7750

) authored by @charlieegan3

docs: Revise docs index page wording (

#7805

https://github.com/open-policy-agent/opa/pull/7805

) authored by @charlieegan3

docs: Update warning note in GraphQL API docs (

#7737

https://github.com/open-policy-agent/opa/pull/7737

) authored by @charlieegan3

website: Add wildcard CORS for data/versions.json (

#7784

https://github.com/open-policy-agent/opa/pull/7784

) authored by @charlieegan3

website: Ensure no hscroll on built-in tables (

#7773

https://github.com/open-policy-agent/opa/pull/7773

) authored by @charlieegan3

website: Render versions under 

/data/versions.json

 (

#7783

https://github.com/open-policy-agent/opa/pull/7783

) authored by @charlieegan3

website: Set mobile and desktop tab sizes (

#7774

https://github.com/open-policy-agent/opa/pull/7774

) authored by @charlieegan3

website: Show link to the edge release of the docs (

#7776

https://github.com/open-policy-agent/opa/pull/7776

) authored by @charlieegan3

Miscellaneous

Benchmark fixes (

#7765

https://github.com/open-policy-agent/opa/pull/7765

) authored by @anderseknert

Use Regal for linting Rego (

#7752

https://github.com/open-policy-agent/opa/pull/7752

) authored by @anderseknert

Use shorthand form for types (

#7757

https://github.com/open-policy-agent/opa/pull/7757

) authored by @anderseknert

.github: Use types for issues (

#7751

https://github.com/open-policy-agent/opa/pull/7751

) authored by @charlieegan3

build: Add top-level token permissions for workflows (

#7795

https://github.com/open-policy-agent/opa/pull/7795

) authored by @timothyklee

docs/build: Link checker fixes (

#7743

https://github.com/open-policy-agent/opa/pull/7743

) authored by @charlieegan3

Dependency updates; notably:

build(deps): bump github.com/containerd/containerd/v2 from 2.1.1 to 2.1.3

build(deps): bump google.golang.org/grpc from 1.73.0 to 1.74.2

build(deps): bump go.opentelemetry.io deps from 1.36.0/0.61.0 to 1.37.0/0.62.0

1.6.0

This release contains a mix of new features, performance improvements, and bugfixes. Notably:

Improvements to the OPA website and documentation

Allowing keywords in Rego references

Parallel test execution

Faster built-in function execution

Modernized OPA Website (

)

We're continuing to modernize the OPA website with a new design and improved user experience.

Some highlights:

Builtins

https://www.openpolicyagent.org/docs/policy-reference#built-in-functions

: You can now search them on the docs page!

Sidebar redesign: Making it easier to find what you're looking for in our docs

Feedback forms: Closing the feedback loop between docs authors and readers -- Please let us know if you dislike, or like, a docs page.

Downloads page

https://www.openpolicyagent.org/docs#1-download-opa

: Find your OS' installation instructions on a less cluttered page!

And much more

Authored by @sky3n3t and @charlieegan3

Allowing keywords in Rego references (

)

Previously, Rego references could not contain terms that conflict with Rego keywords such as 

package

, 

if

, 

else

, 

not

, etc.

 

in certain constructs:

package example

allow if {
    input.package.source         # not allowed (before v1.6.0)
    input["package"].destination # allowed
}


rego

The constraints for valid Rego references have been relaxed to allow keywords.

 

The above example is now valid and will no longer cause a compilation error.

Authored by @johanfylling

Parallel Test Execution (

)

By default, OPA will now run tests in parallel (defaulting to one parallel execution thread per available CPU core), significantly speeding up test execution time for large test suites.

 

The performance boost is closely tied to the number of tests in your project and your selected parallelism level. For larger projects and default settings, 2-3x performance gains have been measured on a MacBook Pro.

Parallelism can be disabled to run tests sequentially by setting the 

--parallel

 flag to 

1

. E.g. 

opa test . --parallel=1

.

Authored by @sspaink reported by @anderseknert

Faster Builtin Function Evaluation

The builtin context, an internal construct of OPA's evaluation engine, was previously provided to every builtin function.

 

As it turns out, only very few of them actually need it, for caching, cancellation, or lookups.

 

Those builtins are still provided with a builtin context, but for calls to all other builtins, we save the memory required by it.

 

The impact is tremendous: Even though the size of a single builtin context is only about 270 bytes, in an example application (Regal), this change brings about 360 MB of reduced memory usage!

Authored by @anderseknert

Runtime, Tooling, SDK

cmd/check: 

opa check --bundle

 report virtual/base doc conflicts (

#7701

https://github.com/open-policy-agent/opa/pull/7701

) authored by @anderseknert




When 

opa check

 is used with the 

--bundle

 flag, an error will be reported if the provided json/yaml data has a conflicting overlap with the virtual documents generated by Rego rules. Such conflicts are ambiguous and can lead to unexpected evaluation results, and should be resolved.

cmd/inspect: Fixing missing annotations location in 

opa inspect

 with JSON format (

#7459

https://github.com/open-policy-agent/opa/issues/7459

) authored by @johanfylling reported by @mostealth

cmd/parse: Expose 

--v0-compatible

 flag (

#7668

https://github.com/open-policy-agent/opa/pull/7668

) authored by @tsandall

cmd/refactor: Fix src:dst parsing to deal with colons (

#7648

https://github.com/open-policy-agent/opa/pull/7648

) authored by @tsandall

metrics: Fix restartable timer bug. (

#7669

https://github.com/open-policy-agent/opa/pull/7669

) authored by @philipaconrad

metrics: Prealloc maps + add benchmark (

#7664

https://github.com/open-policy-agent/opa/pull/7664

) authored by @philipaconrad

oracle: Add support for some and every (

#7716

https://github.com/open-policy-agent/opa/pull/7716

) authored by @charlieegan3

oracle: Support object refs in FindDefinition (

#7711

https://github.com/open-policy-agent/opa/pull/7711

) authored by @charlieegan3

plugin/decision: Check if event is too large after compression (

#7526

https://github.com/open-policy-agent/opa/issues/7526

) authored by @sspaink

runtime,server: Replace gorilla/mux dependency with http.ServeMux (

#7676

https://github.com/open-policy-agent/opa/pull/7676

) authored by @anderseknert




Note

: This is a potentially breaking change for go API users directly interfacing with the OPA server's routing.

server: Fix deferred metrics timers. (

#7671

https://github.com/open-policy-agent/opa/pull/7671

) authored by @philipaconrad

server: Fix query url when opa is served not from root path (

#7644

https://github.com/open-policy-agent/opa/pull/7644

) authored by @olegKoshmeliuk




Note

: This is only applicable for the web UI hosted by OPA on its root path (

/

) and OPA is served at some other path than root.

Compiler, Topdown and Rego

ast: Ensure surplus leading zeros always error (

#7726

https://github.com/open-policy-agent/opa/pull/7726

) authored by @charlieegan3




Note

: Primitive Rego number values with leading zeros (e.g. 

0123

) are now considered invalid at time of parsing and will generate an error. If you're impacted by this change, please update your policies to not have numbers with leading zeros. E.g. 

0123

 should be changed to 

123

.

ast: Fixing type-checker schema cache race condition for inlined schemas (

#7679

https://github.com/open-policy-agent/opa/issues/7679

, 

7571

https://github.com/open-policy-agent/opa/issues/7571

) authored by @johanfylling reported by @daniel-petrov-gig

perf: Improve performance when referencing "global" in loop (

#7654

https://github.com/open-policy-agent/opa/issues/7654

) authored by @anderseknert

topdown: Fix issue where path in 

walk

 would get mutated (

#7656

https://github.com/open-policy-agent/opa/issues/7656

) authored by @anderseknert reported by @robmyersrobmyers

topdown/http: Lenient application/json Content-Type header (

#6684

https://github.com/open-policy-agent/opa/issues/6684

) authored by @sspaink reported by @mrvanes

Docs, Website, Ecosystem

adopters: add Pix4D as adopters for its RBAC service (

#7645

https://github.com/open-policy-agent/opa/pull/7645

) authored by @marcaurele

api: Expand docs for RegisterBuiltin — no thread-safety (

#7667

https://github.com/open-policy-agent/opa/issues/7667

) authored by @anderseknert reported by @parth-mehta-989

docs: Added a search function for the builtins section of policy-reference (

#7704

https://github.com/open-policy-agent/opa/pull/7704

) authored by @sky3n3t

docs: Add another OR note in AND section (

#7706

https://github.com/open-policy-agent/opa/pull/7706

) authored by @charlieegan3

docs: Add basic docs covering CI/CD use case (

#7703

https://github.com/open-policy-agent/opa/pull/7703

) authored by @charlieegan3

docs: Add current ecosystem contribution docs (

#7678

https://github.com/open-policy-agent/opa/pull/7678

) authored by @charlieegan3

docs: Add EvergreenCodeBlock for code with version (

#7706

github.com/open-policy-agent/opa/pull/7706

) authored by @charlieegan3

docs: Add feedback form for user reported issues (

#7662

https://github.com/open-policy-agent/opa/pull/7662

) authored by @charlieegan3

docs: Address broken links (

#7661

https://github.com/open-policy-agent/opa/pull/7661

) authored by @charlieegan3

docs: Archive explain that only latest patch is shown (

#7682

https://github.com/open-policy-agent/opa/pull/7682

)  authored by @charlieegan3

docs: Fix bug where the search match respects case (

#7713

https://github.com/open-policy-agent/opa/pull/7713

) authored by @sky3n3t

docs: Hide feedback pop-up forever if dismissed (

#7674

https://github.com/open-policy-agent/opa/pull/7674

) authored by @charlieegan3

docs: Improve bundle structure documentation (

#7683

https://github.com/open-policy-agent/opa/pull/7683

) authored by @charlieegan3

docs: Improve explanations for initial examples (

#7677

https://github.com/open-policy-agent/opa/pull/7677

) authored by @charlieegan3

docs: Install/Download Instruction Update (

#7687

https://github.com/open-policy-agent/opa/pull/7687

) authored by @charlieegan3

docs: Move code example data inside the PlaygroundComponent (

#7724

https://github.com/open-policy-agent/opa/pull/7724

) authored by @sky3n3t

docs: policy-reference, update sig algs formatting (

#7685

https://github.com/open-policy-agent/opa/pull/7685

) authored by @charlieegan3

docs: Redirect old admission control link (

#7730

https://github.com/open-policy-agent/opa/pull/7730

) authored by @charlieegan3

docs: Refactored Networking Reference docs (

#7686

https://github.com/open-policy-agent/opa/pull/7686

) authored by @sky3n3t

docs: Revise sidebar order and layout (

#7731

https://github.com/open-policy-agent/opa/pull/7731

) authored by @charlieegan3

docs: Reworked existing policy examples to use PlaygroundExample (

#7690

https://github.com/open-policy-agent/opa/pull/7690

) authored by @sky3n3t

docs: Show a feedback popup on the docs site (

#7663

https://github.com/open-policy-agent/opa/pull/7663

) authored by @charlieegan3

docs: Show edge rather than latest release (

#7717

https://github.com/open-policy-agent/opa/pull/7717

) authored by @charlieegan3

docs: Show TOC on CLI page (

#7712

https://github.com/open-policy-agent/opa/pull/7712

) authored by @charlieegan3

docs: Update colors for feedback form in dark mode (

#7691

https://github.com/open-policy-agent/opa/pull/7691

) authored by @charlieegan3

docs: Update policy-ref allowing anchor linking (

#7675

https://github.com/open-policy-agent/opa/pull/7675

) authored by @charlieegan3

docs: Update rego in deployment examples (

#7707

https://github.com/open-policy-agent/opa/pull/7707

) authored by @charlieegan3

docs: Update sidebar (

#7723

https://github.com/open-policy-agent/opa/pull/7723

) authored by @charlieegan3

website: Disable cancel script (

#7719

https://github.com/open-policy-agent/opa/pull/7719

) authored by @charlieegan3

website: Explain automation in RELEASE.md (

#7721

https://github.com/open-policy-agent/opa/pull/7721

) authored by @charlieegan3

website: Fix badge endpoints (

#7653

https://github.com/open-policy-agent/opa/pull/7653

) authored by @charlieegan3

website: Refactor site components with CSS modules (

#7666

https://github.com/open-policy-agent/opa/pull/7666

) authored by @charlieegan3

website: Update docusaurus components to 3.8.1 (

#7718

https://github.com/open-policy-agent/opa/pull/7718

) authored by @charlieegan3

Miscellaneous

build: Better detection of go changes (

#7696

https://github.com/open-policy-agent/opa/pull/7696

) authored by @charlieegan3

build: Bump golang 1.24.3 -> 1.24.4 (

#7672

https://github.com/open-policy-agent/opa/pull/7672

) authored by @srenatus

Adding Clarification to merge instructions when cutting a patch release (

#7660

https://github.com/open-policy-agent/opa/pull/7660

) authored by @johanfylling

build: Make summary failure source clearer (

#7697

https://github.com/open-policy-agent/opa/pull/7697

) authored by @charlieegan3

build: Skip jobs for non docs changes (

#7688

https://github.com/open-policy-agent/opa/pull/7688

) authored by @charlieegan3

deps: Use 

google.golang.org/protobuf

 (

#7655

https://github.com/open-policy-agent/opa/pull/7655

) authored by @sspaink

perf: Simplify interning (

#7714

https://github.com/open-policy-agent/opa/pull/7714

) authored by @anderseknert

perf: Only pass built-in context to calls depending on it (

#7728

https://github.com/open-policy-agent/opa/pull/7728

) authored by @anderseknert

perf: Improve built-in 

concat

 performance (

#7702

https://github.com/open-policy-agent/opa/pull/7702

) authored by @anderseknert

perf: More efficient data/v1 POST handler (

#7673

https://github.com/open-policy-agent/opa/pull/7673

) authored by @anderseknert

test: Fix flaky TestRaisingHTTPClientQueryError (

#7698

https://github.com/open-policy-agent/opa/pull/7698

) authored by @sspaink

test: Fix flaky topdown query cache tests (

#7590

https://github.com/open-policy-agent/opa/issues/7590

) authored by @sspaink

Dependency updates; notably:

build(deps): Bump gqlparser from v2.5.27 to v2.5.28 (

#7699

https://github.com/open-policy-agent/opa/issues/7699

) authored by @robmyersrobmyers

build(deps): bump github.com/go-logr/logr from 1.4.2 to 1.4.3

build(deps): bump github.com/vektah/gqlparser/v2 from 2.5.26 to 2.5.27

build(deps): bump golang.org/x/net from 0.39.0 to 0.40.0

build(deps): bump google.golang.org/grpc from 1.72.0 to 1.72.2

build(deps): bump oras.land/oras-go/v2 from 2.5.0 to 2.6.0

build(deps): bump go.opentelemetry.io deps to 1.36.0/0.61.0

1.5.1

This is a bug fix release addressing a regression to the 

walk

https://www.openpolicyagent.org/docs/policy-reference#builtin-graph-walk

 built-in function, introduced in v1.5.0. See 

#7656

https://github.com/open-policy-agent/opa/issues/7656

 (authored by @anderseknert reported by @robmyersrobmyers)

1.5.0

This release contains a mix of new features, performance improvements, and bugfixes. Among others:

Support for AWS SSO credentials provider

Support for signing client assertions with Azure Keyvault

Faster 

object.get

, 

walk

 and builtin-function evaluation

Improved guardrails in the parser

Improvements to decision logging

Modernized OPA Website (

)

The 

OPA website

https://www.openpolicyagent.org/

 has been modernized with a new design and improved user experience.

The new site is based on Docusaurus and React which makes it easier to build live functionality and add non-documentation resources.

 

This lays the groundwork for even more improvements in the future!

Documentation for older OPA versions are still available in the 

version archive

https://www.openpolicyagent.org/docs/archive

.

Authored by @charlieegan3

Runtime, Tooling, SDK

ast: Only use JSON-escaped literal when needed in ref to string convertion (

#7550

https://github.com/open-policy-agent/opa/issues/7550

) reported and authored by @xubinzheng

ast: Parser recursion depth guard (

#7568

https://github.com/open-policy-agent/opa/pull/7568

) authored by @thevilledev

ast: Retaining 

SomeDecl

 

Location

 field when compiler resolves refs (

#7543

https://github.com/open-policy-agent/opa/issues/7543

) authored by @johanfylling

bundle: Setting default rego-version in bundle API (

#7588

https://github.com/open-policy-agent/opa/issues/7588

) authored by @johanfylling reported by @xubinzheng

perf: Improved "baseline" metrics of opa bench for trivial queries (

#7580

https://github.com/open-policy-agent/opa/pull/7580

) authored by @anderseknert

plugins/decision: Don't drop adaptive uncompressed size limit on upload (

#7562

https://github.com/open-policy-agent/opa/issues/7562

) authored by @sspaink

plugins/decision: Set config boundaries to upload_size_limit_bytes (#7563) (authored by @sspaink)

plugins/rest: Add support for AWS SSO credentials provider (

#7527

https://github.com/open-policy-agent/opa/pull/7527

) authored by @efiShtain

plugins/rest: Support signing of client assertions with Azure Keyvault (

#7462

https://github.com/open-policy-agent/opa/issues/7462

) reported and authored by @Od1nB

plugins/status: Support graceful shutdown timeout (

#7576

https://github.com/open-policy-agent/opa/issues/6676

) authored by @sspaink

rego: Don't generate JSON values for wildcard/generated keys in result set (

#7567

https://github.com/open-policy-agent/opa/pull/7567

) authored by @anderseknert

runtime: Don't override user set version 

commit

 and 

timestamp

 (

#7471

https://github.com/open-policy-agent/opa/issues/7471

) reported by @kastl-ars authored by @sspaink

Planner, Topdown and Rego

planner: Deal with var-for-function replacement in indirect calls (

#5311

https://github.com/open-policy-agent/opa/issues/5311

) authored by @srenatus

topdown: Faster 

object.get

 built-in function (

#7593

https://github.com/open-policy-agent/opa/pull/7593

) authored by @anderseknert

topdown: Faster 

walk

 built-in function (

#7612

https://github.com/open-policy-agent/opa/pull/7612

) authored by @anderseknert

topdown: Improved default rule value inlining ( (

#1418

https://github.com/open-policy-agent/opa/issues/1418

) authored by @johanfylling

topdown: Improved GraphQL error handling (

#7622

https://github.com/open-policy-agent/opa/issues/7622

) reported and authored by @robmyersrobmyers

Docs, Website, Ecosystem

docs: Fix helm-kubernetes-quickstart bundle (

#7606

https://github.com/open-policy-agent/opa/pull/7606

) reported and authored by @nejec

docs: Add Swift-OPA to the Ecosystem Page (

#7610

https://github.com/open-policy-agent/opa/pull/7610

) authored by @charlieegan3

docs: Add Tutorial Redirects ([#7603]https://github.com/open-policy-agent/opa/issues/7603) reported by @nataraj24 authored by @charlieegan3

Fix links in README (

#7633

https://github.com/open-policy-agent/opa/pull/7633

) authored by @ffjlabo

Miscellaneous

github_actions: Adding monthly check for broken hyperlinks (

#7537

https://github.com/open-policy-agent/opa/pull/7537

) authored by @sspaink

perf: Extended interning (

#7636

https://github.com/open-policy-agent/opa/pull/7636

) authored by @anderseknert

perf: 

Ref.String()

 shortcut on single var term ref (

#7595

https://github.com/open-policy-agent/opa/pull/7595

) authored by @anderseknert

refactor: Don't return error from 

opaTest

 (

#7560

https://github.com/open-policy-agent/opa/pull/7560

) authored by @sspaink

refactor: Remove internal/gqlparser and use upstream dependency instead. (

#7520

https://github.com/open-policy-agent/opa/issues/7520

) authored by @robmyersrobmyers

test: Fix flaky TestContextErrorHandling (

#7587

https://github.com/open-policy-agent/opa/pull/7587

) authored by @sspaink

Apply modernize linter fixes (

#7599

https://github.com/open-policy-agent/opa/pull/7599

) authored by @anderseknert

Use 

any

 in place of 

interface{}

 (

#7566

https://github.com/open-policy-agent/opa/pull/7566

) authored by @anderseknert

Dependency updates; notably:

build: bump go from 1.24.0 to 1.24.3

build(deps): bump containerd to v2.1.1 (

#7627

https://github.com/open-policy-agent/opa/issues/7627

) authored by @johanfylling reported by @robmyersrobmyers

build(deps): bump github.com/fsnotify/fsnotify from 1.8.0 to 1.9.0

build(deps): bump github.com/prometheus/client_golang from 1.21.1 to 1.22.0

build(deps): bump github.com/prometheus/client_model from 0.6.1 to 0.6.2

build(deps): bump golang.org/x/net from 0.38.0 to 0.39.0

build(deps): bump google.golang.org/grpc from 1.71.1 to 1.72.0

1.4.2

This is a bug fix release addressing the missing 

capabilities/v1.4.1.json

 in the v1.4.1 release.

1.4.1

This is a security fix release for the fixes published in Go 

1.24.1

https://groups.google.com/g/golang-announce/c/4t3lzH3I0eI

 and 

1.24.2

https://groups.google.com/g/golang-announce/c/Y2uBTVKjBQk

build: bump go to 1.24.2 (#7544) (authored by @sspaink)

 

Addressing 

CVE-2025-22870

 and 

CVE-2025-22871

 vulnerabilities in the Go runtime.

1.4.0

This release contains a security fix addressing CVE-2025-46569.

 

It also includes a mix of new features, bugfixes, and dependency updates.

Security Fix: CVE-2025-46569 - OPA server Data API HTTP path injection of Rego (

)

A vulnerability in the OPA server's 

Data API

https://www.openpolicyagent.org/docs/latest/rest-api/#data-api

 allows an attacker to craft the HTTP path in a way that injects Rego code into the query that is evaluated.




The evaluation result cannot be made to return any other data than what is generated by the requested path, but this path can be misdirected, and the injected Rego code can be crafted to make the query succeed or fail; opening up for oracle attacks or, given the right circumstances, erroneous policy decision results.

 

Furthermore, the injected code can be crafted to be computationally expensive, resulting in a Denial Of Service (DoS) attack.

Users are only impacted if all of the following apply:

OPA is deployed as a standalone server (rather than being used as a Go library)

The OPA server is exposed outside of the local host in an untrusted environment.

The configured 

authorization policy

https://www.openpolicyagent.org/docs/latest/security/#authentication-and-authorization

 does not do exact matching of the input.path attribute when deciding if the request should be allowed.

or, if all of the following apply:

OPA is deployed as a standalone server.

The service connecting to OPA allows 3rd parties to insert unsanitised text into the path of the HTTP request to OPA’s Data API.

Note: With 

no

 

Authorization Policy

https://www.openpolicyagent.org/docs/latest/security/#authentication-and-authorization

 configured for restricting API access (the default configuration), the RESTful 

Data API

https://www.openpolicyagent.org/docs/latest/rest-api/#data-api

 provides access for managing Rego policies; and the RESTful 

Query API

https://www.openpolicyagent.org/docs/latest/rest-api/#query-api

 facilitates advanced queries.

 

Full access to these APIs provides both simpler, and broader access than what the security issue describes here can facilitate.

 

As such, OPA servers exposed to a network are 

not

 considered affected by the attack described here if they are knowingly not restricting access through an Authorization Policy.

This issue affects all versions of OPA prior to 1.4.0.

See the 

Security Advisory

https://github.com/open-policy-agent/opa/security/advisories/GHSA-6m8w-jc87-6cr7

 for more details.

Reported by @GamrayW, @HyouKash, @AdrienIT, authored by @johanfylling

Runtime, Tooling, SDK

ast: Adding 

rego_v1

 feature to 

--v0-compatible

 capabilities (

#7474

https://github.com/open-policy-agent/opa/pull/7474

) authored by @johanfylling

executable: Add version and icon to OPA windows executable (

#3171

https://github.com/open-policy-agent/opa/issues/3171

) authored by @sspaink reported by @christophwille

format: Don't panic on format due to unexpected comments (

#6330

https://github.com/open-policy-agent/opa/issues/6330

) authored by @sspaink reported by @sirpi

format: Avoid modifying strings when formatting (

#6220

https://github.com/open-policy-agent/opa/issues/6220

) authored by @sspaink reported by @zregvart

plugins/status: FIFO buffer channel for status events to prevent slow status API blocking (

#7522

https://github.com/open-policy-agent/opa/pull/7522

) authored by @sspaink

Topdown and Rego

gqlparser: Add JSON annotation in 

internal/gqlparser/ast

 to Position fields (

#7509

https://github.com/open-policy-agent/opa/pull/7509

) authored by @robmyersrobmyers

graphql: Cache GraphQL schema parse results (

#7457

https://github.com/open-policy-agent/opa/pull/7457

) authored by @robmyersrobmyers

topdown: Handling default functions in Partial Eval (

#7220

https://github.com/open-policy-agent/opa/issues/7220

) authored by @johanfylling

topdown: Fix wall clock time init for 

PartialRun()

 (

#7490

https://github.com/open-policy-agent/opa/issues/7490

) authored by @srenatus

topdown: Zero alloc lower/upper unless changed (

#7472

https://github.com/open-policy-agent/opa/pull/7472

) authored by @anderseknert

Docs, Website, Ecosystem

adopters: Cloudsmith adds support for OPA (

#7498

https://github.com/open-policy-agent/opa/pull/7498

) authored by @ndouglas-cloudsmith

docs: Fixed broken docs link (

#7452

https://github.com/open-policy-agent/opa/issues/7452

) reported and authored by @fvarg00

docs: Update built-in function examples for OPA v1 (

#7514

https://github.com/open-policy-agent/opa/issues/7514

) reported and authored by @robmyersrobmyers

docs: Add link to inline schema annotations (

#7496

https://github.com/open-policy-agent/opa/pull/7496

) authored by @kmadan

docs: Add manual trigger to integration docs (

#7473

https://github.com/open-policy-agent/opa/pull/7473

) authored by @charlieegan3

docs: Point path versioned requests to new sites (

#7531

https://github.com/open-policy-agent/opa/pull/7531

) authored by @charlieegan3

docs: Update community slack inviter link (

#7488

https://github.com/open-policy-agent/opa/pull/7488

, 

#7493

https://github.com/open-policy-agent/opa/pull/7493

) authored by @charlieegan3

docs: Set versioned docs links to point to archive (

#7528

https://github.com/open-policy-agent/opa/pull/7528

) authored by @charlieegan3

docs: Update helm-kubernetes-quickstart bundle (

#7469

https://github.com/open-policy-agent/opa/pull/7469

) authored by @johanfylling

docs: Update opa-docker-authz example to use ghcr and v0.10 release tag (

#7513

https://github.com/open-policy-agent/opa/pull/7513

) authored by @larhauga

docs: Fix post merge badge (

#7532

https://github.com/open-policy-agent/opa/pull/7532

) authored by @sspaink

docs: Improve request headers documentation in REST APIs (

#7524

https://github.com/open-policy-agent/opa/pull/7524

) authored by @ali-jalaal

docs: Update edge links to use 

/docs/edge/

 path (

#7529

https://github.com/open-policy-agent/opa/pull/7529

) authored by @charlieegan3

ecosystem: Add NACP integration (

#7503

https://github.com/open-policy-agent/opa/pull/7503

) authored by @charlieegan3

ecosystem: Update traefik integration docs (

#7506

https://github.com/open-policy-agent/opa/pull/7506

) authored by @charlieegan3

ecosystem: Add Principled Evolution integration (

#7495

https://github.com/open-policy-agent/opa/pull/7495

) authored by @kmadan

ecosystem: Add tavo to ecosystem integration (

#7511

https://github.com/open-policy-agent/opa/pull/7511

) authored by @percyding-tavo

Miscellaneous

Dependency updates; notably:

build(deps): bump github.com/hypermodeinc/badger from v4.6.0 to v4.7.0

build(deps): bump github.com/spf13/viper from 1.18.2 to 1.20.1

build(deps): bump golang.org/x/net from 0.37.0 to 0.38.0

build(deps): bump google.golang.org/grpc from 1.71.0 to 1.71.1

build(deps): bump oras.land/oras-go/v2 from 2.3.1 to 2.5.0

1.3.0

This release contains a mix of features, bugfixes, and dependency updates.

New Buffer Option for Decision Logs (

)

A new, optional, buffering mechanism has been added to decision logging.

 

The default buffer is designed around making precise memory footprint guarantees, which can produce lock contention at high loads, negatively impacting query performance.

 

The new event-based buffer is designed to reduce lock contention and improve performance at high loads, but sacrifices the memory footprint guarantees of the default buffer.

The new event-based buffer is enabled by setting the 

decision_logs.reporting.buffer_type

 

configuration option

https://www.openpolicyagent.org/docs/latest/configuration/#decision-logs

 to 

event

.

For more details, see the decision log plugin 

README

https://github.com/open-policy-agent/opa/blob/main/v1/plugins/logs/README.md

.

Reported by @mjungsbluth, authored by @sspaink

OpenTelemetry: HTTP Support and Expanded Batch Span Configuration (

)

Distributed tracing through OpenTelemetry has been extended to support HTTP collectors (enabled by setting the 

distributed_tracing.type

 configuration option to 

http

).

 

Additionally, configuration has been expanded with fine-grained batch span processor 

options

https://www.openpolicyagent.org/docs/latest/configuration/#distributed-tracing

.

Authored and reported by @sqyang94

Runtime, Tooling, SDK

compile: Require multi-term entrypoint paths for optimized bundle building (

#7321

https://github.com/open-policy-agent/opa/issues/7321

) authored by @johanfylling reported by @nikpivkin

fmt: Allow one liner rule grouping (

#6760

https://github.com/open-policy-agent/opa/issues/6760

) authored by @anderseknert

fmt: Fix v0-compatible fmt with stdin (

#7409

https://github.com/open-policy-agent/opa/issues/7409

) authored and reported by @charlieegan3

ir: Fix nil pointer deref in Unmarshal() when handling IsSetStmt (

#7415

https://github.com/open-policy-agent/opa/issues/7415

) authored and reported by @KrisKennawayDD

planner: Fix Wasm vs non-Wasm evaluation difference bug related to the overeager optimization of ref head rules (

#7439

https://github.com/open-policy-agent/opa/pull/7439

) authored by @srenatus

sdk: Removing repeat args from sub-func call (

#7443

https://github.com/open-policy-agent/opa/pull/7443

) authored by @alingse

tester: Including parameterized test cases in test report counter (

#7407

https://github.com/open-policy-agent/opa/issues/7407

) authored by @johanfylling

tester: Only including failed sub-test cases in report summary when non-verbose (

#7426

https://github.com/open-policy-agent/opa/pull/7426

) authored by @johanfylling

Docs, Website, Ecosystem

docs: Add some notes about AI assisted patches (

#7436

https://github.com/open-policy-agent/opa/pull/7436

) authored by @charlieegan3

docs: Add query_parameters_to_set (

#7405

https://github.com/open-policy-agent/opa/pull/7405

) authored by @sedovmik

docs: Delete reference to license key in Envoy tutorial (

#7466

https://github.com/open-policy-agent/opa/pull/7466

) authored by @joostholslag

docs: Fix typo in Envoy tutorial (

#7464

https://github.com/open-policy-agent/opa/pull/7464

) authored by @joostholslag

docs: Update slack inviter link (

#7450

https://github.com/open-policy-agent/opa/pull/7450

) authored by @charlieegan3

docs: Update terraform examples (

#7429

https://github.com/open-policy-agent/opa/pull/7429

) authored by @charlieegan3

docs: Simplify 

kind

 usage instruction in Envoy tutorial (

#7465

https://github.com/open-policy-agent/opa/pull/7465

) authored by @joostholslag

Miscellaneous

Enable unused-receiver linter (revive) (

#7448

https://github.com/open-policy-agent/opa/pull/7448

) authored by @anderseknert

Dependency updates; notably:

build(deps): bump github.com/containerd/containerd from 1.7.26 to 1.7.27

build(deps): bump github.com/dgraph-io/badger/v4 from 4.5.1 to 4.6.0

build(deps): bump github.com/opencontainers/image-spec from 1.1.0 to 1.1.1

build(deps): bump github.com/prometheus/client_golang 1.21.0 to 1.21.1

build(deps): bump golang.org/x/net from 0.35.0 to 0.37.0

build(deps): bump golang.org/x/time from 0.10.0 to 0.11.0

build(deps): bump google.golang.org/grpc from 1.70.0 to 1.71.0

build(deps): bump go.opentelemetry.io deps to 1.35.0/0.60.0

1.2.0

This release contains a mix of features, performance improvements, and bugfixes.

Parameterized Rego Tests (

)

Rego tests now support parameterization, allowing a single test rule to include multiple, hierarchical, named test cases.

 

This feature is useful for data-driven testing, where a single test rule can be used for multiple test cases with different inputs and expected outputs.

package example_test

test_concat[note] if {
	some note, tc in {
		"empty + empty": {
			"a": [],
			"b": [],
			"exp": [],
		},
		"empty + filled": {
			"a": [],
			"b": [1, 2],
			"exp": [1, 2],
		},
		"filled + filled": {
			"a": [1, 2],
			"b": [3, 4],
			"exp": [1, 2, 3], # Faulty expectation, this test case will fail
		},
	}

	act := array.concat(tc.a, tc.b)
	act == tc.exp
}


rego

$ opa test example_test.rego
example_test.rego:
data.example_test.test_concat: FAIL (263.375µs)
  empty + empty: PASS
  empty + filled: PASS
  filled + filled: FAIL
--------------------------------------------------------------------------------
FAIL: 1/1


cmd

See the 

documentation

https://www.openpolicyagent.org/docs/latest/policy-testing/#parameterized-tests-and-data-driven-testing

 for more information.

Authored by @johanfylling, reported by @anderseknert

Performance Improvements

perf: Add ref.CopyNonGround (

#7350

https://github.com/open-policy-agent/opa/pull/7350

) authored by @anderseknert

perf: 

opa fmt

 3x faster formatting (

#7341

https://github.com/open-policy-agent/opa/pull/7341

) authored by @anderseknert

perf: Cost of indexing greatly reduced (

#7370

https://github.com/open-policy-agent/opa/pull/7370

) authored by @anderseknert

perf: Eval optimizations (

#7367

https://github.com/open-policy-agent/opa/pull/7367

) authored by @anderseknert

perf: Intern annotation terms (

#7365

https://github.com/open-policy-agent/opa/pull/7365

) authored by @anderseknert

perf: Slightly more efficient policy scanning (

#7368

https://github.com/open-policy-agent/opa/pull/7368

) authored by @anderseknert

perf: Switch to a faster xxhash package (

7362

https://github.com/open-policy-agent/opa/pull/7362

) authored by @Juneezee

perf: Use GetByValue to avoid boxing to interface{} (

#7372

https://github.com/open-policy-agent/opa/pull/7372

) authored by @anderseknert

perf: Various small improvements (

#7357

https://github.com/open-policy-agent/opa/pull/7357

) authored by @anderseknert

perf: Improve storage lookup performance (

#7336

https://github.com/open-policy-agent/opa/pull/7336

) authored by @anderseknert

perf: optimize iteration (

#7327

https://github.com/open-policy-agent/opa/pull/7327

) authored by @anderseknert

Topdown and Rego

rego+topdown: Allow providing custom base cache (

#7329

https://github.com/open-policy-agent/opa/pull/7329

) authored by @anderseknert

Runtime, Tooling, SDK

ast: Add missing 

BuildAnnotationSet

 to 

ast

 v0 (

#7347

https://github.com/open-policy-agent/opa/issues/7347

) authored by @anderseknert

ast: Eliminate allocation in Value.Find, and other improvements (

#7319

https://github.com/open-policy-agent/opa/pull/7319

) authored by @anderseknert

ast: Use byte for RuleKind and DocKind (

#7332

https://github.com/open-policy-agent/opa/pull/7332

) authored by @anderseknert

ast.InterfaceToValue: add test case for 

[]byte

 (

#7379

https://github.com/open-policy-agent/opa/pull/7379

) authored by @dennygursky

ast: support []string and ast.Value in ast.InterfaceToValue (

#7306

https://github.com/open-policy-agent/opa/pull/7306

) authored by @regeda

bundle: Fixing issue where 

--v0-compatible

 isn't respected for custom bundles (

#7338

https://github.com/open-policy-agent/opa/pull/7338

) authored by @johanfylling

cmd: Handle failing tests in 

opa test --bench

 (

#7205

https://github.com/open-policy-agent/opa/issues/7205

) authored by @anderseknert

cmd: Add decision ID to 

opa exec

 output (

#7373

https://github.com/open-policy-agent/opa/pull/7373

) authored by @anderseknert

oracle: Make oracle public under v1/ast/oracle (

#7265

https://github.com/open-policy-agent/opa/issues/7265

) authored by @anderseknert

oracle: Allow passing own compiler to oracle (

#7354

https://github.com/open-policy-agent/opa/pull/7354

) authored by @anderseknert

plugins/discovery: Enable tracing for discovery plugin (

#7299

https://github.com/open-policy-agent/opa/pull/7299

) authored by @mjungsbluth

plugins/rest: Do not attach authorization header in bearerAuthPlugin if response is a redirect (

#7308

https://github.com/open-policy-agent/opa/pull/7308

) authored by @carabasdaniel

server+distributedtracing: Add Additional Resource Attributes for OpenTelemetry (

#7322

https://github.com/open-policy-agent/opa/issues/7322

) authored by @briankahoot reported by @briankahoot

util: Add util.HasherMap (

#7363

https://github.com/open-policy-agent/opa/pull/7363

) authored by @anderseknert

Docs, Website, Ecosystem

docs: Add support link to README (

#7359

https://github.com/open-policy-agent/opa/pull/7359

) (authored by @anderseknert)

docs: Update example bundle to be v1 compatible (

#7342

https://github.com/open-policy-agent/opa/pull/7342

) authored by @ashutosh-narkar

docs: Add note about v1.0 addr behaviour (

#7360

https://github.com/open-policy-agent/opa/issues/7360

) authored by @charlieegan3 reported by @ali-jalaal

docs: Update homepage examples to drop 

v1 import

 (

#7391

https://github.com/open-policy-agent/opa/pull/7391

) authored by @charlieegan3

docs: Updating 

--v1-compatible

 mentions outside the v1 upgrade guide and v0 compatibility docs (

#7337

https://github.com/open-policy-agent/opa/pull/7337

) authored by @johanfylling

docs: Fixed invalid links to examples (

#7326

https://github.com/open-policy-agent/opa/pull/7326

) authored by @JonathanDeLaCruzEncora

MAINTAINERS: Add Anders and Charlie as maintainers (

#7318

https://github.com/open-policy-agent/opa/pull/7318

) authored by @charlieegan3

Miscellaneous

build+test: Add 

make test-short

 task (#7364) (authored by @anderseknert)

build: Add gocritic linter (

#7377

https://github.com/open-policy-agent/opa/pull/7377

) authored by @anderseknert

build: Add nilness linter from govet (

#7335

https://github.com/open-policy-agent/opa/pull/7335

) authored by @anderseknert

build: Add perfsprint linter (

#7334

https://github.com/open-policy-agent/opa/pull/7334

) authored by @anderseknert

ci: Tagging release binaries with build version (

#7395

https://github.com/open-policy-agent/opa/pull/7395

, 

#7397

https://github.com/open-policy-agent/opa/pull/7397

, 

#7400

https://github.com/open-policy-agent/opa/pull/7400

) authored by @johanfylling

test: fix race in 

TestIntraQueryCache_ClientError

 and 

TestInterQueryCache_ClientError

 (

#7280

https://github.com/open-policy-agent/opa/pull/7280

) authored by @Juneezee

misc: Use Go 1.22+ int ranges (

#7328

https://github.com/open-policy-agent/opa/pull/7328

) authored by @anderseknert

Dependency updates; notably:

build: bump go from 1.23.5 to 1.24.0

build(deps): bump github.com/agnivade/levenshtein from 1.2.0 to 1.2.1

build(deps): bump github.com/containerd/containerd from 1.7.25 to 1.7.26

build(deps): bump github.com/google/go-cmp from 0.6.0 to 0.7.0

build(deps): bump github.com/prometheus/client_golang

build(deps): bump github.com/spf13/cobra from 1.8.1 to 1.9.1

build(deps): bump github.com/spf13/pflag from 1.0.5 to 1.0.6

build(deps): bump golang.org/x/net from 0.34.0 to 0.35.0

build(deps): bump golang.org/x/time from 0.9.0 to 0.10.0

build(deps): bump ossf/scorecard-action from 2.4.0 to 2.4.1

Bump golangci-lint from v1.60.1 to 1.64.5

1.1.0

This release contains a mix of features, performance improvements, and bugfixes.

Performance Improvements

ast: Remove jsonOptions from AST nodes and terms (

#7281

https://github.com/open-policy-agent/opa/pull/7281

) authored by @anderseknert

ast+plugins: Optimize activation of bundles with no inter-bundle path overlap (

#7144

https://github.com/open-policy-agent/opa/issues/7144

) authored and reported by @sqyang94

bundle: Optimizing rego-version management in bundle activation (

#7296

https://github.com/open-policy-agent/opa/pull/7296

) authored by @johanfylling

cmd: Don't generate JSON from result in 

opa bench

 (

#7291

https://github.com/open-policy-agent/opa/issues/7291

) authored by @anderseknert

topdown: Adding configurable token cache to 

io.jwt

 token verification built-ins (

#7274

https://github.com/open-policy-agent/opa/pull/7274

) authored by @johanfylling

topdown: Reduce allocations in hot path (

#7288

https://github.com/open-policy-agent/opa/pull/7288

) authored by @anderseknert

perf: Improvements to terms and built-in functions (

#7284

https://github.com/open-policy-agent/opa/pull/7284

) authored by @anderseknert

perf: add Regorus ACI benchmark tests (

#7298

https://github.com/open-policy-agent/opa/pull/7298

) authored by @anderseknert

plugins: Don't use reflect.DeepEqual for errors (

#7238

https://github.com/open-policy-agent/opa/issues/7238

) authored by @anderseknert

testing: replace reflect.DeepEqual where possible (

#7286

https://github.com/open-policy-agent/opa/pull/7286

) authored by @anderseknert

Topdown and Rego

topdown: Fix out of range error in 

numbers.range

 built-in (

#7269

https://github.com/open-policy-agent/opa/issues/7269

) authored by @anderseknert

topdown+rego+server: Allow opt-in for evaluating non-det builtins in PE (

#6496

https://github.com/open-policy-agent/opa/issues/6496

) authored by @srenatus

Runtime, Tooling, SDK

bundle: Add info about the correct rego version to parse modules on the store (

#7278

https://github.com/open-policy-agent/opa/pull/7278

) co-authored by @ashutosh-narkar and @johanfylling

bundle+plugins: Fixing issue where bundle plugin could panic on reconfiguration (SDK use) (

#7297

https://github.com/open-policy-agent/opa/issues/7297

) authored by @johanfylling reported by @carabasdaniel

cmd: Fix printed representation of ref head rules in 

opa repl

 (

#7301

https://github.com/open-policy-agent/opa/issues/7301

) authored by @anderseknert reported by @tsandall

cmd: Respect 

--v0-compatible

 for 

opa eval

 partial eval support modules (

#7251

https://github.com/open-policy-agent/opa/pull/7251

) authored by @johanfylling

golangci: fix invalid 

linter-settings

 configuration name (

#7244

https://github.com/open-policy-agent/opa/pull/7244

) authored by @Juneezee

plugins/logs: Add support for masking with array keys (

#6883

https://github.com/open-policy-agent/opa/issues/6883

) authored by @charlieegan3

tester: code nitpicks (

#7252

https://github.com/open-policy-agent/opa/pull/7252

) authored by @srenatus

util: Add util.Keys and util.KeysSorted (

#7285

https://github.com/open-policy-agent/opa/pull/7285

) authored by @anderseknert

Docs, Website, Ecosystem

docs: Update docker compose file in HTTP API tutorial and use addr for binding (

#7264

https://github.com/open-policy-agent/opa/issues/7264

) authored and reported by @zanliffick

docs: Make 'ancient' warnings closable (

#7253

https://github.com/open-policy-agent/opa/issues/7253

) authored by @srenatus reported by @konradzagozda

docs: Redirect opa-1 to v0-upgrade (

#7259

https://github.com/open-policy-agent/opa/pull/7259

) authored by @charlieegan3

docs: Use preformatted strings in fmt help (

#7263

https://github.com/open-policy-agent/opa/pull/7263

) authored by @charlieegan3

docs: Fix typo in k8s primer (

#7242

https://github.com/open-policy-agent/opa/pull/7242

) authored by @vicentinileonardo

docs: Formatting and wording fixes (

#7268

https://github.com/open-policy-agent/opa/pull/7268

) authored by @kamilturek

docs: Update output document of Envoy plugin. (

#7241

https://github.com/open-policy-agent/opa/pull/7241

) authored by @regeda

Miscellaneous

ci(nightly): Remove vendor w/o modproxy check (

#7292

https://github.com/open-policy-agent/opa/pull/7292

) authored by @srenatus

Dependency updates; notably:

build(go): bump to 1.23.5 (

7279

https://github.com/open-policy-agent/opa/pull/7279

) authored by @srenatus

build(deps): upgrade github.com/dgraph-io/badger to v4 (4.5.1) (

#7239

https://github.com/open-policy-agent/opa/pull/7239

) authored by @Juneezee

build(deps): bump github.com/containerd/containerd from 1.7.24 to 1.7.25

build(deps): bump github.com/tchap/go-patricia/v2 from 2.3.1 to 2.3.2

build(deps): bump golang.org/x/net from 0.33.0 to 0.34.0

build(deps): bump golang.org/x/time from 0.8.0 to 0.9.0

build(deps): bump google.golang.org/grpc from 1.69.2 to 1.70.0

build(deps): bump go.opentelemetry.io deps to 1.34.0/0.59.0

1.0.1

This is a bug fix release addressing the following issues:

build(go): bump to 1.23.5 (authored by @srenatus).

 

Addressing 

CVE-2024-45341

 and 

CVE-2024-45336

 vulnerabilities in the Go runtime.

bundle: Add info about the correct rego version to parse modules on the store, co-authored by @ashutosh-narkar and @johanfylling in 

#7278

https://github.com/open-policy-agent/opa/pull/7278

.

 

Fixing an issue where the rego-version for individual modules was lost during bundle deactivation (bundle lifecycle) if this version diverged from the active runtime rego-version.

 

This could cause reloading of v0 bundles to fail when OPA was not running with the 

--v0-compatible

 flag.

1.0.0

NOTES:

The minimum version of Go required to build the OPA module is 

1.22

We are excited to announce 

OPA 1.0

, a milestone release consolidating an improved developer experience for the future of Policy as Code.

 

The release makes new functionality designed to simplify policy writing and improve the language's consistency the default.

Changes to Rego in OPA 1.0

Below we highlight some key changes to the defaults in OPA 1.0:

Using 

if

 for all rule definitions and 

contains

 for multi-value rules is now mandatory, not just when using the 

rego.v1

 import.

Other new keywords (

every

, 

in

) are available without any imports.

Previously requirements that were only run in "strict mode" (like 

opa check --strict

) are now the default. Duplicate imports and imports which shadow each other are no longer allowed.

OPA 1.0 comes with a range of backwards compatibility features to aid your migrations, please see the 

v0 compatibility guide

https://www.openpolicyagent.org/docs/latest/v0-compatibility/

 

if you must continue to support v0 Rego.

Read more about the OPA 1.0 announcement on the 

OPA blog

https://blog.openpolicyagent.org/

.

Following are other changes that are included in OPA 1.0.

Improvements to memory allocations

PRs 

#7172

https://github.com/open-policy-agent/opa/pull/7172

, 

#7190

https://github.com/open-policy-agent/opa/pull/7190

,

 

#7193

https://github.com/open-policy-agent/opa/pull/7193

, 

#7165

https://github.com/open-policy-agent/opa/pull/7165

,

 

#7168

https://github.com/open-policy-agent/opa/pull/7168

, 

#7191

https://github.com/open-policy-agent/opa/pull/7191

 &

 

#7222

https://github.com/open-policy-agent/opa/pull/7222

 together improve the memory performance of OPA. Key strategies

 

include reusing pointers and optimizing array and object operations, minimizing intermediate object creation, and using 

sync.Pool

 

to manage memory-heavy operations. These changes cumulatively greatly reduced the number of allocations and improved

 

evaluation speed by 10-20%. Additional benchmarks highlighted significant memory and speed improvements in custom

 

function evaluation.

Authored by @anderseknert.

Wrap http.RoundTripper for SDK users

PR 

#7180

https://github.com/open-policy-agent/opa/pull/7180

 adds an 

EvalHTTPRoundTrip

 EvalOption and query-level 

WithHTTPRoundTrip

 option.

 

Both use a new function type which converts an 

http.Transport

 configured by topdown to an 

http.RoundTripper

.

 

This supports use cases requiring the customization of the 

http.send

 built in behavior.

Authored by @evankanderson.

Improvements to scientific notation parsing in 

units.parse

PR 

#7147

https://github.com/open-policy-agent/opa/pull/7147

 extends the behaviour of 

extractNumAndUnit

 to support

 

scientific notation values. This means values such as 

1e3KB

 can now be handled by this function.

Authored by @berdanA.

Support customized buckets 

bundle_loading_duration_ns

 metric

PR 

#7156

https://github.com/open-policy-agent/opa/pull/7156

 extends OPA’s Prometheus configuration to allow the

 

setting of user defined buckets for metrics. This aids when debugging the loading of slow bundles.

Authored by @jwu730-1.

Test suite performance improvements

PR 

#7126

https://github.com/open-policy-agent/opa/pull/7126

 updates tests to improve performance. Topdown and 

storage/disk/

 

tests now run around 50% and 75% faster respectively.

Authored by @philipaconrad.

OPA 1.0 Preparation

Update v1 capabilities by @johanfylling in 

#7216

https://github.com/open-policy-agent/opa/pull/7216

v1 API by @johanfylling in 

#7215

https://github.com/open-policy-agent/opa/pull/7215

Updating formatter to not drop 

rego.v1

 and 

future.keywords

 imports for v1 by @johanfylling in 

#7224

https://github.com/open-policy-agent/opa/pull/7224

Update docs and server binding address per OPA 1.0 specs by @ashutosh-narkar & @charlieegan3 in 

#7140

https://github.com/open-policy-agent/opa/pull/7140

Renaming 

--rego-v1

 cmd flag to 

--v0-v1

 by @johanfylling in 

#7225

https://github.com/open-policy-agent/opa/pull/7225

Topdown and Rego

Provide a more useful error message when there are conflicting default rules by @tjons in 

#7164

https://github.com/open-policy-agent/opa/pull/7164

Fix test flakes in 

topdown/cache

 by @evankanderson in 

#7188

https://github.com/open-policy-agent/opa/pull/7188

Add description to all built-in function args and return values by @anderseknert in 

#7153

https://github.com/open-policy-agent/opa/pull/7153

Built-in function 

to_number

 now rejects "Inf", "Infinity" and "NaN" values by @sikehish in 

#7203

https://github.com/open-policy-agent/opa/pull/7203

Update eval_cancel_error logic to separate context canceled, timeout errors by @mchitten in 

#7202

https://github.com/open-policy-agent/opa/pull/7202

Runtime, Tooling, SDK

Respect runtime rego-version in RESTful policy API by @johanfylling in 

#7183

https://github.com/open-policy-agent/opa/pull/7183

Debugger: allow YAML to be used as input by @anderseknert in 

#7178

https://github.com/open-policy-agent/opa/pull/7178

opa build

: provide an option to preserve print statements for the "wasm" target (#7194) by @me-viper in 

#7195

https://github.com/open-policy-agent/opa/pull/7195

Fix improper formatter behavior when comprehension contains comment by @tjons in 

#7169

https://github.com/open-policy-agent/opa/pull/7169

runtime: send version report less often when OPA long-running by @srenatus in 

#7211

https://github.com/open-policy-agent/opa/pull/7211

opa eval

: Return error if illegal arguments passed with 

--unknowns

 flag by @kd-labs in 

#7149

https://github.com/open-policy-agent/opa/pull/7149

Enable direct error handling for bundle plugin trigger method by @torwunder in 

#7143

https://github.com/open-policy-agent/opa/pull/7143

Docs, Website, Ecosystem

Add VodafoneZiggo as adopters by @Parsifal-M in 

#7154

https://github.com/open-policy-agent/opa/pull/7154

Add opa-java-wasm to docs by @andreaTP in 

#7199

https://github.com/open-policy-agent/opa/pull/7199

Dependency Updates

(build) golangci-lint: v1.59.1 -> v1.60.1 by @srenatus in 

#7175

https://github.com/open-policy-agent/opa/pull/7175

github.com/containerd/containerd: v1.7.23 -> v1.7.24

github.com/fsnotify/fsnotify: v1.7.0 -> v1.8.0

golang.org/x/net: v0.30.0 -> v0.33.0

golang.org/x/time: v0.7.0 -> v0.8.0

google.golang.org/grpc: v1.67.1 -> v1.69.2

go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp: v0.53.0 -> v0.58.0

go.opentelemetry.io/otel: v1.28.0 -> v1.33.0

go.opentelemetry.io/otel/exporters/otlp/otlptrace: v1.28.0 -> v1.33.0

go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc: v1.28.0 -> v1.33.0

go.opentelemetry.io/otel/sdk: v1.28.0 -> v1.33.0

go.opentelemetry.io/otel/trace: v1.28.0 -> v1.33.0

0.70.0

This release contains a mix of features, performance improvements, and bugfixes.

Optimized read mode for OPA's in-memory store (

)

A new optimized read mode has been added to the default in-memory store, where data written to the store is eagerly converted

 

to AST values (the data format used during evaluation). This removes the time spent converting raw data values to AST

 

during policy evaluation, thereby improving performance.

The memory footprint of the store will increase, as processed AST values generally take up more space in memory than the

 

corresponding raw data values, but overall memory usage of OPA might remain more stable over time, as pre-converted data

 

is shared across evaluations and isn't recomputed for each evaluation, which can cause spikes in memory usage.

This mode can be enabled for 

opa run

, 

opa eval

, and 

opa bench

 by setting the 

--optimize-store-for-read-speed

 flag.

More information about this feature can be found 

here

https://www.openpolicyagent.org/docs/v0.70.0/policy-performance/#storage-optimization

.

Co-authored by @johanfylling and @ashutosh-narkar.

Topdown and Rego

topdown: Use new Inter-Query Value Cache for 

json.match_schema

 built-in function (

#7011

https://github.com/open-policy-agent/opa/issues/7011

) authored by @anderseknert reported by @lcarva

ast: Fix location text attribute for multi-value rules with generated body  (

#7128

https://github.com/open-policy-agent/opa/issues/7128

) authored by @anderseknert

ast: Fix regression in 

opa check

 where a file that referenced non-provided schemas failed validation (

#7124

https://github.com/open-policy-agent/opa/pull/7124

) authored by @tjons

test/cases/testdata: Fix bug in test by replacing unification by explicit equality check (

#7093

https://github.com/open-policy-agent/opa/pull/7093

) authored by @matajoh

ast: Replace use of yaml.v2 library with yaml.v3. The earlier version would parse 

yes

/

no

 values as boolean. The usage of yaml.v2 in the parser was unintentional and now has been updated to yaml.v3 (

#7090

https://github.com/open-policy-agent/opa/issues/7090

) authored by @anderseknert

Runtime, Tooling, SDK

cmd: Make 

opa check

 respect 

--ignore

 when 

--bundle

 flag is set (

#7136

https://github.com/open-policy-agent/opa/issues/7136

) authored by @anderseknert

server/writer: Properly handle result encoding errors which earlier on failure would emit logs such as 

superfluous call to WriteHeader()

 while still returning 

200

 HTTP status code. Now, errors encoding the payload properly lead to 

500

 HTTP status code, without extra logs. Also use Header().Set() not Header().Add() to avoid duplicate content-type headers  (

#7114

https://github.com/open-policy-agent/opa/pull/7114

) authored by @srenatus

cmd: Support 

file://

 format for TLS key material file flags in 

opa run

 (

#7094

https://github.com/open-policy-agent/opa/pull/7094

) authored by @alexrohozneanu

plugins/rest/azure: Support managed identity for App Service / Container Apps (

#7085

https://github.com/open-policy-agent/opa/issues/7085

) reported and authored by @apc-kamezaki

debug: Fix step-over behaviour when exiting partial rules (

#7096

https://github.com/open-policy-agent/opa/pull/7096

) authored by @johanfylling

util+plugins: Fix potential memory leaks with explicit timer cancellation (

#7089

https://github.com/open-policy-agent/opa/pull/7089

) authored by @philipaconrad

Docs, Website, Ecosystem

docs: Fix OCI example with updated flag used by the ORAS CLI  (

#7130

https://github.com/open-policy-agent/opa/pull/7130

) authored by @b3n3d17

docs: Delete Atom editor from supported editor integrations (

#7111

https://github.com/open-policy-agent/opa/pull/7111

) authored by @KaranbirSingh7

docs/website: Add Styra OPA ASP.NET Core SDK integration (

#7073

https://github.com/open-policy-agent/opa/pull/7073

) authored by @philipaconrad

docs/website: Update compatibility information on the rego-cpp integration (

#7078

https://github.com/open-policy-agent/opa/pull/7078

) authored by @matajoh

Miscellaneous

Dependency updates; notably:

build(deps): bump github.com/containerd/containerd from 1.7.22 to 1.7.23

build(deps): bump github.com/prometheus/client_golang from 1.20.4 to 1.20.5

build(deps): bump golang.org/x/net from 0.29.0 to 0.30.0

build(deps): bump golang.org/x/time from 0.6.0 to 0.7.0

build(deps): bump google.golang.org/grpc from 1.67.0 to 1.67.1

0.69.0

This release contains a mix of features, bugfixes and necessary tooling and test changes required to support the upcoming OPA 

1.0

 release.

Inter-Query Value Cache (

)

OPA now has a new inter-query value cache added to the SDK. It is intended to be used for values that are expensive to

 

compute and can be reused across multiple queries. The cache can be leveraged by built-in functions to store values

 

that otherwise aren't appropriate for the existing inter-query cache; for instance when the entry size isn't an

 

appropriate or primary limiting factor for cache eviction.

The default size of the inter-query value cache is unbounded, but can be configured via the

 

caching.inter_query_builtin_value_cache.max_num_entries

 configuration field. OPA will drop random items from the cache

 

if this limit is exceeded.

The cache is used by the 

regex

 and 

glob

 built-in functions, which previously had individual, non-configurable

 

caches with a max entry size of 

100

 each.

Currently, the cache is only exercised when running OPA in server mode (ie. 

opa run -s

). Also this feature is unsupported

 

for WASM.

Authored by @ashutosh-narkar, reported by @amirsalarsafaei

Topdown and Rego

Future-proofing tests in the 

ast

, 

topdown

, 

rego

 etc. packages to be 

1.0

 compatible (authored by @johanfylling)

ast: Attach annotation to static part of rule ref (

#7050

https://github.com/open-policy-agent/opa/issues/7050

) authored by @anderseknert

ast: Make 

Module.String()

 include 

if

/

contains

 for v1 modules (

#6973

https://github.com/open-policy-agent/opa/issues/6973

) authored by @johanfylling reported by @nikpivkin

topdown/http: Stop 

http.send

 latency timer when an error is encountered (

#7007

https://github.com/open-policy-agent/opa/pull/7007

) authored by @lukyer

ast/compile: Refactor local variable replacement and replace declared variables in 

with

's target (

#6979

https://github.com/open-policy-agent/opa/issues/6979

) authored by @srenatus reported by @bluebrown

ast: Update type checker to cache schema types (

#6970

https://github.com/open-policy-agent/opa/pull/6970

) authored by @nikpivkin

test: Fix indentation in a YAML test case (

#7039

https://github.com/open-policy-agent/opa/pull/7039

) authored by @matajoh

format: Bracketing keyword ref elements in formatter output (

#7010

https://github.com/open-policy-agent/opa/pull/7010

) authored by @johanfylling

Runtime, Tooling, SDK

Future-proofing tests in the 

sdk

, 

downlaod

, 

server

 , 

cmd

 etc. packages to be 

1.0

 compatible (authored by @johanfylling)

cmd: Add 

--v0-compatible

 flag to make OPA behave as 

v0.x

 post 

v1.0

 release (

#7065

https://github.com/open-policy-agent/opa/pull/7065

) authored by @johanfylling

util: Strip  UTF-8 BOM from input JSON when found (

#6988

https://github.com/open-policy-agent/opa/issues/6988

) authored by @anderseknert reported by @adhilto

plugins/rest: Support reading AWS token from the filesystem for the AWS container credential provider (

#6997

https://github.com/open-policy-agent/opa/pull/6997

) authored by @cmaddalozzo

debug: Add 

RegoOption

 launch option to debugger for setting custom Rego options (

#7045

https://github.com/open-policy-agent/opa/issues/7045

) authored by @johanfylling

debug: Always include 

Input

 and 

Data

 variable scopes to ease discoverability of the scopes (

#7074

https://github.com/open-policy-agent/opa/pull/7074

) authored by @johanfylling

wasm: Fix arithmetic comparison for large numbers, caused by an integer overflow (

#6991

https://github.com/open-policy-agent/opa/issues/6991

) authored by @Ptroger

Docs, Website, Ecosystem

Add Marsh McLennan to adopters (

#7060

https://github.com/open-policy-agent/opa/issues/7060

) authored by @anderseknert reported by @pratimsc

Add APIwiz to adopters (

#7067

https://github.com/open-policy-agent/opa/pull/7067

) authored by @anderseknert

docs: Fix misnomer in OPA-Istio tutorial to document Istio's AuthorizationPolicy API (

#6984

https://github.com/open-policy-agent/opa/pull/6984

) authored by @tjons

docs: Readme updates to highlight more up-to-date information about OPA (

#7066

https://github.com/open-policy-agent/opa/pull/7066

) authored by @charlieegan3

docs: Update documentation to show Debug API uses (

#7036

https://github.com/open-policy-agent/opa/pull/7036

)  authored by @charlieegan3

docs: Simplify the OPA-Istio tutorial example policy (

#7059

https://github.com/open-policy-agent/opa/pull/7059

) authored by @anderseknert

website: Update policy examples on the OPA home page to be 

1.0

 compatible  (

#7033

https://github.com/open-policy-agent/opa/pull/7033

)  authored by @charlieegan3

Miscellaneous

build: Bump github.com/golang/glob, remove replace directive (

#7024

https://github.com/open-policy-agent/opa/issues/7024

) authored by @srenatus reported by @mmannerm

Dependency updates; notably:

build(deps): bump github.com/containerd/containerd from 1.7.21 to 1.7.22

build(deps): bump github.com/prometheus/client_golang from 1.20.2 to 1.20.4

build(deps): bump go.uber.org/automaxprocs from 1.5.3 to 1.6.0

build(deps): bump golang.org/x/net from 0.28.0 to 0.29.0

build(deps): bump google.golang.org/grpc from 1.66.0 to 1.67.0

build(go): bump 1.22.5 to 1.23.1 (

#7006

https://github.com/open-policy-agent/opa/pull/7006

) authored by @srenatus

0.68.0

This release contains a mix of features and bugfixes.

Breaking Changes

entrypoint

 annotation implies 

document

 scope (

)

The 

entrypoint annotation's

https://www.openpolicyagent.org/docs/latest/policy-language/#entrypoint

 scope requirement

 

has changed from 

rule

 to 

document

 (

https://github.com/open-policy-agent/opa/issues/6798

#6798

).

 

Furthermore, if no 

scope

 annotation is declared for a METADATA block preceding a rule, the presence of an 

entrypoint

 

annotation with a 

true

 value will assign the block a 

document

 scope, where the 

rule

 scope is otherwise the default.

In practice, a rule entrypoint always point to the entire document and not a particular rule definition. The previous behavior was a bug, and one we've now addressed.

Authored by @anderseknert

Topdown and Rego

ast: Fixing nil-pointer dereference in compiler for partial rule edge case (

#6930

https://github.com/open-policy-agent/opa/issues/6930

) authored by @johanfylling

ast+parser: Add hint to future-proof imports (

6968

https://github.com/open-policy-agent/opa/pull/6968

) authored by @srenatus

topdown: Adding unification scope to virtual-cache key. Fixing issue where false positive cache hits can occur when unification "restricts" the scope of ref-head rule evaluation (

#6926

https://github.com/open-policy-agent/opa/issues/6926

) authored by @johanfylling reported by @anderseknert

topdown: Marshal JWT encode sign inputs as JSON (

#6934

https://github.com/open-policy-agent/opa/pull/6934

) authored by @charlieegan3

Runtime, Tooling, SDK

ast: Make type checker 

copy

 method copy all values (

#6949

https://github.com/open-policy-agent/opa/pull/6949

) authored by @anderseknert

ast: Include term locations in rule heads when requested (

#6860

https://github.com/open-policy-agent/opa/issues/6860

) authored by @anderseknert

debug: Adding experimental debugger SDK (

#6876

https://github.com/open-policy-agent/opa/issues/6876

) authored by @johanfylling

distributedtracing: allow OpenTelemetry resource attributes to be configured under distributed_tracing config (

#6942

https://github.com/open-policy-agent/opa/issues/6942

) authored and reported by @brettmc

download: Fixing issue when saving OCI bundles on disk (

#6939

https://github.com/open-policy-agent/opa/issues/6939

) authored and reported by @Sergey-Kizimov

logging: Always include HTTP request context in incoming req context (

#6951

https://github.com/open-policy-agent/opa/issues/6951

) authored by @ashutosh-narkar reported by @alvarogomez93

plugins/bundle: Avoid race-condition during bundle reconfiguration and activation (

#6849

https://github.com/open-policy-agent/opa/issues/6849

) authored by @ashutosh-narkar reported by @Pushpalanka

plugins/bundle: Escape reserved chars used in persisted bundle directory name (

#6915

https://github.com/open-policy-agent/opa/issues/6915

) authored by @ashutosh-narkar reported by @alvarogomez93

plugins/rest: Support AWS_CONTAINER_CREDENTIALS_FULL_URI metadata endpoint (

#6893

https://github.com/open-policy-agent/opa/issues/6893

) authored and reported by @mbamber

util+server: Fix bug around chunked request handling. (

#6904

https://github.com/open-policy-agent/opa/issues/6904

) authored by @philipaconrad reported by @David-Wobrock

opa exec

: This command never supported "pretty" formatting (

--format=pretty

 or 

-f pretty

), only 

json

. Passing 

pretty

 is now invalid. (

#6923

https://github.com/open-policy-agent/opa/pull/6923

) authored by @srenatus

 

Note that the flag is now unnecessary, but it's kept so existing calls like 

opa exec -fjson ...

 remain valid.

Security Fix: CVE-2024-8260 (

)

This release includes a fix where OPA would accept UNC locations on Windows. Reading those could leak NTLM hashes.

 

The attack vector would include an adversary tricking the user in passing an UNC path to OPA, e.g. 

opa eval -d $FILE

.

 

UNC paths are now forbidden. If this is an issue for you, please reach out on Slack or GitHub issues.

Reported by Shelly Raban

 

Authored by @ashutosh-narkar

Docs, Website, Ecosystem

docs: Suggest using 

opa-config.yaml

 as name for config file (#6966) (

#6959

https://github.com/open-policy-agent/opa/issues/6959

) authored by @anderseknert

docs: Add documentation for OPA Spring Boot integration (

#6898

https://github.com/open-policy-agent/opa/pull/6898

) authored by @charlieegan3

docs: Update Istio tutorial (

#6896

https://github.com/open-policy-agent/opa/pull/6896

) authored by @Pindar

docs: Update contrib docs (

#6974

https://github.com/open-policy-agent/opa/pull/6974

) authored by @charlieegan3

docs: Add Lula to the OPA ecosystem (

#6902

https://github.com/open-policy-agent/opa/pull/6902

) authored by @brandtkeller

docs: Add github action policy testing automation (

#6954

https://github.com/open-policy-agent/opa/pull/6954

) authored by @oycyc

docs: Mention 

http.send

 in inter-query cache config docs (

#6953

https://github.com/open-policy-agent/opa/pull/6953

) authored by @anderseknert

docs+topdown: Fixing typos in built-in descriptions (

#6940

https://github.com/open-policy-agent/opa/pull/6940

) authored by @msorens

Miscellaneous

build: Make it possible to build only wasm testcases (

#6920

https://github.com/open-policy-agent/opa/pull/6920

) authored by @andreaTP

Dependency updates; notably:

build(deps): bump github.com/containerd/containerd from 1.7.20 to 1.7.21

build(deps): bump github.com/prometheus/client_golang from 1.19.1 to 1.20.2

build(deps): bump golang.org/x/net from 0.27.0 to 0.28.0

build(deps): bump golang.org/x/time from 0.5.0 to 0.6.0

build(deps): bump google.golang.org/grpc from 1.65.0 to 1.66.0

0.67.1

This is a bug fix release addressing the following issue:

util+server: Fix bug around chunked request handling (

#6906

https://github.com/open-policy-agent/opa/pull/6906

) authored by @philipaconrad, reported by @David-Wobrock. A request handling bug was introduced in (

#6868

https://github.com/open-policy-agent/opa/pull/6868

), which caused OPA to treat all incoming chunked requests as if they had zero-length request bodies.

0.67.0

This release contains a mix of features, a new builtin function (

strings.count

), performance improvements, and bugfixes.

Breaking Change

Request Body Size Limits

OPA now automatically rejects very large requests (

#6868

https://github.com/open-policy-agent/opa/pull/6868

) authored by @philipaconrad.

 

Requests with a 

Content-Length

 larger than 128 MB uncompressed, and gzipped requests with payloads that decompress to

 

larger than 256 MB will be rejected, as part of hardening OPA against denial-of-service attacks. Previously, a large

 

enough request could cause an OPA instance to run out of memory in low-memory sidecar deployment scenarios, just from

 

attempting to read the request body into memory.

These changes allow improvements in memory usage for the OPA HTTP server, and help OPA deployments avoid some accidental out-of-memory situations.

For most users, no changes will be needed to continue using OPA. However, to control this behavior, two new configuration

 

keys are available: 

server.decoding.max_length

 and 

server.decoding.gzip.max_length

. These control the max size in

 

bytes to allow for an incoming request payload, and the maximum size in bytes to allow for a decompressed gzip request payload, respectively.

Here's an example OPA configuration using the new keys:

# Set max request size to 64 MB and max gzip size (decompressed) to be 128 MB.
server:
  decoding:
    max_length: 67108864
    gzip:
      max_length: 134217728


yaml

Topdown and Rego

topdown: New 

strings.count

 builtin which returns the number of non-overlapping instances of a substring in a string (

#6827

https://github.com/open-policy-agent/opa/issues/6827

) authored by @Manish-Giri

format: Produce error when 

--rego-v1

  formatted module has rule name conflicting with keyword (

#6833

https://github.com/open-policy-agent/opa/issues/6833

) authored by @johanfylling

topdown: Add cap to caches for regex and glob built-in functions (

#6828

https://github.com/open-policy-agent/opa/issues/6828

) authored by @johanfylling. This fixes possible memory leaks where caches grow uncontrollably when large amounts of regexes or globs are generated or originate from the input document.

Runtime, Tooling, SDK

repl: Add support for correctly loading bundle modules (

#6872

https://github.com/open-policy-agent/opa/issues/6872

) authored by @ashutosh-narkar

plugins/discovery: Allow un-registration of discovery listener (

#6851

https://github.com/open-policy-agent/opa/pull/6851

) authored by @mjungsbluth. The discovery plugin allows OPA to register a bundle download status listener but previously did not offer a method to unregister that listener

plugins/logs: Reduce amount of work performed inside global lock in decision log plugin (

#6859

https://github.com/open-policy-agent/opa/pull/6859

) authored by @johanfylling

plugins/rest: Add a new client credential attribute to support Azure Workload Identity. This would allow workloads deployed on an Azure Kubernetes Services (AKS) cluster to authenticate and access Azure cloud resources (

#6802

https://github.com/open-policy-agent/opa/pull/6802

) authored by @ledbutter

cmd/inspect: Add ability for opa inspect to inspect a single file outside of any bundle (

#6873

https://github.com/open-policy-agent/opa/pull/6873

) authored by @tjons

cmd+bundle: Add 

--follow-symlinks

 flag to the 

opa build

 command to allow users to build directories with symlinked files, and have the contents of those symlinked files included in the built bundle (

#6800

https://github.com/open-policy-agent/opa/pull/6800

) authored by @tjons

server: Add missing handling in the server for the 

explain=fails

 query value (

#6886

https://github.com/open-policy-agent/opa/pull/6886

) authored by @acamatcisco

Docs, Website, Ecosystem

docs: Update bundle section with an example of a manifest with 

rego_version

 and 

file_rego_versions

 attributes (

#6885

https://github.com/open-policy-agent/opa/pull/6885

) authored by @ashutosh-narkar

docs: Better link language SDKs to make them more discoverable (

#6866

https://github.com/open-policy-agent/opa/pull/6866

) authored by @charlieegan3

Miscellaneous

ci: Add the OpenSSF Scorecard Github Action to help evaluate the OPA project's security posture (

#6848

https://github.com/open-policy-agent/opa/pull/6848

) authored by @harshitasao

Dependency updates; notably:

build(go): bump golang from 1.22.4 to 1.22.5

build(deps): bump github.com/containerd/containerd from 1.7.18 to 1.7.20

build(deps): bump golang.org/x/net from 0.26.0 to 0.27.0

build(deps): bump google.golang.org/grpc from 1.64.0 to 1.65.0

build(deps): bump go.opentelemetry.io modules (

#6847

https://github.com/open-policy-agent/opa/pull/6847

)

0.66.0

This release contains a mix of features, performance improvements, and bugfixes.

Improved Test Reports (

)

The 

opa test

 command now includes a new 

--var-values

 flag that enriches reporting of failed tests with the values and locations for variables in the failing expression.

 

E.g.:

FAILURES
--------------------------------------------------------------------------------
data.test.test_my_policy: FAIL (0ms)

  test.rego:8:
    	x == y + z
    	|    |   |
    	|    |   3
    	|    y + z: 5
    	|    y: 2
    	1

SUMMARY
--------------------------------------------------------------------------------
test.rego:
data.test.test_foo: FAIL (0ms)
--------------------------------------------------------------------------------
FAIL: 1/1


Authored by @johanfylling, reported by @grosser.

Reading stdin in 

opa exec

 (

)

The 

opa exec

 command now supports reading 

input

 documents from stdin with the 

--stdin-input

 (

-I

) flag.

 

E.g.:

$ echo '{"user": "alice"}' | opa exec --stdin-input --bundle my_bundle


shell

Authored by @colinjlacy, reported by @humbertoc-silva.

Topdown and Rego

ast: Fix blanket "unexpected assign token" error message / usability issue (

#6563

https://github.com/open-policy-agent/opa/issues/6563

) authored by @anderseknert

ast: Fix wrong location on metadata parse errors on first line (

#6587

https://github.com/open-policy-agent/opa/issues/6587

) authored by @anderseknert

ast: Fix/inspect unknowns in with stmt (

#6812

https://github.com/open-policy-agent/opa/issues/6812

) authored by @johanfylling reported by @surajupadhyay01

ast: Include original text in annotation location text attribute (

#6779

https://github.com/open-policy-agent/opa/issues/6779

) authored by @anderseknert

ast: Expanding nested expressions in 

every

 domain (

#6790

https://github.com/open-policy-agent/opa/issues/6790

) authored by @johanfylling reported by @anakrish

topdown: Add http.send request attribute to ignore headers for caching key (

#6642

https://github.com/open-policy-agent/opa/issues/6642

) authored and reported by @rudrakhp

Runtime, Tooling, SDK

build: Use chainguard images from dockerhub (

#6830

https://github.com/open-policy-agent/opa/pull/6830

) authored by @srenatus

bundle: Preallocate buffers for file contents. (

#6818

https://github.com/open-policy-agent/opa/pull/6818

) authored by @philipaconrad

plugins: Reduce locks during decision logging (

#6797

https://github.com/open-policy-agent/opa/pull/6797

) authored by @mjungsbluth

plugins/rest: Do local map modification in OAuth2 client credentials flow (

#6769

https://github.com/open-policy-agent/opa/issues/6769

) authored and reported by @eubaranov

loader: Use a better error message when trying to merge non-objects (

#6803

https://github.com/open-policy-agent/opa/issues/6803

) authored by @anderseknert

server/authorizer: Fix gzip payload handling (

#6804

https://github.com/open-policy-agent/opa/issues/6804

) authored by @philipaconrad reported by @nevumx

Docs, Website, Ecosystem

docs: Remove missing prometheus metric 

go_memstats_gc_cpu_fraction

 (

#6783

https://github.com/open-policy-agent/opa/issues/6783

) authored by @philipaconrad

docs: Mention that default functions may not evaluate (

#6265

https://github.com/open-policy-agent/opa/issues/6265

) authored by @anderseknert

docs: Fix spelling and grammar of 

an HTTP

 (

#6786

https://github.com/open-policy-agent/opa/pull/6786

) authored by @jdbaldry

docs/website: Add vs code and zed to ecosystem page (

#6788

https://github.com/open-policy-agent/opa/pull/6788

) authored by @charlieegan3

docs/website: Add Flipt to the OPA ecosystem (

#6781

https://github.com/open-policy-agent/opa/pull/6781

) authored by @markphelps

docs/website: Add Flipt blog to their ecosystem page (

#6789

https://github.com/open-policy-agent/opa/pull/6789

) authored by @charlieegan3

docs/website: Revise language SDK content (

#6811

https://github.com/open-policy-agent/opa/pull/6811

) authored by @charlieegan3

Miscellaneous

Dependency updates; notably:

build(go): bump golang from 1.22.3 to 1.22.4

build(deps): bump github.com/containerd/containerd from 1.7.17 to 1.7.18

build(deps): bump golang.org/x/net from 0.25.0 to 0.26.0

0.65.0

This release contains a mix of features and bugfixes.

Runtime, Tooling, SDK

ast: Include annotations in rule AST, to help external tooling analyzing the AST (

#6771

https://github.com/open-policy-agent/opa/pull/6771

) authored by @ashutosh-narkar

aws: Always read HTTP response body, to re-use persistent connections for non-200 responses (

#6734

https://github.com/open-policy-agent/opa/pull/6734

) authored by @johanneslarsson

plugins/discovery: Update comparison logic for overrides (

#6723

https://github.com/open-policy-agent/opa/pull/6723

) authored by @ashutosh-narkar

plugins/logs: Include http request context in decision logs (

#6693

https://github.com/open-policy-agent/opa/issues/6693

) authored by @ashutosh-narkar reported by @stiidk

plugins/rest: Disable the Authorization header for ECR redirects (

6728

https://github.com/open-policy-agent/opa/pull/6728

) authored by @gdlg reported by @vazquezf2000

runtime: Fix OpenTelemetry graceful shutdown (

#6651

https://github.com/open-policy-agent/opa/issues/6651

) authored by @nicolaschotard and @David-Wobrock reported by @nicolaschotard

Topdown and Rego

topdown: Asserting the 

every

 domain is a collection type before evaluation (

#6762

https://github.com/open-policy-agent/opa/issues/6762

) authored by @johanfylling reported by @anderseknert

Miscellaneous

docs: Add arrays to composite values section (

#6727

https://github.com/open-policy-agent/opa/issues/6727

) authored by @anderseknert reported by @SpecLad

docs: Add remainder operator to grammar (

#6767

https://github.com/open-policy-agent/opa/pull/6767

) authored by @anderseknert

docs: Fix dynamic metadata object in docs (

#6709

https://github.com/open-policy-agent/opa/pull/6709

) authored by @antonioberben

docs: Use best practice package name in test examples (

#6731

https://github.com/open-policy-agent/opa/pull/6731

) authored by @asleire

docs: Update query API doc with details about overriding the def decision path (

#6745

https://github.com/open-policy-agent/opa/pull/6745

) authored by @ashutosh-narkar

ci: pin GitHub Actions macos runner version and build for darwin/amd64 (

#6720

https://github.com/open-policy-agent/opa/issues/6720

) reported and authored by @suzuki-shunsuke

Dependency updates; notably:

build(go): bump golang from 1.22.2 to 1.22.3

build(deps): bump github.com/containerd/containerd from 1.7.15 to 1.7.17

build(deps): bump github.com/prometheus/client_golang

build(deps): bump golang.org/x/net from 0.24.0 to 0.25.0

build(deps): bump google.golang.org/grpc from 1.63.2 to 1.64.0

Breaking changes

A new 

IsSetStmt

https://www.openpolicyagent.org/docs/latest/ir/#issetstmt

 statement has been added to the intermediate representation (IR).

 

This is a breaking change for custom IR evaluators, which must interpret this statement in IR plans generated by this OPA version and later.

 

No actions are required for Wasm users, as long as Wasm modules are built by this OPA version or later.

0.64.1

This is a bug fix release addressing the following issues:

ci: Pin GitHub Actions macos runner version. The architecture of the GitHub Actions Runner 

macos-latest

 was changed from 

amd64

 to 

arm64

 and as a result 

darwin/amd64

 binary wasn't released (

#6720

https://github.com/open-policy-agent/opa/issues/6720

) authored by @suzuki-shunsuke

plugins/discovery: Update comparison logic used in the discovery plugin for handling overrides. This fixes a panic that resulted from the comparison of uncomparable types (

#6723

https://github.com/open-policy-agent/opa/pull/6723

) authored by @ashutosh-narkar

0.64.0

NOTES:

The minimum version of Go required to build the OPA module is 

1.21

This release contains a mix of features, a new builtin function (

json.marshal_with_options()

), performance improvements, and bugfixes.

Breaking Change

Bootstrap configuration overrides Discovered configuration

Previously if Discovery was enabled, other features like bundle downloading and status reporting could not be configured manually.

 

The reason for this was to prevent OPAs being deployed that could not be controlled through discovery. It's possible that

 

the system serving the discovered config is unaware of all options locally available in OPA. Hence, we relax the configuration

 

check when discovery is enabled so that the bootstrap configuration can contain plugin configurations. In case of conflicts,

 

the bootstrap configuration for plugins wins. These local configuration overrides from the bootstrap configuration are included

 

in the Status API messages so that management systems can get visibility into the local overrides.

In general, the bootstrap configuration overrides the discovered configuration.

 Previously this was not the case for all

 

configuration fields. For example, if the discovered configuration changes the 

labels

 section, only labels that are

 

additional compared to the bootstrap configuration are used, all other changes are ignored. This implies labels in the

 

bootstrap configuration override those in the discovered configuration. But for fields such as 

default_decision

, 

default_authorization_decision

,

 

nd_builtin_cache

, the discovered configuration would override the bootstrap configuration. Now the behavior is more consistent

 

for the entire configuration and helps to avoid accidental configuration errors. (

#5722

https://github.com/open-policy-agent/opa/issues/5722

) authored by @ashutosh-narkar

Add 

rego_version

 attribute to the bundle manifest

A new global 

rego_version

 attribute is added to the bundle manifest, to inform the OPA runtime about what Rego version (

v0

/

v1

) to

 

use while parsing/compiling contained Rego files. There is also a new 

file_rego_versions

 attribute which allows individual

 

files to override the global Rego version specified by 

rego_version

.

When the version of the contained Rego is advertised by the bundle through this attribute, it is not required to run OPA with the

 

--v1-compatible

 (or future 

--v0-compatible

) flag in order to correctly parse, compile and evaluate the bundle's modules.

A bundle's 

rego_version

 attribute takes precedence over any applied 

--v1-compatible

/

--v0-compatible

 flag.  (

#6578

https://github.com/open-policy-agent/opa/issues/6578

) authored by @johanfylling

Runtime, Tooling, SDK

compile: Fix panic from CLI + metadata entrypoint overlaps. The panic occurs when 

opa build

 was provided an entrypoint from both a CLI flag, and via entrypoint metadata annotation. (

#6661

https://github.com/open-policy-agent/opa/issues/6661

) authored by @philipaconrad

cmd/deps: Improve memory footprint and execution time of 

deps

 command for policies with high dependency connectivity (

#6685

https://github.com/open-policy-agent/opa/issues/6685

) authored by @johanfylling

server: Keep default decision path in-sync with manager's config (

#6697

https://github.com/open-policy-agent/opa/issues/6697

) authored by @ashutosh-narkar

server: Remove unnecessary AST-to-JSON conversions (

#6665

https://github.com/open-policy-agent/opa/pull/6665

) and (

#6669

https://github.com/open-policy-agent/opa/pull/6669

) authored by @koponen-styra

sdk: Allow customizations of the plugin manager via SDK (

#6662

https://github.com/open-policy-agent/opa/issues/6662

) authored by @xico42

sdk: Fix issue where active parser options aren't propagated to module reload during bundle activation resulting in errors while activating bundles with 

v1

 syntax (

#6689

https://github.com/open-policy-agent/opa/pull/6689

) authored by @xico42

plugins/rest: Close response body in OAuth2 client credentials flow (

#6708

https://github.com/open-policy-agent/opa/pull/6708

) authored by @johanneslarsson

Topdown and Rego

ast: Import 

rego.v1

 in 

v0

 support modules when applicable (

#6450

https://github.com/open-policy-agent/opa/issues/6450

) authored by @johanfylling

rego: Set query Rego version from configured imports (

#6701

https://github.com/open-policy-agent/opa/issues/6701

) authored by @johanfylling

topdown: New 

json.marshal_with_options()

 builtin for indented/"pretty-printed" and/or line-prefixed JSON (

#6630

https://github.com/open-policy-agent/opa/issues/6630

) authored by @sean-r-williams

Docs, Website, Ecosystem

Add Raygun to ecosystem projects (

#6712

https://github.com/open-policy-agent/opa/pull/6712

) authored by @johndbro1

Add env0 to ecosystem projects (

#6658

https://github.com/open-policy-agent/opa/pull/6658

) authored by @yarivg

Add Rego Language Comparisons to ecosystem projects (

#6663

https://github.com/open-policy-agent/opa/pull/6663

) authored by @charlieegan3

docs/configuration: Tidy up headers in Services section (

#6695

https://github.com/open-policy-agent/opa/pull/6695

) authored by @tsandall

docs: Use cuboid rather than cube to explain concepts of sets and composite values in policy-language section of documentation (

#6691

https://github.com/open-policy-agent/opa/pull/6691

) authored by @kd-labs

Miscellaneous

go.{mod,sum}: Update the 

go

 stanza of OPA's 

go.mod

 to 

go 1.21

. OPA, used as Go dependency, requires at least 

go 1.21

, and thus works with all officially supported Go versions (

1.21.x

 and 

1.22.x

) (

#6678

https://github.com/open-policy-agent/opa/pull/6678

) authored by @srenatus

ci: Update Github Actions for Node 20. This change updates the 

upload-artifact

 and 

download-artifact

 Github actions to the latest version (v4) (

#6670

https://github.com/open-policy-agent/opa/pull/6670

) authored by @philipaconrad

build: Update WASM Rego test generation docker command to address CVE-2022-24765 in Git (

#6703

https://github.com/open-policy-agent/opa/issues/6703

) authored by @ashutosh-narkar

Dependency updates; notably:

build(go): bump 1.22.1 -> 1.22.2 (

#6672

https://github.com/open-policy-agent/opa/pull/6672

) authored by @srenatus

build(deps): bump aquasecurity/trivy-action from 0.18.0 to 0.19.0

build(deps): bump github.com/containerd/containerd from 1.7.14 to 1.7.15

build(deps): bump github.com/prometheus/client_model from 0.5.0 to 0.6.1

build(deps): bump golang.org/x/net from 0.22.0 to 0.24.0

build(deps): bump google.golang.org/grpc from 1.62.1 to 1.63.2

0.63.0

This release contains a mix of features, performance improvements, and bugfixes.

Runtime, Tooling, SDK

cmd/exec: Add 

--timeout

 flag to 

opa exec

 to prevent infinite hangs. (

#6613

https://github.com/open-policy-agent/opa/issues/6613

) authored by @philipaconrad

download: Surface bundle download errors via debug logging (

#6609

https://github.com/open-policy-agent/opa/issues/6609

) authored by @ashutosh-narkar reported by @nevumx

topdown: Fixing overactive Early Exit suppression (

#6566

https://github.com/open-policy-agent/opa/issues/6566

) authored by @johanfylling reported by @ashwinhb

plugins/rest: Add support to get temp creds via AssumeRole (

#6634

https://github.com/open-policy-agent/opa/pull/6634

) authored by @ashutosh-narkar

Topdown and Rego

topdown: Adding a new 

crypto.x509.parse_and_verify_certificates_with_options

 built-in function. (

#5882

https://github.com/open-policy-agent/opa/issues/5882

) authored by @yogisinha reported by @IxDay

format: Preserve brackets around set union operation (

#6588

https://github.com/open-policy-agent/opa/issues/6588

) authored by @ashutosh-narkar reported by @HarshPathakhp

aws: Support for Unsigned Payload or provided content sha256 in AWS signing (

#6581

https://github.com/open-policy-agent/opa/pull/6611

) authored by @prasanthj

Docs + Website + Ecosystem

ADOPTERS.md: Add Facets.cloud to the list (

#6640

https://github.com/open-policy-agent/opa/issues/6640

) authored by @ashutosh-narkar reported by @samarthya-gupta1

docs: Mention homebrew install option (

#6622

https://github.com/open-policy-agent/opa/issues/6622

) authored by @anderseknert

docs: Add Rego v1 keywords to list of reserved names (

#6649

https://github.com/open-policy-agent/opa/pull/6649

) authored by @anderseknert

docs: Add Tunnelmole as an open source tunneling option in the Cloudformation hooks documentation (

#6626

https://github.com/open-policy-agent/opa/pull/6626

) authored by @robbie-cahill

docs: Add docs on using env vars in place of CLI flags (

#6631

https://github.com/open-policy-agent/opa/pull/6631

) authored by @anderseknert

docs: Adding integration for Backstage (

#6629

https://github.com/open-policy-agent/opa/pull/6629

) authored by @Parsifal-M

docs: Clear up some uses of future keywords (

#6653

https://github.com/open-policy-agent/opa/pull/6653

) authored by @charlieegan3

docs: Update delta bundle patch doc for remove op (

#6645

https://github.com/open-policy-agent/opa/pull/6645

) authored by @0marq

docs: Fix typo in 

Debugging OPA

 (

#6637

https://github.com/open-policy-agent/opa/pull/6637

) authored by @setchy

Miscellaneous

chore: Remove repetitive words (

#6644

https://github.com/open-policy-agent/opa/pull/6644

) authored by @occupyhabit

Dependency updates; notably:

build(deps): bump github.com/containerd/containerd from 1.7.13 to 1.7.14

build(deps): bump github.com/golang/protobuf from 1.5.3 to 1.5.4

build(deps): bump google.golang.org/grpc from 1.62.0 to 1.62.1

0.62.1

This is a security fix release for the fixes published in 

Golang 1.22.1

https://groups.google.com/g/golang-announce/c/5pwGVUPoMbg

.

OPA servers using 

--authentication=tls

 would be affected: crafted malicious client

 

certificates could cause a panic in the server.

Also, crafted server certificates could panic OPA's HTTP clients, in bundle plugin,

 

status and decision logs; and 

http.send

 calls that verify TLS.

This affects all crypto/tls clients, and servers that set Config.ClientAuth to

 

VerifyClientCertIfGiven or RequireAndVerifyClientCert. The default behavior is

 

for TLS servers to not verify client certificates.

This is CVE-2024-24783 (https://pkg.go.dev/vuln/GO-2024-2598).

Note that there are other security fixes in this Golang release, but whether or not

 

OPA is affected is harder to tell. An update is advised.

Miscellaneous

Add Trino to OPA ecosystem (authored by @mosabua)

update: ADOPTERS.md (#6608) (authored by @fredmaggiowski)

0.62.0

NOTES:

The minimum version of Go required to build the OPA module is 

1.20

This release contains a mix of improvements and bugfixes.

Runtime, Tooling, SDK

cmd: Add environment variable backups for command-line flags (

#6508

https://github.com/open-policy-agent/opa/pull/6508

) authored by @colinjlacy

download/oci: Add missing 

WithBundleParserOpts

 method to OCI downloader (

#6571

https://github.com/open-policy-agent/opa/pull/6571

) authored by @slonka

logging: avoid 

%!F(MISSING)

 in logs by skipping calls to the 

{Debug,Info,Warn,Error}f

 functions when there are no arguments (

#6555

https://github.com/open-policy-agent/opa/pull/6555

) authored by @srenatus

Topdown and Rego

ast+cmd: Allow bundle to contain calls to unknown Rego functions when inspected (

#6591

https://github.com/open-policy-agent/opa/issues/6591

) authored by @johanfylling

topdown/http: Respect 

raise_error

 flag during input validation (

#6553

https://github.com/open-policy-agent/opa/pull/6553

) authored by @ashutosh-narkar

Docs + Website + Ecosystem

Add OpaDotNet to ecosystem projects (

#6554

https://github.com/open-policy-agent/opa/pull/6554

) authored by @me-viper

Add updated logos for Permit.io and OPAL (

#6562

https://github.com/open-policy-agent/opa/pull/6562

) authored by @danielbass37

docs: Update description of the url path usage when accessing values inside object and array documents for v1/data GET and POST (

#6567

https://github.com/open-policy-agent/opa/pull/6567

) authored by @ashutosh-narkar

docs: Use 

application/yaml

 instead of 

application/x-yaml

 as the former is now a recognized content type (

#6565

https://github.com/open-policy-agent/opa/pull/6565

) authored by @anderseknert

Miscellaneous

Add Elastic to ADOPTERS.md (

#6568

https://github.com/open-policy-agent/opa/pull/6568

) authored by @orouz

Dependency updates; notably:

bump golang 1.21.5 -> 1.22 (

#6595

https://github.com/open-policy-agent/opa/pull/6595

) authored by @srenatus

bump google.golang.org/grpc from 1.61.0 to 1.62.0

bump golang.org/x/net from 0.19.0 to 0.21.0

bump github.com/containerd/containerd from 1.7.12 to 1.7.13

bump aquasecurity/trivy-action from 0.16.1 to 0.17.0

bump github.com/prometheus/client_golang from 1.18.0 to 1.19.0

bump github.com/opencontainers/image-spec from 1.1.0-rc5 to 1.1.0-rc6

0.61.0

This release contains a mix of new features and bugfixes.

Runtime, SDK

Adding 

--v1-compatible

 flag to all previously unsupported command line commands (

#6520

https://github.com/open-policy-agent/opa/issues/6520

) authored by @johanfylling

Don't load files in tarball exceeding 

size_limit_bytes

 (

#6514

https://github.com/open-policy-agent/opa/issues/6514

) authored by @anderseknert reported by @dolevf

Allow TLS cipher suites to be set for the OPA server (

#6537

https://github.com/open-policy-agent/opa/pull/6537

) authored by @ashutosh-narkar

Removing deprecated fields and functions related to rego-v1 compatibility (

#6542

https://github.com/open-policy-agent/opa/pull/6542

) authored by @johanfylling

bundle: Make func newDescriptor and withCloser public (

#6517

https://github.com/open-policy-agent/opa/pull/6517

) authored by @antgubarev

runtime/logging: Do not panic when rctx is missing (

#6506

https://github.com/open-policy-agent/opa/pull/6506

) authored by @srenatus

Topdown

topdown: Clean expired 

http.send

 cache entries periodically (

#5320

https://github.com/open-policy-agent/opa/issues/5320

) authored by @rudrakhp reported by @lukyer

Docs

docs: Add documentation for new cache config parameters (

#6518

https://github.com/open-policy-agent/opa/pull/6518

) authored by @rudrakhp

docs: Update docker-authorization.md to use new plugin version (

#6539

https://github.com/open-policy-agent/opa/pull/6539

) authored by @denis-accesa

docs: Fix a typo in _index.md (

#6491

https://github.com/open-policy-agent/opa/pull/6491

) authored by @trungnguyen

docs: Add a new debugging page (

#6513

https://github.com/open-policy-agent/opa/pull/6513

) authored by @charlieegan3

docs: Update log masking policy examples to be Rego v1 compatible (

#6545

https://github.com/open-policy-agent/opa/pull/6545

) authored by @ashutosh-narkar

docs: Update version for non docs pages (

#6526

https://github.com/open-policy-agent/opa/pull/6526

) authored by @charlieegan3

Integrations, Ecosys

## CODE_OF_CONDUCT.md



Community Code of Conduct

We follow the 

CNCF Code of Conduct

https://github.com/cncf/foundation/blob/main/code-of-conduct.md

.

## COMMUNITY_GUIDELINES.md



OPA Community Guidelines v2.0

The 

CNCF Code of Conduct

https://github.com/cncf/foundation/blob/main/code-of-conduct.md

 is enforced in all areas of the OPA community, plus the following.

Relevancy

Any content posted or shared in the OPA community should be relevant to the specific Slack Channel or GitHub Category, and generally to the OPA community. If you're unsure about the content you want to share, posting in #help channel in Slack or the Community category in GitHub Discussions is always a safe choice; admins will be around to help guide new members.

Spamming

Excessive re-posting, unnecessary cross-posting, unsolicited advertisements for services or products are not allowed on any of the OPA communication channels and are considered spam. Posting content that is considered spam will be removed and these actions are subject to the same enforcement rules as unacceptable behavior.

Vendors

The OPA community has a rich ecosystem of tools, integrations, and Vendors to support them. Any company whose primary revenue stream includes a cloud-native service or technology is considered a Vendor. As a valuable part of the OPA ecosystem Vendors are encouraged to participate in the community with the expectation that they have good intentions, this means interacting with members with the intent to be helpful and supportive. Any unsolicited advertisements will be removed and are subject to our enforcement rules.

End-users

Companies that use cloud-native services internally, but do not sell any of these services externally, are considered an End User Company in the OPA Community. End User companies are expected to operate with positive intentions, this is not the place to build your marketing funnel for external tools and services.

Member Participation

The OPA community is here for everyone to connect with one another, share information, and build amazing products. By choosing to participate in the OPA community as a Vendor, End User, or general contributor you are agreeing to respect these guidelines. When interacting with any of our social channels, Slack, Twitter, GitHub, and any other channels we participate in, there is an expectation that you will exhibit the values of the OPA community.

Values

Be Respectful

Value each other’s ideas, styles and viewpoints. We may not always agree, but disagreement is no excuse for poor manners. Be open to different possibilities and to being wrong. Be respectful in all interactions and communications, especially when debating the merits of different options. Be aware of your impact and how intense interactions may be affecting people. Be direct, constructive and positive. Take responsibility for your impact and your mistakes – if someone says they have been harmed through your words or actions, listen carefully, apologize sincerely, and correct the behavior going forward.

Be Direct but Professional

We are likely to have some discussions about if and when criticism is respectful and when it’s not. We must be able to speak directly when we disagree and when we think we need to improve. We cannot withhold hard truths. Doing so respectfully is hard, doing so when others don’t seem to be listening is harder, and hearing such comments when one is the recipient can be even harder still. We need to be honest and direct, as well as respectful.

Be Inclusive

Seek diverse perspectives. Diversity of views and of people on teams powers innovation, even if it is not always comfortable. Encourage all voices. Help new perspectives be heard and listen actively. If you find yourself dominating a discussion, it is especially important to step back and encourage other voices to join in. Be aware of how much time is taken up by dominant members of the group. Provide alternative ways to contribute or participate when possible.

Be inclusive of everyone in an interaction, respecting and facilitating people’s participation whether they are:

Remote (on video or phone)

Not native language speakers

Coming from a different culture

Using pronouns other than “he” or “she”

Living in a different time zone

Facing other challenges to participate

Think about how you might facilitate alternative ways to contribute or participate. If you find yourself dominating a discussion, step back. Make way for other voices and listen actively to them.

These values were inspired by the 

Mozilla Community Participation Guidelines

https://www.mozilla.org/en-US/about/governance/policies/participation/

Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior will not be tolerated. An admin may take any action deemed appropriate, up to and including, a warning, a temporary ban(30 days), and a permanent ban for repeated violation of these guidelines. Admins may also remove content that violates the guidelines.

Reporting

Please reach out to one of the admins below:

Anders Eknert (a_eknert@apple.com or @anderseknert)

Torin Sandall (torinsandall@gmail.com or @tsandall)

Jorge Castro (CNCF Slack)

## CONTRIBUTING.md



Contributing

Thanks for your interest in contributing to the Open Policy Agent (OPA) project!

Please refer to 

OPA's contribution guidelines

https://www.openpolicyagent.org/docs/contributing

 

to find out how you can help.

## GOVERNANCE.md



Project Governance

This document defines the governance process for the open-policy-agent GitHub organization.

The MAINTAINERS.md file in this repository contains the list of OPA project maintainers and their "area of expertise". An area of expertise is defined as a set of repositories or repository subtrees.

Voting

Maintainers use "organizational voting" to approve changes so that no single organization can dominate an area of expertise.

"Organizations relevant to a change" are all those organizations with an area of expertise that covers the change.

"Organizations with an area of expertise" are those organizations for which there is a maintainer from that organization with that area of expertise.

Individuals not associated with or employed by a company or organization are allowed one organization vote.

Each company or organization (regardless of the number of maintainers associated with or employed by that company/organization) receives one organization vote.  Any maintainer from an organization may cast the vote for that organization.

For example, consider the following scenario.

Two maintainers are employed by Company X, two by Company Y, two by Company Z, and one maintainer is an unaffiliated individual

Area of expertise E covers the repository R

One maintainer from Company X, two from Company Y, and the un-affiliated individual all have expertise E

For any change requiring a vote to repository R, three "organization votes" are possible: one for X, one for Y, and one for the un-affiliated individual.

Unless specified otherwise, a vote passes when greater than fifty percent of the organization votes are in favour.

Code Changes

All code changes should go through the Pull Request (PR) process. PRs should only be merged after receiving approval (via GitHub) from at least one other member of the GitHub team associated with the area(s) of expertise.

We do not vote formally on every code change, but we do expect that every code change merged has the same community support as if the change were approved by a formal vote. When a merge occurs without sufficient community support, the change should be reverted until the dispute is resolved through discussion. Any team member who feels that a technical decision cannot be reached can call for a formal vote following the rules outlined above in either the PR or a separate issue.

Non-code Changes

Changes that are not PRs will be voted on through GitHub issues.  Maintainers should indicate their yes/no vote on that GitHub issue, and after a suitable period of time, the votes will be tallied and the outcome noted.

The following changes, while governed by the language above, require additional clarification.

Changes in Maintainership

New maintainers for an area of expertise are proposed by an existing maintainer for that area of expertise and are elected by a 2/3 majority of the organizations with that area of expertise.

Maintainer status expires after 1 year but a request to self-renew can be made within 1 month of expiry.

Maintainers for an area of expertise can be removed by a 2/3 majority of the organizations with that area of expertise.

Changes in Governance

All changes in Governance require a 2/3 majority organization vote from all areas of expertise.

New Repositories

New repositories require a 2/3 majority organization vote from all areas of expertise.

GitHub Project Administration

Maintainers for an area of expertise belong to the associated GitHub team(s) (e.g., 

opa-maintainers

, 

gatekeeper-maintainers

, etc.) so that GitHub permissions reasonably follow this governance model.

Individuals may be added to that repository's GitHub team but need not be added to the MAINTAINERS.md file. This provision enables new subprojects and contributors to be onboarded without immediately creating new maintainers.

## MAINTAINERS.md



Maintainers

The following table lists OPA project maintainers and areas of expertise in alphabetical order:

Name

GitHub

Email

Organization

Repositories/Area of Expertise

Added/Renewed On

Anders Eknert

@anderseknert

anders@eknert.com

Apple

opa

2025-01-27

Ash Narkar

@ashutosh-narkar

anarkar4387@gmail.com

Apple

opa, opa-envoy-plugin

2024-03-31

Charlie Egan

@charlieegan3

opa@charlieegan3.com

Apple

opa

2025-01-27

Max Smythe

@maxsmythe

smythe@google.com

Google

frameworks/constraints, gatekeeper, gatekeeper-library, cert-controller

2024-03-31

Rita Zhang

@ritazh

rita.z.zhang@gmail.com

Microsoft

frameworks/constraints, gatekeeper, gatekeeper-library, cert-controller

2026-01-30

Sertaç Özercan

@sozercan

sozercan@gmail.com

Microsoft

gatekeeper, gatekeeper-library, cert-controller, gatekeeper-external-data-provider

2026-01-30

Jaydip Gabani

@JaydipGabani

gabanijaydip@gmail.com

Microsoft

frameworks/constraints, gatekeeper, gatekeeper-library, cert-controller

2026-01-30

Stephan Renatus

@srenatus

stephan.renatus@gmail.com

Apple

opa

2024-03-31

Tim Hinrichs

@timothyhinrichs

timothy.l.hinrichs@gmail.com

Apple

all repositories

2024-03-31

Torin Sandall

@tsandall

torinsandall@gmail.com

Apple

all repositories

2024-03-31

Emeritus

Craig Tabita

https://github.com/ctab

Ernest Wong

https://github.com/chewong

Patrick East

https://github.com/patrick-east

Will Beason

https://github.com/willbeason

Oren Shomron

https://github.com/shomron

Andrew Peabody

https://github.com/apeabody

Nilekh Chaudhari

https://github.com/nilekhc

## README.md



 Open Policy Agent

 

 

 

Open Policy Agent (OPA) is an open source, general-purpose policy engine that enables unified, context-aware policy enforcement across the entire stack.

OPA is proud to be a graduated project in the 

Cloud Native Computing Foundation

https://www.cncf.io/

 (CNCF) landscape. For details read the CNCF 

announcement

https://www.cncf.io/announcements/2021/02/04/cloud-native-computing-foundation-announces-open-policy-agent-graduation/

.

Get started with OPA

Write your first Rego policy with the 

Rego Playground

https://play.openpolicyagent.org

 or use it to share your work with others for feedback and support. Have a look at the 

Access Control examples

https://play.openpolicyagent.org/?example-group=access-control

 if you're not sure where to start.

Install the 

VS Code extension

https://marketplace.visualstudio.com/items?itemName=tsandall.opa

 to get started locally with live diagnostics, debugging and formatting. See 

Editor and IDE Support

https://www.openpolicyagent.org/docs/editor-and-ide-support

 for other supported editors.

Go to the 

OPA Documentation

https://www.openpolicyagent.org/docs

 to

 

learn about the Rego language as well as how to deploy and integrate OPA.

Check out the learning resources in the 

Learning Rego

https://www.openpolicyagent.org/ecosystem/by-feature/learning-rego

 section of the ecosystem directory.

Follow the 

Running OPA

https://www.openpolicyagent.org/docs/latest/#running-opa

 instructions to get started with the OPA CLI locally.

See 

Docker Hub

https://hub.docker.com/r/openpolicyagent/opa/tags/

 for container images and the 

GitHub releases

https://github.com/open-policy-agent/opa/releases

 for binaries.

Check out the 

OPA Roadmap

https://github.com/orgs/open-policy-agent/projects/10

 to see a high-level snapshot of OPA features in-progress and planned.

Want to talk about OPA or get support?

Join the 

OPA Slack

https://slack.openpolicyagent.org

 to talk to other OPA users and maintainers. See 

#help

 for support.

Check out the 

Community Discussions

https://github.com/orgs/open-policy-agent/discussions

 to ask questions.

See the 

Support

https://www.openpolicyagent.org/support

 page for commercial support options.

Interested to learn what others are doing with OPA?

Browse community projects on the 

OPA Ecosystem Directory

https://www.openpolicyagent.org/ecosystem

 - don't forget to 

list your own

https://github.com/open-policy-agent/opa/tree/main/docs#opa-ecosystem

!

Check out the 

ADOPTERS.md

./ADOPTERS.md

 file for a list of production adopters. Does your organization use OPA in production? Support the OPA project by submitting a PR to add your organization to the list with a short description of your OPA use cases!

Want to integrate OPA?

See the high-level 

Go SDK

https://www.openpolicyagent.org/docs/integration#integrating-with-the-go-sdk

 or the low-level Go API

 

 

to integrate OPA with services written in Go.

See the 

REST API

https://www.openpolicyagent.org/docs/rest-api.html

 

reference to integrate OPA with services written in other languages.

See the 

integration docs

https://www.openpolicyagent.org/docs/integration

 for more options.

Want to contribute to OPA?

Read the 

Contributing Guide

https://www.openpolicyagent.org/docs/contributing

 to learn how to make your first contribution.

Use 

#contributors

https://openpolicyagent.slack.com/?redir=%2Farchives%2FC02L1TLPN59%3Fname%3DC02L1TLPN59

 in Slack to talk to other contributors and OPA maintainers.

File a 

GitHub Issue

https://github.com/open-policy-agent/opa/issues

 to request features or report bugs.

How does OPA work?

OPA gives you a high-level declarative language to author and enforce policies

 

across your stack.

With OPA, you define 

rules

 that govern how your system should behave. These

 

rules exist to answer questions like:

Can user X call operation Y on resource Z?

What clusters should workload W be deployed to?

What tags must be set on resource R before it's created?

You integrate services with OPA so that these kinds of policy decisions do not

 

have to be 

hardcoded

 in your service. Services integrate with OPA by

 

executing 

queries

 when policy decisions are needed.

When you query OPA for a policy decision, OPA evaluates the rules and data

 

(which you give it) to produce an answer. The policy decision is sent back as

 

the result of the query.

For example, in a simple API authorization use case:

You write rules that allow (or deny) access to your service APIs.

Your service queries OPA when it receives API requests.

OPA returns allow (or deny) decisions to your service.

Your service 

enforces

 the decisions by accepting or rejecting requests accordingly.

For concrete examples of how to integrate OPA with systems like

 

Kubernetes

https://www.openpolicyagent.org/docs/kubernetes

,

 

Terraform

https://www.openpolicyagent.org/docs/terraform

,

 

Docker

https://www.openpolicyagent.org/docs/docker-authorization

,

 

SSH

https://www.openpolicyagent.org/docs/ssh-and-sudo-authorization

,

 

and more, see 

openpolicyagent.org

https://www.openpolicyagent.org

.

Presentations

Open Policy Agent (OPA) Intro & Deep Dive @ Kubecon EU 2026: 

video

https://www.youtube.com/watch?v=TENlj4r6IXk

Open Policy Agent (OPA) Intro & Deep Dive @ Kubecon NA 2025: 

video

https://www.youtube.com/watch?v=tDBYMF2XXLA

Open Policy Agent (OPA) Intro & Deep Dive @ Kubecon EU 2025: 

video

https://www.youtube.com/watch?v=XtA-NKoJDaI

Open Policy Agent (OPA) Intro & Deep Dive @ Kubecon NA 2024: 

video

https://www.youtube.com/watch?v=QuotLxFb2f4

Open Policy Agent (OPA) Intro & Deep Dive @ Kubecon EU 2024: 

video

https://www.youtube.com/watch?v=hENwFyrtm1g

Open Policy Agent (OPA) Intro & Deep Dive @ Kubecon NA 2023: 

video

https://www.youtube.com/watch?v=wJkjsvVpj_Q

Open Policy Agent (OPA) Intro & Deep Dive @ Kubecon EU 2023: 

video

https://www.youtube.com/watch?v=6RNp3m_THw4

Running Policy in Hard to Reach Places with WASM & OPA @ CN Wasm Day EU 2023: 

video

https://www.youtube.com/watch?v=BdeBhukLwt4

OPA maintainers talk @ Kubecon NA 2022: 

video

https://www.youtube.com/watch?v=RMiovzGGCfI

Open Policy Agent (OPA) Intro & Deep Dive @ Kubecon EU 2022: 

video

https://www.youtube.com/watch?v=MhyQxIp1H58

Open Policy Agent Intro @ KubeCon EU 2021: 

Video

https://www.youtube.com/watch?v=2CgeiWkliaw

Using Open Policy Agent to Meet Evolving Policy Requirements @ KubeCon NA 2020: 

video

https://www.youtube.com/watch?v=zVuM7F_BTyc

Applying Policy Throughout The Application Lifecycle with Open Policy Agent @ CloudNativeCon 2019: 

video

https://www.youtube.com/watch?v=cXfsaE6RKfc

Open Policy Agent Introduction @ CloudNativeCon EU 2018: 

video

https://youtu.be/XEHeexPpgrA

, 

slides

https://www.slideshare.net/slideshow/opa-the-cloud-native-policy-engine/96644504

Rego Deep Dive @ CloudNativeCon EU 2018: 

video

https://youtu.be/4mBJSIhs2xQ

, 

slides

https://www.slideshare.net/slideshow/rego-deep-dive/96644608

How Netflix Is Solving Authorization Across Their Cloud @ CloudNativeCon US 2017: 

video

https://www.youtube.com/watch?v=R6tUNpRpdnY

, 

slides

https://www.slideshare.net/slideshow/how-netflix-is-solving-authorization-across-their-cloud/84384095

.

Policy-based Resource Placement in Kubernetes Federation @ LinuxCon Beijing 2017: 

slides

https://www.slideshare.net/slideshow/policybased-resource-placement-across-hybrid-cloud/83876901

, 

screencast

https://www.youtube.com/watch?v=hRz13baBhfg&feature=youtu.be

Enforcing Bespoke Policies In Kubernetes @ KubeCon US 2017: 

video

https://www.youtube.com/watch?v=llDI8VvkUj8

, 

slides

https://www.slideshare.net/slideshow/enforcing-bespoke-policies-in-kubernetes/83877237

Istio's Mixer: Policy Enforcement with Custom Adapters @ CloudNativeCon US 2017: 

video

https://www.youtube.com/watch?v=czZLXUqzd24

, 

slides

https://www.slideshare.net/slideshow/istios-mixer-policy-enforcement-with-custom-adapters-cloud-nativecon-17/83877455

Security

A third party security audit was performed by Cure53, you can see the full report 

here

SECURITY_AUDIT.pdf

.

Please report vulnerabilities by email to 

open-policy-agent-security

mailto:open-policy-agent-security@googlegroups.com

.

 

We will send a confirmation message to acknowledge that we have received the

 

report and then we will send additional messages to follow up once the issue

 

has been investigated.

## SECURITY.md



Security Policy

Please refer to the 

OPA Security Policy

https://www.openpolicyagent.org/security

 

for details on how to report security issues, our disclosure policy, and how to

 

receive notifications about security issues.

## docs\.gitignore



.docusaurus

 

build

 

node_modules*

 

package-lock.json

this is generated by the build process

static/data/versions.json

 

static/schemas/ir/v1/plan.schema.json

 

static/schemas/bundle/v1/manifest.schema.json

## docs\.markdownlint-cli2.jsonc



{

 

// Configuration for markdownlint-cli2

 

"config": {

 

// Use default rules with some exceptions

 

"default": true,

 

// Allow inline HTML (common in documentation)

 

"MD033": false,

 

// Allow long lines (code blocks and tables can be long)

 

"MD013": false,

 

// Allow multiple headers with the same content (Docusaurus indexes duplicates for us)

 

"MD024": false,

 

// Allow emphasis as heading

 

"MD036": false,

 

// Allow fenced code blocks without blank lines around them

 

"MD031": false,

 

// Allow fenced code blocks without language specified

 

"MD040": false,

 

// Configure hard tabs to convert to spaces, can be auto fixed

 

"MD010": {

 

"spaces_per_tab": 4

 

},

 

// Configure MD025 to ignore frontmatter titles

 

"MD025": {

 

"front_matter_title": ""

 

}

 

},

 

"globs": [

 

"**/*.md"

 

],

 

"ignores": [

 

"node_modules",

 

"build",

 

".docusaurus",

 

// Imported from other repos, should not be checked

 

"projects/regal",

 

"docs/cheatsheet.md",

 

"docs/style-guide.md",

 

// Auto-generated, should not be checked

 

"docs/cli.md"

 

]

 

}

## docs\.npmrc



registry=https://registry.npmjs.org

## docs\.nvmrc



24

## docs\.vale.ini



StylesPath = config

 

MinAlertLevel = suggestion

Vocab = Vale

[*.md]

 

BasedOnStyles = Vale, OPA

 

Vale.Terms = NO

 

BlockIgnores = (?s)(

.*?

)

[build/**]

 

BasedOnStyles =

[src/data/ecosystem/entries/*.md]

 

Vale.Spelling = NO

[src/data/ecosystem/features/*.md]

 

Vale.Spelling = NO

[projects/regal/**/*.md]

 

BasedOnStyles =

[docs/cheatsheet.md]

 

BasedOnStyles =

[docs/style-guide.md]

 

BasedOnStyles =

## docs\Makefile



.PHONY: install

 

install:

 

npm install

.PHONY: ci

 

ci:

 

npm ci

.PHONY: dev

 

dev:

 

# --no-open means that the browser will not be opened on start.

 

# This is done to avoid opening many tabs repeatedly when editing

 

# docusaurus.config.js.

 

npx docusaurus start --no-open

.PHONY: build

 

build:

 

npx docusaurus build

.PHONY: build-latest

 

build-latest:

 

./bin/build-latest.sh

.PHONY: clean

 

clean:

 

rm -rf build .docusaurus

.PHONY: generate-cli-docs

 

generate-cli-docs:

 

$(CURDIR)/../build/gen-cli-docs.sh > $(CURDIR)/src/data/cli.json

.PHONY: smoke-test

 

smoke-test:

 

./bin/smoke-test.sh

.PHONY: fmt

 

fmt:

 

npx dprint fmt

.PHONY: fmt-check

 

fmt-check:

 

npx dprint check

.PHONY: lint

 

lint:

 

npx eslint --fix .

.PHONY: lint-check

 

lint-check:

 

npx eslint .

.PHONY: markdownlint

 

markdownlint:

 

npx markdownlint-cli2 --fix

.PHONY: markdownlint-check

 

markdownlint-check:

 

npx markdownlint-cli2

.PHONY: spell-check

 

spell-check:

 

vale --config=.vale.ini .

.PHONY: gen

 

gen:

 

./bin/eval-examples.sh

.PHONY: gen-check

 

gen-check:

 

./bin/eval-examples.sh

 

@if [ -n "

(git status --porcelain)" ]; then 




echo "Error: working directory is not clean after running gen"; 




git diff; 




exit 1; 




fi

## docs\README.md



Documentation and Website Development

Please see the

 

contributing documentation

https://www.openpolicyagent.org/docs/contrib-docs

 

for information about how to get started contributing to the OPA documentation

 

and website.

## docs\bin\build-latest.sh



#!/usr/bin/env bash

set -euo pipefail

if ! git diff --quiet HEAD -- || ! git diff --cached --quiet; then

 

echo "Latest release build must be done without working changes"

 

git status

 

exit 1

 

fi

git fetch --tags origin

LATEST_TAG=

(git tag --sort=-version:refname | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+

' | head -1)

if [ -z "$LATEST_TAG" ]; then

 

echo "No valid release tag found (expected format: v1.2.3)"

 

exit 1

 

fi

for docs content we use the latest release

git checkout "$LATEST_TAG" -- docs

BUILD_VERSION="$LATEST_TAG" npx docusaurus build

## docs\bin\eval-examples.sh



#!/usr/bin/env bash

 

set -euo pipefail

SCRIPT_DIR="

(cd "

(dirname "

0")" && pwd)"
ROOT_DIR="

(cd "$SCRIPT_DIR/.." && pwd)"

failed=0

 

passed=0

 

skipped=0

 

total=0

while IFS= read -r config_file; do

 

dir="

(dirname "

config_file")"

 

total=

((total + 1))
rel_dir="

{dir#$ROOT_DIR/}"

Check if this example should be skipped

skip_reason=

(jq -r '.skip_output_reason // empty' "

config_file")

 

if /-n "$skip_reason"; then

 

echo "SKIP: 

rel_dir (

skip_reason)"

 

skipped=$((skipped + 1))

 

continue

 

fi

Read the command from config.json, default to data.play

command=

(jq -r '.command // "data.play"' "

config_file")

Build the opa eval args

args=()

 

args+=(-d "$dir/policy.rego")

if /-f "

dir/input.json"; then
args+=(-i "

dir/input.json")

 

fi

if /-f "

dir/data.json"; then
args+=(-d "

dir/data.json")

 

fi

args+=("$command")

 

args+=(-f pretty)

Run opa eval and write output

if output=

(opa eval "

{args[@]}" 2>&1); then

 

echo "

output" > "

dir/output.json"

 

echo "PASS: 

rel_dir"
passed=

((passed + 1))

 

else

 

echo "FAIL: $rel_dir"

 

echo "  

output" | head -5
failed=

((failed + 1))

 

fi

 

done < <(find "$ROOT_DIR" -name config.json -path '

/_examples/

')

echo ""

 

echo "Results: $passed passed, $failed failed, $skipped skipped, $total total"

 

exit $((failed > 0 ? 1 : 0))

## docs\bin\import-regal-docs.sh



#!/usr/bin/env bash

set -euo pipefail

if ! command -v curl >/dev/null 2>&1

 

then

 

echo "curl could not be found"

 

exit 1

 

fi

if ! command -v unzip >/dev/null 2>&1

 

then

 

echo "unzip could not be found"

 

exit 1

 

fi

function to extract title from frontmatter or first H1

extract_title() {

 

local yaml_file="

1"
local md_file="

2"

Try to extract title from YAML frontmatter

local title=

(grep '^title:' "

yaml_file" | sed 's/^title: *//; s/^"//; s/"$//')

If no title, try sidebar_label

if /-z "

title"; then
title=

(grep '^sidebar_label:' "

yaml_file" | sed 's/^sidebar_label: *//; s/^"//; s/"

//')

 

fi

If still no title, extract from first H1 in markdown

if /-z "

title" && -f "

md_file"; then

 

title=

(grep '^# ' "

md_file" | head -1 | sed 's/^# *//')

 

fi

Default fallback

if /-z "$title"; then

 

title="Regal"

 

fi

echo "$title"

 

}

download_regal() {

 

ref="heads/main"

 

if -v VERSION; then

 

ref="tags/$VERSION";

 

fi

examples

https://github.com/open-policy-agent/regal/archive/refs/heads/main.zip

https://github.com/open-policy-agent/regal/archive/refs/tags/v0.35.1.zip

url="https://github.com/open-policy-agent/regal/archive/refs/$ref.zip"

curl --silent -L -o regal.zip "$url"

 

}

if /-v REGAL_LOCAL_PATH && -d "$REGAL_LOCAL_PATH"; then

 

echo "Using local Regal directory: 

REGAL_LOCAL_PATH"
regal_docs_src="

REGAL_LOCAL_PATH/docs"

 

else

 

if /! -e regal.zip; then

 

download_regal

 

else

 

echo "Using existing regal.zip"

 

fi

tempdir=$(mktemp -d)

unzip regal.zip -d "$tempdir" 2>&1 > /dev/null

mv $tempdir/

/

 $tempdir

regal_docs_src="$tempdir/docs"

 

fi

 

regal_docs_dest="projects/regal"

rm -rf "

regal_docs_dest"
mkdir -p "

regal_docs_dest"

copy assets

rsync -ah "

regal_docs_src/assets/." "

regal_docs_dest/assets" --delete

generate index from readme-sections

readme_sections_dir="

regal_docs_src/readme-sections"
manifest="

readme_sections_dir/website-manifest"

{

 

while IFS= read -r file; do

 

section_path="

readme_sections_dir/

file"

 

if /-f "

section_path"; then
cat "

section_path"

 

echo ""

 

fi

 

done < "

manifest"
} > "

regal_docs_dest/index.md"

copy rules directory

cp -r "

regal_docs_src/rules" "

regal_docs_dest/"

process .md.yaml pairs to add head metadata

find "

regal_docs_src" -type f -name '*.md.yaml' | while read -r yaml_file; do
md_file="

(dirname 

yaml_file)/

(basename "

yaml_file" .yaml)"
md_file_rel=

{md_file#"

regal_docs_src/"}
dest_md_file="

regal_docs_dest/$md_file_rel"

mkdir -p "$(dirname $dest_md_file)"

if /! -e $md_file; then

 

echo "Warning: 

md_file missing"
else
# extract title for head metadata
title=

(extract_title "

yaml_file" "

md_file")

# generate file with frontmatter, head metadata, and content
{
  echo -e "---\n$(cat $yaml_file)\n---\n"
  echo -e "<head>\n  <title>$title | Regal</title>\n</head>\n"
  cat $md_file
} > "$dest_md_file"


fi

 

done

## docs\bin\import-rego-cheat-sheet.sh



#!/usr/bin/env bash

set -euo pipefail

if ! command -v curl >/dev/null 2>&1

 

then

 

echo "curl could not be found"

 

exit 1

 

fi

if ! command -v unzip >/dev/null 2>&1

 

then

 

echo "unzip could not be found"

 

exit 1

 

fi

download_cheatsheet() {

Always download from main branch

ref="heads/main"

https://github.com/open-policy-agent/rego-cheat-sheet/archive/refs/heads/main.zip

url="https://github.com/open-policy-agent/rego-cheat-sheet/archive/refs/$ref.zip"

curl --silent -L -o rego-cheat-sheet.zip "$url"

 

}

if /! -e rego-cheat-sheet.zip; then

 

download_cheatsheet

 

else

 

echo "Using existing rego-cheat-sheet.zip"

 

fi

tempdir=$(mktemp -d)

unzip rego-cheat-sheet.zip -d "$tempdir" 2>&1 > /dev/null

mv $tempdir/

/

 $tempdir

cheatsheet_src="$tempdir/build"

Destination paths relative to docs directory

cheatsheet_md_dest="docs/cheatsheet.md"

 

cheatsheet_pdf_dest="static/cheatsheet.pdf"

Copy the markdown file

if /-f "

cheatsheet_src/cheatsheet.md"; then
cp "

cheatsheet_src/cheatsheet.md" "$cheatsheet_md_dest"

 

echo "Copied cheatsheet.md to $cheatsheet_md_dest"

 

else

 

echo "Error: cheatsheet.md not found in $cheatsheet_src"

 

exit 1

 

fi

Copy the PDF file

if /-f "

cheatsheet_src/cheatsheet.pdf"; then
cp "

cheatsheet_src/cheatsheet.pdf" "$cheatsheet_pdf_dest"

 

echo "Copied cheatsheet.pdf to $cheatsheet_pdf_dest"

 

else

 

echo "Error: cheatsheet.pdf not found in $cheatsheet_src"

 

exit 1

 

fi

Clean up

rm -rf "$tempdir"

echo "Cheat sheet import complete!"

## docs\bin\import-rego-style-guide.sh



#!/usr/bin/env bash

set -euo pipefail

if ! command -v curl >/dev/null 2>&1

 

then

 

echo "curl could not be found"

 

exit 1

 

fi

if ! command -v unzip >/dev/null 2>&1

 

then

 

echo "unzip could not be found"

 

exit 1

 

fi

download_style_guide() {

Always download from main branch

ref="heads/main"

https://github.com/open-policy-agent/rego-style-guide/archive/refs/heads/main.zip

url="https://github.com/open-policy-agent/rego-style-guide/archive/refs/$ref.zip"

curl --silent -L -o rego-style-guide.zip "$url"

 

}

if /! -e rego-style-guide.zip; then

 

download_style_guide

 

else

 

echo "Using existing rego-style-guide.zip"

 

fi

tempdir=$(mktemp -d)

unzip rego-style-guide.zip -d "$tempdir" 2>&1 > /dev/null

mv $tempdir/

/

 $tempdir

style_guide_src="$tempdir/style-guide.md"

Destination path relative to docs directory

style_guide_dest="docs/style-guide.md"

Copy the markdown file

if /-f "

style_guide_src"; then
cp "

style_guide_src" "$style_guide_dest"

 

echo "Copied style-guide.md to $style_guide_dest"

 

else

 

echo "Error: style-guide.md not found in $tempdir"

 

exit 1

 

fi

Clean up

rm -rf "$tempdir"

echo "Style guide import complete!"

## docs\bin\smoke-test.sh



#!/usr/bin/env bash

this script contains a number of automated tests for website URLs that are

depended on externally. During the rollout of the new website, we hit some

issues with these URLs not being available so this script is here to be run

in post merge to ensure we don't break them again.

urls=(

 

"https://www.openpolicyagent.org/downloads/v1.4.2/opa_darwin_arm64_static"

 

"https://www.openpolicyagent.org/bundles/helm-kubernetes-quickstart"

 

"https://www.openpolicyagent.org/img/logos/opa-horizontal-color.png"

 

"https://www.openpolicyagent.org/img/logos/opa-no-text-color.png"

 

)

exit_code=0

for url in "${urls[@]}"; do

 

echo -n "Testing $url ... "

status=

(curl -s -o /dev/null -w "%{http_code}" -I "

url")

if /"

status" =~ ^2; then
echo "PASS (

status)"

 

else

 

echo "FAIL ($status)"

 

exit_code=1

 

fi

 

done

exit $exit_code

## docs\config\OPA\WeOur.yml



extends: existence

 

message: "Avoid first-person plural '%s'. Use direct address, active before passive."

 

level: error

 

ignorecase: false

Prefix excludes hyphen-prefixed matches (e.g. en-us in frontmatter URLs).

nonword: true

 

tokens:

'(?:^|[^-\w])[Ww]e\b'

'(?:^|[^-\w])[Oo]ur\b'

'(?:^|[^-\w])[Uu]s\b'

## docs\config\config\vocabularies\Vale\accept.txt



Rego

 

OPA

 

opa

 

OPA's

 

OPAs

 

Wasm

 

APIs

 

ACLs

 

stdin

 

boolean

 

booleans

 

Makefile

 

GitHub

 

Netlify

 

Algolia

 

Bugfix

 

bugfix

 

Rebase

 

Trivy

 

ngrok

 

tunnelmole

 

upstreamed

 

unexported

 

Vendoring

 

vendoring

 

repo

 

Conftest

 

Jsonnet

 

swiss

 

Dev

 

Builtins

 

untrusted

 

inlined

 

Inlined

 

inlining

 

namespace

 

namespaces

 

namespacing

 

namespaced

 

hostname

 

hostnames

 

subpackages

 

Subpackage

 

subschemas

 

subSchemas

 

Metaschemas

 

metasyntactic

 

Metasyntactic

 

oneOf

 

enum

 

dynamicity

 

eval

 

const

 

toc

 

arity

 

ORs

 

Datalog

 

datalog

 

unkeyed

 

SDKs

 

toolchain

 

Trino

 

Traefik

 

Quali

 

Troque

 

Strimzi

 

Tavo

 

Sysdig

 

Spacelift

 

spacelift

 

authorizer

 

SVIDs

 

Scalr

 

Raygun

 

iptables

 

destructuring

 

Regal

 

Regal's

 

JUnit

 

Config

 

CRDs

 

Gzip

 

superset

 

liveness

 

multitarget

 

subcommand

 

Javascript

 

hoc

 

runtimes

 

JSON

 

NGINX

 

sudo

 

sudoer

 

sshd

 

Istio

 

Istio's

 

Gloo

 

JWTs

 

errored

 

profiler

 

todos

 

RBAC

 

SemVer

 

substring

 

precompute

 

downloader

 

Etag

 

upsert

 

datasource

 

middleware

 

Postgres

 

MySQL

 

Neovim

 

Nano

 

Minikube

 

AWS

 

impactful

 

reachability

 

postprocessing

 

declaratively

 

toolset

 

sidebar_label

 

sidebar_position

 

GCP

 

Unicode

 

walkthrough

 

colocating

 

datasources

 

OCP's

 

subnets

 

bool

## docs\config\config\vocabularies\Vale\reject.txt



## docs\devel\DEVELOPMENT.md



Development

The development guide has become part of the Contributing documentation

 

and can be found 

in the Contributing documentation

https://www.openpolicyagent.org/docs/contrib-development

.

## docs\devel\RELEASE.md



Release Process

Overview

The release process consists of two phases: versioning and publishing the release.

Versioning involves maintaining the following files:

CHANGELOG.md

 - this file contains a list of all the important changes in each release.

Makefile

 - the Makefile contains a VERSION variable that defines the version of the project.

The steps below explain how to update these files. In addition, the repository

 

should be tagged with the semantic version identifying the release.

Publishing involves creating a new 

Release

 on GitHub with the relevant

 

CHANGELOG.md snippet and uploading the binaries from the build phase.

Note: This release process is subject to change without notice.

Release Cadence

There are two version tracks for the OPA project:

Release Candidate (vX.Y.Z-rc.A)

Stable (vX.Y.Z)

A new version of OPA is scheduled to release on the last Friday of every month. At the beginning of that week,

 

a release candidate branch (

release-<major>.<minor>-rc.0

) will be created from the main branch and a release

 

candidate tag (

v<major>.<minor>.0-rc.0

) will be created based on the release candidate branch for pre-release. Once the pre-release

 

is published, users are encouraged to try out the features, bug fixes in the release candidate. If regressions or bugs

 

are detected, they need to get fixed before cutting the stable release. It is not recommended to use OPA release

 

candidates in a production environment. The stable release that comes out after the release candidate may be identical

 

to the release candidate if no other features or bug fixes are introduced to the main branch in between.

See the next section for details on cutting an individual release.

Versioning

The steps below assume an OPA development environment has configured for the

 

standard GitHub fork workflow. See 

OPA Dev Instructions

DEVELOPMENT.md

The following steps assume a remote named 

upstream

 exists that references the OPA source

 

repository. As needed, add an 

upstream

 remote for the repository:

Note: This stage can fail if you have not registered an 

SSH key

https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account

 

on your GitHub account.

Create a release branch off of 

main

, to ensure you don't mangle your

 

fork while creating the release:

Create a 

personal access token

https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens

 

for GitHub with the 'read:org' scope. Export it to the 

GITHUB_TOKEN

 environment variable.

Execute the release-patch target to generate boilerplate patch. Give the semantic version of the release:

Apply the release patch to the working copy and preview the changes:

Commit the changes and push to remote repository fork.

Create a Pull Request for the release preparation commit.

Once the Pull Request has merged fetch the latest changes and tag the commit to prepare for publishing:

Create a new branch for the dev-patch work:

Execute the dev-patch target to generate boilerplate patch. Give the semantic version of the next release:

Apply the patch to the working copy and preview the changes:

Commit the changes and push to remote repository fork.

Create a Pull Request for the development preparation commit.

Publishing

Push the release tag to remote source repository.

Open browser and go to 

https://github.com/open-policy-agent/opa/releases

https://github.com/open-policy-agent/opa/releases

Update the draft release (may take up to 20 min for the draft to become

 

available, track its process under

 

https://github.com/open-policy-agent/opa/actions

https://github.com/open-policy-agent/opa/actions

).

 

Ensure everything looks OK and publish when ready.

Notes

The openpolicyagent/opa Docker image is automatically built and published to

 

Docker Hub as part of the Travis-CI pipeline. There are no manual steps

 

involved here.

The docs and website should update and be published automatically. If they are not you can

 

trigger one by a couple of methods:

Login to Netlify (requires permission for the project) and manually trigger a build.

Post to the build webhook via:

The Algolia search index is automatically updated when the site is crawled daily at 20:30 (UTC). The

 

crawling process takes around 25 minutes to complete and can be triggered from

 

crawler.algolia.com

https://crawler.algolia.com

 (login details required).

Bugfix Release Process

The following steps assume a remote named 

upstream

 exists that references the OPA source

 

repository. As needed, add an 

upstream

 remote for the repository:

git remote add upstream git@github.com:open-policy-agent/opa.git
git fetch --tags upstream


sh

If this is the first bugfix for the release, create the release branch from the

 

release tag and push to the source repository.

git checkout -b release-0.14 v0.14.0
git push upstream release-0.14


bash

Otherwise, checkout the release branch and sync with 

upstream

 (as needed):

git fetch upstream
git checkout release-0.14
git reset --hard upstream/release-0.14


bash

Cherry pick the changes from main or other branches onto the bugfix branch:

git cherry-pick -x <commit-id>


bash

Using 

-x

 helps to keep track of where the commit came from originally

Update the 

VERSION

 variable in the Makefile and CHANGELOG, same workflow as a normal release.

make release-patch VERSION=0.14.1 > ~/release.patch


bash

Apply the patch to the working copy and preview the changes:

patch -p1 < ~/release.patch
git diff


bash

The generated CHANGELOG will likely need some manual adjustments for bugfix releases!

Commit this change and push to fork:

git commit -s -a -m 'Prepare v0.14.1 release'
git push origin release-0.14


bash

Open a Pull Request against the upstream release branch. Be careful to open the

 

Pull Request against the correct upstream release branch. 

DO NOT

 open/merge

 

the Pull Request into main or other release branches.

Note: Make sure to do a "Rebase and merge" and NOT a squash when merging the PR, to preserve the cherry-picked commits.

 

Alternatively, the cherry-picks can be pushed to 

upstream

 before submitting the PR.

Once the Pull Request has merged fetch the latest changes and tag the commit to

 

prepare for publishing. Use the same instructions as defined above in normal

 

release 

publishing

#publishing

 guide (being careful to tag the appropriate commit).

Last step is to copy the CHANGELOG snippet and generated files

 

(builtin_metadata.json and capabilities.json) for the version to 

main

. Create

 

a new PR with the version information added below the 

Unreleased

 section.

 

Remove any 

Unreleased

 notes if they were included in the bugfix release.

## docs\docs\assets\OverviewDiagram.jsx



import Mermaid from "@theme/Mermaid";

const logoPath = require("./logo.png").default;

const diagram = 

graph TD; Client -->|Request/Event| Service; Service -->|"Query<br/>(any JSON Value)"| OPA["<img src='${logoPath}' width='50' />"]; OPA -->|"Decision<br/>(any JSON Value)"| Service; Policy["Policy (Rego)"] --> OPA; Data["Data (JSON)"] --> OPA;

;

const OverviewDiagram = () => 

<Mermaid value={diagram} />

;

export default OverviewDiagram;

## docs\docs\assets\logo.png



�PNG

 


```
