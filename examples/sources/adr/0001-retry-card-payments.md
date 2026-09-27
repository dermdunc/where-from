---
id: ADR-0001
title: Retry card payments with idempotency keys
status: accepted
date: 2026-02-11
services: checkout
cites: code/checkout/retry.py, code/checkout/idempotency.py
---
Card authorisation calls time out often enough that we retry them. Every
retry reuses the idempotency key from the first attempt, so a slow success
followed by a retry cannot charge the customer twice.
