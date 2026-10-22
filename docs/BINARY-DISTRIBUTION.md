# Linux compiled plugin distribution

The original CommonJS entry is compiled into eager V8 bytecode inside an ELF native Node addon (.node). A thin adapter loads it through Aide. It requires Linux Node 24.22.0 and the recorded V8 ABI, rather than being a standalone CLI. Rebuild when the host Node changes; there is no source fallback.

Original licensing and source visibility remain unchanged. Compilation is not anti-reverse-engineering or commercial license activation. Browser HTML and data assets remain visible. Packages stay local; no marketplace upload.

Build both architectures with scripts/build-native-module.py --arch arm64 and --arch amd64, then scripts/package-native-module.py. Docker, matching Node/g++ images and the pinned official Node SDK are required. SDK SHA-256 is checked; compilation is offline, 1 CPU / 512 MiB. Node/V8 license notices are included.

External services, execution nodes and hardware retain their original deployment requirements. Compiling this plugin entry is not acceptance of external hardware. Final extracted-package test results are recorded separately.
