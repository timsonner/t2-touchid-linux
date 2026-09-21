# Native password hunt: raw-form fails, module generation gap found (2026-09-20)

Branch: `research/mba91-aks-ep7`. No repo changes (all runs via
existing scripts/inline). No passwords/fingers involved in the new
tests except the operator-typed creation password at earlier
windows. Shapes/statuses/counts only.

## Raw-form unlock test (new, autonomous)

Piped byte-exact 16 B ACM external forms (fresh contexts, CR/LF
screened, contexts deleted after) into `unlock-keybag-stdin` for
the bound native handle: clean forms → `EREMOTEIO` (3 attempts).
Same transport wall as password strings post-reboot. The secret
ENCODING is not the variable — nothing password-shaped opens a
fresh native bag here.

## Module generation gap (the actual finding)

Their `t2_sep_transport.c` (2591 lines, 104 provisioning refs) vs
ours (2440 lines, 0): different kernel generations. Theirs carries
`identity_create_version` param, versioned-app selection,
provisioning-enabled/poisoned ioctl states, and a provisioned
`/dev/t2-aks` ABI our build lacks. Their native password flow runs
through that interface; our build physically cannot issue its
decisions. Forward-porting ~150 lines of provisioning machinery
into the MBA91 warm-surviving build — without reintroducing the
killer defaults — is the real remaining native task. It is weeks
of careful kernel work, not another live window.

## Standing ledger (native track, closed for live work)

- Create/export/bind/UID-space/enroll-shapes: PROVEN on MBA91.
- Password credential on native bags: REFUSED at every layer
  tried (prompt, stdin-string, raw-form, ACM-bound, bound and
  unbound, two boots): rc=1, `-5` ×4 paths, EREMOTEIO ×5.
- macOS-bag reader: fully working (sudo by finger, fallback).
- Next: unattended credential for daily friction (operator call),
  activation/module-generation port on paper first.
