# Module trial verdict: their generation is warm-safe (2026-09-20)

Branch: `research/mba91-aks-ep7`. No repo changes (trial used
their tree at `/home/tim/t2touch-ref`, outside git).

## Verdict

**Their driver generation loads warm-safe on MBA91 at two
levels.** Inert defaults (no params): PCI probe + mailbox peek,
no DMA, no writes, survived 14 s. `register_ool=1`: OOL
registered, `/dev/t2-aks` live, survived 14 s. No CPU-start poke,
no discover storm, no canaries anywhere in the log — warm-safe by
construction where ours kills. rmmod works while DMA-free and
blocks once OOL pins (same rule both generations). The port is
VIABLE; warm survival is no longer the risk — the remaining work
is provisioning-path behavior, staged next.

## Test-boot lessons (paid in reboots)

- PCI modalias autoloads the installed module even with its
  service disabled (keybag-load's Requires pulled it first;
  blacklist alone lost — the load happens where modprobe.d
  visibility is uncertain). To test foreign modules: stash the
  installed `.ko` + depmod (alias unresolvable, deterministic).
- Our service's explicit modprobe-by-name bypasses blacklist
  semantics; belt (blacklist) AND suspenders (stash) both.
- Restore path proven in advance: blacklist removed, `.ko`
  reinstalled + depmod, services re-enabled — next boot is
  production again with no further commands.

## Standing state (this boot)

Their module OOL-pinned (can't unload); ours staged for next
boot. Reboot returns to the working reader. Host ops and
provisioning reads against their `/dev/t2-aks` were NOT reached
— next trial, same method, deeper params.
