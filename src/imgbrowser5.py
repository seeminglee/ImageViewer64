#!/usr/bin/env python
# encoding: utf-8
"""
imgbrowser.py

Created by See-ming Lee on 2011-10-26.
Copyright (c) 2011 See-ming Lee. All rights reserved.
"""
import os
import os.path
import pyglet
from pyglet import image
from pyglet.window import key
import time
# from itertools import cycle, tee
import re
import itertools

# 
# 
# def next_n(iterable, n=2):
# 	''' Generator which yield a tuple of the next n item in iterable.
# 	The generator cycles infinitely. '''
# 	cycled = cycle(iterable)
# 	gens = tee(cycled, n)
# 	# advance the iterators, this is 0 (n^2)
# 	for (ii,g) in zip(xrange(n), gens):
# 		for jj in xrange(ii):
# 			gens[ii].next()
# 	while True:
# 		yield tuple([x.next() for x in gens])




class Slide(pyglet.sprite.Sprite):
	"""A slide of the slideshow as expressed as a sprite"""

	slide_count = 0
	
	STATE_INIT    = 0
	STATE_FADEIN  = 1
	STATE_OPAQUE  = 2
	STATE_FADEOUT = 3

	def __init__(self, window, path, x=0, y=0, blend_src=770, blend_dest=771,
			batch=None, group=None, usage='dynamic'):
		
		# define and load image
		self.img = image.load(path)
		super(Slide, self).__init__(img=self.img)
		
		# access class variable to retrieve a unique id
		self.id = Slide.slide_count
		Slide.slide_count += 1

		self.window     = window
		self.path       = path
		self.batch      = None
		self.group      = None
		self.usage      = 'dynamic'
		self.x          = -200
		self.y          = -200
		self.blend_src  = 770
		self.blend_dest = 771
		
		self.reset()
		
		self.img.width = self.window.width
		self.img.height = self.window.height
		self.img.blit(0, 0)
		
		
		print("Slide id:%d path:%s image:%d x %d" % (self.id, path, self.img.width, self.img.height))
		

	def scale_to_window(self):
		"""scale image to fit window"""
		img_w = self.img.width
		img_h = self.img.height
		win_w = self.window.width
		win_h = self.window.height

		print("window size: %d x %d" % (win_w, win_h))
		print("image  size: %d x %d" % (img_w, img_h))

		# if img_h is not None:
		# 	if win_h is not None:
		# 		if win_h > 0:
		# 			if img_h > 0:
		# 				if (win_w / win_h) > (img_w / img_h) :
		# 					img_h = win_h
		# 					img_w = win_w / win_h * img_h
		# 				else:
		# 					img_w = win_w
		# 					img_h = win_h / win_w * img_w
		#
		# 				self.img.width = img_w
		# 				self.img.height = img_h


	def load_image(self):
		"""load image. delay this to the very last second to save on resources"""
		self.img = image.load(self.path)


	def reset(self):
		"""reset animation"""
		self.state = Slide.STATE_INIT
		self.opacity = 0

	def fadeIn(self):
		"""start animation"""
		self.state = Slide.STATE_FADEIN

	def stop_animation(self):
		"""stop animation"""
		self.state = Slide.STATE_OPAQUE
		self.opacity = 255

	def fadeOut(self):
		"""fadeOut animation"""
		self.state = Slide.STATE_FADEOUT



	def draw(self):
		super(Slide, self).draw()
		
		if self.state == Slide.STATE_FADEIN:
			self.opacity = min(255, int((self.opacity + 1) * 1.2))
		
			if self.opacity >= 253:
				self.stop_animation()
						
		elif self.state == Slide.STATE_FADEOUT:
			self.opacity = max(0, int(self.opacity * 0.95))
		
			if self.opacity <= 4:
				self.reset()
				
		#####################################
		# For Debugging                     #
		#####################################
		self.debug()
		
	
	def debug(self):
		print "Slide id: %d \tState:\t%s \tOpacity: %s" % (
				self.id, 
				'*' * (self.state+1), 
				'O' * int(self.opacity * 10 // 255))
				
	
			

#### ----------------------------------------------------------------------


		




#### ----------------------------------------------------------------------

isJPG = re.compile(r'\.jpg$',re.IGNORECASE)

class SlideshowWindow(pyglet.window.Window):
	"""The core of the program. Displays images as slideshow"""

	def __init__(self, path=os.curdir):
		"""
		constructor.
		"""
		super(SlideshowWindow, self).__init__(self)

		self.set_size(640,480)
		self.path = path
		self.files = [ os.path.join(path, f) for f in os.listdir(self.path) if isJPG.search(f) ]

		self.slides = [	Slide(window=self, path=f) for f in self.files ]


		def item_feed(iterable):
			for item in itertools.cycle(iterable):
				yield item
		
		self.item = item_feed(self.slides)
		
		self.previtem = None
		self.curritem = self.item.next()


	def startShow(self):
		"""begin slideshow animation"""
		self.animating = True
		self.timestarted = time.time()

		# animation loop
		pyglet.clock.set_fps_limit(20)
		pyglet.clock.schedule(self.animate)
		
		if self.curritem is not None:
			self.curritem.fadeIn()


	def animate(self, dt):
		"""update sprite if need be"""
		print("window.animate()")
		elapsed = time.time() - self.timestarted

		# introduce the next file when elapsed over 3 seconds
		if elapsed > 3:
			print("elapsed = %f" % elapsed)
			self.timestarted = time.time()
			self.animateNextSlide()

		
		if self.curritem is not None:
			self.curritem.draw()
			
		if self.previtem is not None:
			self.previtem.draw()
			


	def animateNextSlide(self):
		
		self.previtem = self.curritem
		self.previtem.fadeOut()
		
		self.curritem = self.item.next()
		self.curritem.fadeIn()
		
		
	# window.event
	def on_draw(self):
		self.clear()
		# self.batch.draw()
		
		if self.curritem is not None:
			self.curritem.draw()
			
		if self.previtem is not None:
			self.previtem.draw()
		


	# window.event	
	def on_key_press(self, symbol, modifiers):
		# F: toggle full screen
		if key.F == symbol:
			if self.fullscreen:
				self.set_fullscreen(fullscreen=False)
				return True
			else:
				self.set_fullscreen(fullscreen=True)
				return True

	# window.event
	def on_resize(self, width, height):
		"""resize images to fit new width"""
		if self.curritem is not None: pass
			# self.curritem.scale_to_window()
		if self.previtem is not None: pass
			# self.previtem.scale_to_window()




if __name__ == '__main__':
	window = SlideshowWindow(path='/Users/sml/Pictures/tmp')
	window.startShow()
	pyglet.app.run()


	
		
	