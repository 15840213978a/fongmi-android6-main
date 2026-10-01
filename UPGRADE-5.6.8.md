# Upgrade to 5.6.8

This branch imports `15840213978a/fongmi` at
`0b9835bd0c5350f47476c05377545d6e9134614c`, including its matching
Media3 build, Node.js module, Chaquopy setup, player code and native verification.

- Version: 5.6.8, versionCode 568 (previously 5.6.3 / 564).
- Minimum Android: 7.0 / API 24. Android 6 compatibility shims are removed.
- Application ID remains `com.fongmi.android.tv.b6`. The b6 suffix is an
  installation identity retained for upgrades, not an Android 6 support claim.
- Signing uses existing `RELEASE_KEYSTORE_BASE64`, `RELEASE_KEY_ALIAS`, and
  `RELEASE_STORE_PASSWORD` secrets. CI compares the signing certificate with
  the previous 5.6.3 release APK before publishing any upgrade APK.
- APKs retain the `<mobile|leanback>-<arm64_v8a|armeabi_v7a>-b6.apk` names.
- The JSON updater and download proxy setting are retained. Update URLs now
  point to this repository, instead of `yilishawk/fongmi-android6`.
- Settings and playback follow the 5.6.8 source baseline. The old branch's
  custom debug-log server, shell proxy and Android 6-specific player patches
  are not carried into the new baseline. Existing preferences are not erased.
- Room migration 35 -> 36 is supplied by upstream. Track selections are rebuilt;
  configuration, favorites and viewing history should remain. Device testing
  is still needed before recommending this as a stable upgrade.

Push builds publish uniquely tagged **prereleases**, never replace the current
stable release. A manual build on `main` may publish stable only with the
`stable_release` input enabled after review and device testing.

The first upgrade branch build imports the exact source revision with
`scripts/import_568.py`, preserves the reviewed repository-specific files,
and commits the result on this branch. Later builds use the committed tree.
Release tags point to the actual imported commit. `.upstream-568` records its
provenance; editing it is not an update mechanism.
