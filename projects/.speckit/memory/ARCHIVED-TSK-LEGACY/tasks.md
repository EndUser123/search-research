# TSK-LEGACY Task Registry

## Task Summary
- **Total Tasks**: 106
- **Status Distribution**:
  - ACTIVE: 78 tasks
  - COMPLETED: 8 tasks
  - PENDING: 15 tasks (conversation analysis)
  - UNKNOWN: 5 tasks

- **Priority Distribution**:
  - CRITICAL: 2 tasks
  - HIGH: 25 tasks
  - MEDIUM: 79 tasks

- **Source Systems**:
  - Task completion tracker: 91 tasks
  - Conversation analysis: 15 tasks

## High Priority Tasks (Top 10)

### CRITICAL Priority
1. **2d9e4d693abe994f** - Fix critical security vulnerability in authentication (ACTIVE)
2. **8757c8f763ab5f76** - Another security issue (ACTIVE)

### HIGH Priority (Conversation Analysis)
3. **task-2025-11-29-sessionstart-concurrent-execution** - Fix SessionStart hook concurrent execution (45 min, impact 0.9)
4. **task-2025-11-29-cwo12-docs-mismatch** - Fix CWO12 documentation vs implementation mismatch (120 min, impact 0.8)
5. **task-2025-11-29-requirements-clarification** - Improve requirements clarification process (90 min, impact 0.8)

### HIGH Priority (Development)
6. **78f9c300cb5f9105** - Implement user authentication (ACTIVE)
7. **6620cc0fe8794dcb** - Implement API endpoint (ACTIVE)
8. **5f7b568cb32bb957** - Write API tests (ACTIVE)
9. **38b7f32ae973d83e** - Implement user registration (ACTIVE)
10. **df7ce1840ce78976** - Red phase development (ACTIVE)

## Task Categories

### Development Tasks (60%)
- Feature implementation
- API development
- Authentication systems
- User management

### Infrastructure & Security (25%)
- Security fixes
- Authentication
- System configuration
- Deployment tasks

### Quality & Process (10%)
- Testing
- Code review
- Process improvements
- Documentation

### Conversation Analysis (5%)
- Development process improvements
- Organizational issues
- Tool standardization

## Recent Activity
- Most recent task created: 2025-10-28
- Migration completed: 2025-11-29
- Active development focus on authentication and API systems

## Migration Planning
Tasks are organized by natural project groupings for future migration:
- **Authentication/Security**: 15+ tasks
- **API Development**: 20+ tasks
- **Testing**: 10+ tasks
- **Documentation**: 8+ tasks
- **Process Improvement**: 15 tasks (conversation analysis)
- **Infrastructure**: 15+ tasks
- **General Development**: 23+ tasks

## Access Instructions
```bash
# Read tasks from canonical location
cat .speckit/memory/TSK-LEGACY/tasks.json

# Query specific task
jq '.tasks[] | select(.id == "TASK_ID")' .speckit/memory/TSK-LEGACY/tasks.json

# Get high priority tasks
jq '.tasks[] | select(.priority == "CRITICAL" or .priority == "HIGH")' .speckit/memory/TSK-LEGACY/tasks.json
```