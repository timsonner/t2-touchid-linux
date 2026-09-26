# SEP boot-state publisher

Cold Linux boots on this MacBookAir9,1 leave SMC `EFMV` at the `0xfe`
sentinel and endpoint 7 silent. This `applesmc` build publishes Apple's
boot-state transaction once at probe, before the SEP transport registers
its buffers.

The source is the `t2touch` package `packaging/applesmc-t2touch/applesmc.c`
at the carried hash
`4edb24f48a39b1f56522be4dd5d6f8c2650e8b1c63d279cf9a3c2ccff6d561a6`.
That tree describes it as Linux `v7.2.4` plus the Arch and t2linux
`applesmc` series, the boot-state patch, and two `kcalloc` substitutions.
It is GPL-2.0-only. It does not own the T2 PCI device.

`install.sh` builds and installs it only when
`T2_TOUCHID_MBA91_WARM_SEP=1`. The module lands in
`/lib/modules/$(uname -r)/updates/applesmc.ko`, and
`/etc/modprobe.d/applesmc-t2-sep-boot.conf` sets `t2_sep_boot_state=1`.
A copy that is already loaded stays loaded. The next boot is what probes
the new module. Do not unload it to force the transaction, and do not
unload a pinned `t2_sep_transport`.

On 2026-09-26 the publication returned `response-received:1` for bridgeOS
`23.16.16068.0.0,0`, epoch 1.0, and the following capabilities read
returned `0x2`. The SEP service had been disabled and the module
blacklisted so PCI autoload could not register endpoint 7 first.
`t2-keybag-load.service` still started the transport through `Requires=`
after the publication. Those two hold files are not installed by default.
