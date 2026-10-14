---
name: code-writing-guidelines
description: You must always use this SKILL before writing non-trivial code from scratch, in any domain — embedded/firmware, networking, machine learning/data, backend/web, frontend, systems/OS, DevOps/infra, security/crypto, data engineering, compilers/language tooling, graphics/multimedia, CLI tooling, mobile. Essentially anything a programmer won't know down pat — algorithms, parsers, protocol/format handling, API integrations, CLI argument parsing, regex-heavy logic.
---
## Scope — per-role examples

Non-trivial means anything a programmer won't know down pat. If the task touches any of these, follow the retrieval-first procedure below:

- **Embedded/firmware:** register/bitfield manipulation, interrupt handlers, DMA and ring buffers, memory-mapped I/O, fixed-point math, CRC/checksums, endianness conversion, I2C/SPI/UART/CAN drivers, watchdog timers, button debouncing, bootloader and firmware image formats, linker scripts, RTOS tasks/semaphores/queues, low-power sleep-wake.

- **Networking:** raw sockets, TCP/UDP state machines, TLS handshake and certificate validation, HTTP/2 framing, DNS wire format, WebSocket framing, packet parsing/crafting, protobuf/MessagePack/ASN.1 serialization, NAT traversal, connection pooling, retry with exponential backoff and jitter.

- **Machine learning/data:** tokenizers, batching/padding/masking, data loaders, tensor broadcasting, numerically-stable softmax/log-sum-exp, custom losses and metrics, quantization, ONNX/safetensors/GGUF serialization, CUDA kernels, feature encoding, embedding and ANN search, streaming dataset sharding.

- **Backend/web:** OAuth2/OIDC flows, JWT signing/validation, session management, webhook signature verification, rate limiting, idempotency keys, cursor pagination, cache invalidation, DB migrations and transaction isolation, multipart uploads, streaming responses.

- **Frontend:** complex state machines, virtualized lists, drag-and-drop, debounce/throttle, form validation schemas, requestAnimationFrame loops, Web Workers, IntersectionObserver, ARIA wiring, i18n pluralization, timezone-safe date math.

- **Systems/OS:** process and signal handling, IPC (pipes, shared memory),epoll/kqueue/IOCP event loops, mmap, filesystem watching, atomics/locks/channels, lock-free structures.

- **DevOps/infra:** strict-mode shell scripting, log parsing, CI pipeline logic, container entrypoints, health checks.

- **Security/crypto:** key derivation (argon2/PBKDF2), AEAD ciphers, constant-time comparison, secure randomness, X.509 certificates, input sanitization.

- **Data engineering:** ETL transforms, schema evolution, window functions, Kafka consumer groups, partitioning, exactly-once semantics.

- **Compilers/language tooling:** lexers, recursive-descent/Pratt parsers, AST transforms, macro expansion.

- **Graphics/multimedia:** shaders, matrix/quaternion math, collision detection, DSP filters, codecs, color-space conversion.

- **CLI tooling:** argument parsing, TTY detection, progress bars, shell completion, exit codes, signal-safe cleanup.

- **Mobile:** lifecycle and background tasks, permissions, push notifications, offline sync.

- **The classics:** algorithms, parsers, protocol/format handling, API integrations, regex-heavy logic, Unicode/encoding edge cases, compression, calendar math.

## Retrieval-first implementation

**CRITICAL: You are far more reliable adapting a correct example than deriving logic in one pass. Good programmers write code; great programmers adapt working code.**

1. SEARCH before drafting. Use `websearch` for the standard idiom: official docs, stdlib source, or a well-starred repo solving the same problem. For multi-source research, `dispatch` a sub-coder so your context stays clean.
2. FETCH, don't guess. Use `webfetch` on the actual source or doc page. A search-result snippet alone is not enough.
3. ADAPT, don't transcribe. Rewrite the example into this project's conventions, types, and error handling. Recode the pattern line by line — that is what makes it debuggable later. Prefer stdlib over copying a third-party dependency. Note the source in a short comment.
4. VERIFY against the task, not the source. The reference is a starting point, not ground truth for this repo's requirements. Run the existing build/tests after adapting, same as any other change.

## Maintainability pass

Re-read as an unfamiliar teammate: could they understand, change, debug, and recover this without you?

- Contracts explicit at the interface; no hidden coupling or implicit caller obligations.
- One responsibility per unit; no giant one-liners or dense blocks you cannot breakpoint.
- Comment the why (intent, invariants, recovery notes), never the what.

Skip when: one-line changes, project-specific business logic, or edits to code that already exists in this repo (read-before-edit governs those).

Stop conditions:
- Reference found and adapted -> implement, then run tests/build.
- 2-3 search refinements yield nothing usable -> say so explicitly, then write from scratch and flag the assumption in a comment. Never present unverified code as if it were adapted from a working source.
