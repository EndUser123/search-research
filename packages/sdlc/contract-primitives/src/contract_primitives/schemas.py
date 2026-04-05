from __future__ import annotations

from dataclasses import dataclass, field
import re

REQUIRED_PLAN_MATRIX_FIELDS = [
    "Boundary",
    "Contract authority packet",
    "Producer",
    "Consumer",
    "Input Schema",
    "Output Schema",
    "Required Fields",
    "Freshness Authority",
    "Invalidation Trigger",
    "Failure Behavior",
    "Packet Alignment",
    "Test Binding",
]

REQUIRED_BOUNDARY_FIELDS = {
    "producer",
    "consumer",
    "schema.id",
    "schema.version",
    "required_fields",
    "freshness_authority",
    "invalidation_trigger",
    "precedence_rule",
    "failure_behavior",
    "validator_owner",
    "proof_owner",
}

PLACEHOLDER_BINDINGS = {
    "[tbd]",
    "[tbd per phase]",
    "tbd",
    "todo",
    "n/a",
}

ACTIVE_PLAN_ARTIFACT_FAILURE_BEHAVIOR = (
    "Blocking gate in /planning before implementation-ready; blocker for /code and /verify"
)


@dataclass(slots=True)
class BoundaryContract:
    boundary_id: str
    producer: str = ""
    consumer: str = ""
    schema_id: str = ""
    schema_version: str = ""
    required_fields: list[str] = field(default_factory=list)
    optional_fields: list[str] = field(default_factory=list)
    freshness_authority: str = ""
    invalidation_trigger: str = ""
    precedence_rule: str = ""
    failure_behavior: str = ""
    validator_owner: str = ""
    proof_owner: str = ""
    downstream_consumers: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ContractAuthorityPacket:
    packet_version: str = ""
    boundaries: dict[str, BoundaryContract] = field(default_factory=dict)


def _normalize_cell(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def extract_markdown_table(section_text: str) -> tuple[list[str], list[dict[str, str]]]:
    """Extract the first markdown table from a section."""
    lines = [line.rstrip() for line in section_text.splitlines() if line.strip()]
    header_idx = -1
    # Markdown table separator: row of only |, -, :, space (with optional leading/trailing |)
    # e.g. |---|---|---| or |---|:---|:---|  or |-------------|-----------------|
    for idx in range(len(lines) - 1):
        if lines[idx].startswith("|"):
            # Strip outer | delimiters; remaining chars must be valid separator content
            sep = lines[idx + 1]
            inner = sep[1:-1] if sep.startswith("|") and sep.endswith("|") else sep
            # Valid: whitespace, -, :, |
            if all(c in ("-", ":", " ", "|") for c in inner):
                header_idx = idx
                break

    if header_idx < 0:
        return [], []

    headers = [_normalize_cell(cell) for cell in lines[header_idx].strip("|").split("|")]
    rows: list[dict[str, str]] = []

    for raw_line in lines[header_idx + 2 :]:
        if not raw_line.startswith("|"):
            break
        cells = [_normalize_cell(cell) for cell in raw_line.strip("|").split("|")]
        if len(cells) != len(headers):
            continue
        rows.append(dict(zip(headers, cells, strict=False)))

    return headers, rows


def find_contract_boundary_rows(plan_text: str) -> tuple[list[str], list[dict[str, str]]]:
    pattern = r"^##\s+Contract Boundary Matrix.*?(?=^##\s|\Z)"
    match = re.search(pattern, plan_text, flags=re.MULTILINE | re.DOTALL)
    if not match:
        return [], []
    return extract_markdown_table(match.group(0))


def parse_contract_authority_packet(markdown_text: str) -> ContractAuthorityPacket:
    """Parse the markdown-rendered packet block from an ADR.

    The packet is written as YAML-like markdown. This parser keeps to the
    stable fields that downstream validators need for alignment checks.
    """
    packet = ContractAuthorityPacket()
    packet_match = re.search(
        r"contract_authority_packet:\s*(.*?)(?=^```|\Z)",
        markdown_text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if not packet_match:
        return packet

    packet_body = packet_match.group(1)
    version_match = re.search(r"packet_version:\s*\"?([^\n\"]+)\"?", packet_body)
    if version_match:
        packet.packet_version = version_match.group(1).strip()

    boundary_pattern = re.compile(
        r"^\s*-\s+boundary_id:\s*\"([^\"]+)\"(.*?)(?=^\s*-\s+boundary_id:|\Z)",
        flags=re.MULTILINE | re.DOTALL,
    )

    for match in boundary_pattern.finditer(packet_body):
        boundary_id = match.group(1).strip()
        block = match.group(2)
        contract = BoundaryContract(boundary_id=boundary_id)

        simple_fields = {
            "producer": "producer",
            "consumer": "consumer",
            "freshness_authority": "freshness_authority",
            "invalidation_trigger": "invalidation_trigger",
            "precedence_rule": "precedence_rule",
            "failure_behavior": "failure_behavior",
            "validator_owner": "validator_owner",
            "proof_owner": "proof_owner",
        }
        for target, attr in simple_fields.items():
            field_match = re.search(rf"{re.escape(target)}:\s*\"([^\"]*)\"", block)
            if field_match:
                setattr(contract, attr, field_match.group(1).strip())

        id_match = re.search(r"schema:\s*.*?id:\s*\"([^\"]+)\"", block, flags=re.DOTALL)
        version_match = re.search(r"schema:\s*.*?version:\s*\"([^\"]+)\"", block, flags=re.DOTALL)
        if id_match:
            contract.schema_id = id_match.group(1).strip()
        if version_match:
            contract.schema_version = version_match.group(1).strip()

        for field_name, attr in (("required_fields", "required_fields"), ("optional_fields", "optional_fields"), ("downstream_consumers", "downstream_consumers")):
            list_match = re.search(rf"{field_name}:\s*\[(.*?)\]", block, flags=re.DOTALL)
            if list_match:
                values = [
                    _normalize_cell(item.strip("\"' "))
                    for item in list_match.group(1).split(",")
                    if item.strip()
                ]
                setattr(contract, attr, values)
            else:
                values = re.findall(rf"{field_name}:\s*\n((?:\s*-\s+[^\n]+\n?)*)", block, flags=re.DOTALL)
                if values:
                    items = [
                        _normalize_cell(item)
                        for item in re.findall(r"-\s+([^\n]+)", values[0])
                    ]
                    setattr(contract, attr, items)

        packet.boundaries[boundary_id] = contract

    return packet
