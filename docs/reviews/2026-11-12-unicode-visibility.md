# Unicode search and AI graph visibility — 2026-11-12

Source candidate 0.1.5 fixes centralized Aide issues [#804](https://github.com/skyelan1999/aide/issues/804), [#805](https://github.com/skyelan1999/aide/issues/805) and the StarLink consumer half of [#796](https://github.com/skyelan1999/aide/issues/796).

- Default Unicode 17 full folding uses official `CaseFolding.txt` C/F mappings (SHA-256 `ff8d8fefbf123574205085d6714c36149eb946d717a0c585c27f0f4ef58c4183`), canonical normalization, and original-text grapheme offsets for excerpts. The Unicode notice is embedded in the source and included in both package formats. Regenerate/check with `python3 scripts/generate-casefold.py --check`.
- Both graph identity and updates use `scope=ai`; the host must explicitly acknowledge `scope: ai`. Older hosts are rejected before graph download. Visibility-policy changes discard cached nodes; the host preserves manual browsing separately.
- PASS: 20 Node regressions, including composed/decomposed accents in both directions, sharp S, final sigma, ligature, Hangul, reordered combining marks, exact original excerpts, hidden-source cache invalidation and legacy-host rejection.
- PASS: actual isolated Aide `App.Handler()` TLS server, current Go source and Node plugin daemon/IPC: Unicode searches, TypeScript worker/caller and TSX symbol queries, a static caller-to-worker path, and reference visibility changed after the first cached query. Hidden reference text disappeared from the next AI result while the manual graph retained it. Test: `TestRemainingStarLinkDaemon` with this checkout supplied as `AIDE_STARLINK_SOURCE`.

No paid model call, actual SSH/Windows workspace acceptance, public 0.1.5 binary Release, marketplace replacement or installed-plugin upgrade was performed. Published 0.1.4 universal compiled artifacts and prior dated acceptance remain unchanged. Aide's companion source fix and full issue audit are in `docs/reviews/2026-11-12-remaining-issues/` in the Aide repository.
