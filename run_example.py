from ecommerce_receipt import Order, build_service


if __name__ == "__main__":
    order = Order("ord-1042", "buyer@example.com", "Coffee grinder", 1, "129.00", "paid")
    print(build_service().process(order))

