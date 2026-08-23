# ADR 0003: Snapshot partial failure

Accepted. Snapshot requests run concurrently and return successful components plus safe failures by
default. Authentication fails immediately. Strict mode raises one project-owned aggregate error.

