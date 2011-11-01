#!/usr/bin/env pythonw
# encoding: utf-8
"""
gldraw: used to test gl funcitonality during devel
Using example here as blueprint:
http://www.bryceboe.com/2011/10/08/moving-images-in-3d-space-with-pyglet/

Image Viewer using the pyglet framework

Created by See-ming Lee on 2011-10-29.
Copyright (c) 2011 See-ming Lee. All rights reserved.
"""
from pyglet.event import EventDispatcher
from pyglet.gl import gl
from pyglet.sprite import Sprite
from pyglet.text.document import UnformattedDocument
from pyglet.text.layout import IncrementalTextLayout
import sys

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
#			# below additional / experimental
#			texture = image.get_texture()
#			gl.glEnable(texture.target, texture.id)
#			gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB,
#			                image.width, image.height,
#			                0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE,
#			                image.get_image_data().get_data('RGBA',
#			                image.width * 4))
#			rect_w = float(image.width) / image.height
#			rect_h = 1
#
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
		self._current_id = (self._current_id + len(self.files)) \
				% len(self.files)
			
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
	gl.glBegin(gl.GL_QUADS)
	gl.glVertex2f(x,  y)
	gl.glVertex2f(x + width, y)
	gl.glVertex2f(x + width, y + height)
	gl.glVertex2f(x, y + height)
	gl.glEnd()



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
			gl.glColor3f(1, 0, 0)
		draw_rect(self.x, self.y, self.width, self.height)
		gl.glColor3f(1, 1, 1)
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
	rect_w = 640
	rect_h = 30
	x = 0
	y = 0

	def draw(self):
		draw_rect(self.x, self.y, self.rect_w, self.rect_h)

	def on_slideshow_model_update(self, model):
		self.filename   = model['current_file']
		self.file_id    = model['current_id']
		self.file_total = model['total_files']
		
		# show dipslay as 1-based instead of 0 for huamn readability
		self.text = '[%d/%d]:\n%s' % (
			self.file_id+1, self.file_total, self.filename
		)

		self.document = UnformattedDocument(self.text)
		self.document.set_style(
			0, -1, dict(
				font_name='Gill Sans Light', font_size=9.0,
			    color = (250, 250, 250, 255),
			    background_color = (0, 0, 0, 255)
			)
		)
		self.layout = IncrementalTextLayout(
			self.document, width=self.rect_w, height=self.rect_h,
			multiline=True, batch=self.batch, group=self.group
		)



	


class ImageView(object):
	"""Container of an image"""

	def __init__(self, parent, **kwargs):
		self.parent = parent
		self.x = 0
		self.y = 0
		self.batch = None
		self.group = None
		self.sprite = None
		self.image = None
		self.texture = None

		for key in ('img', 'x', 'y', 'batch', 'group', 'usage', 'folder'):
			if key in kwargs:
				setattr(self, key, kwargs[key])


	def on_slideshow_model_update(self, model):
		self.filename = model['current_file']
		self.image, self.texture = self.load_texture(self.filename)

		self.sprite = Sprite(img=self.image, batch=self.batch,
		                     group=self.group)
		self.fit(self.parent.width, self.parent.height)


	@classmethod
	def load_texture(cls, file):
		try:
			image = pyglet.image.load(file)
		except pyglet.image.codecs.dds.DDSException:
			print ("%s is not a valid image file." % file)
			raise ImageViewerError

		texture = image.get_texture()

		return image, texture

	


	def on_resize(self, width, height):
		self.fit(width, height)

	def fit(self, dst_w, dst_h):
		print ('image_view fit')
		
		if self.sprite is not None:
			rect_w = self.image.width
			rect_h = self.image.height
			xratio = float(rect_w) / float(dst_w)
			yratio = float(rect_h) / float(dst_h)
			maxratio = max(xratio, yratio)
			rect_w = int(rect_w / maxratio + 1)
			rect_h = int(rect_h / maxratio + 1)
			scale_x = float(rect_w) / float(self.image.width)
			scale_y = float(rect_h) / float(self.image.height)
			self.sprite.scale = scale_x


	def draw(self):
		print("ImageView.draw()")
		if self.sprite is not None:
			self.sprite.draw()
		

class AppWindow(pyglet.window.Window):
	"""Main app window"""

	def __init__(self, folder, width=640, height=480, caption="Image Viewer",
	             resizable= True, *args, **kwargs):

		self.folder = folder
		self.width  = width
		self.height = height
		
		super(AppWindow, self).__init__(caption=caption, resizable=resizable,
		                                *args, **kwargs)

		# Batch
		self.batch = pyglet.graphics.Batch()

		# Group
		self.bg_group = pyglet.graphics.OrderedGroup(0)
		self.fg_group = pyglet.graphics.OrderedGroup(2)

		# Slideshow model
		self.ss_model = SlideshowModel(folder)

		# Slideshow: Views + Controls
		self.image_view  = ImageView(
			self,
			img    = self.ss_model.current_image,
			batch  = self.batch,
			group  = self.bg_group,
		    folder = folder
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

		# EVENTS: slideshow events
		self.ss_control.add_model_observer( self.image_view )
		self.ss_control.add_model_observer( self.file_info )
		# EVENTS: window UI events
		self.push_handlers(self.ss_control)
		self.push_handlers(self.image_view)
#

	def update(self, _):
		self.on_draw()
		self.clock += .01

	def on_draw(self):
		self.image_view.draw()
		self.file_info.draw()


if __name__ == '__main__':
	window = AppWindow(
		folder='/Volumes/Proteus/Pictures/test/',
		caption='GL Draw',
		)
	pyglet.app.run()

	pass

