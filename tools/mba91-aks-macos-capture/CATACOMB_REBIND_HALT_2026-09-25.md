# Catacomb rebind halt: -501 will not take the scratch bag again (2026-09-25)

Branch: `research/mba91-aks-ep7`. No Catacomb prepare, complete, or
confirm was sent. No enroll. No finger contact.

## Verdict

**The rewrite did not start.** Installing scratch handle 5 onto alias
`-501` returned SEP status `-1`. `-501` still names the macOS bag
(handle 6). User 501 still has 2 identities. Its Catacomb UUID query
returns status 0 with a nonzero component.

The scratch bag is still loaded as positive handle 5. Alias `-502` is
absent, and binding handle 5 there also returns `-1`. Earlier, the
same handle installed onto `-501` with status 0, the saved reference
verified, and enroll for uid 501 returned `22`. After that alias was
pointed back at the macOS bag, the scratch UUID no longer installs as
a special alias.

The stock Catacomb sync also refuses this job. It preserves the
archived keybag UUID and aborts if a save would change it. A SEP save
while `-501` still names the macOS bag would record that same bag,
not the scratch one.
