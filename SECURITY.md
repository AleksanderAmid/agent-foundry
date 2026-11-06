# Security and trust boundaries

Foundry's helpers use the Python standard library, make no network calls, and
do not execute declared repository commands. Inspection lists selected filenames;
it is not a secret scanner or a security audit. Generated instruction files are
guidance, not an enforcement boundary.

Treat a repository and its command declarations as untrusted until reviewed for
the task. The host controls authorization. `command` only resolves metadata.
The validator rejects path traversal and links/junctions in declared paths, but
it is not a filesystem sandbox and does not defend against a hostile concurrent
process changing the filesystem. Use actual isolation for untrusted work.

Installation refuses existing destinations. Review local modifications before
updating. A digest identifies content; it is not a publisher-trust guarantee.

For a suspected issue, send a minimal non-sensitive reproduction through a
GitHub issue. Do not include credentials, private repository contents, or live
exploitable details. Use GitHub's private vulnerability reporting if enabled.
