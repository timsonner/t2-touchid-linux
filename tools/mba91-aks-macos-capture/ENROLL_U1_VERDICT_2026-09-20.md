# U1 verdict: unbound form gets 257, authorization required (2026-09-20)

Branch: `research/mba91-aks-ep7`. U1 gate disabled (verified). No
password, no finger, no state change. Shapes/statuses/counts only.

## Verdict

**`dispatch_status: 257` — a new refusal word, and authorization
is required.** The zero-group token carrying a 16 B reference to
an already-DELETED ACM context answers 257 (cancel 0, 3→3
preserved). The emerging refusal vocabulary is now coherent:

| Form | Dispatch | Meaning |
|---|---|---|
| none (token-free) | -3 | no credential offered |
| dead reference (U1, context deleted pre-dispatch) | 257 | unresolvable reference |
| live form, wrong shape or gated UID (old group-1, C5-502) | 22 | refused arguments/account |
| live form, authorized, provisioned UID (E1/E4) | 0 | opens |

Structure alone does not pass; the live password-bound
policy-satisfied context is load-bearing. The native story still
runs through the activation ceremony — no shortcut via
ceremony-free forms.

## Run (single shot, fully self-contained)

Mint tracking context → externalize → delete → dispatch 0x03 v2
zero-group with the dead reference → 257 → cancel 0 → post 3/3.
No operator involvement possible or needed; nothing to place,
nothing to type.
