# Attachment storage usage

Java 17 with no external dependencies. Comments use English.

`AttachmentStore` owns a private normalized directory and a byte quota. Its public
API is the constructor and `usedBytes()`. Each call must scan the current tree
independently and return the bytes of regular files, including nested directories.
Directories named `.staging` and everything beneath them are excluded. Symbolic
links are not followed or counted, including links to regular files. An I/O failure
or total above the quota must produce `IOException`, without modifying any files.
The quota is inclusive. The configured root itself is always visited, even if its
name is `.staging`; only descendants with that name are excluded.

This scanner uses the JDK `Files.walkFileTree` visitor protocol: directory pruning,
file attributes supplied by the walk, and fail-fast `IOException` propagation are
part of the integration contract. Keep that protocol. No result DTO, extension
point, exposed root, exposed mutable accumulator or new public API is needed.
Java source files under `src` may be added or changed. No dependencies, build
configuration, project-context edits or Git actions are needed.
