# LXBG Module SDK — Draft 0.1

This document defines the first public draft of the LXBG module package format. It is intentionally small and will evolve before being declared stable.

## Package

A module is a directory or archive containing a `module.json` manifest and its implementation.

Example:

```json
{
  "id": "org.example.hello",
  "name": "Hello Module",
  "version": "0.1.0",
  "api": "0.1",
  "lxbg": ">=1.0.0",
  "entrypoint": "module.py",
  "permissions": ["irc.message.send"],
  "hooks": ["channel.join"]
}
```

## Rules

- IDs use reverse-domain style and must be unique.
- Semantic versions are recommended.
- Modules explicitly request permissions.
- Hooks must be declared in the manifest.
- Core files must never be overwritten by a module.
- Database changes should use versioned migrations.
- Secrets must never be shipped inside a module package.

The current SDK is a specification preview; the production runtime/installer is not yet part of Community Edition 1.0.
