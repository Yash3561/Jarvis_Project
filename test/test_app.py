# test_app.py

import tkinter as tk

def on_click():
    print("Button was clicked! The test is a success.")

root = tk.Tk()
root.title("Jarvis Desktop Driver Test")
root.geometry("400x200")

label = tk.Label(root, text="If you can see this window, the test worked.")
label.pack(pady=20)

button = tk.Button(root, text="Click Me!", command=on_click)
button.pack(pady=20)

root.mainloop()