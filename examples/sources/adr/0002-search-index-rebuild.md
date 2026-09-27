---
id: ADR-0002
title: Rebuild the search index nightly instead of streaming updates
status: accepted
date: 2026-03-04
services: search
cites: code/search/rebuild.py, https://example.com/search-vendor/limits
---
Streaming updates kept drifting from the product table. A full nightly
rebuild is slower but always converges. The vendor's rate limits page is
cited for the batch size; we can't hash a web page, so that citation is
unverifiable by design.
