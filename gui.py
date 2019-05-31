from Neobux import Neobux

import tkinter
import idlelib.tooltip
from base64 import b64decode
from PIL import Image
from PIL import ImageTk
from io import BytesIO

class Application(tkinter.Tk):

    LOADING_IMAGE_BASE64 = ("iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAADEElEQVRYhcXXr28aYRzHcf4GBGpp"
                             "mhOIU+SCQCFQCFTFqYpTiCoEClF1ourUCUTFoypOEEQVokkbKLv+3hgpbToW6G6lHcu6pWHZr7wn"
                             "lnvCBTIgBfYk3xyC3Od13+/DhSfElKt0X8Jsm+gNHc3VUOsqkYMImqtNe4uxKzTpC8IT6A2dleoK"
                             "4f0w4f0wkYMIkYOI/LwQgNNzMJoGSk3hRfWFDB2u8H6Y1Glq/gDhCZInSVaqKyM1DjJXgN21Uesq"
                             "Sk2ZCpA+T88PIDyB5mooNUUCVmurgfDEcQKjaZC/zmN1LKyONR9A6b5E6jRF9DCKUlOIHkZZra3K"
                             "Sp4ksbv2s8L+CdhobaDWVaKH0UApNYX8dX7uwQGA8AQxN4ZaVwMIta5its2FhUtA9jJLzI0FEGpd"
                             "XeiTS4DTc4gfxYm5MTRXk9e1V2sLDwcImW1TBseP4miuhuZqC9lwYwFG05Ch8aM48aP4s3/bMwEy"
                             "FxkSx4lA5a5yywMkT5IMV+I4wda7rf8HSJ2mKN4W/y9gWRsQIJQ+T5M6TZE+T8t67vt9JoDe0APh"
                             "6fM0m283lwfIXeUC4ZmLDEbTWB7A6lgy2L/qDR3hieUAnJ5D5iIjS2/o6A19ae+CEED+Oh8IX3+z"
                             "jtE0lrIZQwA7dzsyfBhgNI1njeLX71/TAQDMtsn6m3UZnr3Mkr3MkrvKsf1+e+bwwc/BbIDyQ5ns"
                             "ZXYsoHBTwOpY7H7cnXjD/vc+jz8eZwfA31H4rTeaBrmrHPnrPIWbAptvN7E6FsITlB/K7H3a4+zL"
                             "Ga+/vqb11KL11KI76PLh2wf63/sMfg5GEONAI3/LhSfYaG3Ip/cBZttk690WdtemeFtk526H8kOZ"
                             "Sr/Cy8eXnH05k4jhLvgIvyYC4O+pqHBTGAGYbRO7a7P9flt2otKvUP1cDQD8Lgx3YqoRDK/yQxm7"
                             "awcA/jmgeFtEeAKn57D7cZe9T3sjXRhG/GtNPJz6EH8EVsfC7toIT4ztgr8n/FFMWhMB/qr0Kzg9"
                             "B+EJOQLhCUr3JSr9ityUrafWtLcE4A/pZVYfNQqusQAAAABJRU5ErkJggg==")

    def __init__(self, master = None, title = "clicker"):
        tkinter.Tk.__init__(self, master)
        self.master = master
        self.title(title)
        self.grid()
        self._generate_frames()
        self.login_prompt.grid(column = 0, row = 0)

    def _generate_frames(self):
        self._build_login_prompt()

    def _build_login_prompt(self):
        self.login_prompt = tkinter.Frame(self)

        self.username_frame = tkinter.Frame(self.login_prompt)
        self.username_frame.grid(row = 0)
        self.username_label = tkinter.Label(self.username_frame, text = "Username:")
        self.username_label.grid(row = 0, column = 0, sticky = tkinter.E)
        self.username_entry = tkinter.Entry(self.username_frame, exportselection = 0)
        self.username_entry.grid(row = 0, column = 1, sticky = tkinter.W)

        self.password_frame = tkinter.Frame(self.login_prompt)
        self.password_label = tkinter.Label(self.password_frame, text = "Password:")
        self.password_label.grid(row = 0, column = 0, sticky = tkinter.E)
        self.password_entry = tkinter.Entry(self.login_prompt, show = u"\u2022")
        self.password_entry.grid(row = 0, column = 1, sticky = tkinter.W)

        self.secondary_password_frame = tkinter.Frame(self.login_prompt)
        self.seconda
        self.secondary_password_label = tkinter.Label(self.secondary_password_frame, text = "Secondary Password:")
        self.secondary_password_label.grid(row = 2, column = 0, sticky = tkinter.E)
        self.secondary_password_entry = tkinter.Entry(self.secondary_password_frame, show = u"\u2022")
        self.secondary_password_entry.grid(row = 2, column = 1, sticky = tkinter.W)
        self.secondary_password_tooltip = Tooltip(self.secondary_password_frame,
                                                  "Leave blank if you do not\nhave a secondary password")
        self.loading_graphic = tkinter.Canvas(self.login_prompt, height = 46)
        self.loading_graphic.grid(row = 3, column = 0, columnspan = 2)
        self._update_loading_graphic()

        self.login_button = tkinter.Button(self.login_prompt, height = 10, text = "Login")
        self.login_button.grid(row = 4

    def _update_loading_graphic(self):
        loading_image = Image.open(BytesIO(b64decode(Application.LOADING_IMAGE_BASE64)))
        angle = 0
        loading = ImageTK.PhotoImage(loading_image.rotate(angle))
        canvas_object = self.loading_graphic.create_image(32, 32, image = loading)
        self.after_idle(self.update)
        yield
        self.loading_graphic.delete(canvas_object)
        angle += 10
        angle %= 360

class Tooltip(idlelib.tooltip.OnHoverTooltipBase):
    def __init__(self, anchor_widget, text, hover_delay = 500):
        super(Tooltip, self).__init__(anchor_widget, hover_delay = hover_delay)
        self.text = text

    def showcontents(self):
        tkinter.Label(self.tipwindow, text = self.text, borderwidth = 1,
                      relief = tkinter.RAISED, justify = tkinter.CENTER,
                      background = "#ffffe0").pack()

clicker = Application(title = "Neobux Clicker")
clicker.mainloop()
