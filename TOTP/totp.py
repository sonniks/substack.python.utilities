import argparse
import pyotp
import qrcode
import base64
import hashlib
import hmac
import time


# Random generation for testing PPE3NCWMO4YUPMCQWAT2SRQ47QIXS3AT


def generate_secret():
    """
    Generate a shared secret and QR code for Google Authenticator.
    :return:
    """
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name="user@example.com", issuer_name="MyApp")
    # Change above line to use your own email and app name to embed in the QR code
    # Google Authenticator allows these values to be edited by swiping left
    print(f"Secret: {secret}")
    print("Scan this QR code with Google Authenticator:")
    qr = qrcode.QRCode()
    qr.add_data(uri)
    qr.make()
    qr.print_ascii()


def show_totp(secret, verbose=False):
    """
    Show the current TOTP for the given shared secret.
    :param secret: full string of initial secret
    :param verbose: boolean if full process (hash, decimal, six digit truncation)
    :return:
    """
    totp = pyotp.TOTP(secret)
    now = int(time.time())
    time_remaining = 30 - (now % 30)
    interval = now // 30  # 30 second intervals - same as Google Authenticator
    key = base64.b32decode(secret, True)
    msg = interval.to_bytes(8, 'big')
    h = hmac.new(key, msg, hashlib.sha1).digest()
    offset = h[19] & 0x0F
    binary = ((h[offset] & 0x7f) << 24 |
              (h[offset + 1] & 0xff) << 16 |
              (h[offset + 2] & 0xff) << 8 |
              (h[offset + 3] & 0xff))
    otp = binary % 1000000
    print(f"TOTP: {otp:06d} (valid for {time_remaining}s)")
    if verbose:
        print(f"Raw HMAC hash (hex): {h.hex()}")
        print(f"Offset: {offset}")
        print(f"Truncated binary: {binary}")
        print(f"Final TOTP (mod 1,000,000): {otp:06d}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TOTP Tool")
    parser.add_argument('--generate', action='store_true', help="Generate a shared secret and QR code")
    parser.add_argument('--showtotp', metavar='SECRET',
                        help="Show the current TOTP for the given shared secret")
    parser.add_argument('--verbose', action='store_true', help="Show raw hash and extra data")
    args = parser.parse_args()
    if args.generate:
        generate_secret()
    elif args.showtotp:
        show_totp(args.showtotp, args.verbose)
    else:
        parser.print_help()
