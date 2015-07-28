#!/usr/bin/python
# -*- coding: utf-8 -*-

from tkinter import *
from tkinter.ttk import *

import time

class Gui(Frame):
    
    def __init__(self, parent):
        Frame.__init__(self, parent)   
         
        self.parent = parent
        self.display = Text(self)
        self.display.grid(row=1, column=0, columnspan=2, rowspan=6, padx=5, sticky=E+W+S+N)
        
        self.initUI()
        
    def initUI(self):
        
        self.parent.title("GUI TEST")

        self.style= Style()
        self.style.theme_use("default")
        
        self.columnconfigure(1, weight=1)
        self.columnconfigure(3, pad=5)
        self.rowconfigure(6, weight = 1) 
        self.rowconfigure(5, pad=5) 

        self.box_value = StringVar()
        
        getBtn = Button(self, text="Get")
        getBtn.grid(row=1, column=3, pady=5)

        putBtn = Button(self, text="Put", command = callback)
        putBtn.grid(row=2, column=3, pady=5)

        postBtn = Button(self, text="Post")
        postBtn.grid(row=3, column=3, pady=5)

        obsBtn = Button(self, text="Observe")
        obsBtn.grid(row=4, column=3,pady=5)

        cancelBtn = Button(self, text="Cancel")
        cancelBtn.grid(row=5, column=3,pady=5)

        self.display.configure(state='disabled')
        
        helpBtn = Button(self, text='Help')
        helpBtn.grid(row=7, column=0, padx = 5, pady=5, sticky=W)
        
        closeBtn = Button(self, text='Close', command=self.quit)
        closeBtn.grid(row=7, column=3, padx = 5, pady=5)
        
        rscLbl= Label (self, text='Resources available: ')
        rscLbl.grid(row=0, column=0, padx=5, pady=5)
       
        rscAvl = Combobox(self, textvariable=self.box_value, state='readonly')
        rscAvl.grid(row=0, column=1, pady=5, stick=W)
        
        self.pack()

    def insertText(self):

        self.display.configure(state="normal")
        self.display.insert(INSERT, '{}... \n'.format(terminal))
        self.display.configure(state="disabled")


def main():

    root = Tk()
    app = Gui(root)
    root.mainloop()  
   
def callback():
    print("click!!!!")


if __name__ == '__main__':
    main()  
