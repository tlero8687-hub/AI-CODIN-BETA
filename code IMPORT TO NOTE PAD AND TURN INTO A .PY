import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()
import os
import sys
import tempfile
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from openai import OpenAI

# ---------------- CONFIGURATION ----------------

APP_NAME = "CodePilot AI"
MODEL = "gpt-5.5"

BG = "#10131c"
PANEL = "#191e2b"
EDITOR_BG = "#111722"
ACCENT = "#8066ff"
TEXT = "#e6e9f2"
MUTED = "#929bb0"
GREEN = "#56d69a"
RED = "#ff647c"

client = OpenAI() if os.getenv("OPENAI_API_KEY") else None


# ---------------- MAIN APPLICATION ----------------

class CodePilot:

    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("1250x800")
        self.root.minsize(900, 600)
        self.root.configure(bg=BG)

        self.current_file = None
        self.chat_history = []

        self.setup_styles()
        self.build_ui()
        self.insert_welcome_code()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "TButton",
            background=PANEL,
            foreground=TEXT,
            padding=8,
            borderwidth=0
        )

        style.map(
            "TButton",
            background=[("active", ACCENT)]
        )

    # ---------------- INTERFACE ----------------

    def build_ui(self):

        # Top navigation
        top = tk.Frame(self.root, bg=PANEL, height=55)
        top.pack(fill="x")
        top.pack_propagate(False)

        tk.Label(
            top,
            text="⚡ CODEPILOT",
            bg=PANEL,
            fg=ACCENT,
            font=("Arial", 17, "bold")
        ).pack(side="left", padx=20)

        ttk.Button(
            top, text="New",
            command=self.new_file
        ).pack(side="left", padx=5, pady=8)

        ttk.Button(
            top, text="Open",
            command=self.open_file
        ).pack(side="left", padx=5, pady=8)

        ttk.Button(
            top, text="Save",
            command=self.save_file
        ).pack(side="left", padx=5, pady=8)

        ttk.Button(
            top, text="▶ RUN",
            command=self.run_code
        ).pack(side="right", padx=15, pady=8)

        # Main split
        main = tk.PanedWindow(
            self.root,
            orient=tk.HORIZONTAL,
            bg=BG,
            sashwidth=5,
            bd=0
        )
        main.pack(fill="both", expand=True, padx=10, pady=10)

        # LEFT: Editor and terminal
        left = tk.Frame(main, bg=PANEL)
        main.add(left, width=760)

        tk.Label(
            left,
            text="  EDITOR  /  Python",
            bg=PANEL,
            fg=MUTED,
            anchor="w",
            font=("Arial", 10, "bold")
        ).pack(fill="x", pady=8)

        editor_frame = tk.Frame(left, bg=EDITOR_BG)
        editor_frame.pack(fill="both", expand=True, padx=5)

        self.editor = tk.Text(
            editor_frame,
            bg=EDITOR_BG,
            fg=TEXT,
            insertbackground="white",
            selectbackground="#394366",
            font=("Consolas", 12),
            undo=True,
            wrap="none",
            padx=12,
            pady=12,
            borderwidth=0,
            tabs=4
        )
        self.editor.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(
            editor_frame,
            command=self.editor.yview
        )
        scrollbar.pack(side="right", fill="y")
        self.editor.configure(yscrollcommand=scrollbar.set)

        # Terminal
        tk.Label(
            left,
            text="  TERMINAL / OUTPUT",
            bg=PANEL,
            fg=MUTED,
            anchor="w",
            font=("Arial", 10, "bold")
        ).pack(fill="x", pady=(12, 5))

        self.output = tk.Text(
            left,
            height=10,
            bg="#0c1018",
            fg=GREEN,
            insertbackground="white",
            font=("Consolas", 10),
            padx=10,
            pady=8,
            borderwidth=0,
            state="disabled"
        )
        self.output.pack(fill="x", padx=5, pady=(0, 5))

        # RIGHT: AI assistant
        right = tk.Frame(main, bg=PANEL)
        main.add(right, width=380)

        tk.Label(
            right,
            text="  ✨ AI CODING ASSISTANT",
            bg=PANEL,
            fg=ACCENT,
            anchor="w",
            font=("Arial", 12, "bold")
        ).pack(fill="x", pady=12)

        self.chat = tk.Text(
            right,
            bg=EDITOR_BG,
            fg=TEXT,
            font=("Arial", 10),
            wrap="word",
            padx=12,
            pady=12,
            borderwidth=0,
            state="disabled"
        )
        self.chat.pack(fill="both", expand=True, padx=7)

        self.chat.tag_config("user", foreground="#a991ff")
        self.chat.tag_config("ai", foreground=GREEN)
        self.chat.tag_config("error", foreground=RED)

        # AI quick actions
        actions = tk.Frame(right, bg=PANEL)
        actions.pack(fill="x", padx=7, pady=8)

        ttk.Button(
            actions,
            text="Explain Code",
            command=lambda: self.quick_ai("Explain my code step by step.")
        ).pack(fill="x", pady=2)

        ttk.Button(
            actions,
            text="Find Bugs",
            command=lambda: self.quick_ai("Find bugs and suggest fixes in my code.")
        ).pack(fill="x", pady=2)

        ttk.Button(
            actions,
            text="Improve Code",
            command=lambda: self.quick_ai("Improve my code and explain the improvements.")
        ).pack(fill="x", pady=2)

        # Message input
        self.prompt = tk.Text(
            right,
            height=4,
            bg="#222a3b",
            fg=TEXT,
            insertbackground="white",
            font=("Arial", 10),
            wrap="word",
            padx=10,
            pady=8,
            borderwidth=0
        )
        self.prompt.pack(fill="x", padx=7, pady=(5, 5))

        ttk.Button(
            right,
            text="Send to AI  ➜",
            command=self.send_message
        ).pack(fill="x", padx=7, pady=(0, 10))

        self.status = tk.Label(
            self.root,
            text="● Ready",
            bg=BG,
            fg=GREEN,
            anchor="w",
            padx=15
        )
        self.status.pack(fill="x", pady=3)

    # ---------------- EDITOR ----------------

    def insert_welcome_code(self):
        code = '''# Welcome to CodePilot AI!

def greet(name):
    return f"Hello, {name}!"

print(greet("Developer"))

# Write your Python code here.
'''
        self.editor.insert("1.0", code)

    def get_code(self):
        return self.editor.get("1.0", "end-1c")

    def new_file(self):
        if messagebox.askyesno("New file", "Create a new file?"):
            self.editor.delete("1.0", "end")
            self.current_file = None
            self.root.title(APP_NAME)

    def open_file(self):
        path = filedialog.askopenfilename(
            filetypes=[
                ("Python files", "*.py"),
                ("All files", "*.*")
            ]
        )

        if path:
            try:
                with open(path, "r", encoding="utf-8") as file:
                    code = file.read()

                self.editor.delete("1.0", "end")
                self.editor.insert("1.0", code)
                self.current_file = path
                self.root.title(f"{APP_NAME} - {os.path.basename(path)}")
            except OSError as error:
                messagebox.showerror("Open error", str(error))

    def save_file(self):
        path = self.current_file

        if not path:
            path = filedialog.asksaveasfilename(
                defaultextension=".py",
                filetypes=[("Python files", "*.py")]
            )

        if path:
            try:
                with open(path, "w", encoding="utf-8") as file:
                    file.write(self.get_code())

                self.current_file = path
                self.root.title(f"{APP_NAME} - {os.path.basename(path)}")
                self.set_status("File saved", GREEN)
            except OSError as error:
                messagebox.showerror("Save error", str(error))

    # ---------------- RUN PYTHON ----------------

    def run_code(self):
        code = self.get_code()

        self.set_output("Running Python code...\n")
        self.set_status("Running...", ACCENT)

        threading.Thread(
            target=self.execute_code,
            args=(code,),
            daemon=True
        ).start()

    def execute_code(self, code):
        try:
            # Temporary working directory.
            # This is NOT a security sandbox.
            with tempfile.TemporaryDirectory(prefix="codepilot_") as folder:

                script = os.path.join(folder, "main.py")

                with open(script, "w", encoding="utf-8") as file:
                    file.write(code)

                result = subprocess.run(
                    [sys.executable, "-I", script],
                    cwd=folder,
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                output = result.stdout

                if result.stderr:
                    output += "\nERRORS:\n" + result.stderr

                if not output:
                    output = "Program finished with no output."

                if result.returncode != 0:
                    color = RED
                else:
                    color = GREEN

                self.root.after(
                    0,
                    lambda: self.set_output(output, color)
                )

                self.root.after(
                    0,
                    lambda: self.set_status("Execution finished", color)
                )

        except subprocess.TimeoutExpired:
            self.root.after(
                0,
                lambda: self.set_output(
                    "Execution stopped: 5 second time limit reached.",
                    RED
                )
            )
        except Exception as error:
            self.root.after(
                0,
                lambda: self.set_output(str(error), RED)
            )

    def set_output(self, text, color=GREEN):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("1.0", text)
        self.output.configure(fg=color, state="disabled")

    # ---------------- AI ASSISTANT ----------------

    def add_chat(self, sender, text):
        self.chat.configure(state="normal")

        tag = "user" if sender == "YOU" else "ai"

        self.chat.insert("end", f"\n{sender}\n", tag)
        self.chat.insert("end", text + "\n\n")

        self.chat.see("end")
        self.chat.configure(state="disabled")

    def quick_ai(self, instruction):
        self.prompt.delete("1.0", "end")
        self.prompt.insert("1.0", instruction)
        self.send_message()

    def send_message(self):
        question = self.prompt.get("1.0", "end-1c").strip()

        if not question:
            return

        if not client:
            self.add_chat(
                "AI",
                "AI is not configured yet.\n\n"
                "Set your OPENAI_API_KEY environment variable "
                "and restart CodePilot."
            )
            return

        self.prompt.delete("1.0", "end")

        self.add_chat("YOU", question)
        self.set_status("AI is thinking...", ACCENT)

        code = self.get_code()

        threading.Thread(
            target=self.ask_ai,
            args=(question, code),
            daemon=True
        ).start()

    def ask_ai(self, question, code):
        try:
            response = client.responses.create(
                model=MODEL,
                instructions=(
                    "You are CodePilot, a friendly expert Python coding "
                    "assistant. Help the user learn programming. "
                    "Explain errors clearly. Give working Python examples. "
                    "When asked to fix code, provide the complete corrected "
                    "code in a Python code block. Do not claim to have "
                    "changed the editor automatically."
                ),
                input=(
                    f"CURRENT PYTHON CODE:\n"
                    f"```python\n{code}\n```\n\n"
                    f"USER QUESTION:\n{question}"
                )
            )

            answer = response.output_text

            self.root.after(
                0,
                lambda: self.add_chat("AI", answer)
            )

            self.root.after(
                0,
                lambda: self.set_status("AI ready", GREEN)
            )

        except Exception as error:
            self.root.after(
                0,
                lambda: self.add_chat("AI", f"API error: {error}")
            )
            self.root.after(
                0,
                lambda: self.set_status("AI error", RED)
            )

    def set_status(self, message, color):
        self.status.configure(
            text=f"● {message}",
            fg=color
        )


# ---------------- START APP ----------------

if __name__ == "__main__":
    root = tk.Tk()
    app = CodePilot(root)
    root.mainloop()
