# qr_tool_mac.py
import tkinter as tk
from tkinter import simpledialog
from PIL import Image, ImageTk
from pyzbar.pyzbar import decode
import qrcode
import io
import subprocess
from AppKit import NSPasteboard, NSPasteboardTypePNG, NSImage
from Foundation import NSData


def generate_qr_image(data):
    """
    Generates QR Image
    :param data:
    :return:
    """
    qr = qrcode.QRCode(border=2, box_size=8)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img

def copy_png_mac(img):
    """
    Copies the QR image to the clipboard
    :param img:
    :return:
    """
    output = io.BytesIO()
    img.save(output, format="PNG")
    png_data = output.getvalue()
    pb = NSPasteboard.generalPasteboard()
    pb.clearContents()
    data = NSData.dataWithBytes_length_(png_data, len(png_data))
    image = NSImage.alloc().initWithData_(data)
    pb.writeObjects_([image])


def show_generated_qr(img):
    """
    Shows the generated QR code
    :param img:
    :return:
    """
    win = tk.Tk()
    win.title("Generated QR Code")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    pil_img = Image.open(buffer)
    tk_img = ImageTk.PhotoImage(pil_img, master=win)
    label = tk.Label(win, image=tk_img)
    label.image = tk_img
    label.pack()
    def on_copy():
        copy_png_mac(pil_img)
    btn = tk.Button(win, text="Copy Image to Clipboard", command=on_copy)
    btn.pack(pady=10)
    win.mainloop()


def generate_qr():
    """
    Generates QR code
    :return:
    """
    root = tk.Tk()
    root.withdraw()
    text = simpledialog.askstring("Enter Text", "Text or URL to encode:\n(Must include http/https for links)", parent=root)
    root.destroy()
    if text:
        img = generate_qr_image(text)
        show_generated_qr(img)


def capture_and_decode_qr():
    """
    Obtains QR code and decodes it
    :return:
    """
    tmpfile = "/tmp/qr_snap.png"
    subprocess.run(["screencapture", "-i", "-x", tmpfile])
    try:
        img = Image.open(tmpfile)
    except FileNotFoundError:
        return  # User canceled
    result = decode(img)
    text = ""
    if result:
        for obj in result:
            text += obj.data.decode('utf-8') + "\n"
    else:
        text = "No QR code found."
    show_text_window(text)


def show_text_window(text):
    """
    Shows the text window
    :param text:
    :return:
    """
    win = tk.Tk()
    win.title("Decoded QR Text")
    win.geometry("400x200")
    textbox = tk.Text(win, wrap='word')
    textbox.insert(tk.END, text.strip())
    textbox.pack(expand=True, fill='both')
    textbox.focus_set()
    textbox.bind("<Escape>", lambda e: win.destroy())
    win.mainloop()


def ask_mode_and_dispatch():
    """
    Asks the user to select a mode and dispatch it
    :return:
    """
    def choose(mode_choice):
        win.destroy()
        if mode_choice == "capture":
            capture_and_decode_qr()
        elif mode_choice == "generate":
            generate_qr()
    win = tk.Tk()
    win.title("QR Tool - Select Mode")
    win.geometry("300x120")
    win.resizable(False, False)
    label = tk.Label(win, text="Choose an action:", font=("Arial", 12))
    label.pack(pady=10)
    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=5)
    capture_btn = tk.Button(btn_frame, text="Capture QR from Screen", width=25, command=lambda: choose("capture"))
    capture_btn.grid(row=0, column=0, padx=5)
    generate_btn = tk.Button(btn_frame, text="Generate QR from Text", width=25, command=lambda: choose("generate"))
    generate_btn.grid(row=1, column=0, padx=5, pady=5)
    win.mainloop()


if __name__ == "__main__":
    ask_mode_and_dispatch()
