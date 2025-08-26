import qrcode

# WiFi credentials
SSID = "Guest-WiFi"
PASSWORD = "Welcome123"
ENCRYPTION = "WPA"

# Format WiFi configuration string for QR code
wifi_string = f"WIFI:T:{ENCRYPTION};S:{SSID};P:{PASSWORD};;"

# Create QR code instance
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=4,
)

# Add WiFi data to QR code
qr.add_data(wifi_string)
qr.make(fit=True)

# Create an image from the QR code
img = qr.make_image(fill_color="black", back_color="white")

# Save the QR code image
img.save("../output/guest_wifi_qr.png")

print("QR code for Guest WiFi has been generated and saved as 'guest_wifi_qr.png'")