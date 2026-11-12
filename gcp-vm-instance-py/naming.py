"""Helpers that guard against invalid Google Cloud resource names.

Compute Engine resource names must follow RFC 1035:
https://cloud.google.com/compute/docs/naming-resources

  - 1-63 characters
  - match ^[a-z]([-a-z0-9]*[a-z0-9])?$  (lowercase letters, digits and hyphens,
    starting with a letter and not ending with a hyphen)

Pulumi auto-naming appends "-" plus 7 random hex characters to the logical name
to build the physical name, so the logical name must leave room for that suffix.
"""
import hashlib
import re

import pulumi

# Characters Pulumi auto-naming appends to the logical name ("-" + 7 hex chars).
AUTONAME_SUFFIX_LENGTH = 8
GCP_MAX_NAME_LENGTH = 63

# Longest logical name that still yields a valid physical name after auto-naming.
MAX_LOGICAL_NAME_LENGTH = GCP_MAX_NAME_LENGTH - AUTONAME_SUFFIX_LENGTH


def gcp_resource_name(name: str, max_length: int = MAX_LOGICAL_NAME_LENGTH) -> str:
    """Return a logical name that yields a valid GCP name once auto-named.

    Lowercases the name, replaces invalid characters with hyphens, ensures it
    starts with a letter and does not end with a hyphen, and truncates it to
    max_length. Truncated names get a short hash of the original so that
    different long names do not collide.
    """
    safe = re.sub(r"[^a-z0-9-]", "-", name.lower())
    safe = re.sub(r"-{2,}", "-", safe)
    safe = safe.lstrip("-0123456789").rstrip("-")
    if not safe:
        safe = "r"

    if len(safe) > max_length:
        digest = hashlib.sha1(name.encode("utf-8")).hexdigest()[:6]
        safe = f"{safe[:max_length - len(digest) - 1].rstrip('-')}-{digest}"

    if safe != name:
        pulumi.log.info(
            f"Resource name '{name}' is not valid for Google Cloud; using '{safe}'."
        )
    return safe
