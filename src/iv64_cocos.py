#!/usr/bin/env python
# encoding: utf-8
"""
cocos_imageviewer. Third time is a charm? Testing cocos2d framework
which is based on the pyglet framework. It appears to have some more concrete
examples of how the authors envisioned apps be pieced together. Since it's
based on Pyglet, it also uses the very fast OpenGL underneath.
Let's see if this will cut my coding time by half.

Created by See-ming Lee on 2011-11-01.
Copyright (c) 2011 See-ming Lee. All rights reserved.
"""
import re
import os
import os.path
from cocos.director import director
from pyglet import event
import cocos
from pyglet.gl import gl
import pyglet





### Exceptions ----------------------------------------------------------------

class ImageViewerError(Exception):
	def __init__(self, msg):
		self.msg = msg
	def __str__(self):
		return repr(self.msg)


class ImageLoadFileIOError(ImageViewerError): pass
class FontUnavailableError(ImageViewerError): pass
class InvalidFolderError(ImageViewerError): pass


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





class EnumUtil(object):
	"""Utility for enum'ing constants.
	Usage:
			Numbers = enum('ZERO', 'ONE', 'TWO')
			Numbers.ZERO --> 0
			Numbers.ONE  --> 1
	Source:
	http://stackoverflow.com/questions/36932/whats-the-best-way-to-implement-an-enum-in-python
	"""
	@staticmethod
	def enum(*sequential, **named):
		enums = dict(zip(sequential, range(len(sequential))), **named)
		return type('Enum', (), enums)



class Util_Scaler(object):
	"""Utility to keep aspect ratio the same before and after scaling using
	three different algorithms."""

	FitType = EnumUtil.enum('ScaleFitFull',
	                        'ScaleFitAspectFit',
	                        'ScaleFitAspectFill')

	@staticmethod
	def scaleToSize(orig_w, orig_h, target_w, target_h,
	                fit_type=FitType.ScaleFitFull):
		orig_w = float(orig_w)
		orig_h = float(orig_h)
		target_w = float(target_w)
		target_h = float(target_h)

		target_aspect = target_w / target_h
		orig_aspect = orig_w / orig_h

		if fit_type is FitType.ScaleFitFull:
			x_scale = target_w / origin_w
			y_scale = target_h / origin_h

		elif fit_type is FitType.ScaleFitAspectFit:
			if target_aspect > orig_aspect:
				x_scale = y_scale = target_h / orig_h
			else:
				y_scale = x_scale = target_w / orig_w

		elif fit_type is FitType.ScaleFitAspectFill:
			if target_aspect > orig_aspect:
				x_scale = y_scale = target_w / orig_w
			else:
				y_scale = x_scale = target_h / orig_h

		return x_scale, y_scale


class BackgroundLayer(cocos.layer.ColorLayer):
	"""The absolute bottomest window."""

	is_event_handler = True

	def __init__(self, r, g, b, a, width=100, height=100):
		super(BackgroundLayer, self).__init__(r, g, b, a, width, height)
		print("INIT >>> BackgroundLayer.init() ")



class ImageLayer(cocos.layer.Layer):
	"""Container of an image"""

	is_event_handler = False

	def __init__(self):
		print("INIT >>> ImageLayer.init() ")
		super(ImageLayer, self).__init__()
		self.texture = None
		self.sprite = None
		self.image_file = None

	def on_slideshow_model_update(self, model):
		print("ImageLayer.on_slideshow_model_update")
		self.image_file = model.current_file
		self.create_sprite()


	def create_sprite(self):
		print("ImageLayer.create_sprite()")

		scale = Util_Scaler.scaleToSize(
				self.texture.width, self.texture.height,
				winsize.width, winsize.height,
				FitType.ScaleFitAspectFit
			)
		self.sprite = cocos.sprite.Sprite(
				self.image_file, scale=scale, anchor=(0,0)
			)

	def on_key_press(self, symbol, modifiers):
		print("ImageLayer.on_key_press")

	@classmethod
	def load_texture(cls, file):
		try:
			image = pyglet.image.load(file)
		except pyglet.image.codecs.dds.DDSException:
			print ("%s is not a valid image file." % file)
			raise ImageViewerError

		return image



