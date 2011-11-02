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
from _ctypes import POINTER
from ctypes import c_int
from pyglet.event import EventDispatcher
from pyglet.gl import gl
from pyglet.image import SolidColorImagePattern
from pyglet.sprite import Sprite
from pyglet.text.document import UnformattedDocument
from pyglet.text.layout import IncrementalTextLayout
from pyglet.window import key
import pyglet
import os
import random
import re
import sys

__author__ = 'See-ming Lee'
__email__ = 'seeminglee@gmail.com'

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
		self._autonext_interval_msec = 2000 # in milliseconds
		
		# animation started
		self._playing = False

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
		
	@property
	def playing(self):
		return self._playing
			
	def play(self):
		"""Schedule and start auto-advance to next slide"""
		print("play args:")
		print(args)
		pyglet.clock.schedule_once( self.play_next, 
									self._autonext_interval_msec)
		# instead of using interval schedules, it just callls the same
		# function repeated so if the system is backed up it won't create 
		# additional problems
		self._playing = True
									
	def stop(self):
		"""Stop animation"""
		pyglet.clock.unschedule(self.play_next)
		self._playing = False
		
	def play_next(self):
		"""auto advance to next"""
		print("plext_next() args:")
		print(args)
		self.next()
		self.play()
		
	def toggle_play(self):
		"""toggle playing and not playing states"""
		if self._playing:
			self.stop()
			self._playing = False
		else:
			self.play()
			self._playing = True
			
	def change_play_interval(self, msec):
		"""change the time interval between advances"""
		msec = max(msec, 500)   # at least 500msec
		msec = min(10000, msec) # at most 10s
		self.stop()
		self._autonext_interval_msec = msec
		self.start()
		

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

	# started = False

	def __init__(self, model):
		"""init control with model"""
		self.model = model

	def add_model_observer(self, view):
		"""Made sure all the views will listen to any model updates"""
		self.model.push_handlers(view)

		
	def on_key_press(self, symbol, modifiers):
		"""key press event: mostly listening for slideshow navigation"""
		if symbol in [key.RIGHT, key.LEFT]:

			if symbol == key.RIGHT:
				self.model.next()
			elif symbol == key.LEFT:
				self.model.prev()
		
		# slideshow start/stop
		elif symbol in [key.S, key.SPACE]:
			self.model.toggle_play()
			
		# adjust show timing and starts it off if not already playing
		else:
			time = 10000
			timekeys = (key.GRAVE, key._1, key._2, key._3, key._4, key._5,
						key._6, key._7, key._8, key._9, key._0)
			if symbol in timekeys:
				time = timekeys.index(symbol) * 1000
			if symbol == key.GRAVE:
				time = 500
			self.model.change_play_interval(time)
									

	# def toggle_show(self):
		# self.started = not self.started

### Helpers -------------------------------------------------------------------
def draw_rect(x, y, width, height):
	gl.glBegin(gl.GL_QUADS)
	gl.glVertex2f(x,  y)
	gl.glVertex2f(x + width, y)
	gl.glVertex2f(x + width, y + height)
	gl.glVertex2f(x, y + height)
	gl.glEnd()


class Rectangle(Sprite):
	def __init__(self, r=255, g=255, b=255, a=255, x=0, y=0, width=100, height=100,
	             batch=None, group=None, blend_src=gl.GL_SRC_ALPHA,
	             blend_dest=gl.GL_ONE_MINUS_SRC_ALPHA, usage='dynamic'):

		pattern = SolidColorImagePattern((int(r),int(g),int(b),int(a)))

		self._r = r
		self._g = g
		self._b = b
		self._a = a
		self._x = x
		self._y = y
		self._width = width
		self._height = height
		self._group = None
		self._batch = None
		self._blend_src = blend_src
		self._blend_dest = blend_dest
		self._usage = usage
		if batch is not None:
			self._batch = batch
		if group is not None:
			self._group = group

		super(Rectangle, self).__init__(
			pattern.create_image(width, height),
			x=self._x, y=self._y, batch=self._batch, group=self._group
		)

	def resize(self, width, height):
		"""resize through changing the image texture"""
		self._set_image(
			SolidColorImagePattern(
				color=(self._r,self._g,self._b,self._a)
			).create_image(width, height)
		)

	def __repr__(self):
		return super(Rectangle, self).__repr__() + ' :: ' + ' '.join(
				["%s=%s" % (k, getattr(self, k)) for k
				 in ('_r','_g','_b','_a','_x','_y','_width','_height')]
			)


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


class FileInfoBackground(Control):
	"""Moving the backgroud from widget to another class because they're not
	ordered correctly. not sure why.
	"""
	## Background
	def __init__(self, parent, x=0, y=0, width=100, height=100,
	             group=None, batch=None, **kwargs):
		super(FileInfoBackground, self).__init__(
			parent, group, batch, **kwargs
		)

		self._parent = parent
		self._x = x
		self._y = y
		self._width = width
		self._height = height
		self._group = group
		self._batch = batch

		self._rect = Rectangle(64, 64, 64, 255, x, y, width, height,
		                      self._batch, self._group)
	def draw(self):
		self._rect.draw()

	def on_fileinfo_update(self, dict): # layout_dict, parent_dict, style_dict
