# Native-track survey: what macOS-free would actually require (2026-09-20)

Branch: `research/mba91-aks-ep7`. **Paper only — no code, no live
windows, no state touched.** Answers "can we drop the keybag" with
the project's own static evidence.

## The three layers (separate systems, separate fates)

From `enrollment_research/FINDINGS.md` ("AKS provisioning boundary"):

1. **Apple account + AKS bag provisioning/unlock** — lives in the
   privileged `com.apple.applekeystored` XPC service
   (`AKSIdentityCreate`, `AKSIdentityAdd`, `AKSIdentityLoad`,
   `AKSIdentityReset`, …), backed by the AppleKeyStore/OD/APFS
   provisioning transaction. Message and side-effect ordering are
   recovered, but failure windows are non-atomic — unsafe to expose.
2. **BiometricKit/SEP enrollment** — proven on this Air (E1/E4).
   The server contains NO user/keybag creation path (exhaustive
   command audit: enroll/match/cancel/Catacomb/delete/`0x48`
   whole-user-delete only). It reads the account UUID and bag UUID
   from the platform layers and INVALIDATES the biometric user if
   they change. Recovering layer 3 never provides layers 1–2.
3. **Host Catacomb persistence** — Linux-local story unwritten;
   SEP-only identities today.

## What this means for "native"

- The keybag file + macOS password are layer-1/2 artifacts Linux
  cannot mint through any SEP command — there is no such command.
  Native provisioning means reimplementing Apple's privileged
  identity-create transaction, with identity-destroying failure
  modes, against a SEP that invalidates users on UUID mismatch.
- The tree already holds non-exposed scaffolding in this direction
  (`t2_aks_identity_create.py`, replacement/reconciliation
  modules, policy-gated brokers). All of it is rightly unexposed:
  zero hardware proof, destructive failure windows.
- The missing experimental cell remains **loaded-but-locked vs
  absent**: September proved absent-mutes; K1/K2 proved
  unlocked-verdicts. If loaded-but-locked also mutes, unlock is
  structurally required and provisioning must include an unlock
  story, not just a file story.

## Recommended order (no shortcuts exist)

1. **Separation window** (cheap, non-destructive, next boot):
   loader → NO unlock → token-free window (expect mute) →
   unlock → token-free window (expect verdict). Decides whether
   presence or unlock is the lever.
2. **Unattended credential** (daily-UX, orthogonal): removes the
   per-boot password friction while native stays research.
   Operator's call; host-key tradeoff already documented.
3. **Provisioning design only** until (1) + explicit risk
   acceptance with macOS recovery in hand: map the
   AKSIdentityCreate-family transaction to Linux-side
   prerequisites, failure windows, and rollback — no live
   dispatches before the paper closes.
4. **Empty-SEP authorized start** stays behind the nuke decision
   (destructive, capacity full, untested dispatch).

## Bottom line

Native-only is a layer-1/2 project, not a layer-3 project — and
layer 3 (the hard-won match/enroll/delete science on this branch)
is the part already done. Nothing about the SEP side blocks
native; everything about the Apple identity platform does.
