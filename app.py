import customtkinter as ctk
from gui import FolderAnalyzerApp

def main():
    root = ctk.CTk()
    app = FolderAnalyzerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()