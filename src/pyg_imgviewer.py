#!/usr/bin/env pythonw
# encoding: utf-8
"""
pyg_imgviewer

Image Viewer using the pyglet framework

Created by See-ming Lee on 2011-10-29.
Copyright (c) 2011 See-ming Lee. All rights reserved.
"""
from pyglet.event import EventDispatcher
from pyglet.gl.gl import glColor3f, glVertex2f, GL_LINE_LOOP, glBegin, \
	GL_ONE_MINUS_SRC_ALPHA
from pyglet.sprite import Sprite
from pyglet.text.document import UnformattedDocument
from pyglet.text.layout import IncrementalTextLayout

__author__ = 'See-ming Lee'
__email__ = 'seeminglee@gmail.com'

import pyglet
from pyglet.window import key
import os
import random
import re

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
		except IOError, message:
			print 'Cannot load image:', fullname
			raise ImageLoadFileIOError, message
		return image

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
			self.folder = folder
			if not os.path.exists(self.folder):
				raise InvalidFolderError('Path entered does not exist.')
			if os.path.isfile(self.folder):
				self.folder = os.path.dirname(self.folder)
			self.folder = os.path.abspath(self.folder)
		except InvalidFolderError as e:
			print "An exception occurred: message: ", e.msg
			self.folder = None

		self.all_files = [f for f in os.listdir(self.folder)
		                 if FileType.isnot_sys.match(f)]
		self.image_files = [f for f in self.all_files
		                   if FileType.is_image.match(f)]
		self.files = self.image_files

		self.loop = True
		self.random = False
		
		self._current_id = 0
		self._direction = "forward"
		self._play_random = False

		# used for tracking random files. in particular, allow
		# to go back to files just previously viewed when playing in random
		self._play_random = False
		self._id_queue_past = []
		self._id_queue = []

		# animation properties
		self.animation_rate = 2000 # in milliseconds

	@property
	def direction(self):
		return self._direction

	@property
	def play_random(self):
		return self._play_random

	@property
	def current_id(self):
		return  self._current_id

	@property
	def current_file(self):
		if self.play_random:
			filename = self.files.index(self.current_id)
		else:
			filename = self.files[self.current_id]
		return os.path.join(self.folder, filename)

	@property
	def total_files(self):
		return len(self.files)

	@property
	def current_image(self):
		return Loader.load_image(self.current_file)

	def next(self):
		"""move to the next item"""
		if not self.play_random:
			# normal
			if self.direction is "forward":
				self._current_id += 1
			else:
				self._current_id -= 1
			self.limit_id_range()

		# random
		else:
			if not len(self._id_queue):
				self._id_queue = range(len(self.files))
			else:
				self._current_id = random.randrange(len(self._id_queue))
				self._id_queue.remove(self.current_id)
				self._id_queue_past.append(self.current_id)

		self._dispatch_update()

	def prev(self):
		"""move to the previous item"""
		if not self.play_random:
			# normal
			if self.direction is "forward":
				self._current_id -= 1
			else:
				self._current_id += 1
			self.limit_id_range()

		# random
		else:
			if not len(self._id_queue_past):
				return # no more previous queue to go to, so don't do anything
			else:
				self._current_id = self._id_queue_past.pop()
				self._id_queue.append(self.current_id)

		self._dispatch_update()

	def limit_id_range(self):
		if self._current_id < 0:
			self._current_id = len(self.files) - 1
		elif len(self.files) < self._current_id:
			self._current_id = 0

			
	def _dispatch_update(self):
		self.dispatch_event(
		    "on_slideshow_model_update",
		    dict(
			    current_id   = self.current_id,
		        current_file = self.current_file,
		        total_files  = self.total_files
		    )

		)

SlideshowModel.register_event_type("on_slideshow_model_update")


### Controllers ---------------------------------------------------------------

class SlideshowController(EventDispatcher):
	"""controller for slideshow interactions"""

	started = False

	def __init__(self, model):
		"""init control with model"""
		self.model = model

	def add_model_observer(self, view):
		"""Made sure all the views will listen to any model updates"""
		self.model.push_handlers(view)

		
	def on_key_press(self, symbol, modifiers):
		"""key press event: mostly listening for slideshow navigation"""
		if symbol in [key.RIGHT, key.LEFT, key.SPACE]:

			if symbol == key.RIGHT:
				self.model.next()
			elif symbol == key.LEFT:
				self.model.prev()
			elif symbol == key.SPACE:
				self.toggle_show()
		print "SS Controller: Event: on key press"

	def toggle_show(self):
		self.started = not self.started

### Helpers -------------------------------------------------------------------
def draw_rect(x, y, width, height):
	glBegin(GL_LINE_LOOP)
	glVertex2f(x,  y)
	glVertex2f(x + width, y)
	glVertex2f(x + width, y + height)
	glVertex2f(x, y + height)
	glEnd()



