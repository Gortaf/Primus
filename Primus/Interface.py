# -*- coding: utf-8 -*-
"""
Created on Fri Apr 23 14:40:42 2021

@author: Nicolas

https://github.com/Gortaf
"""

# Generaly usefull stuff
from tqdm import tqdm

# UI stuff
import tkinter as tk
import tkinter.font as tkFont
import tkinter.ttk as ttk

# threading stuff
import concurrent.futures
import threading

# stuff from other files
from Browser import Browser, BrowserController


# A small class that wraps all of the software's information
class Infos():
    def __init__(self):
        self.version = "0.0.5 <BETA>"
        self.author = "Nicolas Jacquin"

# This class represents the main UI frame
class Interface(tk.Frame):
    def __init__(self, fenetre, *args, **kwargs):

        # Initialising browserController
        self.browser_controller = BrowserController(self, threads = 5)

        # Setting up the main frame informations & on_close event
        infos = Infos()
        self.fenetre = fenetre
        self.fenetre.title(f"Primus {infos.version}")
        self.fenetre.protocol("WM_DELETE_WINDOW", self.on_close)

        # Attributs referenced by widgets
        self.user_text = str()
        self.mdp_text = str()
        self.session_menu_text = tk.StringVar(self.fenetre)
        self.bg_col = "#2c2f33"  # lightmode hex: #f0f0ed
        self.bg_col_hover = "#23272a"
        self.is_working = False

        # packs the main frame with specific background color
        tk.Frame.__init__(self, self.fenetre, width=720, height=480, **kwargs)
        self.pack(fill=tk.BOTH)
        self.configure(bg=self.bg_col)

        # Adds subframs (divs) on the left and right of the main frame
        self.right_div = tk.Frame(self, borderwidth=3, relief=tk.RAISED)
        self.right_div.configure(bg=self.bg_col)
        self.right_div.grid(row=1, column=3)
        self.right_div.bind("<Enter>", lambda event: self.hover_in(event, self.right_div))
        self.right_div.bind("<Leave>", lambda event: self.hover_out(event, self.right_div))
        self.left_div = tk.Frame(self, borderwidth=3, relief=tk.RAISED)
        self.left_div.configure(bg=self.bg_col)
        self.left_div.grid(row=1, column=1, sticky=tk.N)
        self.left_div.bind("<Enter>", lambda event: self.hover_in(event, self.left_div))
        self.left_div.bind("<Leave>", lambda event: self.hover_out(event, self.left_div))
        self.left_bot_div = tk.Frame(self, borderwidth=3, relief=tk.RAISED)
        self.left_bot_div.configure(bg=self.bg_col)
        self.left_bot_div.grid(row=1, column=1)
        self.left_bot_div.bind("<Enter>", lambda event: self.hover_in(event, self.left_bot_div))
        self.left_bot_div.bind("<Leave>", lambda event: self.hover_out(event, self.left_bot_div))

        # Configure rows & column sizes for ui architecture
        self.grid_rowconfigure(0, minsize=40)
        self.grid_columnconfigure(0, minsize=30)
        self.grid_columnconfigure(2, minsize=40)
        self.grid_columnconfigure(4, minsize=40)
        self.grid_rowconfigure(2, minsize=40)

        # Input zones (Identifiant & Mot de passe)
        self.notice_label_inp = tk.Label(self.left_div, bg="#1a1818", text="↓ Entrer creditentiels ↓", fg="#ffffff", relief="ridge", borderwidth=2)
        self.notice_label_inp.grid(column=0, row=0, sticky=tk.N, pady=5, padx=5)
        self.mdp_row = TextField(self.left_div, default="Unip", password=True, textvariable=self.mdp_text, width=30)
        self.user_row = TextField(self.left_div, default="Identifiant", textvariable=self.user_text, width=30)
        self.user_row.grid(column=0, row=1, sticky=tk.N, pady=5, padx=10)
        self.mdp_row.grid(column=0, row=2, sticky=tk.S, pady=5, padx=10)

        self.val_cred_btn = tk.Button(self.left_div, text="Commencer", command=lambda: threading.Thread(target=self.first_sequence).start())
        self.val_cred_btn.grid(column=0, row=3, pady=5, padx=12)

        # Session selection zone
        self.notice_label_sess = tk.Label(self.left_bot_div, bg="#1a1818", text="En attente de connexion...", fg="#bfbcbb", relief="ridge", borderwidth=2)
        self.notice_label_sess.grid(column=0, row=0, padx=5, pady=5)
        self.session_menu = tk.OptionMenu(self.left_bot_div, self.session_menu_text, "")
        self.session_menu.configure(state=tk.DISABLED, width=24)
        self.session_menu.grid(column=0, row=1, pady=5, padx=5)
        self.val_sess_btn = tk.Button(self.left_bot_div, text="Selectionner", command=lambda: threading.Thread(target=self.second_sequence).start())
        self.val_sess_btn.configure(state=tk.DISABLED)
        self.val_sess_btn.grid(column=0, row=2, pady=5, padx=12)

        # Label de la sequence principale
        self.notice_label_main = tk.Label(self, bg="#1a1818", text="En attente de selection de sessions...", fg="#bfbcbb", relief="ridge", borderwidth=4)
        self.notice_label_main.grid(row=1, column=1, sticky=tk.S, pady=100)

        # Output zones
        self.session_label = tk.Label(self.right_div, bg="#1a1818", text="↓ Cours inscrits ↓", fg="#34ebe8", relief="ridge", borderwidth=2)
        self.session_label.grid(row=0, column=0, sticky=tk.N, columnspan=3)
        self.session_text = tk.Label(self.right_div, bg="white", fg="#30D6D4", width=35, height=8, padx=15, pady=15)
        self.session_text.grid(row=1, column=0, columnspan=3, padx=5)
        self.invalid_label = tk.Label(self.right_div, bg="#1a1818", text="↓ Cours invalides ↓", fg="#b80d1b", relief="ridge", borderwidth=2)
        self.invalid_label.grid(row=2, column=0, sticky=tk.S, padx=5, pady=2)
        self.invalid_text = tk.Label(self.right_div, text="", bg="white", fg="red", width=15, height=15, padx=15, pady=15)
        self.invalid_text.grid(row=3, column=0, padx=5)
        self.right_div.grid_columnconfigure(1, minsize=30)
        self.unknown_label = tk.Label(self.right_div, bg="#1a1818", text="↓ Cours inconnus ↓", fg="#f77707", relief="ridge", borderwidth=2)
        self.unknown_label.grid(row=2, column=2, sticky=tk.S, padx=5, pady=2)
        self.unknown_text = tk.Label(self.right_div, text="", bg="white", fg="orange", width=15, height=15, padx=15, pady=15)
        self.unknown_text.grid(row=3, column=2, padx=5)
        self.right_div.grid_rowconfigure(2, minsize=30)
        self.valid_label = tk.Label(self.right_div, bg="#1a1818", text="↓ Cours valides ↓", fg="#2bd918", relief="ridge", borderwidth=2)
        self.valid_label.grid(row=5, column=0, pady=2, columnspan=3)
        self.valid_text = tk.Label(self.right_div, text="", bg="white", fg="green", width=40, height=10, padx=15, pady=15)
        self.valid_text.grid(row=6, column=0, columnspan=3, padx=5)


    # Event for "hover in" effect on right & left div
    def hover_in(self, event, frame):
        frame.configure(bg=self.bg_col_hover)

    # Event for cancelling "hover in" effect on right & left div
    def hover_out(self, event, frame):
        frame.configure(bg=self.bg_col)

    # Called when the UI receive a termination signal
    def on_close(self):
        self.fenetre.destroy()
        self.browser_controller.end_sequence()

    # begins the first main sequence for connection and retrieving sessions
    def first_sequence(self):

        # Prevents double execution (should already be disabled, but you're never too sure)
        if self.is_working:
            return
        self.is_working = True

        # Disables the first field's entry points & changes label
        self.val_cred_btn.config(state=tk.DISABLED)
        self.user_row.config(state=tk.DISABLED)
        self.mdp_row.config(state=tk.DISABLED)
        self.notice_label_inp.configure(fg="#bfbcbb", text="En attente de synchro...")

        # Transfert creditentials to login page and attempts to connect
        user, unip = self.user_row.get(), self.mdp_row.get()
        result = self.browser_controller.login_sequence(user, unip)

        # Checks if the connection was a success
        if not result:
            # If connection failed, we re-enable the entry field for another try.
            self.val_cred_btn.config(state=tk.NORMAL)
            self.user_row.config(state=tk.NORMAL)
            self.mdp_row.config(state=tk.NORMAL)
            self.notice_label_inp.configure(fg="#ffffff", text="Échec... Essaie encore?")
            self.is_working = False
            return

        # Removes user's creditentials from RAM if connection was a success
        del user, unip

        # Updates the option menu for the second field and enables it
        self.notice_label_inp.configure(fg="#2bd918", text="Connexion établie!")
        self.notice_label_sess.configure(text="Récupération des sessions...")
        self.sessions = self.browser_controller.session_selection_sequence()
        for sess in self.sessions:
            self.session_menu["menu"].add_command(label=sess, command=tk._setit(self.session_menu_text, sess))

        self.session_menu_text.set(self.sessions[-1])
        self.session_menu.configure(state=tk.NORMAL)
        self.notice_label_sess.configure(fg="#ffffff", text="↓ Choisir une session ↓")
        self.val_sess_btn.configure(state=tk.NORMAL)

    def second_sequence(self):
        try:
            selection=self.sessions.index(self.session_menu_text.get())
        except ValueError:
            return

        # Disables the second field's entry points
        self.val_sess_btn.configure(state=tk.DISABLED)
        self.session_menu.configure(state=tk.DISABLED)
        self.notice_label_sess.configure(fg="#bfbcbb", text="Préparations en cours...")

        # Executer la selection de session et acquisition de la table de temps
        classes = self.browser_controller.session_timetable_sequence(selection)
        self.display_session_classes(classes)
        self.browser_controller.acquire_bloc_distribution_sequence()

        self.notice_label_sess.configure(fg="#2bd918", text="Préparations terminées!")
        self.notice_label_main.configure(fg="#ffffff", text="Séquence principale en cours!")

        self.browser_controller.main_extraction_sequence()

        self.notice_label_main.configure(fg="#2bd918", text="Séquence principale terminée!")

    def add_result(self, class_name, field):
        to_add = f"{class_name}  "
        if field == "valid":
            zone = self.valid_text
            max_chars = 30

        else:
            max_chars = 10
            if field == "invalid":
                zone = self.invalid_text

            elif field == "unknown":
                zone = self.unknown_text

        last_line = zone["text"].split("\n")[-1]
        if len(last_line+to_add) > max_chars:
            to_add+="\n"

        zone.configure(text=zone["text"]+to_add)

    def display_session_classes(self, classes):
        to_add = ""
        for i, cl in enumerate(classes):
            cl = cl[0:8].replace(" ", "")
            if i%4 == 0:
                to_add += "\n"
            if cl not in to_add:
                to_add += f"{cl}   "

        self.session_text.configure(text=to_add)

