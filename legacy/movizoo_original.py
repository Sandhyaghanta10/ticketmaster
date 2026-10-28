# ---------------------------------------------------------------------------
# LEGACY: original MOVIZOO college prototype (2018), kept for reference.
#
# Reconstructed from the original source text: quotes, line breaks and indentation were
# restored; the logic is untouched, bugs included. The ONLY edit is the OMDb API key, which was hardcoded
# in the original and is now read from the OMDB_API_KEY environment variable.
#
# Do not build on this file. See ../ticketmaster/ for the refactored version, and the README
# for a list of the problems this prototype had.
# ---------------------------------------------------------------------------
#tkinter movizoo movie app
from tkinter import *
from os import environ  # (the original defines its own `os()` function below, so we avoid `import os`)
import time
import calendar
import random
import requests
win=Tk()
win.geometry("1000x1000")
win.title("MOVIZOO")
win.configure(bg="gold")
sumt=0
def api():
    url="http://www.omdbapi.com/?i=tt3896198&apikey="+environ.get("OMDB_API_KEY","")
    data=requests.get(url).json()
    return data["Year"],data["Rated"],data["Plot"],data["Genre"]
def cm1(w):
    u=e1.get()
    nom=e2.get()
    some=e3.get()
    cm=Tk()
    cm.geometry("1000x1000")
    if u.isalpha() and nom.isdigit() and len(nom)==10:
        if str(so)==some:
            def counte():
                global sumt
                sumt=sumt+120
            q1=["","red","grey","yellow","dark slate grey","blue","orange","green","cyan","deep pink","midnight blue"]
            for i in range(1,11):
                for j in range(25,0,-1):
                    w=Checkbutton(cm,bg=q1[i],fg="red",bd=20,command=counte)
                    w.grid(row=i,column=j)
            k=Button(cm,bd=10,bg="green",text="BOOK YOUR SEAT",command=lambda: p(cm))
            k.grid(row=15,column=11)
            scr=Label(cm,bg="black",fg="white",font="Times",bd=10,text="------@ ALL EYES THIS WAY @-------")
            scr.grid(row=18,column=11)
            cm.mainloop()
        else:
            otperr=Label(cm,bg="red",fg="black",font="Times",bd=60,text="------@ *OTP MISMATCH ERROR*@-------\nTRY AGAIN BY ENTERING CAREFULLY WITHOUT SPACE\nIF PROBLEM PERSIST CONTACT US AT : 8807-924-084 OR EMAIL US AT movizoo@gmail.com").pack()
    else:
        err=Label(cm,bg="red",fg="black",font="Times",bd=60,text="------@ INVALID USERNAME OR PASSWORD @-------\nPLS. TRY AGAIN BY ENTERING A USERNAME CONTAINING ALPHABETS AND MOBILE NUMBER CONTAINING 10 DIGITS \nIF PROBLEM PERSIST CONTACT US AT : 8807-924-084 OR EMAIL US AT movizoo@gmail.com").pack()
def os():
    finlas=Tk()
    doneby=Label(finlas,bd=50,bg="black",fg="white",font="Times",text="Thank You For Using MOVIZOO software").pack()
    finlas.mainloop()
def final(some12):
    fin=Tk()
    fin.geometry("1000x1000")
    lala1=Label(fin,bd=40,bg="yellow",font="Times",text="MOVIZOO HAS SUCCESSFULLY BOOKED YOUR MOVIE TICKETS AT ").pack()
    lala2=Label(fin,bd=40,bg="yellow",font="Times",text=time.ctime()).pack()
    lala4=Label(fin,bd=40,bg="yellow",font="Times",text="YOUR TICKET NUMBER IS : "+str(random.randint(1000,9999))).pack()
    button=Button(fin,bd=30,bg="black",fg="white",text="EXIT",command=os).pack()
    #some12.destroy()
    fin.mainloop()
