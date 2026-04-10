#!/usr/bin/env python3
"""
revolve_gui.py

Tkinter-based GUI for revolve_about_axis.py
Run directly:
    python3 construct_3d/revolve_gui.py
"""


import os
import io
import tkinter as tk
from tkinter import filedialog, messagebox
from revolve_about_axis import revolve_path_from_file_about_axis_and_save



class RevolveGUI:

    def __init__(self, root, show_preview):
        self.root = root
        self.show_preview = show_preview
        root.title('Revolve About Axis')
        root.minsize(450, 100)

        # Input file
        tk.Label(root, text='Input SVG file:').grid(row=0, column=0, sticky='e')
        self.input_var = tk.StringVar()
        self.input_entry = tk.Entry(root, textvariable=self.input_var)
        self.input_entry.grid(row=0, column=1, sticky='ew')
        def browse_input():
            path = filedialog.askopenfilename(filetypes=[('SVG files', '*.svg')])
            if path:
                self.input_var.set(path)
        tk.Button(root, text='Browse...', command=browse_input).grid(row=0, column=2)

        # Output file
        tk.Label(root, text='Output SVG file:').grid(row=1, column=0, sticky='e')
        self.output_var = tk.StringVar()
        self.output_entry = tk.Entry(root, textvariable=self.output_var)
        self.output_entry.grid(row=1, column=1, sticky='ew')
        def browse_output():
            path = filedialog.asksaveasfilename(defaultextension='.svg', filetypes=[('SVG files', '*.svg')])
            if path:
                self.output_var.set(path)
        tk.Button(root, text='Browse...', command=browse_output).grid(row=1, column=2)

        # Number of faces
        tk.Label(root, text='Number of faces:').grid(row=2, column=0, sticky='e')
        self.faces_var = tk.StringVar(value="4")
        tk.OptionMenu(root, self.faces_var, "2", "4", "8", "16", "32").grid(row=2, column=1, sticky='w')

        # Material thickness
        tk.Label(root, text='Material thickness (mm):').grid(row=3, column=0, sticky='e')
        self.thickness_var = tk.DoubleVar(value=3.175)
        tk.Entry(root, textvariable=self.thickness_var).grid(row=3, column=1, sticky='w')

        # Buffer size
        tk.Label(root, text='Buffer size (mm):').grid(row=4, column=0, sticky='e')
        self.buffer_var = tk.DoubleVar(value=0.1)
        tk.Entry(root, textvariable=self.buffer_var).grid(row=4, column=1, sticky='w')

        # Max width (optional)
        tk.Label(root, text='Max width (mm, optional):').grid(row=5, column=0, sticky='e')
        self.max_width_var = tk.StringVar(value='')
        tk.Entry(root, textvariable=self.max_width_var).grid(row=5, column=1, sticky='w')

        tk.Button(root, text='Run', command=self.run_revolve).grid(row=6, column=1, pady=10)

        # Make columns 1 (entries) expand with window
        root.grid_columnconfigure(1, weight=2)

        if self.show_preview:
            # SVG Preview in a Frame with Canvas
            self.preview_frame = tk.Frame(root)
            self.preview_frame.grid(row=7, column=0, columnspan=3, pady=10, sticky='nsew')
            self.preview_canvas = tk.Canvas(self.preview_frame, bg='white', highlightthickness=1, highlightbackground='#cccccc')
            self.preview_canvas.pack(fill='both', expand=True)
            # Make the preview frame expandable
            root.grid_rowconfigure(7, weight=1)
            root.grid_columnconfigure(1, weight=1)

            # Bind resize event

            # Debounce for resize events
            self._resize_after_id = None
            self.preview_frame.bind('<Configure>', self.on_preview_resize)

            # Bind parameter changes to preview update
            self.input_var.trace_add('write', lambda *args: self.update_preview())
            self.faces_var.trace_add('write', lambda *args: self.update_preview())
            self.thickness_var.trace_add('write', lambda *args: self.update_preview())
            self.buffer_var.trace_add('write', lambda *args: self.update_preview())
            self.max_width_var.trace_add('write', lambda *args: self.update_preview())

    def run_revolve(self):
        in_file = self.input_var.get()
        out_file = self.output_var.get()
        if not in_file or not out_file:
            messagebox.showerror('Error', 'Please select both input and output files.')
            return
        if not os.path.isfile(in_file):
            messagebox.showerror('Error', f'Input file does not exist:\n{in_file}')
            return
        try:
            faces = int(self.faces_var.get())
            thickness = float(self.thickness_var.get())
            buffer = float(self.buffer_var.get())
            max_width_str = self.max_width_var.get().strip()
            max_width = float(max_width_str) if max_width_str else None
        except Exception:
            messagebox.showerror('Error', 'Invalid numeric input.')
            return
        try:
            revolve_path_from_file_about_axis_and_save(in_file, out_file, faces, thickness, buffer, max_width)
            messagebox.showinfo('Success', f'Output saved to {out_file}')
        except Exception as e:
            messagebox.showerror('Error', f'Failed: {e}')


    def on_preview_resize(self, event):
        # Debounce rapid resize events
        if self._resize_after_id is not None:
            self.root.after_cancel(self._resize_after_id)
        self._resize_after_id = self.root.after(150, lambda: self.update_preview(event.width, event.height))

    def update_preview(self, width=None, height=None):
        # Use current frame size if not provided
        if width is None or height is None:
            width = self.preview_frame.winfo_width()
            height = self.preview_frame.winfo_height()
            # Fallback to default if not mapped yet
            if width < 50 or height < 50:
                width = 400
                height = 400
        # Ignore tiny sizes to avoid feedback loop
        if width < 50 or height < 50:
            return
        in_file = self.input_var.get()
        if not os.path.isfile(in_file):
            self.preview_canvas.delete('all')
            return
        try:
            from PIL import Image, ImageTk
            import cairosvg
            # Generate SVG to a temp file
            tmp_svg = 'preview_tmp.svg'
            max_width_str = self.max_width_var.get().strip()
            max_width = float(max_width_str) if max_width_str else None
            revolve_path_from_file_about_axis_and_save(
                in_file, tmp_svg,
                int(self.faces_var.get()),
                float(self.thickness_var.get()),
                float(self.buffer_var.get()),
                max_width
            )
            # Convert SVG to PNG in memory, scaled to fit the frame
            png_bytes = cairosvg.svg2png(url=tmp_svg, output_width=width, output_height=height)
            image = Image.open(io.BytesIO(png_bytes))
            photo = ImageTk.PhotoImage(image)
            self.preview_canvas.delete('all')
            self.preview_canvas.create_image(0, 0, anchor='nw', image=photo)
            self.preview_canvas.image = photo  # Keep reference!
        except Exception as e:
            print(f'Preview error: {e}')
            self.preview_canvas.delete('all')

import argparse

def launch_gui():
    parser = argparse.ArgumentParser(description='Revolve SVG path about axis to create faces for 3D construction.')
    parser.add_argument('--show-preview', action='store_true', help='Show live preview of the revolved shape (requires Pillow and cairosvg).', default=False)
    args = parser.parse_args()
    root = tk.Tk()
    gui = RevolveGUI(root, show_preview=args.show_preview)
    root.mainloop()


if __name__ == '__main__':
    launch_gui()