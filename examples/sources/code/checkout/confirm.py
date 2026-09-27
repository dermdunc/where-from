def confirm(order, bus):
    bus.publish("order-confirmed", {"order_id": order.id, "email": order.email})
