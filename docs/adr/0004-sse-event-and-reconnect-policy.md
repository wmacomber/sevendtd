# ADR 0004: SSE events and reconnect

Accepted. Unknown/malformed events remain iterable. Reconnect is explicit in library, capped by
policy, cancellation-safe, and never retries authentication or non-transient client errors.

