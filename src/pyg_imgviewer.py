#!/usr/bin/env pythonw
# encoding: utf-8
"""
pyg_imgviewer

Image Viewer using the pyglet framework

Created by See-ming Lee on 2011-10-29.
Copyright (c) 2011 See-ming Lee. All rights reserved.
"""
from pyglet.event import EVENT_HANDLED, EventDispatcher
from pyglet.sprite import Sprite

__author__ = 'See-ming Lee'
__email__ = 'seeminglee@gmail.com'

import pyglet
from pyglet.window import Window
from pyglet.window import key
import os
from PIL import Image
import string
import random
import re
import sys

class ImageViewerError(Exception):
	def __init__(self, msg):
		self.msg = msg
	def __str__(self):
		return repr(self.msg)

### Exceptions ----------------------------------------------------------------
	
class ImageLoadFileIOError(ImageViewerError): pass
class FontUnavailableError(ImageViewerError): pass
class InvalidFolderError(ImageViewerError): pass

### Resource Loaders ----------------------------------------------------------
class Loader(object):
	"""Used for loading things"""
	@classmethod
	def load_image(cls, fullname):
		"""Load image and return image object and its bounding size"""
		try:
			image_stream = open(fullname, 'rb')
			image = pyglet.image.load(fullname, file=image_stream)
			size = (image.width, image.height)
		except IOError, message:
			print 'Cannot load image:', fullname
			raise ImageLoadFileIOError, message
		return image, size

### Model Helper --------------------------------------------------------------
class FileType(object):
	"""small class used to store regular expression patterns to be used
	in conjunction with the Foleer class"""

	# constants
	JPG = 0
	GIF = 1
	PNG = 2
	TIF = 3

	# re patterns
	isnot_sys = re.compile(r'^[^\.].+') # not system hidden files.
	is_image = re.compile(r'.+\.(jpg|jpeg|gif|png|tif)$', re.IGNORECASE)
	is_jpg = re.compile(r'.+\.(jpg|jpeg)$', re.IGNORECASE)
	is_gif = re.compile(r'.+\.(gif)$', re.IGNORECASE)
	is_png = re.compile(r'.+\.(png)$', re.IGNORECASE)
	is_tif = re.compile(r'.+\.(tif)$', re.IGNORECASE)

### Models _-------------------------------------------------------------------
class SlideshowModel(EventDispatcher):
	"""model of the slideshow"""
	def __init__(self, folder):
		"""initialize with name of the folder"""
		try:
			if not os.path.exists(folder):
				raise InvalidFolderError('Path entered does not exist.')
			if os.path.isfile(self.folder):
				self.folder = os.path.dirname(self.folder)
			self.folder = os.path.abspath(self.folder)
		except InvalidFolderError as e:
			print "An exception occurred: message: ", e.msg

		self.allfiles = [f for f in os.listdir(self.path) if FileType.isnot_sys.match(f)]
		self.imagefiles = [f for f in self.allfiles if FileType.is_image.match(f)]

		self.files = self.imagefiles

		self.loop = True
		self.random = False
		
		self.sort_method = "alpha"
		self.sort_direction ="asc"
		self.direction = "asc"
		self.current_id = 0

		# used for tracking random files. in particular, allow
		# to go back to files just previously viewed when playing in random
		self.play_random = False
		self.id_queue_past = []
		self.id_queue = []

		# animation properties
		self.animation_rate = 2000 # in milliseconds

		EventDispatcher.register_event_type("on_slideshow_model_update")



	def direction(self):
		return self.direction

	def filerandom(self):
		return self.filerandom

	def current_id(self):
		return  self.current_id

	def current_file(self):
		return self.files.index(self.current_id)

	def total_files(self):
		return len(self.files)

	def next(self):
		"""move to the next item"""
		if not self.random:
			# normal
			if self.sort_direction is "asc":
				self.current_id += 1
			else:
				self.current_id -= 1
			limit_id_range()

		# random
		else:
			if not len(self.id_queue):
				self.id_queue = range(len(self.files))
			else:
				self.current_id = random.randrange(len(self.id_queue))
				self.id_queue.remote(self.current_id)
				self.id_queue_past.append(self.current_id)

		dispatch_event("on_slideshow_model_update")

	def prev(self):
		"""move to the previous item"""
		if not self.random:
			# normal
			if self.sort_direction is "asc":
				self.current_id -= 1
			else:
				self.current_id += 1
			limit_id_range()

		# random
		else:
			if not len(self.id_queue_past):
				return # no more previous queue to go to, so don't do anything
			else:
				self.current_id = self.id_queue_past.pop()
				self.id_queue.append(self.current_id)

		dispatch_event("on_slideshow_model_update")



	def limit_id_range(self):
		if self.current_id < 0:
			self.current_id = len(self.files) - 1
		elif len(self.files) < self.currentid:
			self.current_id = 0
			

	

