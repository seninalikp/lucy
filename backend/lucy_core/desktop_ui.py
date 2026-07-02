"""
desktop_ui.py
Tkinter desktop interface for Lucy.
"""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, simpledialog, ttk

from backend.lucy_core.router import CommandRouter


class LucyDesktopApp:
    def __init__(self, runtime) -> None:
        self.runtime = runtime
        self.router = CommandRouter(runtime)

        self.root = tk.Tk()
        self.root.title("Lucy Desktop")
        self.root.minsize(860, 560)

        self.command_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Lucy Desktop is online")

        self._build_layout()
        self._append("Lucy", "Desktop UI online. Type a command or use the controls.")
        self._append("Lucy", self.router.handle("dashboard").message)

    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        top = ttk.Frame(self.root, padding=(12, 10))
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(0, weight=1)

        title = ttk.Label(top, text="LUCY", font=("Segoe UI", 16, "bold"))
        title.grid(row=0, column=0, sticky="w")
        status = ttk.Label(top, textvariable=self.status_var)
        status.grid(row=1, column=0, sticky="w", pady=(2, 0))

        controls = ttk.Frame(top)
        controls.grid(row=0, column=1, rowspan=2, sticky="e")
        ttk.Button(controls, text="Dashboard", command=lambda: self._run_command("dashboard")).grid(row=0, column=0, padx=3)
        ttk.Button(controls, text="Health", command=lambda: self._run_command("health")).grid(row=0, column=1, padx=3)
        ttk.Button(controls, text="Learning", command=lambda: self._run_command("learning status")).grid(row=0, column=2, padx=3)
        ttk.Button(controls, text="NVIDIA Key", command=self._setup_nvidia_key).grid(row=0, column=3, padx=3)
        ttk.Button(controls, text="Fallback", command=self._memory_fallback_dialog).grid(row=0, column=4, padx=3)
        ttk.Button(controls, text="Overnight 100", command=self._confirm_overnight).grid(row=0, column=5, padx=3)

        self.output = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Consolas", 10),
        )
        self.output.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 8))

        bottom = ttk.Frame(self.root, padding=(12, 0, 12, 12))
        bottom.grid(row=2, column=0, sticky="ew")
        bottom.columnconfigure(0, weight=1)

        entry = ttk.Entry(bottom, textvariable=self.command_var)
        entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        entry.bind("<Return>", lambda _event: self._submit())
        entry.focus_set()

        ttk.Button(bottom, text="Send", command=self._submit).grid(row=0, column=1)

    def _append(self, speaker: str, text: str) -> None:
        self.output.configure(state=tk.NORMAL)
        self.output.insert(tk.END, f"{speaker}> {text.strip()}\n\n")
        self.output.see(tk.END)
        self.output.configure(state=tk.DISABLED)

    def _set_status(self, text: str) -> None:
        self.status_var.set(text)

    def _submit(self) -> None:
        command = self.command_var.get().strip()
        if not command:
            return
        self.command_var.set("")
        if command.lower() in {"setup nvidia key", "nvidia setup", "nvidia key"}:
            self._setup_nvidia_key()
            return
        self._run_command(command)

    def _run_command(self, command: str) -> None:
        self._append("You", command)
        self._set_status(f"Running: {command}")
        thread = threading.Thread(target=self._handle_command_thread, args=(command,), daemon=True)
        thread.start()

    def _handle_command_thread(self, command: str) -> None:
        try:
            response = self.router.handle(command)
            message = response.message
        except Exception as exc:
            message = f"Lucy desktop error: {exc}"
        self.root.after(0, lambda: self._finish_command(message))

    def _finish_command(self, message: str) -> None:
        self._append("Lucy", message)
        self._set_status("Ready")

    def _setup_nvidia_key(self) -> None:
        value = simpledialog.askstring(
            "NVIDIA Key",
            "Paste NVIDIA_API_KEY. Lucy saves it encrypted for this Windows user.",
            show="*",
            parent=self.root,
        )
        if value is None:
            self._append("Lucy", "NVIDIA key setup cancelled.")
            return
        result = self.runtime.set_nvidia_key(value, permanent=True)
        if result.get("saved"):
            self._append(
                "Lucy",
                "NVIDIA key saved permanently as an encrypted local secret. It was not saved to memory, logs, or config.",
            )
        else:
            self._append("Lucy", f"NVIDIA key not saved: {result.get('reason', 'unknown reason')}")

    def _memory_fallback_dialog(self) -> None:
        query = simpledialog.askstring(
            "Memory Fallback",
            "Ask Lucy what local memory should fall back on.",
            parent=self.root,
        )
        if query:
            self._run_command(f"memory fallback {query}")

    def _confirm_overnight(self) -> None:
        ok = messagebox.askyesno(
            "Overnight 100",
            "Create enough safe local checkpoint records to reach 100 total?",
            parent=self.root,
        )
        if ok:
            self._run_command("overnight checkpoints 100")

    def run(self) -> None:
        self.root.mainloop()


def run_desktop_ui(runtime) -> None:
    app = LucyDesktopApp(runtime)
    app.run()
