---
title: "Pydantic Models and Serialization"
created: 2026-08-09
source: nlm-sync-2026-08-09
tags: [nlm-synced, reference, pydantic]
summary: >
  A Pydantic Model is a class inheriting from pydantic.BaseModel whose annotated attributes define a schema; Pydantic parses, coerces, and validates inputs so that the resulting instance conforms to declared types and constraints. Pydantic also provides serialization in two modes (Python mode via mode
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 0fa07246-ba84-43fd-a9cd-f86999f24286" (LLM-Driven Behavior Trees for Autonomous Robot Task Planning, synced 2026-08-09)
  - "NotebookLM source 18fa8ee0-f1f9-46c0-bdc3-2fe1e1abf18c" (grok_report (1).pdf, synced 2026-08-09)
  - "Models - Pydantic Validation" (https://docs.pydantic.dev/latest/concepts/models/, transcript synced 2026-08-09)
  - "pydantic_graph.persistence | Pydantic Docs" (https://pydantic.dev/docs/ai/api/pydantic_graph/persistence/, transcript synced 2026-08-09)
  - "Models - Pydantic documentation (en)" (https://pydantic.com.cn/en/concepts/models/, transcript synced 2026-08-09)
  - "NotebookLM source 69578f3d-1c3c-4a69-a119-fbfd2c126e3b" (grok_report (2).pdf, synced 2026-08-09)
  - "Pydantic Recursive Models in FastAPI: A Detailed Tutorial - Orchestra" (https://www.getorchestra.io/guides/pydantic-recursive-models-in-fastapi-a-detailed-tutorial, transcript synced 2026-08-09)
  - "Models - Pydantic" (https://docs.pydantic.dev/2.4/concepts/models/, transcript synced 2026-08-09)
  - "Models | Pydantic Docs" (https://pydantic.dev/docs/validation/2.4/concepts/models/, transcript synced 2026-08-09)
  - "Serialization - Pydantic Validation" (https://docs.pydantic.dev/latest/concepts/serialization/, transcript synced 2026-08-09)
  - "Serialization Of Pydantic Data Models With JSON Whilst Preserving Type Data" (https://janhendrikewers.uk/serialization_of_pydantic_data_models_with_json_whilst_preserving_type_data, transcript synced 2026-08-09)
  - "Models | Pydantic Docs" (https://pydantic.dev/docs/validation/latest/concepts/models/, transcript synced 2026-08-09)
  - "Serialization | Pydantic Docs" (https://pydantic.dev/docs/validation/latest/concepts/serialization/, transcript synced 2026-08-09)
provenance:
  chain:
    - level: concept
      id: pydantic-models-and-serialization
    - level: notebook
      id: 0fa07246-ba84-43fd-a9cd-f86999f24286
      title: LLM-Driven Behavior Trees for Autonomous Robot Task Planning
      url: https://notebooklm.google.com/notebook/0fa07246-ba84-43fd-a9cd-f86999f24286
    - level: cluster
      id: 2
      name: pydantic-docs-https
    - level: source_url
      url: https://docs.pydantic.dev/latest/concepts/models/
      title: Models - Pydantic Validation
    - level: source_url
      url: https://pydantic.dev/docs/ai/api/pydantic_graph/persistence/
      title: pydantic_graph.persistence | Pydantic Docs
    - level: source_url
      url: https://pydantic.com.cn/en/concepts/models/
      title: Models - Pydantic documentation (en)
    - level: source_url
      url: https://www.getorchestra.io/guides/pydantic-recursive-models-in-fastapi-a-detailed-tutorial
      title: Pydantic Recursive Models in FastAPI: A Detailed Tutorial - Orchestra
    - level: source_url
      url: https://docs.pydantic.dev/2.4/concepts/models/
      title: Models - Pydantic
    - level: source_url
      url: https://pydantic.dev/docs/validation/2.4/concepts/models/
      title: Models | Pydantic Docs
    - level: source_url
      url: https://docs.pydantic.dev/latest/concepts/serialization/
      title: Serialization - Pydantic Validation
    - level: source_url
      url: https://janhendrikewers.uk/serialization_of_pydantic_data_models_with_json_whilst_preserving_type_data
      title: Serialization Of Pydantic Data Models With JSON Whilst Preserving Type Data
    - level: source_url
      url: https://pydantic.dev/docs/validation/latest/concepts/models/
      title: Models | Pydantic Docs
    - level: source_url
      url: https://pydantic.dev/docs/validation/latest/concepts/serialization/
      title: Serialization | Pydantic Docs
relations:
  - target: wiki/concepts/typeadapter.md
    type: related
  - target: wiki/concepts/field-and-field_validator.md
    type: related
  - target: wiki/concepts/configdict-and-configuration.md
    type: related
---

# Pydantic Models and Serialization

## Decision context

**Definition:** A Pydantic Model is a class inheriting from pydantic.BaseModel whose annotated attributes define a schema; Pydantic parses, coerces, and validates inputs so that the resulting instance conforms to declared types and constraints. Pydantic also provides serialization in two modes (Python mode via model_dump() and JSON mode via model_dump_json()), with custom serializers, field inclusion/exclusion controls, and duck-typing options.

Synthesized from **12 contributing transcripts** in NotebookLM notebook *LLM-Driven Behavior Trees for Autonomous Robot Task Planning*, clustered into the "pydantic-docs-https" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Models are conceptually similar to C structs or a single API endpoint's schema requirements, and similar to Python dataclasses but tailored for validation, serialization, and JSON schema generation.
- Pydantic guarantees that the OUTPUT model conforms to declared types and constraints, not the input; a single ValidationError is raised containing all errors at once when parsing fails.
- The term 'validation' is a deliberate misnomer for instantiation, which may include copying and coercion (e.g., '123' coerced to int 123; 3.000 coerced to int 3; bytes coerced to str); a strict mode is available to disable coercion.
- Fields without defaults are required; fields with defaults are optional; fields supplied at instantiation are tracked via model_fields_set; model_dump() recursively converts nested models to dicts while dict(model) does not.
- Models are mutable by default; faux immutability is enabled via ConfigDict(frozen=True), which replaces V1's allow_mutation=False and raises ValidationError on attribute reassignment (deep mutation of mutable containers is still possible).
- Three validation modes are supported: Python (via __init__ or model_validate), JSON (via model_validate_json for str/bytes), and strings (via model_validate_strings for (nested) dicts of strings, validated in JSON mode).
- model_construct() builds a model without running validation; it does not recursively convert nested dicts, does not call __init__, and treats extra='forbid' as ignore; in V2 the performance gap vs __init__ has narrowed and may favor __init__ for simple models.
- Nested models support hierarchical data; self-referencing/recursive models use postponed/forward annotations, and model_rebuild() (replacing V1's update_forward_refs()) resolves them; calling rebuild() on the outermost model requires all nested types to be defined first.
- Generic models are declared via TypeVars and inherit from BaseModel plus typing.Generic (or PEP 695 syntax on Python 3.12+); parametrized classes are cached at runtime, and using parametrized generics in isinstance() is discouraged (subclass the parametrization instead).
- RootModel[T] defines a model with a single root value accessed via .root; subclasses can add methods or implement __iter__/__getitem__; the root value is passed positionally to __init__ and model_validate.
- Dynamic model creation uses pydantic.create_model(name, **fields) with special kwargs __base__, __config__, and __validators__; pickling requires the model to be defined globally with __module__ provided.
- Arbitrary class instances (formerly ORM Mode/from_orm) are validated via model_config['from_attributes'] = True or the from_attributes argument to model_validate(); aliases take priority over field names (useful for reserved attributes like SQLAlchemy 'metadata').
- Extra data behavior is controlled by ConfigDict(extra=...): 'ignore' (default, silently dropped), 'forbid' (raises ValidationError), or 'allow' (preserved in __pydantic_extra__, which can be typed via __pydantic_extra__: Dict[str, T] for validation); model_validate() accepts an extra argument that overrides config per call.
- Serialization supports Python mode (model_dump(), preserving non-JSON types like tuples by default) and JSON mode (model_dump_json(), converting types like tuple→list and datetime→ISO string); mode='json' on model_dump() forces JSON-compatible output; model_dump_json() accepts indent for pretty printing.
- Custom serializers can be field-level (PlainSerializer, WrapSerializer, or @field_serializer) or model-level (@model_serializer), with plain and wrap modes; only ONE serializer can be defined per field/model, and serializers may receive an info argument exposing context, mode, and method parameters.
- Duck-typing serialization (preserving subclass fields, V1 behavior) is enabled per-field via SerializeAsAny[T] or globally via serialize_as_any=True on model_dump()/model_dump_json(); V2 default excludes subclass-only fields to avoid leaking secrets.
- Field filtering options include include/exclude (sets or nested dicts, with negative indices and '__all__'), exclude_defaults, exclude_none, exclude_unset (tracked via model_fields_set), and Field(exclude=True)/Field(..., exclude_if=callable); the experimental MISSING sentinel excludes fields whose value is MISSING.

## Verifiable values

| Name | Value |
|---|---|
| Extra data behaviors | `'ignore' (default), 'forbid', 'allow'` |
| Validation modes | `Python, JSON, strings` |
| Serialization modes | `Python (model_dump), JSON (model_dump_json, mode='json')` |
| Serializer modes | `plain, wrap` |
| Documentation versions listed | `Latest, Dev, v2.11, v2.10, v2.9, v2.8, v2.7, v2.6, v2.5, v2.4, v2.3, v2.2, v2.1, v2.0, v1.10` |
| Pydantic Services Inc. copyright span | `2025 to present` |

## Related concepts

- typeadapter — TypeAdapter
- field-and-field_validator — Field and field_validator
- configdict-and-configuration — ConfigDict and Configuration
- json-schema-generation — JSON Schema generation
- strict-mode — Strict Mode
- validators — Validators
- dataclasses — Dataclasses
- type-hints-and-pep-695-generics — Type Hints and PEP 695 generics
- [[serialization-(sub-page)]] — Serialization (sub-page)
- [[pydantic-ai-persistence-(pydantic_graph.persistence)]] — Pydantic AI persistence (pydantic_graph.persistence)
- [[recursion-/-self-referencing-models-in-fastapi]] — Recursion / Self-referencing models in FastAPI

## Citations (from contributing transcripts)

- **Claim:** Pydantic Models are the primary way to define schema; they are classes that inherit from pydantic.BaseModel with fields declared as annotated attributes, conceptually similar to C structs.
  - Source: Models - Pydantic (`98606ed5-01db-458d-810c-9f8db235b4a1`)
  - Context: Pydantic Models are the primary way to define schema in Pydantic; they are classes that inherit from `pydantic.BaseModel` and declare fields as annotated attributes.
- **Claim:** Pydantic guarantees the output conforms to declared types and constraints, not the input; validation is a deliberate misnomer covering parsing and coercion.
  - Source: Models - Pydantic documentation (en) (`6427289f-b96f-4038-83bb-ae952fb782f2`)
  - Context: Pydantic guarantees that the fields of the resulting model instance conform to the declared field types after parsing and validating (potentially untrusted) input data.
- **Claim:** Three validation modes are supported: Python, JSON, and strings.
  - Source: Models | Pydantic Docs (`e8875f97-97e2-4a2a-a9b9-e9f7381a6a4a`)
  - Context: Pydantic supports three validation modes: Python (via `__init__` or `model_validate()`), JSON (via `model_validate_json()` for JSON strings/bytes), and strings (via `model_validate_strings()` for (nested) dicts of strings, which validates in JSON mode).
- **Claim:** Extra fields are controlled via extra='ignore' (default), 'forbid', or 'allow' (stored in __pydantic_extra__).
  - Source: Models - Pydantic Validation (`358daaee-395b-4cd7-a453-2d505ac09ac2`)
  - Context: Extra data behavior is controlled by the `extra` config with three values: `'ignore'` (default, extras silently dropped), `'forbid'` (raises error), `'allow'` (extras stored in `__pydantic_extra__`, which can be typed for validation).
- **Claim:** model_construct() creates models without validation; in V2 the performance gap vs __init__ has narrowed.
  - Source: Models | Pydantic Docs (`e8875f97-97e2-4a2a-a9b9-e9f7381a6a4a`)
  - Context: In Pydantic V2, the performance gap between `BaseModel.__init__` and `BaseModel.model_construct` has narrowed considerably; for simple models, `__init__` may even be faster, so profile before assuming `model_construct` is faster.
- **Claim:** Recursive models can be defined with string forward references and require resolving the reference.
  - Source: Pydantic Recursive Models in FastAPI: A Detailed Tutorial - Orchestra (`73a7767e-d7fa-464d-9735-9d95ccc720b0`)
  - Context: Define `class Category(BaseModel):` with `name: str` and `subcategories: Optional[List['Category']] = None`. Use a string forward reference (`'Category'`) for the self-referencing field. Call `Category.update_forward_refs()` to resolve the forward reference to the model itself.
- **Claim:** Generic models use TypeVars with BaseModel and typing.Generic; parametrized classes are cached; isinstance with parametrized generics is discouraged.
  - Source: Models | Pydantic Docs (`e8875f97-97e2-4a2a-a9b9-e9f7381a6a4a`)
  - Context: Generic models: declare `typing.TypeVar`s; inherit from `BaseModel` and `typing.Generic[...]`; use the `TypeVar`s as annotations. Parametrized instances like `Response[int](...)` validate against the concrete type.
- **Claim:** Serialization has Python mode (model_dump) and JSON mode (model_dump_json); Pydantic uses 'serialize' and 'dump' interchangeably.
  - Source: Serialization - Pydantic Validation (`a6ff5cd0-d6dd-490d-a292-338713f488cb`)
  - Context: Pydantic uses the terms 'serialize' and 'dump' interchangeably; both refer to converting a model (or model-like object such as a dataclass) into a dict or JSON-encoded string.
- **Claim:** Duck-typing serialization includes subclass fields; enabled per-field via SerializeAsAny[T] or globally via serialize_as_any=True.
  - Source: Serialization | Pydantic Docs (`ebc47ec1-1242-4d41-9291-2672e1406077`)
  - Context: Duck typing serialization serializes based on the actual runtime value's fields rather than the annotated type's fields. It is enabled per-field via the `SerializeAsAny[T]` annotation, or globally for a serialization call via `serialize_as_any=True` on `model_dump()`/`model_dump_json()`.
- **Claim:** Only ONE serializer can be defined per field/model; serializers may accept an info argument exposing context, mode, and method parameters.
  - Source: Serialization - Pydantic Validation (`a6ff5cd0-d6dd-490d-a292-338713f488cb`)
  - Context: Custom serializers are defined at the field or model level; only ONE serializer can be defined per field/model (cannot combine plain + wrap, or multiple serializers).

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `0fa07246-ba84-43fd-a9cd-f86999f24286`
(cluster `pydantic-docs-https`). No claims are made
about local workspace implementation. Trigger words like
'mechanism', 'scanner', 'gate', 'hook', 'because' refer to concepts
discussed in the source videos, not to local code behavior.
Implementation path: wiki-yt/scripts/synthesize_subtopics.py
(LLM synthesis from transcripts — no local code inspected).

## What this means for our workspace

Synced from NotebookLM. Provenance chain (concept → notebook → cluster → URL) is in frontmatter; follow it back to the source material.

## Falsifier

If a re-sync of the source notebook produces a different definition or different values, this page should be updated (or marked as superseded). The sync manifest at `P:/.data/wiki/_state/nlm-sync-manifest.json` records when this page was last regenerated.

## Sources

- NotebookLM notebook [LLM-Driven Behavior Trees for Autonomous Robot Task Planning](https://notebooklm.google.com/notebook/0fa07246-ba84-43fd-a9cd-f86999f24286)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)

## Auto-related

- [[sdlc-workflow-improvements-from-session-019fdf3d]]
- [[adaptive-expansion-evidence-triggered-conditional-steps]]
- [[Python-Behavior-Tree-Framework-for-Autonomous-LLM-Agents--Technical-Specificatio]]
- [[skill-catalog]]
- [[pipeline-orchestration-and-transport-reliability]]

