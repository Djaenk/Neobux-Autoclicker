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

class TableFrame(ttk.Frame):
    def __init__(self, master = None, **options):
        ttk.Frame.__init__(self, master, **options)
        
    def format(self, rows, columns):
        self.rows = rows
        self.columns = columns
        for i in range(self.rows):
            self.rowconfigure(i, weight = 1)
            for j in range(self.columns):
                self.columnconfigure(j, weight = 1)
                cellname = "row" + str(i) + "column" + str(j)
                setattr(self, cellname, ttk.Frame(self))
                cell = getattr(self, cellname)
                cell.grid(row = i, column = j, sticky = tkinter.NSEW)

    def update(self, data):
        self.data = data  
        self._label_table()
        self._populate_table()

    def _label_table(self):
        for i in range(self.rows):
            cell = getattr(self, "row" + str(i) + "column0")
            cell.label = ttk.Label(cell, text = list(self.data.keys())[i])
            cell.label.grid(sticky = tkinter.W)

    def _populate_table(self):
        for i in range(self.rows):
            if self.columns == 2:
                cell = getattr(self, "row" + str(i) + "column1")
                cell.label = ttk.Label(cell, text = list(self.data.values())[i])
                cell.label.grid(sticky = tkinter.E)
            else:
                for j in range(1, self.columns):
                    cell = getattr(self, "row" + str(i) + "column" + str(j))
                    cell.label = ttk.Label(cell, text = list(list(self.data.values())[i].values())[j - 1])
                    cell.label.grid(sticky = tkinter.E)

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

class ClickerDashboard(tkinter.Frame):
    def __init__(self, master = None):
        # Initial Window Setup
        tkinter.Frame.__init__(self, master)
        icon = ImageTk.PhotoImage(data = b64decode(Neobux.FAVICON_BASE64))
        self.master.iconphoto(False, icon)
        self.master.title("Neobux Clicker")

        # Banner Initialization
        req = Request('https://www.neobux.com/imagens/banner7.gif', headers={'User-Agent': 'Mozilla/5.0'})
        self.banner = ImageTk.PhotoImage(data = urlopen(req).read())
        self.linked_banner = tkinter.Button(self, bd = 0, highlightthickness = 0,
            relief = tkinter.FLAT, image = self.banner, cursor = "hand2",
            command = lambda : webbrowser.open_new("https://www.neobux.com/?rh=446A61656E6B"))
        self.linked_banner.grid(row = 0, column = 0, columnspan = 2, pady = (0, 5))
        
        # Advertisements Table
        self.advertisements = ttk.LabelFrame(self, text = "Available Advertisements")
        self.advertisements.grid(row = 1, column = 1, sticky = tkinter.EW)
        self.advertisements.columnconfigure(0, weight = 1)
        self.advertisements.table = TableFrame(self.advertisements)
        self.advertisements.table.format(8, 2)
        self.advertisements.table.grid(row = 0, column = 0, rowspan = 3, sticky = tkinter.EW)
        
        # Summary Table
        self.summary = ttk.LabelFrame(self, text = "Account Summary")
        self.summary.grid(row = 2, column = 0, sticky = tkinter.EW)
        self.summary.columnconfigure(0, weight = 1)
        self.summary.table = TableFrame(self.summary)
        self.summary.table.format(6, 2)
        self.summary.table.grid(row = 0, column = 0, sticky = tkinter.EW)
        self.summary.refresh = ttk.Button(self.summary, text = "Refresh")
        self.summary.refresh.grid(row = 1, column = 0)
        
        # Statistics Table
        self.statistics = ttk.LabelFrame(self, text = "10-Day Statistics")
        self.statistics.grid(row = 2, column = 1, sticky = tkinter.EW)
        self.statistics.columnconfigure(0, weight = 1)
        self.statistics.table = TableFrame(self.statistics)
        self.statistics.table.format(6, 3)
        self.statistics.table.grid(row = 0, column = 0, sticky = tkinter.EW)
        self.statistics.refresh = ttk.Button(self.statistics, text = "Refresh")
        self.statistics.refresh.grid(row = 1, column = 0)
        
        # Clicker Interface
        self.start = ttk.Button(self, text = "Start")
        self.interface = ttk.Frame(self)
        self.interface.login = ttk.Button(self.interface, text = "Login")
        self.interface.login.grid(row = 0, column = 0)
        self.interface.start = ttk.Button(self.interface, text = "Start")
        self.interface.start.grid(row = 1, column = 0)
        self.interface.stop = ttk.Button(self.interface, text = "Stop")
        self.interface.stop.grid(row = 2, column = 0)
        # self.interface_connection, self.driver_connection = multiprocessing.Pipe()
        # self.driver = multiprocessing.Process(target = build_Neobux_driver, args = (self.driver_connection, ))
        # self.driver.start()
        self.interface.grid(row = 1, column = 0)
        self.grid()

    def update_advertisements(self, dict):
        dict = {
            "stale" : 0,
            "unique" : 0,
            "fixed" : 0,
            "micro" : 0,
            "mini" : 0,
            "standard" : 0,
            "extended" : 0,
            "adprize" : 0
        }
        self.advertisements.table.update(dict)

    def update_summary(self, dict):
        dict = {
            "membership" : "",
            "member since" : "",
            "seen advertisements" : 0,
            "main balance" : 0,
            "rental balance" : 0,
            "points" : 0
        }
        self.summary.table.update(dict)
        print(self.summary.table.columns)

    def update_statistics(self, dict):
        dict = {
            "unique" : {"Clicks" : 0, "Average" : 0},
            "fixed" : {"Clicks" : 0, "Average" : 0},
            "micro" : {"Clicks" : 0, "Average" : 0},
            "mini" : {"Clicks" : 0, "Average" : 0},
            "standard" : {"Clicks" : 0, "Average" : 0},
            "extended" : {"Clicks" : 0, "Average" : 0}
        }
        self.statistics.table.update(dict)

    def disable(self):
        self.advertisements.refresh.state(["disabled"])
        self.summary.refresh.state(["disabled"])
        self.statistics.refresh.state(["disabled"])

    def enable(self):
        self.advertisements.refresh.state(["!disabled"])
        self.summary.refresh.state(["!disabled"])
        self.statistics.refresh.state(["!disabled"])

class NeobuxGUI(tkinter.Frame):
    """Tkinter-based GUI for interacting with a Neobux autoclicker"""

    def __init__(self, title = "clicker"):
        tkinter.Frame.__init__(self)
        icon = ImageTk.PhotoImage(data = b64decode(Neobux.FAVICON_BASE64))
        self.master.iconphoto(False, icon)
        self.master.title(title)
        self.config(bg = "white")
        self._init_widgets()
        self.grid_rowconfigure(0, weight = 1)
        self.grid_rowconfigure(2, weight = 1)
        self.grid_columnconfigure(0, weight = 1)
        self.grid_columnconfigure(2, weight = 1)
        # self.interface_connection, self.driver_connection = multiprocessing.Pipe()
        # self.driver = multiprocessing.Process(target = build_Neobux_driver, args = (self.driver_connection, ))
        # self.driver.start()
        self.advertisements.grid(row = 1, column = 1)
        self.grid()

    def _init_widgets(self):
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
        self.advertisements = ClickerDashboard(self)

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
    clicker = ClickerDashboard()
    clicker.update_advertisements(" ")
    clicker.update_statistics(" ")
    clicker.update_summary(" ")
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