class SlideshowController(EventDispatcher):
	"""controller for slideshow interactions"""

	def __init__(self, model, *args, **kwargs):
		"""init control with model"""
		self.model = model
		self.started = False

	def add_view(view):
		"""Made sure all the views will listen to any model updates"""
		

		
	def on_key_press(self, symbol, modifiers):
		"""key press event: mostly listening for slideshow navigation"""
		if symbol in [key.RIGHT, key.LEFT, key.SPACE]:

			if symbol == key.RIGHT:
				self.item_next()
			elif symbol == key.LEFT:
				self.item_prev()
			elif symbol == key.SPACE:
				self.toggle_show()

	def toggle_show(self):
		self.started = not self.started
		

	def item_next(self):
		if self.model.next():
			self._dispatch_model_update()
			
	def item_prev(self):
		if self.model.prev():
			self._dispatch_model_update()

	def _dispatch_model_update(self):
		self.dispatch_event(self,
		    "on_slideshow_model_update",
		    dict(
			    current_id = self.model.current_id,
		        current_file = self.model.total_files,
		        total_files = self.model.total_files
		    )

		)








class Rectangle(object):
	"""Draws a rectangle into a batch."""
	def __init__(self, x1, y1, x2, y2, batch):
		self.vertex_list = batch.add(4, pyglet.gl.GL_QUADS, None,
			('v2i', [x1, y1, x2, y1, x2, y2, x1, y2]),
			('c4B', [30, 30, 50, 255] * 4)
		)



class FileInfoWidget(object):
	"""Meta information about the file"""

	def __init__(self, filename, index, total, x, y, width, batch):
		"""initialization. optionally add name of file"""
		self.filename = filename
		self.file_index = index
		self.file_total = total

		text = '[%d/%d]: %s' % (index, total, filename)

		self.document = pyglet.text.document.UnformattedDocument(text)
		self.document.set_style(0, len(self.document.text),
			dict(color=(250, 250, 250, 255))
		)
		font = self.document.get_font()
		width  = width
		height = font.ascent - font.descent

		self.layout = pyglet.text.layout.IncrementalTextLayout(
			self.document, width, height, batch=batch
		)
		self.caret = pyglet.text.caret.Caret(self.layout)

		self.layout.x = x
		self.layout.y = y

		# rectangle outline
		pad = 5
		self.rectangle = Rectangle(x - pad, y - pad,
								   x + width + pad, y + height + pad, batch)

	def hit_test(self, x, y):
		return (0 < x - self.layout.x < self.layout.width and
				0 < y - self.layout.y < self.layout.height)

	def set_meta(self, filename='', index=None, total=None):
		"""set the filename and other meta info
		@filename name of the file, string
		index     position of the file among files, integer
		total     total number of files, integer"""
		self.filename = filename
		self.index = index
		self.total = total
		self.update()

	def update(self):
		pass
		"""display current meta"""
