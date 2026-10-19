# Message window

Java 17, with no external dependencies. `MessageWindow` exposes a read-only
snapshot through the JDK `Iterable<String>` contract. Constructor input is copied,
null arrays and elements are rejected, and each iterator advances independently.
Calling `next` after the last message must throw `NoSuchElementException`;
`remove` is unsupported. The public API is the constructor, `size`, and `iterator`.

The current implementation omits the final item when using `hasNext`. Fix the
boundary behavior while preserving those existing contracts. This is a small
maintenance task, with no requirement to introduce a new public cursor API.

Comments in this project use English.
