# qr_tool.py
import tkinter as tk
from tkinter import simpledialog
from PIL import ImageGrab, ImageTk, Image
from pyzbar.pyzbar import decode
import qrcode
import io
import win32clipboard
import win32con


def ask_mode_and_dispatch():
    """
    Asks the user to choose between capturing a QR code from the screen or generating one from text.
    :return:
    """
    def choose(mode_choice):
        win.destroy()
        if mode_choice == "capture":
            ScreenSnip()
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


def generate_qr_image(data):
    """
    Generates a QR code image from the given data.
    :param data:
    :return:
    """
    qr = qrcode.QRCode(border=2, box_size=8)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img

def copy_png(img):
    """
    Copies the given image to the clipboard in PNG format.
    :param img:
    :return:
    """
    output = io.BytesIO()
    img.convert('RGB').save(output, 'BMP')
    data = output.getvalue()[14:]  # Strip BMP header
    output.close()
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32con.CF_DIB, data)
    win32clipboard.CloseClipboard()


def show_generated_qr(img):
    """
    Displays the generated QR code image in a new window and provides an option to copy it to the clipboard.
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
        copy_png(pil_img)
    btn = tk.Button(win, text="Copy Image to Clipboard", command=on_copy)
    btn.pack(pady=10)
    win.mainloop()


def generate_qr():
    """
    Prompts the user for text or URL to generate a QR code.
    :return:
    """
    root = tk.Tk()
    root.withdraw()
    text = simpledialog.askstring("Enter Text", "Text or URL to encode:\n(Must include http/https for links)", parent=root)
    root.destroy()
    if text:
        img = generate_qr_image(text)
        show_generated_qr(img)


class ScreenSnip:
    def __init__(self):
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-alpha", 0.3)
        self.root.configure(bg='black')
        self.canvas = tk.Canvas(self.root, cursor="cross", bg='grey11')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.start_x = self.start_y = self.rect = None
        self.canvas.bind("<ButtonPress-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.root.mainloop()

    def on_click(self, event):
        """
        Handles mouse click event to start drawing the rectangle.
        :param event:
        :return:
        """
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red', width=2)


    def on_drag(self, event):
        """
        Handles mouse drag event to resize the rectangle.
        :param event:
        :return:
        """
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)


    def on_release(self, event):
        """
        Handles mouse release event to finalize the rectangle and capture the screen.
        :param event:
        :return:
        """
        x1, y1 = self.start_x, self.start_y
        x2, y2 = event.x, event.y
        self.root.destroy()
        self.capture(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))


    def capture(self, x, y, w, h):
        """
        Captures the screen within the specified rectangle and decodes any QR code found.
        :param x:
        :param y:
        :param w:
        :param h:
        :return:
        """
        img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
        self.decode_qr(img)


    def decode_qr(self, image):
        """
        Decodes the QR code from the captured image.
        :param image:
        :return:
        """
        result = decode(image)
        text = ""
        if result:
            for obj in result:
                text += obj.data.decode('utf-8') + "\n"
        else:
            text = "No QR code found."
        self.show_text_window(text)


    def show_text_window(self, text):
        """
        Displays the decoded text in a new window.
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


if __name__ == "__main__":
    ask_mode_and_dispatch()
