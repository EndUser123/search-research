---

description: "Comprehensive standards compliance template for CSF NIP compliance validation"
---

# CSF NIP Standards Compliance Template

**Purpose**: Provide comprehensive standards compliance validation for all CSF NIP development activities
**Usage**: Apply this template before ANY development work to ensure standards compliance
**Blocking**: All development is BLOCKED until compliance requirements are met

## 🚨 MANDATORY Standards Compliance [BLOCKING GATE]

**CRITICAL**: Do NOT proceed with any development work until ALL compliance requirements below are completed

### Phase 1: System Discovery Protocol (MANDATORY)

#### Evidence-Based Discovery (BLOCKS ALL WORK)
- [ ] **Complete System Discovery Protocol**: Run full discovery from `docs/standards/processes/SYSTEM_DISCOVERY_PROTOCOL.md`
- [ ] **Standards Review**: Read `docs/STANDARDS_INDEX.md` and identify all applicable standards
- [ ] **Component Analysis**: Search `src/lib/core_utils/` for existing solutions BEFORE creating anything new
- [ ] **Knowledge System Search**: Search CSF NIP knowledge system for relevant patterns and lessons learned
- [ ] **Existing Solutions Documentation**: Document all existing solutions found with file paths and evidence

#### Infrastructure Usage Protocol (MANDATORY)
- [ ] **TaskMaster Validation**: Verify TaskMaster has required functionality before creating new tools
- [ ] **Tool Registry Consultation**: Check `docs/configuration/tool_registry.json` for existing tools
- [ ] **Anti-Duplication Rule**: Verify no duplicate functionality exists
- [ ] **Script Reference Verification**: Validate all script references before use
- [ **Infrastructure Compliance**: Ensure all operations comply with Infrastructure Usage Protocol

### Phase 2: Evidence Collection Requirements (MANDATORY)

#### Evidence-Based Answers Standard (MANDATORY)
- [ ] **Read Actual Code**: Never claim success without reading actual code
- [ ] **Evidence Collection**: Collect evidence for all technical claims
- [ ] **Anti-Deception Protocol**: Apply self-check: "Am I lying about success?"
- [ ] **Verification Integrity**: Run exact failing commands before/after fixes
- [ ] **Comparison Validation**: Compare output to verify resolution

#### Standards Evidence Documentation (MANDATORY)
- [ ] **Standards Citation**: Cite specific standards sections applicable to each work item
- [ ] **Compliance Evidence**: Document how each standard is being followed
- [ ] **Risk Assessment**: Document potential standards compliance risks
- [ ] **Mitigation Strategies**: Document strategies for standards compliance issues
- [ ] **Evidence Storage**: Store all evidence in CSF NIP knowledge system

### Phase 3: Quality Gate Validation (MANDATORY)

#### Command Verification Protocol (MANDATORY)
- [ ] **Help Flag Verification**: Use --help flag to verify command options
- [ ] **Pre-Execution Validation**: Verify all prerequisites and parameters
- [ ] **Evidence-Based Actions**: Never assume, always verify with real data
- [ ] **Quality Assurance**: Apply validation integrity protocols throughout execution

#### File Organization Standards (MANDATORY)
- [ ] **File Organization Standards**: Follow `docs/FILE_ORGANIZATION_STANDARDS.md`
- [ ] **Lib Component Check**: Check `src/lib/core_utils/` for existing utilities before creating new ones
- [ ] **Module Structure**: Follow proper module structure patterns
- [ ] **File Creation Protocol**: Apply file creation blocking sequence
- [ **Path Validation**: Verify all file paths are correct and accessible

#### Library Usage Protocol (MANDATORY)
- [ ] **Library Standards Check**: Apply Library Usage Protocol for all external libraries
- [ ] **Deprecation Validation**: Check for deprecated libraries and alternatives
- [ ] **Best Practices Integration**: Include library best practices in implementation
- [ ] **Alternative Analysis**: Document analysis of alternative libraries considered
- [ ] **Standards Compliance**: Validate library choices against standards

### Phase 4: Specialized Standards Integration

#### For Architectural Work (Apply when doing architecture/design)
- [ ] **Architectural Thinking Standard**: Generate 3-5 architectural alternatives with evidence
- [ ] **Tradeoff Analysis**: Analyze pros/cons for each approach
- [ ] **Evidence-Based Decisions**: Document rationale with evidence for chosen architecture
- [ ] **Pattern Application**: Document which architectural patterns were applied and why
- [ ] **Anti-Pattern Avoidance**: Document architectural anti-patterns avoided

#### For Custom Commands (Apply when creating commands/tools)
- [ ] **Custom Command Standard**: Follow entry point → instruction file pattern
- [ ] **CLI Enhancement Standard**: Apply proper CLI formatting and help documentation
- [ ] **YAML Frontmatter**: Ensure all required fields are present and correct
- [ ] **Help Documentation**: Include comprehensive help with examples and exit status
- [ ] **Error Handling**: Apply consistent error handling patterns

#### For Code Implementation (Apply when writing code)
- [ ] **Code Quality Standards**: Apply linting, type checking, and formatting standards
- [ ] **Testing Standards**: Include appropriate testing for all implementations
- [ ] **Documentation Standards**: Document all code with clear examples
- [ ] **Security Standards**: Apply security best practices for all code
- [ ] **Performance Standards**: Consider performance implications of implementation

### Phase 5: Knowledge System Integration (MANDATORY)

#### Pattern Storage and Retrieval (MANDATORY)
- [ ] **Pattern Search**: Search CSF NIP knowledge system for relevant patterns
- [ ] **Knowledge Storage**: Store findings and decisions in CSF NIP knowledge system
- [ ] **Lessons Learned**: Document lessons learned for future reference
- [ ] **Pattern Contribution**: Contribute new patterns discovered during work
- [ ] **Evidence Linking**: Link all evidence to knowledge system entries

#### Continuous Improvement (MANDATORY)
- [ ] **Pattern Validation**: Validate patterns against real implementation results
- [ ] **Knowledge Base Enhancement**: Improve knowledge base with new insights
- [ ] **Standards Evolution**: Contribute to standards evolution based on experience
- [ ] **Best Practices Documentation**: Document best practices discovered
- [ ] **Community Contribution**: Share valuable patterns with broader community

## Validation Commands (Run These to Verify Compliance)

### System Discovery Commands
```bash
# MANDATORY: Run System Discovery Protocol
cd "C:\_Python\_Projects\__csf.nip"
python src/modules/orchestration/discovery_engine.py discover --project [project-name]

# MANDATORY: Search Knowledge System
python scripts/knowledge_interface.py search --query "[project-context] patterns"

# MANDATORY: Check TaskMaster
cd "C:\_Python\_Projects\__csf.nip"
python tsk.py --help
python tsk.py list-commands
```

### Infrastructure Validation Commands
```bash
# MANDATORY: Check Tool Registry
cat "C:\_Python\_Projects\__csf.nip\docs\configuration\tool_registry.json"

# MANDATORY: Verify Script References
cd "C:\_Python\_Projects\__csf.nip"
python scripts/[script-name].py --help

# MANDATORY: Check Lib Components
python src/lib/core_utils/library_knowledge_extractor.py tools
```

### Standards Compliance Commands
```bash
# MANDATORY: Validate Against Standards
python src/lib/core_utils/standards_validator.py validate --category [category] --project [project-name]

# MANDATORY: Library Standards Check
python src/lib/core_utils/library_knowledge_extractor.py check --libs [libraries]

# MANDATORY: Evidence Validation
python src/lib/core_utils/evidence_verifier.py validate --artifacts discovery,evidence,standards
```

## Blocking Gates

### Development is BLOCKED until:
- [ ] System Discovery Protocol completed with documented evidence
- [ ] All relevant standards identified and cited in work plan
- [ ] Existing solutions researched and documented with file paths
- [ ] Evidence collected for all major decisions
- [ ] Infrastructure compliance verified (TaskMaster, tool registry, anti-duplication)
- [ ] File organization standards validated
- [ ] Library standards validation completed for all mentioned libraries
- [ ] Knowledge system integration completed with patterns stored
- [ ] All applicable specialized standards applied (architecture, commands, code)
- [ ] All validation commands executed successfully

## Compliance Checklist by Work Type

### For speckit.specify Work
- [ ] System Discovery Protocol completed
- [ ] Evidence-based specification creation
- [ ] Knowledge system integration for patterns
- [ ] File organization standards applied
- [ ] Command verification protocol followed

### For speckit.plan Work
- [ ] All Phase 1-4 requirements above
- [ ] Architectural Thinking Standard applied
- [ ] 3-5 architectural alternatives generated and analyzed
- [ ] Evidence-based architectural decisions documented
- [ ] Architectural patterns researched and applied

### For speckit.tasks Work
- [ ] All Phase 1-4 requirements above
- [ ] Task generation standards applied
- [ ] Evidence-based task definition completed
- [ ] Library standards integration for all mentioned libraries
- [ ] Knowledge system integration for task patterns

### For Code Implementation Work
- [ ] All Phase 1-4 requirements above
- [ ] Code quality standards applied
- [ ] Testing standards followed
- [ ] Documentation standards applied
- [ ] Security and performance standards considered

## Error Prevention and Recovery

### Common Compliance Issues and Solutions

**Issue**: "Proceeded without System Discovery Protocol"
- **Solution**: Stop work, run discovery protocol, document findings, revise approach

**Issue**: "Created duplicate functionality"
- **Solution**: Stop work, check TaskMaster and tool registry, use existing solution

**Issue**: "Made technical claims without evidence"
- **Solution**: Stop work, gather evidence, verify claims with actual code/data

**Issue**: "Violated file organization standards"
- **Solution**: Review standards, reorganize files according to standards

**Issue**: "Used library without standards check"
- **Solution**: Research library standards, apply deprecation checks, validate choice

## Quality Assurance

### Final Compliance Validation
Before considering any work complete:
- [ ] Review all compliance checkboxes are checked
- [ ] Verify all evidence is documented and accessible
- [ ] Confirm all validation commands execute successfully
- [ ] Validate knowledge system integration is complete
- [ ] Ensure standards are cited and followed throughout work

### Continuous Improvement
- [ ] Document any standards that need clarification or improvement
- [ ] Contribute new patterns discovered during work
- [ ] Suggest improvements to compliance templates
- [ ] Share lessons learned to improve future compliance efforts

---

**Template Status**: MANDATORY for all CSF NIP development work
**Compliance Requirement**: 100% completion before any development work
**Template Version**: 1.0
**Last Updated**: [Date]
