# Lucy Research Foundation

This note records the research baseline used before adding more Lucy foundation
code. It is not a claim that Lucy has consumed 100 papers and 100 videos.

## Practical Findings

- ReAct shows that useful agents interleave reasoning with actions, but actions
  need explicit tool boundaries and observations.
- Reflexion shows that feedback and self-review can improve future attempts,
  but reflection should be stored as structured, auditable traces.
- Generative Agents shows the value of memory, reflection, and planning, but it
  also points to why raw chat history is not enough.
- MemGPT frames long-running assistants as memory-management systems with
  different tiers of context.
- Current agent frameworks emphasize tools, handoffs, guardrails, sessions,
  state, and tracing. Lucy should copy those engineering patterns before adding
  active agents.
- OWASP LLM guidance keeps prompt injection, sensitive data exposure, excessive
  agency, insecure output handling, and unbounded consumption at the center.
- NIST AI RMF reinforces that trustworthy systems need risk management,
  measurement, documentation, and ongoing governance.
- The Twelve-Factor config principle supports keeping secrets/config separate
  from code.
- Python standard-library JSON, pathlib, logging, and shlex are enough for this
  foundation stage; adding databases and frameworks can wait.

## Design Rules For Lucy

1. Memory must be typed, searchable, deletable, and small enough to audit.
2. Reflection is not consciousness; it is local state with timestamps and
   boundaries.
3. Tools stay behind Guardian checks and logs.
4. Provider APIs are language tools, not Lucy's identity.
5. File awareness starts read-only and scoped.
6. Daily life context must be user-supplied, local, redacted, and optional.
7. Continuity backups should be local, bounded, non-secret, and restorable by a
   human before any automatic restore is allowed.
8. Agents remain separate roles until Lucy can supervise them with logs and
   permission boundaries.
9. Voice, UI polish, autonomous desktop control, money movement, and root/admin
   actions wait.

## Source Baseline

- ReAct: https://arxiv.org/abs/2210.03629
- Reflexion: https://arxiv.org/abs/2303.11366
- Generative Agents: https://arxiv.org/abs/2304.03442
- MemGPT: https://arxiv.org/abs/2310.08560
- OpenAI Agents SDK: https://platform.openai.com/docs/guides/agents-sdk
- OpenAI Agents guardrails: https://openai.github.io/openai-agents-python/guardrails/
- LangChain long-term memory: https://docs.langchain.com/oss/python/deepagents/long-term-memory
- Microsoft Agent Framework: https://learn.microsoft.com/en-us/agent-framework/overview/
- AutoGen docs: https://microsoft.github.io/autogen/dev/index.html
- OWASP Top 10 for LLM Applications: https://owasp.org/www-project-top-10-for-large-language-model-applications
- OWASP Secrets Management Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html
- NIST AI RMF: https://www.nist.gov/itl/ai-risk-management-framework
- Twelve-Factor config: https://www.12factor.net/config
- Python json: https://docs.python.org/3/library/json.html
- Python pathlib: https://docs.python.org/3/library/pathlib.html
- Python logging: https://docs.python.org/3/library/logging.html
- Python shlex: https://docs.python.org/3/library/shlex.html

## Next Research Upgrade

Build a real research ingestion pipeline before claiming broad coverage:

1. Keep a curated source manifest with title, URL, type, credibility, date, and
   topic.
2. Prefer papers, official docs, talks with transcripts, and trusted course
   material.
3. Save summaries as local notes, not unbounded chat history.
4. Tag each source by memory, tools, safety, planning, UI, voice, or agents.
5. Add a review command so Lucy can say what sources shaped a decision.
