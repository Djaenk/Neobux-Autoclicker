from Neobux import Neobux
from Neobux import NeobuxPage

import tkinter
from tkinter import ttk

import multiprocessing

from PIL import Image
from PIL import ImageTk
from PIL.PngImagePlugin import PngImageFile
from urllib.request import Request, urlopen
from base64 import b64decode
from io import BytesIO

import webbrowser

def build_Neobux_driver(connection):
    Neobux(None, True, connection).mainloop()

class LabeledEntry(ttk.Frame):

    def __init__(self, master = None, label = None, showinput = True, exportselection = 1):
        ttk.Frame.__init__(self, master)
        self.label = ttk.Label(self, text = label, font = ("Segoe UI", -16))
        self.label.grid(row = 0, column = 0)
        self.entry = ttk.Entry(self, exportselection = exportselection, font = ("Trebuchet MS", -14, "bold"))
        if not showinput:
            self.entry["show"] = u"\u2022"
        self.entry.grid(row = 0, column = 1)

    def get(self):
        return self.entry.get()

    def disable(self):
        self.label.state(["disabled"])
        self.entry.state(["disabled"])

    def enable(self):
        self.label.state(["!disabled"])
        self.entry.state(["!disabled"])

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
        
class LoginPrompt(ttk.Frame):
    def __init__(self, master = None, submit = None):
        ttk.Frame.__init__(self, master)
        ttk.Style().configure("Error.TLabel", foreground = "red")
        self.login_label = ttk.Label(self, text = "Neobux Member Login", font = ("Verdana", -20, "bold"))
        self.login_label.grid(row = 0, column = 0)
        self.login_status = ttk.Label(self, style = "Error.TLabel")
        self.login_status.grid(row = 1, column = 0, pady = (10,5))
        self.username_entry = LabeledEntry(self, "Username: ")
        self.username_entry.grid(row = 2, column = 0, pady = (0,1), sticky = tkinter.E)
        self.password_entry = LabeledEntry(self, "Password: ", False, 0)
        self.password_entry.grid(row = 3, column = 0, pady = (0,1), sticky = tkinter.E)
        self.secondary_password_entry = LabeledEntry(self, "Secondary Password: ", False, 0)
        self.secondary_password_entry.grid(row = 4, column = 0, pady = (0,1), sticky = tkinter.E)     
        self.login_submit = ttk.Button(self, text = "Submit", command = submit)
        self.login_submit.grid(row = 5, column = 0, pady = (10, 5))

    def disable(self):
        self.login_status["text"] = ""
        self.username_entry.disable()
        self.password_entry.disable()
        self.secondary_password_entry.disable()

    def enable(self):
        self.username_entry.enable()
        self.password_entry.enable()
        self.secondary_password_entry.enable()

    def set_status(self, status = ""):
        self.login_status["text"] = status

    def get(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        secondary_password = self.secondary_password_entry.get()
        return username, password, secondary_password

class CaptchaPrompt(ttk.Frame):
    def __init__(self, master = None, submit = None):
        ttk.Frame.__init__(self, master)
        self.captcha_label = ttk.Label(self, text = "Verification", font=("Verdana", -20, "bold"))
        self.captcha_label.grid(row = 0, column = 0, columnspan = 2)
        self.captcha_description = ttk.Label(self, text = "Enter the letters you see below:\n", justify = tkinter.CENTER)
        self.captcha_description.grid(row = 1, column = 0, columnspan = 2, pady = (15, 5))
        self.captcha = ImageTk.PhotoImage(file = "example captcha.png")
        self.captcha_image = ttk.Label(self, image = self.captcha)
        self.captcha_image.grid(row = 2, column = 0, padx = (0, 3))
        self.captcha_entry = ttk.Entry(self, font = ("Verdana", -15), width = 9)
        self.captcha_entry.grid(row = 2, column = 1)
        self.captcha_submit = ttk.Button(self, text = "Submit", command = submit)
        self.captcha_submit.grid(row = 3, column = 0, columnspan = 2, pady = (10, 5))

    def set_captcha(self, captcha):
        if isinstance(captcha, ImageTk.PhotoImage):
            self.captcha = captcha
        if isinstance(captcha, PngImageFile):
            self.captcha = ImageTk.PhotoImage(captcha)

    def set_status(self, status):
        self.captcha_label["text"] = "Enter the letters you see below:\n" + status

    def get(self):
        return self.captcha_entry.get()

class AuthenticationPrompt(ttk.Frame):
    def __init__(self, master = None, submit = None):
        ttk.Frame.__init__(self, master)
        self.authentication_label = ttk.Label(self, text = "Two-Factor Authentication", font = ("Verdana", -20, "bold"))
        self.authentication_label.grid(row = 0, column = 0)
        self.authentication_description = ttk.Label(self, text = "Enter the six digits given by your authenticator app:\n")
        self.authentication_description.grid(row = 1, column = 0, pady = (15, 5))
        self.authentication_entry = ttk.Entry(self, font = ("Verdana", -16), width = 10)
        self.authentication_entry.grid(row = 2, column = 0)
        self.authentication_submit = ttk.Button(self, text = "Submit")
        self.authentication_submit.grid(row = 3, column = 0, pady = (10, 5))

    def set_status(self, status):
        self.captcha_label["text"] = "Enter the six digits given by your authenticator app:\n" + status

    def get(self):
        return self.authentication_entry.get()

class ClickerDashboard(ttk.Frame):
    def __init__(self, master = None):
        ttk.Frame.__init__(self, master)
        req = Request('https://www.neobux.com/imagens/banner3.gif', headers={'User-Agent': 'Mozilla/5.0'})
        self.banner = ImageTk.PhotoImage(data = urlopen(req).read())
        self.linked_banner = tkinter.Button(self, bd = 0, relief = tkinter.SUNKEN, image = self.banner, command = lambda : webbrowser.open_new("https://www.neobux.com/?rh=446A61656E6B"))
        self.linked_banner.grid()
        self.summary_table = ttk.LabelFrame(self, text = "Account Summary")
        self.summary_table.grid(row = 1)
        for i in range(6):
            setattr(self.summary_table, "row" + str(i), ttk.Frame(self.summary_table))
            for j in range(2):
                row = getattr(self.summary_table, "row" + str(i))
                setattr(row, "column" + str(j), ttk.Label(row, text = "cell"))
                cell = getattr(row, "column" + str(j))
                cell.grid()
        self.statistics_table = ttk.LabelFrame(self, text = "10-day Statistics")
        self.statistics_table.grid()
        for i in range(7):
            setattr(self.statistics_table, "row" + str(i), ttk.Frame(self.statistics_table))
            for j in range(3):
                row = getattr(self.statistics_table, "row" + str(i))
                setattr(row, "column" + str(j), ttk.Label(row, text = "cell"))
                cell = getattr(row, "column" + str(j))
                cell.grid()

    def populate_summary(self, summary):
        self.summary_table.row0.column0["text"] = "Membership:"
        self.summary_table.row0.column1["text"] = summary["membership"]
        self.summary_table.row1.column0["text"] = "Member Since:"
        self.summary_table.row1.column1["text"] = summary["since"]
        self.summary_table.row2.column0["text"] = "Seen Advertisements:"
        self.summary_table.row2.column1["text"] = summary["seen"]
        self.summary_table.row3.column0["text"] = "Main Balance:"
        self.summary_table.row3.column1["text"] = summary["main_balance"]
        self.summary_table.row4.column0["text"] = "Rental Balance:"
        self.summary_table.row4.column1["text"] = summary["rental_balance"]
        self.summary_table.row5.column0["text"] = "Points:"
        self.summary_table.row5.column1["text"] = summary["points"]

    def populate_statistics(self, data):
        for i in range(6):
            setattr(self.statistics_table, "row" + str(i), ttk.Label())

class NeobuxGUI(tkinter.Frame):
    """Tkinter-based GUI for interacting with a Neobux autoclicker"""

    def __init__(self, title = "clicker"):
        tkinter.Frame.__init__(self)
        icon = ImageTk.PhotoImage(data = b64decode(Neobux.FAVICON_BASE64))
        self.master.iconphoto(False, icon)
        self.master.title(title)
        self.config(bg = "white")
        self.init_widgets()
        self.grid_rowconfigure(0, weight = 1)
        self.grid_rowconfigure(2, weight = 1)
        self.grid_columnconfigure(0, weight = 1)
        self.grid_columnconfigure(2, weight = 1)
        # self.interface_connection, self.driver_connection = multiprocessing.Pipe()
        # self.driver = multiprocessing.Process(target = build_Neobux_driver, args = (self.driver_connection, ))
        # self.driver.start()
        self.dashboard.grid(row = 1, column = 1)
        self.grid()

    def init_widgets(self):
        self.prompt_frame = ttk.Frame(self, width = 400, height = 225)
        self.prompt_frame.grid_rowconfigure(0, weight = 1)
        self.prompt_frame.grid_rowconfigure(2, weight = 1)
        self.prompt_frame.grid_columnconfigure(0, weight = 1)
        self.prompt_frame.grid_columnconfigure(2, weight = 1)
        self.prompt_frame.grid_propagate(False)
        self.loading_animation = NeobuxLoadingGraphic()
        self.authentication_prompt = AuthenticationPrompt(self.prompt_frame)
        self.captcha_prompt = CaptchaPrompt(self.prompt_frame, self.authentication_prompt.grid)
        self.login_prompt = LoginPrompt(self.prompt_frame, self.captcha_prompt.grid)
        self.dashboard = ClickerDashboard(self)

    def show_prompt(self, prompt):
        for child in self.prompt_frame.winfo_children:
            child.grid_forget()
        prompt.grid(row = 1, column = 1)

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
    clicker = NeobuxGUI(title = "Neobux Clicker")
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
