# Dependencies

- When adding or upgrading a dependency, use the latest stable version and read its official documentation; do not assume versions from training data. Existing dependencies follow the version installed in the checkout.
- When the user provides a URL for a tool or package, fetch that URL first — it is authoritative. PyPI/npm/crates search is a fallback only when no URL is given.