def cm3(c1,some1):
    c1.destroy()
    cmcash=Tk()
    cmcash.geometry("1000x1000")
    info=Label(cmcash,bd=30,bg="green",font="Times",text=" YOU HAVE BEEN DIRECTED TO MOVIZOO SECURE"+"e-cash window.PLS. SELECT YOUR BANK FOR PAYMENT PROCESS")
    info.pack()
    v=IntVar()
    v1=IntVar()
    v2=IntVar()
    v3=IntVar()
    v4=IntVar()
    v5=IntVar()
    v6=IntVar()
    b1=Radiobutton(cmcash,fg="blue",bd=20,font="Times",text="SBI BANK",variable=v,value=1).pack()
    b2=Radiobutton(cmcash,fg="DeepPink3",bd=20,font="Times",text="ICICI BANK",variable=v,value=2).pack()
    b3=Radiobutton(cmcash,fg="blue",bd=20,font="Times",text="BANK OF BARODA",variable=v,value=3).pack()
    b4=Radiobutton(cmcash,bd=20,fg="DeepPink3",font="Times",text="MODERN BANK",variable=v,value=4).pack()
    b5=Radiobutton(cmcash,fg="blue",bd=20,font="Times",text="CENTRAL BANK OF INDIA",variable=v,value=5).pack()
    b6=Radiobutton(cmcash,bd=20,fg="DeepPink3",font="Times",text="AXIS BANK",variable=v,value=6).pack()
    b7=Radiobutton(cmcash,fg="blue",bd=20,font="Times",text="SWISS BANK",variable=v,value=7).pack()
    pay=Button(cmcash,bd=30,bg="green",font="Times",text=" PAY ",command=lambda: final(some1)).pack()
    process=Label(cmcash,bd=20,bg="red",fg="white",font="Times",text="TRANSACTION UNDER PROCESS~~~Do not refresh the page").pack()
    cmcash.mainloop()
def p(somevar1):
    cm2 =Tk()
    cm2.geometry("1000x1000")
    lab1=Label(cm2,bg="black",fg="white",bd=30,font="Bold ",text="MOVIZOO HAS SUCCESSFULLY RESERVED YOUR SEATS FOR RUPEES:-").pack()
    lab2=Label(cm2,bg="yellow",bd=50,font="Times",text=str(sumt)+"-/-only").pack()
    cash=Button(cm2,bd=20,bg="green",font="Times",text="PROCEED FOR PAYMENT",command=lambda: cm3(cm2,somevar1)).pack()
    no=Button(cm2,bd=20,bg="red",fg="yellow",font="Times",text="BACK",command=cm2.destroy).pack()
    cm2.mainloop()
def od():
    f=Tk()
    f.configure(bg="deep pink")
    u=e1.get()
    nom=e2.get()
    f.geometry("300x100")
    if u.isalpha() and nom.isdigit() and len(nom)==10:
        kop=Label(f,bg="lawngreen",bd=100,text="NEW MESSAGE RECIEVED\n FROM,TEAM MOVIZOO\n YOUR OTP IS : " + str(so)).pack()
    else:
        err1=Label(f,bg="deep pink",fg="black",font="Times",bd=60,text="------@ ERROR @-------\nTRY AGAIN BY ENTERING A NAME CONTAINING LOWER CASE ALPHABETS AND MOBILE NUMBER CONTAINING 10 DIGITS\nIF PROBLEM PERSIST CONTACT US AT : 8807-924-084 OR EMAIL US AT movizoo@gmail.com").pack()
    f.mainloop()
def url():
    k=Tk()
    k.configure(bg="lavender")
    k.geometry("1000x1000")
    a=api()
    ssn=Label(k,bg="pink",bd=10,text=a,font="Times 10").pack()
    pal=Button(k,bg="red",bd=10,text="OK",font="Times 10",command=lambda:cm1(win)).pack()
    k.mainloop()
el1=Label(win,text="NAME:",bg="gold").pack()
e1=Entry(win,bd=5)
e1.pack()
el2=Label(win,text="MOBILE NUMBER (FOR OTP VERIFICATION) :",bg="gold").pack()
e2=Entry(win,bd=5)
e2.pack()
sm=Button(win,bd=10,bg="orange",font="Times",text="SEND OTP",command=od).pack()
el3=Label(win,text="OTP IS SENT TO YOUR MOBILE NUMBER :",bg="gold").pack()
so=random.randint(1000,9999)
e3=Entry(win,bd=5)
e3.pack()
cal=Label(win,bd=10,bg="black",fg="white",font="Times",text=calendar.month(2018,11)).pack()
f1=Button(win,bd=10,bg="deepskyblue",font="Times",text="THE GUARDIANS OF THE GALAXY",width=40,command=url).pack()
f2=Button(win,bd=10,bg="hotpink1",font="Times",text="2.0",width=40,command=lambda: cm1(win)).pack()
f4=Button(win,bd=10,bg="deepskyblue",font="Times",text="SARKAAR",width=40,command=lambda: cm1(win)).pack()
f5=Button(win,bd=10,bg="hotpink1",font="Times",text="MAHARSHI",width=40,command=lambda: cm1(win)).pack()
f6=Button(win,bd=10,bg="deepskyblue",font="Times",text="MANGALYAAN : INDIA's VOYAGE TO MARS (3D)",width=40,command=lambda: cm1(win)).pack()
win.mainloop()
