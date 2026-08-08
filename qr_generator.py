import qrcode
import io
import base64

def generate_qr(order_id):

    verify_url = f"https://canteen-x.onrender.com/verify_ticket/{order_id}"

    qr = qrcode.make(verify_url)

    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")

    qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return f"data:image/png;base64,{qr_base64}"
