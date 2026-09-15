# LXBG Platform Architecture

LXBG is evolving from a single IRC community into a modular IRC platform.

## Product layers

- **LXBGIRCd** — IRC server/core protocol engine.
- **LXBG Services** — account, channel, moderation and service-bot layer.
- **LXBG Web** — browser onboarding, account administration and web chat.
- **LXBG CAM** — WebRTC community webcam layer.
- **LXBG Modules** — extension API and future module registry.

## Design rule

The core remains small. Optional behaviour belongs in modules communicating through a stable event API. Configuration and module state should be database-backed where practical.

## Module lifecycle

`discover -> validate -> install -> migrate -> enable -> disable -> upgrade -> uninstall`

A module must declare its identity, version, compatible platform/API versions, permissions, hooks and optional database migrations in `module.json`.

## Initial event API

The first stable event namespace is planned around:

- `user.connect`
- `user.authenticated`
- `user.disconnect`
- `channel.created`
- `channel.join`
- `channel.part`
- `message.before`
- `message.after`
- `cam.started`
- `cam.stopped`

`*.before` hooks may eventually support controlled rejection/modification. Other hooks should be observational by default.

## Security model

Third-party modules are untrusted until validated. The future installer/registry should verify compatibility, requested permissions, package hashes/signatures and migration metadata before activation. Modules must not receive unrestricted production credentials by default.

## Registry direction

A future LXBG Module Hub can provide discovery, versions, compatibility metadata, downloads, ratings and developer publishing. The registry and module API are separate: self-hosters must remain able to install a compatible local module without depending on the hosted registry.
