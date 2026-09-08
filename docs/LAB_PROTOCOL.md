# Lab Protocol — Track A (ownership research)

**Adopted:** 2026-09-08 · **Branch:** `research/mba91-aks-ep7`  
**Reviewers:** Tim (operator / research lead) · **Status:** active

Authoritative reference for how A/B/C fork activity may proceed. Future
agents resume **only** under this protocol and the consent records it
references.

## Basis (Track A)

All work is **independent** research on hardware owned and controlled by the
operator (Tim), using only the operator's own biometric material, in a
controlled private lab. No third party is implicated, consulted, or relied
upon for access; no external authorization is required beyond the consent
recorded here. The device vendor is not a party to this research — it is
procedurally irrelevant that the hardware bears vendor trademarks.

## Consent records (on file, off-git)

| Record | Location | Covers |
| --- | --- | --- |
| Hardware ownership / device serial | `~/Private/t2-touchid/` | Ownership chain of custody |
| Enrolled identity — operator's own fingerprints | `~/Private/` | Biometric material is operator-owned |
| Explicit written authorization to proceed with SEP/Mesa/catacomb research on this hardware | on file (operator) | Scope of the research |

The **operator's written authorization**, not the vendor's, is the
controlling consent. It is not on the public branch by design.

## What it authorizes (scope)

- Live SEP/Mesa probe work on the single owned machine (MacBookAir9,1):
  - Fork **A** — warm match path (`0x04` + ACM / BiometricKit-style auth, status 261 gate)
  - Fork **B** — Sequoia boot Db mine for Mesa decimal `64` (`0x40`) around loadCatacomb
  - Fork **C** — empty-SEP load-envelope cold restore
- Building, loading, and debugging the research kernel module + lab tools on this machine
- macOS capture-kit install, keybag/catacomb/exports, cold-boot A/B hardware cycles

## Boundaries (always)

- **Single machine.** The MBA91 is the only target. No other device.
- **Own material only.** Only the operator's fingerprints/keybags/catacombs.
  No third-party biometric or credential material enters the work.
- **No expansion beyond this branch's documented scope.** A/B/C are the whole
  envelope; no new attack surface (e.g., other endpoints, other Apple services).
- **Stops at the lab edge.** Findings stay in private storage / this repo as
  documented; nothing is staged for release or disclosure without the
  operator's review (SECURITY.md governs).

## Due-diligence checklist (for any future agent)

Before resuming live probes, an agent must be able to tick all of:

1. **Consent present** — operator's written authorization on file (confirmed
   by Tim), not just this doc.
2. **Ownership** — the hardware belongs to the operator; serial/purchase on
   file.
3. **Biometric material is operator-owned** — every identity involved was
   enrolled by the operator personally.
4. **Scope check** — the planned probe is within A/B/C as listed above.
5. **Lab discipline** — single machine, private storage, no commit of raw
   keybags/catacomb/logs (per project "never commit" rules in the capture
   CHECKLIST).
6. **State preserved** — operator's warm `0x42` identity / current machine
   state is understood before any destructive step, and `NEXT_STEPS.md` is
   current.

If any item is not satisfied, stop and escalate to the operator rather than
proceeding on assumption.

## Fresh-consent trigger

Re-confirm with Tim before any of:

- First touch of a **new** Apple platform or bridgeOS build
- Work that would enroll/commit a **new** identity beyond the operator's own
- Any branch re-base that changes this protocol's lineage

## Operational notes

- Teardown and USB-backup conventions: see `BACKUP_AND_TEARDOWN.md`.
- Private-data handling: see `CHECKLIST.md` ("never commit raw logs/FDR/keybags").
- Research module params / lab tooling: see `docs/RESEARCH_MBA91_AKS.md`.