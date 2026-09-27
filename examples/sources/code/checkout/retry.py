MAX_ATTEMPTS = 3
BACKOFF_SECONDS = (0.5, 2.0, 8.0)


def authorise_with_retry(client, request, key):
    for delay in BACKOFF_SECONDS[:MAX_ATTEMPTS]:
        result = client.authorise(request, idempotency_key=key)
        if not result.timed_out:
            return result
        client.sleep(delay)
    raise TimeoutError("card authorisation did not complete")