#		if self.visible:
#			info = self.info()
#			text = self.font.render(info, 1, self.bg_color, self.fg_color)
#			textpos = text.get_rect(left=5, bottom=self.bg_height-3)
#			self.image = pygame.Surface((text.get_width()+10, self.bg_height))
#			self.image.fill(self.fg_color)
#			self.image.blit(text, textpos)
#			self.image.set_alpha(255)
#			self.screen = pygame.display.get_surface()
#			self.rect = pygame.Rect((0, 0), self.image.get_size())
#			self.rect.bottomleft = (0, self.screen.get_height()+1)
#		else:
#			self.image.set_alpha(0)
##
##	def toggle_visibility(self):
#		"""show / hide the meta info"""
#		self.visible = not self.visible
#
	def set_meta(self, filename='', index=None, total=None):
		"""set the filename and other meta info
		@filename name of the file, string
		index     position of the file among files, integer
		total     total number of files, integer"""
		self.filename = filename
		self.index = index
		self.total = total

		self.filename = filename
		self.file_index = index
		self.file_total = total

		self.document.text = '[%d/%d]: %s' % (index, total, filename)

		self.update()



class Folder(object):
	"""Keep track of the image folder we are tracking"""

	def __init__(self, path=''):
		"""Initialization"""
		self.set_path(path)

	def set_path(self, path=''):
		if os.path.isfile(path):
			path = os.path.dirname(path) # make sure it's a folder
		self.path = os.path.abspath(path) # get the absolute path
		self.allfiles = [f for f in os.listdir(self.path) if FileType.isnot_sys.match(f)]
		self.imagefiles = [f for f in self.allfiles if FileType.is_image.match(f)]


	def files(self):
		"""Return the list of files contained in the folder"""
		return self.abspath(self.allfiles)

	def images(self):
		"""Return all image files contained in folder"""
		return self.abspath(self.imagefiles)

	def jpgs(self):
		"""Return list of jpegs"""
		return self.abspath([f for f in self.allfiles if FileType.is_jpg.search(f)])

	def gifs(self):
		"""Return list of gifs only"""
		return self.abspath([f for f in self.allfiles if FileType.is_gif.search(f)])

	def pngs(self):
		"""Return list of gifs only"""
		return self.abspath([f for f in self.allfiles if FileType.is_png.search(f)])

	def _abspath(self, files=None):
		"""Return a list of files with absolute paths"""
		if files is None:
			files = self.allfiles
		return [os.path.join(self.path, f) for f in files]




class ImageView(pyglet.sprite.Sprite):
	"""Container of an image"""
	def __init__(self, img, x, y, batch, group):
		pyglet.sprite.Sprite.__init__(self, img, x, y, batch=batch, group=group)
		self.image = img
		self.x = x
		self.y = y
		self.batch = batch
		self.group = group

	def set_image(self, img):
		self.image = img



class Queue(pyglet.event.EventDispatcher):
	"""File queue for slide show"""
	def __init__(self, files=None):
		"""initialization.
		@param  files   list of files to be put into queue"""
		self.current_index = 0
		self.files = []
		self.addfiles(files)

	def addfiles(self, files=None):
		if files is not None:
			self.files.extend(files)

	def next(self):
		"""Iterate to next file without returning the file"""
		self.current_index += 1
		if self.current_index >= len(self.files):
			self.current_index = 0

	def prev(self):
		"""Iterate to previous file"""
		self.current_index -= 1
		if self.current_index < 0:
			self.current_index = len(self.files) - 1


	def current_file(self):
		"""return the currently selected file"""
		return self.files[self.current_index]

	def total_files(self):
		"""return the count total of all files"""
		return len(self.files)

	def current_image(self):
		"""return the currently selected image"""
		image = pyglet.image.load(self.current_file())
		return image

	# events
	def image_next(self):
		self.next()
		self.dispatch_event("on_image_next")

	def image_prev(self):
		self.prev()
		self.dispatch_event("on_image_prev")

	def image_update(self, image, filename, id, total):
		filename = self.current_file()
		image = pyglet.image.load(filename)
		id = self.current_index
		total = self.total_files()
		self.dispatch_event("on_image_update", image, filename, id, total)



