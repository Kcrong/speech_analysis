#!/usr/bin/env python3

from jpype import java, javax, JException, startJVM, setupGuiEnvironment, \
	shutdownGuiEnvironment, getDefaultJVMPath

def run():
	print('Thread started')
	try:
		print(repr(java.awt.Frame))
		javax.swing.JFrame("Test Frame").setVisible(True)
		shutdownGuiEnvironment()
	except JException as ex :
		print(ex)


startJVM(getDefaultJVMPath())

setupGuiEnvironment(run)
