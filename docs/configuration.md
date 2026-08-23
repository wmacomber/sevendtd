# Configuration

Required:

```text
SEVENTDTD_BASE_URL
SEVENTDTD_TOKEN_NAME
SEVENTDTD_SECRET
```

Optional:

```text
SEVENTDTD_TIMEOUT=10
```

The CLI loads `.env` from its current working directory when present. Select another file with
`7dtd --env-file PATH ...`. Loading never overrides variables already present in the process
environment. Explicit CLI connection flags override both sources.

Example `.env`:

```dotenv
SEVENTDTD_BASE_URL=http://server.example:26980
SEVENTDTD_TOKEN_NAME=replace-me
SEVENTDTD_SECRET=replace-me
SEVENTDTD_TIMEOUT=10
```

Credentials have no defaults. Prefer environment injection. Avoid `--secret` because shell
history and process listings may expose it. The transport sends credentials using
`X-SDTD-API-TOKENNAME` and `X-SDTD-API-SECRET` on HTTP, tile, and SSE requests.

Normal logs omit authentication headers, request/response bodies, raw commands, player identity,
and player IP addresses.
