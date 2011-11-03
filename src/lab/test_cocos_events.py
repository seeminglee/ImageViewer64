#!/usr/bin/env python
# encoding: utf-8
"""
Could not get pyglet's event model to run properly in cocos.
Using code here to investigate what I'm doing wrong.

Created by See-ming Lee on 2011-11-03.
Copyright (c) 2011 See-ming Lee. All rights reserved.
"""
import pyglet

__author__ = 'See-ming Lee'
__email__ = 'seeminglee@gmail.com'

import sys
from cocos.director import director
from cocos.layer import Layer
from cocos.layer import ColorLayer
from cocos.scene import Scene
from cocos.text import Label

class Emitter(pyglet.event.EventDispatcher):

	def __init__(self):
		super(Emitter, self).__init__()
		self.handle_count = 0

	def handleLayerEvent(self):
		self.handle_count += 1

		print "Emitter.handleLayeEvent() count=%d" % self.handle_count

		if self.handle_count > 10:
			self.dispatch_event("on_handling_many_events", self.handle_count)
			print("Emitter has received layer orders %d times." % self.handle_count)
			self.handle_count = 0

Emitter.register_event_type("on_handling_many_events")


class MyLayer(ColorLayer):

	is_event_handler = True

	def __init__(self, emitter):
		super(MyLayer, self).__init__(r=200,g=300,b=200,a=255,width=200,
		                              height=300)
		self.handle_count = 0
		self.emitter = emitter

	def on_key_press(self, symbol, modifiers):
		print("MyLayer.handled symbol: %s modifiers: %s" % (symbol, modifiers))
		self.handle_count += 1
		self.emitter.handleLayerEvent()



class Controller():
	def __init__(self):
		director.init(width=800, height=600, fullscreen=False)
		l1 = ColorLayer(0, 0, 234, 255, 400, 200)
		l1.position = (200, 200)

		emit = Emitter()
		emit.push_handlers(self)

		mylayer = MyLayer(emit)

		self.scene = Scene(
			ColorLayer(234, 123, 234, 128, 800, 600),
			ColorLayer(255, 0, 0, 255, 500, 400),
		    l1,
		    mylayer
		)

	def on_handling_many_events(self, count):
		print("Controller received 'on_handling_many_events' event. count=%d" % count)


	def run(self):
		director.run(self.scene)



def main():
	controller = Controller()
	controller.run()


if __name__ == '__main__':
	main()

