import qrcode
import os

def generate_qr(order_id):

    url = f"http://172.16.117.44:5000/verify_ticket/{order_id}"

    qr = qrcode.make(url)

    filename = f"ticket_{order_id}.png"

    path = os.path.join("static", "qr", filename)

    qr.save(path)

    return filename