### User Interface ------------------------------------------------------------
class Control(event.EventDispatcher):
	"""An AbstractControl of the user interface"""
	x = y = 0
	width = height = 10

	def __init__(self):
		pass

	def hit_test(self, x, y):
		return (self.x < x < self.x + self.width and
		        self.y < y < self.y + self.height)

	def capture_events(self):
		self.parent.push_handlers(self)

	def release_events(self):
		self.parent.remove_handlers(self)


#class Button(Control):
#	charged = False
#
#	def __init__(self):
#		pass
#
#
#	def draw(self):
#		if self.charged:
#			gl.glColor3f(1, 0, 0)
#		draw_rect(self.x, self.y, self.width, self.height)
#		gl.glColor3f(1, 1, 1)
#		self.draw_label()
#
#	def on_mouse_press(self, x, y, button, modifiers):
#		self.capture_events()
#		self.charged = True
#
#	def on_mouse_draw(self, x, y, dx, dy, buttons, modifiers):
#		self.charged = self.hit_test(x, y)
#
#	def on_mouse_release(self, x, y, button, modifiers):
#		self.release_events()
#		if self.hit_test(xy):
#			self.dispatch_event('on_button_press')
#		self.charged = False
#
#Button.register_event_type('on_button_press')


class TextWidgetLayer(cocos.layer.Layer):
	"""The absolute bottomest window."""

	is_event_handler = True

	def __init__(self, r=0, g=0, b=0, a=255, width=100, height=100):
		print("INIT >>> TextWidgetLayer.init() ")
		self.color = (r,g,b,a)
		self.width = width
		self.height = height

		super(TextWidgetLayer, self).__init__()


#

class FileInfoLayer(cocos.layer.Layer):

	is_event_handler = False

	def __init__(self, text='', position=(0, 0), **kwargs):
		print("INIT >>> FileInfoLayer.init() ")
		super(FileInfoLayer, self).__init__()
		self.model = None
		self.background = cocos.layer.util_layers.ColorLayer(250, 0, 0, 250, 1000, 30)
		self.label = cocos.text.Label(
			font_name='PT Sans',
			font_size=14,
		    color=(250, 250, 250, 255),
		    anchor_x = "left",
		    anchor_y = "baseline",
		    multiline = False
		)
		self.add(
			self.background,
			self.label
		)

	def on_slideshow_model_update(self, model):
		print("FileInfoLayer.ON_SLIDESOW_MODEL_UPDATE")
		self.model = model
		self.label.text = self.text
		print("FileInfoLayer: %s" % self.text)

	@property
	def text(self):
		if self.model is None:
			return ''
		else:
			return '[%d  / %d] %s' % \
		        (self.model.current_id+1, self.model.total_files,
		        self.model.current_file)


class SlideshowModelUpdate(object):
	def __init__(self):
		pass



class SlideshowModel(pyglet.event.EventDispatcher):
	"""model of the slideshow"""



	def __init__(self, folder):
		"""initialize with name of the folder"""
		super(SlideshowModel, self).__init__()
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
#		print(args)
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
		self.play()


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

		self._dispatch_slideshow_update()

		print("current id: %d" % self.current_id)


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

		self._dispatch_slideshow_update()

	def limit_id_range(self):
		self._current_id = (self._current_id + len(self.files)) \
				% len(self.files)

	def _dispatch_slideshow_update(self):
		print ("SS_MODEL DISPATCH UPDATE >>>\n" +
		       "[%d/%d] file=%s") % (self.current_id,
		                                self.total_files,
										self.current_file)
		self.dispatch_event(
			"on_slideshow_model_update", self
		)
