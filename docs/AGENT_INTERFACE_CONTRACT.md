# Agent Interface Contract

**Stage: Core Runtime Prototype / Agent-Ready Foundation / Not Beta Yet**

This document defines the rules governing the relationship between Lucy and her future agents.
No agent is active in Part 1. This contract prepares for future agent integration.

---

## Core Principle

**Agents do not control Lucy. Agents report to Lucy.**

Lucy is the main system. Agents are specialist tools that serve Lucy's goals.
An agent that tries to become the center, control Lucy, or bypass Lucy's rules
is violating this contract and must not be activated.

---

## Agent Rules

### 1. Agents Do Not Control Lucy

No agent may issue commands to Lucy's core runtime.
No agent may modify Lucy's config, safety rules, identity, or memory directly.
Agents submit reports and requests. Lucy decides what to do with them.

### 2. Agents Report to Lucy

Every agent must have a defined report format.
Reports are submitted to Lucy through an approved reporting channel.
Raw logs stay inside the agent — they do not go into Lucy directly.

### 3. Agents Keep Raw Logs Local

Each agent maintains its own local log files.
Raw logs are never automatically injected into Lucy's memory or log system.
Only summaries and approved lessons move upward to Lucy.

### 4. Agents Send Summaries, Not Raw Dumps

When an agent submits a report to Lucy, it sends:
- A summary of what happened
- Key findings or lessons (not raw data)
- Risk flags (if any)

The full raw log stays in the agent's own data folder.

### 5. Only Approved Lessons Enter Lucy

A lesson is a structured, reviewed insight that the user has approved.
Raw agent output does not become Lucy memory automatically.
The flow is: Agent raw log → Agent summary → Lucy review → Approved lesson → Lucy memory.

### 6. Agents Cannot Change Lucy's Identity

No agent may rename Lucy, change her full form, or alter her personality config.
Lucy's identity is locked at the spine level and protected from agent modification.

### 7. Agents Cannot Change Safety Rules

No agent may modify `lucy_runtime_config.json`, `lucy_protected_actions.json`,
or any file that governs Lucy's safety rules and permission model.

### 8. Agents Cannot Access Protected Files Without Approval

Protected files (config, credentials, spine, safety rules) require explicit user approval
and a checkpoint before any agent may access them — even read-only access.

### 9. Agents Cannot Move Money

No agent may initiate, authorize, or facilitate any financial transaction.
This includes crypto, bank transfers, payment APIs, and invoice generation.

### 10. Agents Cannot Run Root Commands

No agent may execute root, sudo, or system-level commands.
System-level operations require Level 4 approval from the user directly.

### 11. Agents Cannot Become the Center

No agent should position itself as Lucy's replacement, supervisor, or equal.
Agents are specialist tools. Lucy is the main system.
Any agent that tries to absorb Lucy's role violates this contract.

### 12. Lucy Absorbs Lessons, Not Agent Identities

When a lesson from an agent enters Lucy, it is absorbed as knowledge.
The agent's identity, personality, or role does not transfer to Lucy.
Lucy remains Lucy. Agents remain their own specialist tools.

---

## Future Activation Requirements

Before any agent can be activated, it must:
1. Have a defined report format reviewed and approved
2. Pass a safety review checkpoint
3. Have `requires_lucy_approval: true` confirmed in the registry
4. Be activated by explicit user command (never automatically)
5. Have its activation logged as a checkpoint

---

## Current Status (Part 1)

All agents are registered as planned / inactive.
This contract will be implemented as agents are onboarded in future parts.
