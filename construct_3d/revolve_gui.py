#!/usr/bin/env python3
"""
revolve_gui.py

Tkinter-based GUI for revolve_path_from_file_about_axis.
Run directly:
    python3 construct_3d/revolve_gui.py
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox
from revolve_about_axis import revolve_path_from_file_about_axis


def launch_gui():
    root = tk.Tk()
    root.title('Revolve About Axis')

    # Input file
    tk.Label(root, text='Input SVG file:').grid(row=0, column=0, sticky='e')
    input_var = tk.StringVar()
    tk.Entry(root, textvariable=input_var, width=40).grid(row=0, column=1)
    def browse_input():
        path = filedialog.askopenfilename(filetypes=[('SVG files', '*.svg')])
        if path:
            input_var.set(path)
    tk.Button(root, text='Browse...', command=browse_input).grid(row=0, column=2)

    # Output file
    tk.Label(root, text='Output SVG file:').grid(row=1, column=0, sticky='e')
    output_var = tk.StringVar()
    tk.Entry(root, textvariable=output_var, width=40).grid(row=1, column=1)
    def browse_output():
        path = filedialog.asksaveasfilename(defaultextension='.svg', filetypes=[('SVG files', '*.svg')])
        if path:
            output_var.set(path)
    tk.Button(root, text='Browse...', command=browse_output).grid(row=1, column=2)

    # Number of faces
    tk.Label(root, text='Number of faces:').grid(row=2, column=0, sticky='e')
    faces_var = tk.IntVar(value=4)
    tk.OptionMenu(root, faces_var, 2, 4, 8, 16, 32).grid(row=2, column=1, sticky='w')

    # Material thickness
    tk.Label(root, text='Material thickness (mm):').grid(row=3, column=0, sticky='e')
    thickness_var = tk.DoubleVar(value=3.175)
    tk.Entry(root, textvariable=thickness_var).grid(row=3, column=1, sticky='w')

    # Buffer size
    tk.Label(root, text='Buffer size (mm):').grid(row=4, column=0, sticky='e')
    buffer_var = tk.DoubleVar(value=1.0)
    tk.Entry(root, textvariable=buffer_var).grid(row=4, column=1, sticky='w')

    def run_revolve():
        in_file = input_var.get()
        out_file = output_var.get()
        if not in_file or not out_file:
            messagebox.showerror('Error', 'Please select both input and output files.')
            return
        if not os.path.isfile(in_file):
            messagebox.showerror('Error', f'Input file does not exist:\n{in_file}')
            return
        try:
            faces = int(faces_var.get())
            thickness = float(thickness_var.get())
            buffer = float(buffer_var.get())
        except Exception:
            messagebox.showerror('Error', 'Invalid numeric input.')
            return
        try:
            revolve_path_from_file_about_axis(in_file, out_file, faces, thickness, buffer)
            messagebox.showinfo('Success', f'Output saved to {out_file}')
        except Exception as e:
            messagebox.showerror('Error', f'Failed: {e}')

    tk.Button(root, text='Run', command=run_revolve).grid(row=5, column=1, pady=10)

    root.mainloop()


if __name__ == '__main__':
    launch_gui()