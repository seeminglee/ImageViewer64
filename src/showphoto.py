#!/usr/bin/env python
# encoding: utf-8
"""
showphoto - a simple file to test some api theories

Created by See-ming Lee on 2011-10-30.
Copyright (c) 2011 See-ming Lee. All rights reserved.
"""
from pyglet.window import key
import pyglet
import pyglet.app
import pyglet.window

__author__ = 'See-ming Lee'
__email__ = 'seeminglee@gmail.com'





class AppWindow(pyglet.window.Window):
	def __init__(self):
		super(pyglet.window.Window, self).__init__()
		


	def on_mouse_move(self):
		self.mouse_move =  True

	
	def on_key_press(self, symbol, modifiers):
		if symbol == key.RIGHT:
			print 'RIGHT KEY PRESSED'

		elif symbol == key.LEFT:
			print 'LEFT KEY PRESSED'

		elif symbol == key.SPACE:
			print 'SPACE KEY PRESSED'

appwin = AppWindow()
pyglet.app.run()