#		self.dispatch_event(
#		    "on_slideshow_model_update",
#		    dict(
#			    current_id   = self.current_id,
#		        current_file = self.current_file,
#		        total_files  = self.total_files
#		    )
#
#		)

	def __repr__(self):
		return "SlideshowModel:" + \
		       "\n".join([(k, getattr(self, k)) for k in self.__dict__])


SlideshowModel.register_event_type("on_slideshow_model_update")


### Controllers ---------------------------------------------------------------

class SlideshowController(cocos.layer.Layer):
	"""controller for slideshow interactions"""

	is_event_handler = True

	def __init__(self, folder):
		"""Create a controller capable of handling the slidehow user inputs"""
		super(SlideshowController, self).__init__()


		self.model = SlideshowModel(folder)


	def on_key_press(self, symbol, modifiers):
		"""key press event: mostly listening for slideshow navigation"""

		print ("SS CONTROL: ON_KEY_PRESS")

		if symbol in [pyglet.window.key.RIGHT, pyglet.window.key.LEFT]:

			if symbol == pyglet.window.key.RIGHT:
				self.model.next()
			elif symbol == pyglet.window.key.LEFT:
				self.model.prev()

		# slideshow start/stop
		elif symbol in [pyglet.window.key.S, pyglet.window.key.SPACE]:
			self.model.toggle_play()

		# adjust show timing and starts it off if not already playing
		else:
			time = 10000
			timekeys = (pyglet.window.key.GRAVE, pyglet.window.key._1,
			            pyglet.window.key._2, pyglet.window.key._3,
			            pyglet.window.key._4, pyglet.window.key._5,
						pyglet.window.key._6, pyglet.window.key._7,
						pyglet.window.key._8, pyglet.window.key._9,
						pyglet.window.key._0)
			if symbol in timekeys:
				time = timekeys.index(symbol) * 1000
			if symbol == pyglet.window.key.GRAVE:
				time = 500
			self.model.change_play_interval(time)

	def add_model_update_handlers(self, list):
		for obj in list:
			self.model.push_handlers(obj)



class SingleImageScene(cocos.scene.Scene):

	is_event_handler = True

	def __init__(self, folder, *children):
		"""Creates a Scene with layers and / or scenes."""
		super(SingleImageScene, self).__init__(*children)

		ss_control = SlideshowController(folder)
		self.add(ss_control, name="slideshowController")
		self.add(
			BackgroundLayer(64, 0, 0, 255, width=800, height=600),
			name="backgroundLayer"
		)
		self.add(ImageLayer(), name="imageLayer")
		self.add(FileInfoLayer(), name="fileInfoLayer")

		ss_control.add_model_update_handlers(
			[c for c in self.children if c is not ss_control]
		)
#		for c in self.children:
#			self.model.push_handlers(c)


		self.enable_handlers()
		self.push_all_handlers()

		print ("INIT >>> SingleImageScene.init()")


if __name__ == "__main__":

	director.init(
		width=800, height=600, caption="Image Viewer", fullscreen = False
	)
	scene = SingleImageScene('/Volumes/Proteus/virtualbox/_share/bru')
	scene.enable_handlers()
	director.run(scene)

#	ss_model = SlideshowModel('/Volumes/Proteus/virtualbox/_share/bru')
#	ss_control = SlideshowController(ss_model)
#
#	scene = cocos.scene.Scene()
#	scene.add(ss_control, name = "ss_control")
#	scene.add(
#		BackgroundLayer(64, 0, 0, 255, width=800, height=600),
#		name="backgroundLayer"
#	)
#	scene.add(ImageLayer(), name="imageLayer")
#	scene.add(FileInfoLayer(), name="fileInfoLayer")


	# event registration
#	SlideshowModel.register_event_type("on_slideshow_model_update")

	# event handler registrations
#	for c in scene.children:
#		ss_model.push_handlers(c)

#



