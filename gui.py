from Neobux import Neobux

import tkinter
import idlelib.tooltip
from base64 import b64decode
from PIL import Image
from PIL import ImageTk
from io import BytesIO

class Application(tkinter.Tk):

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
                            

    def __init__(self, master = None, title = "clicker"):
        tkinter.Tk.__init__(self, master)
        self.driver = Neobux()
        self.title(title)
        self.grid()
        self.generate_frames()
        self.login_prompt.grid(column = 0, row = 0)

    def generate_frames(self):
        self.init_login_prompt()
        self.init_loading_graphic()

    def init_login_prompt(self):
        self.driver.launch()
        self.login_prompt = tkinter.Frame(self)

        self.username_frame = tkinter.Frame(self.login_prompt)
        self.username_frame.grid(row = 0, column = 0, sticky = tkinter.E)
        self.username_label = tkinter.Label(self.username_frame, text = "Username:")
        self.username_label.grid(row = 0, column = 0, sticky = tkinter.E)
        self.username_entry = tkinter.Entry(self.username_frame, exportselection = 0)
        self.username_entry.grid(row = 0, column = 1, sticky = tkinter.W)

        self.password_frame = tkinter.Frame(self.login_prompt)
        self.password_frame.grid(row = 1, column = 0, sticky = tkinter.E)
        self.password_label = tkinter.Label(self.password_frame, text = "Password:")
        self.password_label.grid(row = 0, column = 0, sticky = tkinter.E)
        self.password_entry = tkinter.Entry(self.password_frame, show = u"\u2022")
        self.password_entry.grid(row = 0, column = 1, sticky = tkinter.W)

        self.secondary_password_frame = tkinter.Frame(self.login_prompt)
        self.secondary_password_frame.grid(row = 2, column = 0, sticky = tkinter.E)
        self.secondary_password_label = tkinter.Label(self.secondary_password_frame, text = "Secondary Password:")
        self.secondary_password_label.grid(row = 0, column = 0, sticky = tkinter.E)
        self.secondary_password_entry = tkinter.Entry(self.secondary_password_frame, show = u"\u2022")
        self.secondary_password_entry.grid(row = 0, column = 1, sticky = tkinter.W)
        self.secondary_password_tooltip = Tooltip(self.secondary_password_frame,
                                                  "Leave blank if you do not\nhave a secondary password")

        self.login_button = tkinter.Button(self.login_prompt, text = "Login", command = self.neobux_login)
        self.login_button.grid(row = 3, column = 0)

    def neobux_login(self):
        self.username_entry.config(state = tkinter.DISABLED)
        self.password_entry.config(state = tkinter.DISABLED)
        self.secondary_password_entry.config(state = tkinter.DISABLED)

    def init_loading_graphic(self):
        self.loading_graphic = tkinter.Canvas(self, height = 32, width = 32, highlightthickness = 0)
        self.rotate_load_graphic = self.update_loading_graphic().__next__
        self.rotate_load_graphic()
    
    def update_loading_graphic(self):
        loading_image = Image.open(BytesIO(b64decode(Application.LOADING_IMAGE_BASE64)))
        angle = 0
        while True:
            image = ImageTk.PhotoImage(loading_image.rotate(angle))
            canvas_object = self.loading_graphic.create_image(0, 0, image = image, anchor = tkinter.NW)
            self.after(34, self.rotate_load_graphic)
            yield
            self.loading_graphic.delete(canvas_object)
            angle -= 12
            angle %= 360

class Tooltip(idlelib.tooltip.OnHoverTooltipBase):
    def _init__(self, anchor_widget, text, hover_delay = 500):
        super(Tooltip, self)._init__(anchor_widget, hover_delay = hover_delay)
        self.text = text

    def showcontents(self):
        tkinter.Label(self.tipwindow, text = self.text, borderwidth = 1,
                      relief = tkinter.RAISED, justify = tkinter.CENTER,
                      background = "#ffffe0").pack()

clicker = Application(title = "Neobux Clicker")
clicker.mainloop()
