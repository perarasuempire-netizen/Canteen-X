import qrcode
import os

def generate_qr(order_id):
    # Your deployed Render URL
    verify_url = f"https://canteen-x.onrender.com/verify-order/{order_id}"

    folder = "static/qr"
    os.makedirs(folder, exist_ok=True)

    path = os.path.join(folder, f"ticket_{order_id}.png")

    qr = qrcode.make(verify_url)
    qr.save(path)

    return f"/static/qr/ticket_{order_id}.png"
