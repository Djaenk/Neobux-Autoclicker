from Neobux import Neobux
from Neobux import NeobuxPage

import tkinter
from idlelib.tooltip import OnHoverTooltipBase

import multiprocessing

from PIL import Image
from PIL import ImageTk
from base64 import b64decode
from io import BytesIO

def build_Neobux_driver(connection):
    Neobux(None, True, connection).mainloop()

class Tooltip(OnHoverTooltipBase):
    def __init__(self, anchor_widget, text, hover_delay = 500):
        super(Tooltip, self).__init__(anchor_widget, hover_delay = hover_delay)
        self.text = text

    def showcontents(self):
        tkinter.Label(self.tipwindow, text = self.text, borderwidth = 1,
                      relief = tkinter.RAISED, justify = tkinter.CENTER,
                      background = "#DDDDC0").pack()

class NeobuxLoadingGraphic(tkinter.Canvas):

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

    def __init__(self, master = None):
        tkinter.Canvas.__init__(self, master, height = 32, width = 32, highlightthickness = 0)
        self.rotate_loading_graphic = self._update_loading_animation().__next__
        self.rotate_loading_graphic()

    def _update_loading_animation(self):
        loading_image = Image.open(BytesIO(b64decode(NeobuxLoadingGraphic.LOADING_IMAGE_BASE64)))
        angle = 0
        while True:
            self.loading_frame = ImageTk.PhotoImage(loading_image.rotate(angle))
            canvas_object = self.create_image(0, 0, image = self.loading_frame, anchor = tkinter.NW)
            self.after(58, self.rotate_loading_graphic)
            yield
            self.delete(canvas_object)
            angle -= 15
            angle %= 360
        
