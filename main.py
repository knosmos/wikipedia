'''
A command line interface for reading articles on wikipedia.
'''

import os # used to find terminal dimensions
import sys # used to update terminal
import keyboard # used to handle keyboard input
import wikipedia # retrieves data from wikipedia
import time # framerate
import textwrap # split text into equal-length lines
import ctypes # for added pain (and to move the cursor)
from ctypes import c_long, c_wchar_p, c_ulong, c_void_p

# Terminal colors
class colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def write(x,y,text,color=""): # Writes text at x, y
    sys.stdout.write(color+"\x1b7\x1b[%d;%df%s\x1b8" % (y, x, text)+colors.ENDC) # Black magic

def drawHorizontal(y,x1,x2,startChar,midChar,endChar): # Draws a horizontal line
    line = startChar+midChar*(x2-x1-2)+endChar
    write(x1,y,line,colors.OKBLUE)

def drawVertical(x,y1,y2,startChar,midChar,endChar): # Draws a vertical line
    write(x,y1+1,startChar,colors.OKBLUE)
    write(x,y2,endChar,colors.OKBLUE)
    for y in range(y1+2,y2):
        write(x,y,midChar,colors.OKBLUE)

def clear(): # Clears the entire terminal window
    if os.name == "nt": # Windows is cls, Linux is clear
        os.system("cls")
    else:
        os.system("clear")

def erase(x1,x2,y1,y2): # Erases a specific rectangle of the window
    for x in range(x1,x2+1):
        for y in range(y1,y2+1):
            write(x,y," ")

gHandle = ctypes.windll.kernel32.GetStdHandle(c_long(-11))
sx, sy = (0,0)
old_query_str = "query string"
query_str = ""
page = []
rawpage = ""
offset = 0 # how much scroll

# padding
pad_t = 1
pad_b = 0
pad_l = 0
pad_r = 0

def keyInput(keyObj):
    global query_str, offset
    key = keyObj.name # get unicode representation of keyObj
    if key == "space": key = " "
    if key == "backspace": query_str = query_str[:-1]
    if len(key) == 1: # check if it is actually a character and not something like [shift]
        query_str += key
    if key == "enter":
        if len(query_str): # Check if there is actually a query
            getPage() # Send request to wikipedia
            query_str = ""
    if key == "up":
        offset = max(0,offset-1)
        writePage()
    if key == "down":
        offset += 1
        writePage()
    drawQuery()

keyboard.on_press(keyInput)

def drawWindow(sx,sy):
    global query_str
    # Clear window
    clear()

    # Write "wikipedia" heading
    write(pad_l+1,0,"Wikipedia, the Free Encyclopedia",colors.OKGREEN)

    # Draw box
    drawHorizontal(1+pad_t,1+pad_l,sx+1-pad_r,"╭","─","╮")
    drawHorizontal(sy,1+pad_l,sx+1-pad_r,"╰","─","╯")
    drawVertical(1+pad_l,pad_t,sy,"╭","│","╰")
    drawVertical(sx-pad_r,pad_t,sy,"╮","│","╯")

    # Draw input/text separation line
    drawHorizontal(3+pad_t,1+pad_l,sx+1-pad_r,"├","─","┤")
    sys.stdout.flush()

def drawQuery():
    global query_str, old_query_str
    erase(2+pad_l,sx-1-pad_r,2+pad_t,2+pad_t)
    write(2+pad_l,2+pad_t,query_str,colors.OKCYAN)
    old_query_str = query_str
    # move cursor
    # https://stackoverflow.com/questions/27612545/how-to-change-the-location-of-the-pointer-in-python/27612978#27612978
    value = len(query_str) + 1 + pad_l + ((1+pad_t) << 16)
    ctypes.windll.kernel32.SetConsoleCursorPosition(gHandle, c_ulong(value))
    sys.stdout.flush()

def getPage():
    global query_str, page, rawpage, offset
    try:
        rawpage = wikipedia.page(query_str,auto_suggest=False)
        rawpage = colors.WARNING+rawpage.title.upper()+colors.ENDC+"\n"+rawpage.content # title (in yellow) and content
    except wikipedia.exceptions.DisambiguationError as e: # Show disabiguation page
        rawpage = colors.WARNING+query_str+" may refer to:"+colors.ENDC+"\n"+"\n".join(e.options)
    except wikipedia.exceptions.PageError:
        rawpage = "No pages found for '%s'. Try a different query." %(query_str)
    # Add color to headings
    rawpage = rawpage.replace(" ==="," ==="+colors.ENDC)
    rawpage = rawpage.replace("=== ",colors.FAIL+"=== ")     
    rawpage = rawpage.replace(" == "," == "+colors.ENDC)
    rawpage = rawpage.replace("== ",colors.FAIL+"== ")
    
    # Textwrap lines
    page = makePage(rawpage)
    offset = 0
    redraw()

def makePage(page):
    w = textwrap.TextWrapper(width=sx-2-pad_l-pad_r,replace_whitespace=False)
    p = page.split("\n")
    newpage = []
    for line in p:
        if len(line) > sx-2-pad_l-pad_r:
            w = textwrap.TextWrapper(width=sx-2-pad_l-pad_r, break_long_words=False)
            for k in w.wrap(line):
                newpage.append(k)
        else:
            newpage.append(line)
    return newpage

def writePage():
    global page, sx, offset
    erase(2+pad_l,sx-1-pad_r,4+pad_t,sy-1)
    for i in range(offset,min(len(page),sy-4+offset-pad_t)):
        write(2+pad_l,4+i-offset+pad_t,page[i])
    sys.stdout.flush()

def redraw():
    global page, rawpage
    drawWindow(sx,sy)
    drawQuery()
    page = makePage(rawpage)
    writePage()

def drawSplash():
    clear()
    title = [
        "_       ___ __   _                ___       ",
        "| |     / (_) /__(_)___  ___  ____/ (_)___ _",
        "| | /| / / / //_/ / __ \/ _ \/ __  / / __ `/",
        "| |/ |/ / / ,< / / /_/ /  __/ /_/ / / /_/ / ",
        "|__/|__/_/_/|_/_/ .___/\___/\__,_/_/\__,_/  ",
        "               /_/                          "
    ]
    for i in range(len(title)):
        write(0,1+i,title[i],colors.OKGREEN)
        sys.stdout.flush()
        time.sleep(0.05)

# Splash screen, for fun
drawSplash()
time.sleep(0.1)
drawQuery()
try:
    while True:
        # Get dimensions of terminal window
        s = os.get_terminal_size()
        nsy = s.lines
        nsx = s.columns
        # If window has been resized, redraw the window
        if nsy != sy or nsx != sx:
            sx, sy = nsx, nsy
            # set left/right padding to 10% if window is large enough
            if sx > 60:
                pad_r = int(sx/10)
                pad_l = int(sx/10)
            else:
                pad_r = 1
                pad_l = 1
            redraw()
        time.sleep(0.05)
except KeyboardInterrupt:
    clear() # Clear the screen before we exit
    sys.exit()
