# Alias-op sweep: 0x23/0x18 unsupported, alias-unlock dead (2026-09-20)

Branch: `research/mba91-aks-ep7`. No gates opened (existing tools
+ lab binary only). No state change (all refusals transport-level
or evaluated-negative). Shapes/statuses/counts only.

## Verdict

**MBA91's SEP image does not implement the alias/ACM-unlock
layer.** Their MBP16,1 unlock-by-alias and selector-`0x9a` ACM
unlock have no live counterpart here:

| Probe | Result |
|---|---|
| op `0x23` alias-config resolve, `-502`/`-501`, ver 1/2 (lab) | EREMOTEIO ×4 |
| op `0x18` ACM alias-unlock, fresh form, `-502` (lab) | EREMOTEIO |
| `unlock-keybag 1 -502` (alias as handle, creation pw) | EREMOTEIO |
| prior: unlock/verify-only/verify-ACm/raw-form on handles | rc=1, `-5` ×4, EREMOTEIO ×5 |

Working EP7 ops on this image stay: create `0x01` ✓, export
`0x02` ✓, load/set-system/unlock/verify on macOS bags ✓,
UUID/state reads ✓. The unsupported set (0x18/0x23/password on
fresh bags) is exactly their per-image warning playing out —
same `23P6068` container, different SEP behavior per board.

## What this decides

- No alias-shaped or ACM-shaped password path reaches fresh bags
  on MBA91 through any known opcode/envelope. The `-5`/EREMOTEIO
  wall is image-level, not framing-level: further opcode
  guessing is closed.
- Remaining native route is the kernel-module generation port
  (provisioning-enabled EP7 path + versioned app selection),
  which may itself route to SEP apps this image lacks — that
  uncertainty stays open until diffed live, and the diff is
  weeks of kernel work, not windows.
- Operational reader unaffected (macOS bags, sudo by finger).