class LoginPrompt(tkinter.Frame):
    def __init__(self, master = None, submit = None):
        tkinter.Frame.__init__(self, master, bg = "white", highlightbackground = "#787878", highlightthickness = 1, bd = 30)
        
        self.login_label = tkinter.Label(self, bg = "white", fg = "#00A0EE", font = ("Trebuchet MS", 18, "bold"), text = "Neobux Member Login")
        self.login_label.grid(row = 0, column = 0)
        
        self.login_status = tkinter.Label(self, bg = "white", fg = "red", font = ("Verdana", -12), text = "text")
        self.login_status.grid(row = 1, column = 0, pady = (3, 5))

        self.username_frame = tkinter.Frame(self, height = 26)
        self.username_frame.grid(row = 2, column = 0, sticky = tkinter.E, pady = 1)
        self.username_label = tkinter.Label(self.username_frame, bg = "white", font = ("Arial", -14), text = "Username:")
        self.username_label.grid(row = 0, column = 0)
        self.username_entry = tkinter.Entry(self.username_frame, exportselection = 0, bd = 0, highlightbackground = "#999", highlightthickness = 1, font = ("Arial", -12, "bold"))
        self.username_entry.grid(row = 0, column = 1)

        self.password_frame = tkinter.Frame(self, height = 26)
        self.password_frame.grid(row = 3, column = 0, sticky = tkinter.E, pady = 1)
        self.password_label = tkinter.Label(self.password_frame, bg = "white", text = "Password:", font= ("Arial", -14))
        self.password_label.grid(row = 0, column = 0)
        self.password_entry = tkinter.Entry(self.password_frame, exportselection = 0, bd = 0, highlightbackground = "#999", highlightthickness = 1, font = ("Arial", -12, "bold"), show = u"\u2022")
        self.password_entry.grid(row = 0, column = 1)

        self.secondary_password_frame = tkinter.Frame(self, height = 26)
        self.secondary_password_frame.grid(row = 4, column = 0, sticky = tkinter.E, pady = 1)
        self.secondary_password_label = tkinter.Label(self.secondary_password_frame, bg = "white", text = "Secondary Password:", font = ("Arial", -14))
        self.secondary_password_label.grid(row = 0, column = 0)
        self.secondary_password_entry = tkinter.Entry(self.secondary_password_frame, exportselection = 0, bd = 0, highlightbackground = "#999", highlightthickness = 1, font = ("Arial", -12, "bold"), show = u"\u2022")
        self.secondary_password_entry.grid(row = 0, column = 1)
        self.secondary_password_tooltip = Tooltip(self.secondary_password_frame, "Leave blank if you do not\nhave a secondary password")
        
        self.login_submit = tkinter.Button(self, bg = "#00AC00", fg = "white", disabledforeground = "#EEE", text = "Submit", command = submit)
        self.login_submit.grid(row = 5, column = 0, pady = (15, 0))

    def disable(self):
        self.config(bg = "#F8F8F8")
        self.login_label.config(bg = "#F8F8F8", fg = "#909090")
        self.login_status.config(bg = "#F8F8F8", text = "")
        self.username_label.config(bg = "#F8F8F8", fg = "#666")
        self.username_entry.config(state = tkinter.DISABLED, highlightbackground = "#BBB", highlightcolor = "#BBB")
        self.password_label.config(bg = "#F8F8F8", fg = "#666")
        self.password_entry.config(state = tkinter.DISABLED, highlightbackground = "#BBB", highlightcolor = "#BBB")
        self.secondary_password_label.config(bg = "#F8F8F8", fg = "#666")
        self.secondary_password_entry.config(state = tkinter.DISABLED, highlightbackground = "#BBB", highlightcolor = "#BBB")
        self.login_submit.config(state = tkinter.DISABLED, relief = tkinter.GROOVE, bg = "#858585")

    def enable(self):
        self.config(bg = "white")
        self.login_label.config(bg = "white", fg = "00A0EE")
        self.login_status.grid(bg = "white")
        self.username_label.config(bg = "white")
        self.username_entry.config(state = tkinter.NORMAL, highlightbackground = "#999", highlightcolor = "black")
        self.password_entry.config(state = tkinter.NORMAL, highlightbackground = "#999", highlightcolor = "black")
        self.secondary_password_entry.config(state = tkinter.NORMAL, highlightbackground = "#999", highlightcolor = "black")
        self.login_submit.config(state = tkinter.NORMAL, relief = tkinter.RAISED, bg = "#00AC00")

    def set_status(self, status = ""):
        self.login_status.config(text = status)

    def get_creds(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        secondary_password = self.secondary_password_entry.get()
        return username, password, secondary_password

class CaptchaPrompt(tkinter.Frame):
    def __init__(self, master = None, submit = None):
        tkinter.Frame.__init__(self, master)

        self.captcha_label = tkinter.Label(self, bg = "white", text = "Verification", font=("Verdana", -20))
        self.captcha_label.grid(row = 0, column = 0, columnspan = 2)

        self.captcha_description = tkinter.Label(self, bg = "white", text = "Enter the letters you see below")
        self.captcha_description.grid(row = 1, column = 0, columnspan = 2)

        captcha = ImageTk.PhotoImage(file = "example captcha.png")
        self.captcha_image = tkinter.Label(self, image = captcha)
        self.captcha_image.grid(row = 2, column = 0)

        self.captcha_entry = tkinter.Entry(self)
        self.captcha_entry.grid(row = 2, column = 1)

        self.captcha_submit = tkinter.Button(self, text = "Submit", command = submit)
        self.captcha_submit.grid(row = 3, column = 0, columnspan = 2)

class AuthenticationPrompt(tkinter.Frame):
    def __init__(self, master = None, submit = None):
        tkinter.Frame.__init__(self, master, bg = "white", border = 30)

        self.authentication_label = tkinter.Label(self, bg = "white", text = "Two-Factor Authentication", font = ("Verdana", -20))
        self.authentication_label.grid(row = 0, column = 0)

        self.authentication_description = tkinter.Label(self, bg = "white", font= ("Arial", -14), text = "Enter the 6 digits given\nby your Authenticator App:")
        self.authentication_description.grid(row = 1, column = 0)

        self.authentication_entry = tkinter.Entry(self, bg = "white", font = ("Verdana", -20), width = 10)
        self.authentication_entry.grid(row = 2, column = 0)

        self.authentication_submit = tkinter.Button(self, text = "Submit")
        self.authentication_submit.grid(row = 3, column = 0)

class ClickerDashboard(tkinter.Frame):
    def __init__(self, master = None):
        

class Application(tkinter.Tk):
    """Tkinter-based GUI for interacting with a Neobux autoclicker"""
    TITLE_STRIP_BASE64 = ("iVBORw0KGgoAAAANSUhEUgAAAPoAAAABCAYAAAD3ubPnAAAARElEQVQokWNQ2+n+f8jibaH/1TYU"
                          "/Vdb1zAgWHpzw3/W/Q3/GY6SiQ/1/WfYs/o/w66dIxNvP/6fYePj/wzrP45iGmMAlwJeC/E1zLcA"
                          "AAAASUVORK5CYII=")

    def __init__(self, title = "clicker"):
        tkinter.Tk.__init__(self, None)
        icon = ImageTk.PhotoImage(data = b64decode(Neobux.FAVICON_BASE64))
        self.iconphoto(True, icon)
        self.title(title)
        self.config(bg = "#BBB")
        self.grid()
        self.init_widgets()
        self.grid_rowconfigure(1, weight = 1)
        self.grid_rowconfigure(3, weight = 1)
        self.grid_columnconfigure(0, weight = 1)
        self.grid_columnconfigure(2, weight = 1)
        # self.interface_connection, self.driver_connection = multiprocessing.Pipe()
        # self.driver = multiprocessing.Process(target = build_Neobux_driver, args = (self.driver_connection, ))
        # self.driver.start()
        self.authentication_prompt.grid(row = 2, column = 1)

    def init_widgets(self):
        self.init_title_strip()
        self.loading_animation = NeobuxLoadingGraphic()
        self.authentication_prompt = AuthenticationPrompt(self)
        self.captcha_prompt = CaptchaPrompt(self, self.authentication_prompt.grid)
        self.login_prompt = LoginPrompt(self, self.neobux_login)

    def init_title_strip(self):
        title_strip = Image.open(BytesIO(b64decode(Application.TITLE_STRIP_BASE64)))
        title_strip = title_strip.resize((350, 3))
        self.title_strip_image = ImageTk.PhotoImage(title_strip)
        self.title_strip = tkinter.Label(self, image = self.title_strip_image, bd = 0)
        self.title_strip.grid(row = 0, column = 1)

    def neobux_login(self):
        self.loading_animation.place()
        self.login_prompt.disable()
        # username, password, secondary_password = self.login_prompt.get_creds()
        # self.interface_connection.send(("data", "username", username))
        # self.interface_connection.send(("data", "password", password))
        # self.interface_connection.send(("data", "secondary_password", secondary_password))
        # self.loading_animation.grid(row = 1, column = 0)
        # self.interface_connection.send(("data", "page"))
        # page = self.interface_connection.recv()
        # if page == NeobuxPage.LOGIN:
        #     self.interface_connection.send(("data", "login_error"))
        #     self.login_status.config(text = self.interface_connection.recv())
        # elif page ==  NeobuxPage.VERIFICATION:
        #     self.login_prompt.grid_forget()
        # elif page == NeobuxPage.VIEW:
        #     pass
        # else:
        #     self.interface_connection.send(("method", "view_ads"))
        # self.loading_animation.forget()

    def destroy(self):
        try:
            self.interface_connection.send(("method", "exit_loop"))
        except:
            pass
        return super().destroy()

if __name__ == "__main__":
    clicker = Application(title = "Neobux Clicker")
    clicker.mainloop()
    # conn1, conn2 = multiprocessing.Pipe()
    # process = multiprocessing.Process(target = build_Neobux_driver, args = (conn2, ))
    # process.start()
    # conn1.send(("method", "launch", ))
    # conn1.send(("data", "username", "Djaenk"))
    # conn1.send(("data", "password", "1234!@#$qwerQWER"))
    # conn1.send(("data", "username"))
    # print(conn1.recv())
    # conn1.send(("data", "password"))
    # print(conn1.recv())
    # conn1.send(("method", "exit_loop"))