# A wrapper of tk.Entry for showing defaults
class TextField(tk.Entry):
    def __init__(self, frame, default=None, password=False, **kwargs):
        self.input_field = tk.Entry(frame, **kwargs)
        self.default = default
        self.password = password
        self.show_default()
        self.input_field.bind("<FocusIn>", self.hide_default)
        self.input_field.bind("<FocusOut>", self.show_default)

    def grid(self, row, column, **kwargs):
        self.input_field.grid(row=row, column=column, **kwargs)

    def pack(self, **kwargs):
        self.input_field.pack(**kwargs)

    def get(self, **kwargs):
        if self.showing_default:
            return ""
        else:
            return self.input_field.get(**kwargs)

    def config(self, **kwargs):
        self.input_field.config(**kwargs)

    def show_default(self, *args, **kwargs):
        if len(self.input_field.get()) != 0:
            return

        if self.password:
            self.config(show="")

        self.showing_default = True
        self.input_field.config(fg="#bbbfbd")
        self.input_field.delete(0, tk.END)
        self.input_field.insert(0, self.default)
        # self.input_field.text = self.default

    def hide_default(self, *args, **kwargs):
        if not self.showing_default:
            return

        if self.password:
            self.config(show="●")

        self.showing_default = False
        self.input_field.config(fg="black")
        self.input_field.delete(0, tk.END)

if __name__ == "__main__":
    ui = Interface(tk.Tk())
    ui.mainloop()