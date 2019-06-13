import Neobux

import tkinter
from idlelib.tooltip import OnHoverTooltipBase

import multiprocessing

from PIL import Image
from PIL import ImageTk
from base64 import b64decode
from io import BytesIO

def build_Neobux_driver(connection):
    Neobux(None, connection).mainloop()

class Application(tkinter.Tk):
    """Tkinter-based GUI for interacting with a Neobux autoclicker"""
    LOADING_IMAGE_BASE64 = ("iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAACuklEQVRYhcWXoW/iUBzH39+AQC2E"
                            "VCCqSFOBQqAqUBNViKoKVEUVAlWBqqpAIJ5CVBAEqoJkC4yVDdiNIwOyscDWjG0sd7vMf08svNDb"
                            "kuMubfdLvmlVP5/3e7/3khKyZzUeGzAWBuSxDMEVwPd4xI/jEFwB+37jv4p6FPJYRqKTQOwohthR"
                            "DPHjOOLHcfYeCthe21AmCrguh4POAYPuJnYUQ26QC16AehTZ8ywSncSHfCYSKNxaWeB7PLgut5eA"
                            "NJKCE6AeheAK4LocE0h2kz545iwDZaJAn+swlybMpRmMQOOxgdwgh9RJClyXQ+okhWQ3yZI9z8Ja"
                            "WeFNfHFaBN/jkTpJ+cJ1OehzPfyjlnbT4Hu8T4Lv8TAWRrhwQghRr1Sk3bRPgu/x4a+ckPfzLvZF"
                            "pN00BFdgz8Nvh+HDCSHEWBgMLPZFCK4AwRXCHbjdUiYKg4p9EWJfDPZs/63yF3lkzjK+aDMtOoHs"
                            "eRa7yZxlULmtfJ1AbpBD9a76tQKRDSAhhEgjCblBDtJIYgnsft+n5LHsg0sjCeWbcnQC2kzzwfMX"
                            "eSgTJToBc2ky8PYpj2VQj0YjYa9t5C/yLPJYhjyWo70L9Lnugxe+F6BMlOiGsf5QZ/BdAWWiRLcV"
                            "xsJA4XuBwdUrFeqVCm2moXZfC1+i+dSEeqV+KlC6LsFcmmg9t8IVqT/UWeuViQJtpkGf6yhdl1C+"
                            "KcNcmqAeRfOpifZLG8PXIS5/XWL6NsX0bRqMHPUoitMiW/1WwFgYqNxWYK0sVO+qqD/U0Xxqwtk4"
                            "OP15iuHrMDgJe22jdF36IGAsDFgrC7X7GuuEs3HQ+dEJVoCQ95mwVpZPYPsfUL2rgnoU9tpG67mF"
                            "9ks7+C78KbLdAnNpwlpZoB79tAvbmQhUghBCnI0De22DepRtAfUoGo8NOBuHDeW/wn8DCAIBcTEu"
                            "hj0AAAAASUVORK5CYII=")
    TITLE_STRIP_BASE64 = ("iVBORw0KGgoAAAANSUhEUgAAAPoAAAABCAYAAAD3ubPnAAAARElEQVQokWNQ2+n+f8jibaH/1TYU"
                          "/Vdb1zAgWHpzw3/W/Q3/GY6SiQ/1/WfYs/o/w66dIxNvP/6fYePj/wzrP45iGmMAlwJeC/E1zLcA"
                          "AAAASUVORK5CYII=")                            

    def __init__(self, title = "clicker"):
        tkinter.Tk.__init__(self, None)
        icon = ImageTk.PhotoImage(data = b64decode(Neobux.FAVICON_BASE64))
        self.iconphoto(True, icon)
        self.title(title)
        self.config(bg = "white")
        self.grid()
        self.init_widgets()
        self.loading_animation.grid(row = 1, column = 0)
        self.gui_conn, self.driver_conn = multiprocessing.Pipe()
        self.driver_builder = multiprocessing.Process(target = build_Neobux_driver, args = (self.driver_conn, ))
        self.driver_builder.start()
        self.driver_builder.join()
        print(self.queue.qsize())
        print(self.queue.get(timeout = 2))
        self.loading_animation.grid_forget()
        self.login_prompt.grid(row = 1, column = 0, padx = 20, pady = 20)

    def init_widgets(self):
        self.init_title_strip()
        self.init_login_prompt()
        self.init_loading_animation()

    def init_title_strip(self):
        title_strip = Image.open(BytesIO(b64decode(Application.TITLE_STRIP_BASE64)))
        title_strip = title_strip.resize((400,5))
        self.title_strip_image = ImageTk.PhotoImage(title_strip)
        self.title_strip = tkinter.Label(self, image = self.title_strip_image)
        self.title_strip.grid(row = 0, column = 0)

    def init_login_prompt(self):
        self.login_prompt = tkinter.Frame(self, highlightbackground = "#777", highlightthickness = 1, bd = 20)

        self.username_frame = tkinter.Frame(self.login_prompt, height = 26)
        self.username_frame.grid(row = 0, column = 0, sticky = tkinter.E)
        self.username_label = tkinter.Label(self.username_frame, bg = "white", text = "Username:", font=("Arial", -14))
        self.username_label.grid(row = 0, column = 0)
        self.username_entry = tkinter.Entry(self.username_frame, exportselection = 0)
        self.username_entry.grid(row = 0, column = 1)

        self.password_frame = tkinter.Frame(self.login_prompt, height = 26)
        self.password_frame.grid(row = 1, column = 0, sticky = tkinter.E)
        self.password_label = tkinter.Label(self.password_frame, bg = "white", text = "Password:", font=("Arial", -14))
        self.password_label.grid(row = 0, column = 0)
        self.password_entry = tkinter.Entry(self.password_frame, show = u"\u2022")
        self.password_entry.grid(row = 0, column = 1)

        self.secondary_password_frame = tkinter.Frame(self.login_prompt, height = 26)
        self.secondary_password_frame.grid(row = 2, column = 0, sticky = tkinter.E)
        self.secondary_password_label = tkinter.Label(self.secondary_password_frame, bg = "white", text = "Secondary Password:", font=("Arial", -14))
        self.secondary_password_label.grid(row = 0, column = 0)
        self.secondary_password_entry = tkinter.Entry(self.secondary_password_frame, show = u"\u2022")
        self.secondary_password_entry.grid(row = 0, column = 1)
        self.secondary_password_tooltip = Tooltip(self.secondary_password_frame, "Leave blank if you do not\nhave a secondary password")

        self.captcha_frame = tkinter.Frame(self.login_prompt, height = 26)
        self.captcha_frame.grid(row = 3, column = 0, sticky = tkinter.E)
        self.captcha_label = tkinter.Label(self.captcha_frame, bg = "white", text = "Verification Code:", font=("Arial", -14))
        self.captcha_label.grid(row = 0, column = 0, columnspan = 2)
        self.captcha_entry = tkinter.Entry(self.captcha_frame)
        self.captcha_entry.grid(row = 0, column = 2)
        #self.captcha_image = ImageTk.PhotoImage(self.driver.captcha_image)

        self.login_button = tkinter.Button(self.login_prompt, text = "Login", command = self.neobux_login)
        self.login_button.grid(row = 4, column = 0)

        self.login_status = tkinter.Label(self.login_prompt)
        self.login_status.grid(row = 5, column = 0)

    def neobux_login(self):
        self.login_status.grid_forget()
        self.username_entry.config(state = tkinter.DISABLED)
        self.password_entry.config(state = tkinter.DISABLED)
        self.secondary_password_entry.config(state = tkinter.DISABLED)
        self.captcha_entry.config(state = tkinter.DISABLED)
        self.driver.username = self.username_entry.get()
        self.driver.password = self.password_entry.get()
        self.driver.secondary_password = self.secondary_password_entry.get()
        self.driver.captcha_key = self.captcha_entry.get()
        self.loading_animation.grid(row = 1, column = 0)
        if self.driver.log_in():
            self.login_prompt.grid_forget()
        self.username_entry.config(state = tkinter.NORMAL)
        self.password_entry.config(state = tkinter.NORMAL)
        self.secondary_password_entry.config(state = tkinter.NORMAL)
        self.captcha_entry.config(state = tkinter.NORMAL)

    def init_loading_animation(self):
        self.loading_animation = tkinter.Canvas(self, height = 32, width = 32, highlightthickness = 0)
        self.rotate_loading_graphic = self._update_loading_animation().__next__
        self.rotate_loading_graphic()
    
    def _update_loading_animation(self):
        loading_image = Image.open(BytesIO(b64decode(Application.LOADING_IMAGE_BASE64)))
        angle = 0
        while True:
            self.loading_frame = ImageTk.PhotoImage(loading_image.rotate(angle))
            canvas_object = self.loading_animation.create_image(0, 0, image = self.loading_frame, anchor = tkinter.NW)
            self.after(58, self.rotate_loading_graphic)
            yield
            self.loading_animation.delete(canvas_object)
            angle -= 15
            angle %= 360

class Tooltip(OnHoverTooltipBase):
    def __init__(self, anchor_widget, text, hover_delay = 500):
        super(Tooltip, self).__init__(anchor_widget, hover_delay = hover_delay)
        self.text = text

    def showcontents(self):
        tkinter.Label(self.tipwindow, text = self.text, borderwidth = 1,
                      relief = tkinter.RAISED, justify = tkinter.CENTER,
                      background = "#ffffe0").pack()

if __name__ == "__main__":
    clicker = Application(title = "Neobux Clicker")
    clicker.mainloop()