### User Interface ------------------------------------------------------------
class Control(EventDispatcher):
	"""An AbstractControl of the user interface"""
	x = y = 0
	width = height = 10

	def __init__(self, parent, group=None, batch=None):
		super(Control, self).__init__()
		self.parent = parent
		self.group = group
		self.batch = batch

	def hit_test(self, x, y):
		return (self.x < x < self.x + self.width and
		        self.y < y < self.y + self.height)

	def capture_events(self):
		self.parent.push_handlers(self)

	def release_events(self):
		self.parent.remove_handlers(self)


class Button(Control):
	charged = False

	def draw(self):
		if self.charged:
			glColor3f(1, 0, 0)
		draw_rect(self.x, self.y, self.width, self.height)
		glColor3f(1, 1, 1)
		self.draw_label()

	def on_mouse_press(self, x, y, button, modifiers):
		self.capture_events()
		self.charged = True

	def on_mouse_draw(self, x, y, dx, dy, buttons, modifiers):
		self.charged = self.hit_test(x, y)

	def on_mouse_release(self, x, y, button, modifiers):
		self.release_events()
		if self.hit_test(xy):
			self.dispatch_event('on_button_press')
		self.charged = False

Button.register_event_type('on_button_press')


class Rectangle(object):
	"""Draws a rectangle into a batch."""
	def __init__(self, x1, y1, x2, y2, batch):
		self.vertex_list = batch.add(4, pyglet.gl.GL_QUADS, None,
			('v2i', [x1, y1, x2, y1, x2, y2, x1, y2]),
			('c4B', [30, 30, 50, 255] * 4)
		)

		
class FileInfoWidget(Control):
	"""Single line text display object for image meta data
	when slide show is running."""
	filename = ''
	file_id = 0
	file_total = 0

	def draw(self):
		draw_rect(self.x, self.y, self.width, self.height)

	def on_slideshow_model_update(self, model):
		self.filename   = model['current_file']
		self.file_id    = model['current_id']
		self.file_total = model['total_files']
		self.text = '[%d/%d]: %s' % (
			self.file_id, self.file_total, self.filename
		)

		self.document = UnformattedDocument(self.text)
		self.document.set_style(
			0, -1, dict(
				font_name='Audimat Mono', font_size=13.0,
			    color = (250, 250, 250, 255),
			    background_color = (10, 10, 10, 255)
			)
		)
		self.layout = IncrementalTextLayout(
			self.document, width=400, height=30,
			batch=self.batch, group=self.group
		)

	


class ImageView(Sprite):
	"""Container of an image"""
	x = y = 0
	batch = None
	group = None
	usage = 'dynamic'
	img = None
	
	def __init__(self, **kwargs):
		for key in ('img', 'x', 'y', 'batch', 'group', 'usage'):
			if key in kwargs:
				setattr(self, key, kwargs[key])
		super(ImageView, self).__init__(**kwargs)

	def on_slideshow_model_change(self, model):
		self.filename = model.filename
		self.img = Loader.load_image(model.filename)
		self.img = self.image.convert()

	def on_resize(self, width, height):
		fit_screen(width, height)

	def fit_screen(self, dst_w, dst_h):
		xratio = float(self._texture.width)  / float(dst_w)
		yratio = float(self._texture.height) / float(dst_h)
		maxratio = max(xratio, yratio)
		self._texture.width  = int(self._texture.width  / maxratio + .5)
		self._texture.height = int(self._texture.height / maxratio + .5)
		



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
	
	width = 640
	height = 480
	caption = "Image Viewer"
	resizable = True


	def __init__(self, folder_path):

		# Batch
		self.batch = pyglet.graphics.Batch()

		# Group
		self.bg_group = pyglet.graphics.OrderedGroup(0)
		self.fg_group = pyglet.graphics.OrderedGroup(2)

		# Slideshow model
		self.ss_model = SlideshowModel(folder_path)

		# Slideshow: Views + Controls
		self.image_view  = ImageView(
			img   = self.ss_model.current_image,
			batch = self.batch,
			group = self.bg_group
		)
		self.file_info = FileInfoWidget(
			self,
			batch = self.batch,
			group = self.fg_group
		)

		# Slideshow: Controller
		self.ss_control = SlideshowController(
			self.ss_model
		)
		self.ss_control.add_model_observer( self.image_view )
		self.ss_control.add_model_observer( self.file_info )
		self.push_handlers(self.ss_control)

		super(AppWindow, self).__init__()

	def on_draw(self):
		self.clear()
		self.batch.draw()



window = AppWindow('/Volumes/Proteus/Pictures/test/')
pyglet.app.run()