import qrcode
import os

def generate_qr(order_id):
    folder = os.path.join("static", "qr")
    os.makedirs(folder, exist_ok=True)

    filename = f"ticket_{order_id}.png"
    path = os.path.join(folder, filename)

    qr = qrcode.make(str(order_id))
    qr.save(path)

    return f"qr/{filename}"
