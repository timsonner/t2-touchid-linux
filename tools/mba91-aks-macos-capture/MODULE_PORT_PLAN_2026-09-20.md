# Module-generation port plan: probe their driver on MBA91 (2026-09-20)

Branch: `research/mba91-aks-ep7`. **Paper only — no code built,
no module loaded.** The password wall (`-5` on fresh bags) likely
ends at the kernel interface, not SEP: their driver generation
carries provisioning/versioned-app machinery ours lacks.

## Generation delta (static diff, both trees on disk)

| Area | Ours (2440 lines) | Theirs (2591 lines) |
|---|---|---|
| Bring-up pokes | `aks_start_cpu`, `aks_ep0_nop`, `aks_discover`, `aks_device_state_canary` — all default TRUE (the warm killers; we pin them off) | No such params; `mirror_apple_start` exists but defaults FALSE (no CPU poke unless asked) |
| Provisioning | absent (0 refs) | `enable_identity_provisioning` + `identity_create_version` (4/5, default 5) + preflight/reply/ioctl states + poisoned flags (104 refs) |
| Replacement | absent | `enable_identity_replacement` (default false) |
| AKS info | none | GET_INFO with OOL/ACM/provisioning/poisoned/versioned-app/inventory/password-bound/runtime flags |
| Identity secret | none | ACM-bound secret tracking, split-target create gates |
| Allowlisting | capability probe + lab (no whitelist) | op allowlists for AKS/ACM + inventory-only mode |
| Platform data | ASID/uniqueid/cdhash stamp params | same params, plus stamping into verify-secret headers |

Key safety read: their defaults are INERT (no OOL, no start
poke, no capability, no provisioning) — first warm load should
do little more than PCI probe + BAR mapping. Stepwise enablement
after that, each step survival-checked past the 9 s death mark.

## Staging order (one variable per boot where noted)

1. **Build only.** Their `src/` against our headers (`make`
   out-of-tree, no install). Zero commitment; binary compared,
   never loaded.
2. **Inert first load (warm SEP).** Their service disabled first
   (ours must NOT be loaded — rmmod is blocked once OOL pins,
   so this needs a boot with our service off). `insmod <path>`
   with all defaults. Expect survival + dmesg probe lines only.
   Any hang → reboot recovers (identities persist per ladder).
3. **`register_ool=1`**: OOL + `/dev/t2-aks` + capability/host
   ops. Compare vitality with ours (load/uuid/state reads).
4. **`enable_identity_provisioning=1 identity_create_version=5`**:
   their native create/export through THEIR transport + userland
   (`t2_aks_provisioning_transport` + codec, standalone-able).
   Then password ops against created bags — the `-5` breaker test.
5. **Fallback discipline:** our installed module + service stay
   the default boot path throughout (re-enable after each test
   boot). Alias competition (same PCI ID, possibly same module
   name) managed via explicit insmod-by-path only — never install
   theirs until a verdict exists. `modprobe.d` pin for ours stays
   authoritative for service loads.

## Risks (stated plainly)

- First warm load of a foreign driver on the T2 power owner:
  hang possible (reboot recovers), identity loss not expected
  (ladder: warm + power-off preserve proven) but never assumed —
  fingerprint verify before AND after each step.
- Their bring-up may poke differently-deadly things (MSI?
  OOL aliasing with our DMA regions? No — fresh boot, ours
  never loaded, regions free).
- No product wiring (DKMS/install/service switch) before a
  verdict on password ops. Ever.

## Do-nots

No install, no DKMS registration, no modprobe.d changes, no
service disablement outside a planned test boot (re-enable
same session), no default-param loads of OUR module (existing
rule), no combining with other experiments.
