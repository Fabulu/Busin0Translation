# 🧠 Memory & Context Optimization

> **Purpose**: Strategies for efficient context management when working with AI coding agents.
>
> **[TODO: Update the document names, constants, and examples in this file to match your
> project's actual documentation structure, file names, and key constants.]**

---

## 🎯 Context Loading Strategy

### Progressive Disclosure Principle

**Don't load everything at once. Load based on task type.**

```
Task Type                → Load These Documents
─────────────────────────────────────────────────
Quick command/fix        → [your quick reference doc] only
Debugging error          → [your troubleshooting doc] + error logs
Adding new feature       → [your examples doc] + [your diagrams doc]
Understanding arch       → [your diagrams doc] → [your architecture doc]
First time contributor   → [your dev workflows doc] → [your examples doc]
```

<!-- [TODO: Replace the bracketed placeholders above with your actual doc file names.
     Example: "[your quick reference doc]" → "QUICK_REFERENCE.md"] -->

---

## 📚 Document Loading Order

### Tier 1: Always Available (Cache These)

**Load at conversation start, keep in working memory:**

1. **CLAUDE.md** — Navigation hub and essential quick reference
2. **Key constants** — Your project's port numbers, import patterns, critical rules
3. **Core architectural rule(s)** — The 1-2 rules that can't be violated

**[TODO: List your Tier 1 constants here once you know your project:**
```
Examples from a real project:
- Service Port Matrix: port A = X, port B = Y
- Import Pattern: from [package]. not from [path.package].
- Dual-Database Rule: Config DB vs Data DB (never mix them)
```
]

### Tier 2: Task-Specific (Load on Demand)

**Load only when task requires:**

| Document Category | When to Load |
|-------------------|--------------|
| Examples / patterns doc | Implementing features |
| Diagrams / flows doc | Understanding architecture |
| Quick reference doc | Need specific commands |
| Troubleshooting doc | Debugging specific error |
| Dev workflows doc | Onboarding / setup tasks |

<!-- [TODO: Fill in your actual doc names and approximate token costs in this table.] -->

### Tier 3: Deep Dives (Load Sparingly)

**Only load for complex architectural work:**

| Document Category | When to Load |
|-------------------|--------------|
| Architecture context doc | Major refactoring |
| Service/module README files | Service-specific work |
| API/endpoint references | API changes |

---

## 🔄 Context Refresh Strategy

### When to Refresh Context

**Indicators you need to reload:**
- ❌ Suggesting patterns that don't exist in current codebase
- ❌ Using import paths that were refactored away
- ❌ Referencing endpoints that were deprecated
- ❌ Assuming file structure that changed

**Refresh triggers:**
- Major codebase changes (file moves, deletions)
- After prolonged conversation (>50 messages)
- When user corrects architectural assumptions
- After significant upstream changes

### Selective Refresh Pattern

```
# Don't refresh everything - refresh what changed

# Scenario: User says "we removed ClassX"
Refresh: examples doc (has ClassX usage)
Keep:    diagrams doc (unchanged)
Keep:    quick reference (unchanged)

# Scenario: User says "we changed port from A to B"
Refresh: quick reference (has port matrix)
Refresh: CLAUDE.md (has port numbers)
Keep:    examples doc (no hardcoded ports)
```

---

## 🎯 Task-Based Loading Patterns

### Pattern 1: Quick Fix Task

**Example**: "Fix the typo in config.py line 96"

**Load Strategy**:
```
1. Read target file only (config.py)
2. Fix typo
3. Done

No docs needed - file path is explicit
```

**Token Usage**: ~500 tokens (file only)

### Pattern 2: Implement New Feature

**Example**: "Add a new API endpoint for weekly reports"

**Load Strategy**:
```
1. Examples doc → Find "endpoint pattern" section
2. Diagrams doc → Understand request flow
3. One existing implementation as reference
4. Implement following pattern exactly
```

**Token Usage**: ~30,000 tokens (2 docs + 1 file)

### Pattern 3: Debug Production Error

**Example**: "Getting 'permission denied' error on table access"

**Load Strategy**:
```
1. Troubleshooting doc → Find relevant section
2. Quick reference → Get debug commands
3. Diagnose: Check permissions configuration
4. Fix: Update access configuration
```

**Token Usage**: ~15,000 tokens (2 docs + minimal code)

### Pattern 4: Understand Architecture for Refactoring

**Example**: "Should we consolidate these two database clients?"

**Load Strategy**:
```
1. Diagrams doc → Understand current architecture
2. Architecture doc → Read design rationale
3. Examples doc → See current usage patterns
4. Trace actual usage in codebase
5. Make informed decision
```

**Token Usage**: ~50,000 tokens (3 docs + code exploration)

---

## 💾 Caching Strategies

### What to Cache Between Tasks

**Cache for entire conversation:**
- Port/service mappings (rarely change)
- Import path patterns
- Core architectural rules (which DB for what, never-mix rules)
- Security validation sequences

**Cache for current task only:**
- Specific file contents
- Endpoint implementation details
- Schema details

**Never cache:**
- Dynamic data (query results)
- User-specific configurations
- Temporary error states

### Pattern: Incremental Knowledge Building

```
Message 1: User: "Add new endpoint"
→ Load: examples doc (endpoint patterns)
→ Cache: Endpoint pattern structure

Message 2: User: "It should query inventory data"
→ Load: examples doc (database patterns) [already loaded, use cached]
→ Cache: DB executor usage pattern

Message 3: User: "Add error handling"
→ Load: examples doc (error handling section) [already loaded, use cached]
→ Use cached endpoint + database patterns
→ Implement complete solution

Token savings: ~32,000 tokens (didn't reload doc 3 times)
```

---

## 🔍 Smart File Reading

### When to Read Full Files vs Targeted Sections

**Read full file when:**
- File is <300 lines
- Need to understand overall structure
- Making changes that could affect multiple areas
- First time encountering this file

**Read targeted sections when:**
- File is >500 lines
- Know exact function/class needed
- Making isolated change
- Have seen file structure before

### Pattern: Lazy Loading Imports

```python
# Don't read every imported file - trace only what you need

# User: "Fix error in database.py endpoint"
# database.py imports: ConfigBuilder, DBConnection, SecurityValidator

Step 1: Read database.py (find error location)
Step 2: Error is in ConfigBuilder.build_from_config() call
Step 3: NOW read config_builder.py (only because error is there)
Step 4: Don't read DBConnection or SecurityValidator (not involved)

Token savings: ~4,000 tokens (didn't read 2 unnecessary files)
```

---

## 📊 Token Budget Guidelines

### Typical Task Token Usage

| Task Type | Typical Token Cost | Budget Allocation |
|-----------|-------------------|-------------------|
| Quick fix | 500-2,000 | 1% of context window |
| Add simple endpoint | 15,000-30,000 | 15% of context window |
| Debug complex error | 30,000-50,000 | 25% of context window |
| Major refactoring | 80,000-120,000 | 60% of context window |

### Token Optimization Techniques

**1. Summarize Before Storing**

```
Instead of caching entire file contents:
Cache: "runs.py has execute_run() at line 42 that calls ConfigBuilder"

Token savings: 90% (500 tokens vs 5,000 tokens)
```

**2. Extract Only Relevant Sections**

```
Full file: 800 lines = ~16,000 tokens
Relevant function: 50 lines = ~1,000 tokens

Read full file first, extract function, cache extraction
Token savings: 94% for repeated access
```

**3. Progressive Disclosure in Code Reading**

```
Step 1: Read function signature only (1 line)
Step 2: If needed, read docstring (5 lines)
Step 3: If needed, read full implementation (50 lines)

Don't jump to Step 3 unless Steps 1-2 prove insufficient
```

---

## 🚀 Optimized Workflow Examples

### Workflow 1: Add New Component (Optimized)

```
❌ Suboptimal (100,000 tokens):
1. Load architecture doc (12,000 tokens)
2. Load examples doc (16,000 tokens)
3. Read all existing components (40,000 tokens)
4. Read related utilities (5,000 tokens)
5. Read security module (5,000 tokens)
6. Implement component
Total: 78,000 tokens before implementation

✅ Optimized (9,000 tokens):
1. Load examples doc → "Creating a Custom Component" section only (3,000 tokens)
2. Read one existing component as reference (5,000 tokens)
3. Read relevant utility → just the function needed (1,000 tokens)
4. Implement component
Total: 9,000 tokens before implementation

Savings: 69,000 tokens (76% reduction)
```

### Workflow 2: Debug Database Connection (Optimized)

```
❌ Suboptimal (80,000 tokens):
1. Load architecture doc (12,000 tokens)
2. Load dev workflows doc (10,000 tokens)
3. Load troubleshooting doc (8,000 tokens)
4. Read db_connection.py (5,000 tokens)
5. Read config_builder.py (6,000 tokens)
6. Read all .env files (2,000 tokens)
Total: 43,000 tokens

✅ Optimized (5,000 tokens):
1. Load troubleshooting doc → "Database Connection Problems" section (2,000 tokens)
2. Run suggested diagnostic command (0 tokens, just execute)
3. Based on error, read relevant file section only (3,000 tokens)
Total: 5,000 tokens

Savings: 38,000 tokens (88% reduction)
```

---

## 🎯 Decision Trees for Context Loading

### Decision Tree: Do I Need to Load Docs?

```
Is the file path explicit in user request?
├─ YES: Read file directly, no docs needed
└─ NO: Continue...

Do I know the exact pattern needed?
├─ YES: Load examples doc → Find pattern → Implement
└─ NO: Continue...

Is this architectural/design question?
├─ YES: Load diagrams doc → Understand → Decide
└─ NO: Continue...

Is this a debugging task?
├─ YES: Load troubleshooting doc → Find solution
└─ NO: Load quick reference for commands
```

### Decision Tree: Which Doc to Load?

```
Task involves...

├─ Commands/quick lookup? → [quick reference doc]
├─ Error message? → [troubleshooting doc]
├─ "How do I..." question? → [examples doc]
├─ "How does X work?" question? → [diagrams doc]
├─ "Why is X designed this way?" → [architecture doc]
├─ New developer setup? → [dev workflows doc]
└─ Simple code change? → No docs, read code directly
```

<!-- [TODO: Replace doc names in the decision trees with your project's actual file names.] -->

---

## 📈 Measuring Optimization Success

### Key Metrics

**1. Token Efficiency Ratio**
```
Formula: (Tokens used for implementation) / (Total tokens loaded)
Target: >0.5 (spent more tokens implementing than loading context)

Good: 10,000 tokens context, 15,000 tokens implementation = 0.6
Bad:  50,000 tokens context, 10,000 tokens implementation = 0.2
```

**2. First-Try Success Rate**
```
Formula: (Tasks completed without reloading docs) / (Total tasks)
Target: >0.7 (most tasks succeed with initial context)

Indicates: Loaded right context the first time
```

**3. Context Reuse Rate**
```
Formula: (Context used in multiple responses) / (Total context loaded)
Target: >2.0 (each loaded doc used at least twice)

Indicates: Efficient caching between related tasks
```

---

## 🛠️ Practical Tips

### Tip 1: Use CLAUDE.md as Your Compass

**Always start here.** It's the navigation hub that tells you where to find specific information.

```
Bad workflow:  Load all docs → Search for answer
Good workflow: CLAUDE.md "When to Use Each Guide" → Load specific doc
```

### Tip 2: Cache Constants and Patterns

**These rarely change and are referenced frequently:**

<!-- [TODO: List your project's key constants and patterns here, e.g.:
- Port mappings: service A = port X, service B = port Y
- Import pattern: from [module]. not from [path.module].
- Security sequence: validate → parameterize → execute
- Core architectural rule (e.g., which DB for which purpose)
] -->

### Tip 3: Lazy Load Everything Else

**Only load when you have concrete evidence you need it:**
- Implementation details (load when implementing)
- Endpoint internals (load when modifying)
- Schema details (load when writing queries)

### Tip 4: Summarize and Compress

**After loading large doc, extract and cache key points:**

```
Instead of keeping 16,000 tokens of an examples doc in memory:

Extract and cache:
- "Endpoint pattern: Hydrate config, execute agent, return structured response"
- "Tool pattern: Inherit BaseTool, accept context, return dict"
- "Security pattern: Validate before execute, parameterize always"

Reduced to: ~500 tokens
```

### Tip 5: Know When to Stop Loading

**Stop loading context when you can answer:**
1. What file(s) do I need to modify?
2. What pattern should I follow?
3. What are the critical constraints (security, validation, etc.)?

**If you can answer these, start implementing. Load more only if blocked.**

---

**Last Updated:** [TODO: update when you customize this file]
