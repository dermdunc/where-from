import uuid


def new_key(order_id):
    return f"{order_id}:{uuid.uuid4()}"