#		rect_x = pad = layout_dict['x']
#		rect_y = layout_dict['y'] - pad
#		rect_w = layout_dict['content_width'] + pad * 2
#		rect_h = layout_dict['content_height'] + pad * 2
#
#		self._rect.resize(rect_w, rect_h)
#		self._rect.x = rect_x
#		self._rect.y = rect_y
		pass

	def move_to(self, x, y):
		self._rect.x = x
		self._rect.y = y


	def on_resize(self, w, h):
		self._rect.resize(w, self._rect.height)
		self.x = 0
		self.y = int(h/2)
		




class FileInfoWidget(Control):
	"""Single line text display object for image meta data
	when slide show is running."""
	filename = ''
	file_id = 0
	file_total = 0

	def __init__(self, parent, x=0, y=100, group=None, batch=None,
	             **kwargs):

		super(FileInfoWidget, self).__init__(self, **kwargs)
		
		self.parent = parent
		self.x = x
		self.y = y
		self.rect_h = 30
		self.rect_w = self.parent.width
		self.group = group
		self.batch = batch

		self.filename   = None
		self.file_id    = None
		self.file_total = None
		self.document = UnformattedDocument(self.text)
		self.document.set_style(
			0, -1, dict(
				font_name='Gill Sans', font_size=12.0,
				color = (255, 255, 255, 255),
				background_color = (0, 0, 0, 0),
			    margin_left = 5,
			    margin_right = 5,
			    margin_top = 5,
			    margin_bottom = 5,
			    wrap = False
			)
		)
		self.layout = IncrementalTextLayout(
			self.document,
			width=self.rect_w, height=self.rect_h,
			batch=self.batch, group=self.group
		)

	def move_to(self, x, y):
		self.layout.x = x
		self.layout.y = y
		self.layout.width = parent.width

	@property
	def text(self):
		if self.filename is None:
			return ''
		else:
			return '[%d/%d]:\n%s' % (
				self.file_id+1, self.file_total, self.filename
			)

	def on_slideshow_model_update(self, model):
		self.filename   = model['current_file']
		self.file_id    = model['current_id']
		self.file_total = model['total_files']

		self.document.text = self.text
		self.layout.width = self.layout.content_width - 20
		self.layout.x = 10
		self.layout.y = 5

		# ie. event comes with three dictionaries
		# 1. self.layout.properties
		# 2. self.parent.properties
		# 3. self.document.get_style(properties)
		self.dispatch_event( "on_fileinfo_update", dict([
			('content_width', self.layout.width)
		]) )
#		self.dispatch_event("on_fileinfo_update",
#			dict([(key, self.layout[key])
#					for key in ('width', 'height',
#					            'content_width', 'content_height',
#		                        'x', 'y')]),
#			dict([(key, self.parent[key])
#					for key in ('width', 'height')]),
#		    dict([(key, self.document.get_style(key))
#		            for key in ('font_name', 'color', 'background_color')])
#		)



	def draw(self):
		if self.text is not '':
			self.batch.draw()

FileInfoWidget.register_event_type("on_fileinfo_update")


class ImageView(object):
	"""Container of an image"""

	def __init__(self, parent, **kwargs):
		self.parent = parent
		self.x = 0
		self.y = 0
		self.batch = pyglet.graphics.Batch()
		self.group = None
		self.sprite = None
		self.image = None
		self.texture = None

		for key in ('img', 'x', 'y', 'batch', 'group', 'usage', 'folder'):
			if key in kwargs:
				setattr(self, key, kwargs[key])

		self.background = Rectangle(0, 0, 0, 255, 0, 0, 90, 90)
		print("Image View Background")
		print(self.background)


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
		self.background.resize(width, height)
		
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
		self.batch.draw()

		

class AppWindow(pyglet.window.Window):
	"""Main app window"""

	def __init__(self, folder, width=800, height=600, caption="Image Viewer",
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
		self.file_info_bg = FileInfoBackground(
			self, x=0, y=0, width=self.width, height=40,
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

		# EVENTS: slideshow events
		self.ss_control.add_model_observer( self.image_view )
		self.ss_control.add_model_observer( self.file_info )
		# EVENTS: file info update event
#		self.file_info.push_handlers(self.file_info_bg)
		# EVENTS: window UI events
		self.push_handlers(self.ss_control)
		self.push_handlers(self.image_view)
		self.push_handlers(self.file_info_bg)


	def update(self, _):
		self.on_draw()
#		self.clock += .01

	def on_draw(self):
		self.clear()

		self.file_info_bg.draw()
		self.file_info.layout.draw()
		self.file_info.draw()
		self.image_view.draw()

	# Window control behavior
	def on_key_press(self, symbol, modifiers):
		if symbol == key.Q:
			pyglet.app.exit()

		if symbol ==  key.BRACKETLEFT:
			self.width  = max(200, int(float(self.width)  * 0.9))
			self.height = max(150, int(float(self.height) * 0.9))
			self.x = int((1400-self.width)/2)
			self.y = int((900-self.height)/2)

		if symbol ==  key.BRACKETRIGHT:
			self.width  = min(1400, int(float(self.width)  * 1.1))
			self.height = min(900,  int(float(self.height) * 1.1))
			self.x = int((1400-self.width)/2)
			self.y = int((900-self.height)/2)

		

	

def main(argv):
	_folder = '/Volumes/Proteus/Pictures/test'
	_caption = 'ImageViewer64'
	if argv is not None:
		if len(argv) > 1:
			_folder = argv[1]
		if len(argv) > 2:
			_caption = argv[2]
	window = AppWindow(folder=_folder, caption=_caption)
	pyglet.app.run()
		
		

if __name__ == '__main__':
	main(sys.argv)

# Debug in terminal with ipython:
# ipythonw -i pyglet_imageviewer.py '{foldername}'
