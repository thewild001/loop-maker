# Agent Reach channel reference

This document describes routing principles for the optional Loop Maker Reach skill. It is not a frozen capability matrix: Agent Reach and its upstream tools evolve. The installed CLI is the source of truth.

## Discover before use

Run:

```bash
agent-reach channels
agent-reach --help
```

Use the channel list and command help from the installed version. Do not infer that a channel is usable merely because it appears in upstream documentation. It may require an optional tool, login, setup, a supported region or a working upstream service.

## Documented channel families

The upstream project has documented these channel families. Availability and implementation status can change:

| Channel family | Typical use | Important caveat |
|---|---|---|
| Web | Public web search and page retrieval | Search snippets are not equivalent to reading the source. |
| YouTube | Video discovery and transcript/content retrieval | Transcripts may be absent, partial, auto-generated or inaccurate. |
| GitHub | Repository, code and project research | Verify repository identity, branch/ref and file provenance. |
| V2EX | Public community discussions | Posts are user-generated claims, not authoritative facts. |
| Bilibili | Video and creator content | Availability and transcript extraction may vary. |
| Xiaohongshu, Reddit, LinkedIn, Boss, Xueqiu, Xiaoyuzhou | Optional platform-specific retrieval | May require additional tools, login or local setup; respect platform rules. |
| Twitter/X, Facebook, Instagram | Experimental or version-dependent retrieval | Do not assume stable support or bypass platform restrictions. |

The table is intentionally descriptive rather than a promise of current support. Use `agent-reach channels` and the installed skill/help for the exact current status.

## Routing policy

1. Prefer a native host connector when it provides the needed source and content.
2. Select the narrowest Agent Reach channel that can answer the retrieval question.
3. Avoid querying multiple channels without a reason; expand only to resolve a material coverage gap or corroborate an important claim.
4. Prefer primary sources for factual claims. Community channels are useful for experience reports, sentiment and leads, but should not be treated as authoritative evidence.
5. For code research, verify the exact repository, branch/tag/commit and file path. A similarly named repository is not sufficient.
6. For video research, distinguish creator claims, transcript text and independently verified facts.
7. If the channel is experimental, unavailable, blocked or login-dependent, disclose that limitation and use a permitted alternative.

## Result handling

Agent Reach's CLI generally emits a structured JSON envelope with channel, action, backend, items, metadata and error information. Fields vary by command/version. Validate the actual payload and preserve original source URLs when present.

A result can be:
- A full extracted document.
- A partial document or transcript.
- A search result or snippet.
- Metadata without substantive content.
- An error or an empty result.

Report which one was actually obtained. Never describe a snippet or metadata-only result as a fully read source.
