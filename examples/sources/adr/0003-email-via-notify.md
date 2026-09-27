---
id: ADR-0003
title: Send order emails through the notify service
status: proposed
date: 2026-04-19
services: checkout, notify
cites: code/notify/templates.py, code/checkout/confirm.py
---
Checkout stops sending email directly. It publishes an order-confirmed
event and notify owns templates and delivery. Notify has no catalogue
entry yet.