class AppWindow(pyglet.window.Window):
	"""Main app window"""
	def __init__(self, folder_path):


		platform = pyglet.window.get_platform()
		screen  = platform.get_default_display().get_default_screen()
		max_width  = screen.width
		max_height = screen.height

		# Batch
		self.batch = pyglet.graphics.Batch()

		# Group
		self.bg_group = pyglet.graphics.OrderedGroup(0)
		self.mg_group = pyglet.graphics.OrderedGroup(1)
		self.fg_group = pyglet.graphics.OrderedGroup(2)


		# Folder Meta
		self.folder = Folder(folder_path)
		self.queue = Queue(self.folder.images())

		filename = self.queue.current_file()
		index = self.queue.current_index
		total = self.queue.total_files()

		# Widget: File Info
		self.fileinfo = FileInfoWidget(filename, index, total, 5, 5,
						   self.width, batch=self.batch)

		self.text_cursor = self.get_system_mouse_cursor('text')

#		self.focus = None
#		self.set_focus(self.fileinfo)

		# ImageView
		self.imageview = ImageView(img=pyglet.image.load(filename), x=0, y=0,
		                           batch=self.batch, group=self.mg_group)

		self.queue.set_handler("on_image_update", self.imageview)

		# Background
		self.background = Rectangle(0, max_height,
		                            max_width, max_height, self.batch)


		# Sprites
		self.sprites = [self.background, self.imageview, self.fileinfo]

		self.ss_event_handler = SlideshowController()
		self.push_handlers(self.ss_event_handler)

		pyglet.window.Window.__init__(self, 640, 480, "Image Viewer", True)


		

	def slideshow_update(self):
		"""update all the players"""
		filename = self.queue.current_file()
		id = self.queue.current_index
		total = self.queue.total_files()
		image = pyglet.image.load(filename)

		self.imageview.set_image(image)
		self.fileinfo.set_meta(filename, id, total)


	# standard OS GUI
	def on_resize(self, width, height):
		super(Window, self).on_resize(width, height)

	def on_draw(self):
		pyglet.gl.glClearColor(0, 0, 0, 1)
		self.clear()
		self.batch.draw()
#
#	def on_mouse_motion(self, x, y, dx, dy):
#		if self.fileinfo.hit_test(x, y):
#			self.set_mouse_cursor(self.text_cursor)
#		else:
#			self.set_mouse_cursor(None)
#
#	def on_mouse_press(self, x, y, button, modifiers):
#		if self.fileinfo.hit_test(x, y):
#			self.set_focus(widget)
#		else:
#			self.set_focus(None)
#
#		if self.focus:
#			self.focus.caret.on_mouse_press(x, y, button, modifiers)
#
#	def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
#		if self.focus:
#			self.focus.caret.on_mouse_drag(x, y, dx, dy, buttons, modifiers)
#
#	def on_text(self, text):
#		if self.focus:
#			self.focus.caret.on_text(text)
#
#	def on_text_motion(self, motion):
#		if self.focus:
#			self.focus.caret.on_text_motion(motion)
#
#	def on_text_motion_select(self, motion):
#		if self.focus:
#			self.focus.caret.on_text_motion_select(motion)
#
#
#
##	def on_key_press(self, symbol, modifiers):
##		"""key press event: mostly listening for slideshow navigation"""
##		slideshow_keys = [key.RIGHT, key.LEFT, key.SPACE]
##
##		if symbol in slideshow_keys:
##
##			print("WINDOW KEY PRESS")
##
##			if symbol == key.RIGHT:
##				self.queue.next()
##			elif symbol == key.LEFT:
##				self.queue.prev()
##			elif symbol == key.SPACE:
##				pass
##			#  start slideshow
#
#
##
##	def on_key_press(self, symbol, modifiers):
##		if symbol == pyglet.window.key.ESCAPE:
##			pyglet.app.exit()
##
###		return pyglet.event.EVENT_HANDLED
##
##
#
#	def set_focus(self, focus):
#		if self.focus:
#			self.focus.caret.visible = False
#			self.focus.caret.mark = self.focus.caret.position = 0
#
#		self.focus = focus
#		if self.focus:
#			self.focus.caret.visible = True
#			self.focus.caret.mark = 0
#			self.focus.caret.position = len(self.focus.document.text)


window = AppWindow('/Volumes/Proteus/Pictures/test/')
pyglet.app.run()