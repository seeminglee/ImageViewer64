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
from cocos.layer import Layer
from cocos.layer import ColorLayer
from cocos.scene import Scene
from cocos.sprite import Sprite
from cocos.text import Label
from cocos.actions import CallFunc
from cocos.actions import CallFuncS
from cocos.actions import FadeIn
from cocos.actions import FadeOut
import PIL
from PIL import Image
from PIL import ImageDraw
from PIL import ImageChops
import cocos
import pyglet
from pyglet.image.codecs.pil import PILImageDecoder
#from cStringIO import StringIO
from StringIO import StringIO
from pyglet.image import SolidColorImagePattern
from pyglet.gl import gl
from random import randrange


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
def shell_quote(s):
	return "'" + s.replace("'", "'\\''") + "'"


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

FitType = EnumUtil.enum('ScaleFitFull',
	                    'ScaleFitAspectFit',
	                    'ScaleFitAspectFill')

class SizeFitting(object):
	"""Utility to keep aspect ratio the same before and after scaling using
	three different algorithms."""

	@staticmethod
	def scaleToSize(orig_w, orig_h, target_w, target_h,
	                fit_type=FitType.ScaleFitFull):
		orig_w = float(orig_w)
		orig_h = float(orig_h)
		target_w = float(target_w)
		target_h = float(target_h)

		target_aspect = target_w / target_h
		orig_aspect = orig_w / orig_h

		x_scale = 0.0
		y_scale = 0.0

		if fit_type is FitType.ScaleFitFull:
			x_scale = target_w / orig_w
			y_scale = target_h / orig_h

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

		xscale = x_scale
		yscale = y_scale
		result_w = int(orig_w * x_scale)
		result_h = int(orig_h * y_scale)
		dx = abs(x_scale*orig_h-target_w)
		dy = abs(y_scale*orig_h-target_h)

		return (xscale, yscale, result_w, result_h, dx, dy)


class BackgroundLayer(ColorLayer):
	"""The absolute bottomest window."""

	is_event_handler = True

	def __init__(self, r, g, b, a, width=100, height=100):
		super(BackgroundLayer, self).__init__(r, g, b, a, width, height)
		print("INIT >>> BackgroundLayer.init() ")


class PaddedSpriteLayer(ColorLayer):
	"""This is a color layer with a sprite in it. Alternativley you can see it
	as a sprite padded by a solid color"""
	def __init___(self, r=0, g=0, b=0, a=255,
	              width=None, height=None, sprite=None):

		super(PaddedSpriteLayer, self).__init__(r,g,b,a, width, height)
		self.add(sprite, z=2, name="sprite")

		if sprite is not None:
			self.sprite = sprite

class ImageUtil(object):
	"""Utility functions for images: mainly for PIL"""

	@staticmethod
	def toPIL(image):
		"""convert a pygame image to a PIL image"""
#		raw = pygame.image.tostring(image, "RGBX")
		raw = image.get_image_data()
		return Image.fromstring("RGBX",
		                           image.get_size(),
		                           raw)

	@staticmethod
	def fromPIL(pilimage):
		"""convert a PIL image to a pygame image"""
		raw = pilimage.tostring()
		return pygame.image.fromstring(raw, pilimage.size, "RGBX")

	@staticmethod
	def resize(image, size, filter=Image.BICUBIC):
		"""resize a pygame image"""
		return fromPIL(toPIL(image).resize(size, filter))


class ImageLayer(Layer):
	"""Container of an image"""

	is_event_handler = False

	def __init__(self):
		print("INIT >>> ImageLayer.init() ")
		super(ImageLayer, self).__init__()
		self.texture = None
		self.sprite = None
		self.image = None
		self.image_file = None
		self.window_width = None
		self.window_height = None
		self.sprites = []
		self.fading = []
		self.z = 10
		self.pads = []
		self.anchor = (0, 0)
		self.transform_anchor = (0, 0)

	def on_slideshow_model_update(self, model):
		print("ImageLayer.on_slideshow_model_update")
		self.image_file = model.current_file
		self.add_image_sprite()


	def add_image_sprite(self):
		print("ImageLayer.add_image_layer()")

		pil = PIL.Image.open(self.image_file)
		pyglet_img = pyglet.image.load(self.image_file)
		target_w = self.window_width
		target_h = self.window_height
		orig_w = pil.size[0]
		orig_h = pil.size[1]

		id = self.next_id
		print(pil)

		( xscale, yscale,
		  result_w, result_h, dx, dy ) = SizeFitting.scaleToSize(
										 orig_w, orig_h,
				                         target_w, target_h,
		                                 FitType.ScaleFitAspectFit)
		imgsprite = Sprite(pyglet_img)
		imgsprite.anchor = (0, 0)
		imgsprite.transform_anchor = (0, 0)

		bg_w = int(float(target_w) / xscale)
		bg_h = int(float(target_h) / yscale)

		background = SolidColorImagePattern(
			color=self.random_color
		).create_image(width=bg_w, height=bg_h)

		bgsprite = Sprite(background)
		bgsprite.add(imgsprite, z=id, name="image%d" % id)
		bgsprite.anchor = (0, 0)
#		bgsprite.anchor = (dx/xscale*-4, dy/yscale*-4)
		bgsprite.scale = xscale


		self.add(bgsprite, z=id, name="spritelayer%d" % id)

		bgsprite.opacity = 0
		bgsprite.do( FadeIn(1) )

		########## DEBUG
		bg = bgsprite
		lists = [ "orig_w result_w bg_w target_w xscale".split(" "),
		          "orig_h result_h bg_h target_h yscale".split(" "),
		          "bg.width bg.height bg.anchor bg.transform_anchor".split(" ")
				]
		debug = "id: %2d " %id
		for list in lists:
			debug += "\n"
			for  key in list:
				debug += "{k:>5}: {v:>4}  ".format(k=key, v=eval(key))
		print debug


	@property
	def random_color(self):
		r = randrange(128, 180, 1)
		g = randrange(128, 180, 1)
		b = randrange(240, 255, 1)
		a = 255
		return (r, g, b, a)

	@property
	def next_id(self):
		self.z += 1
		return self.z

	def on_resize(self, width, height):
		print("ImageLayer.on_resize()")
		self.window_width = width
		self.window_height = height

	@classmethod
	def load_texture(cls, file):
		try:
			image = pyglet.image.load(file)
		except pyglet.image.codecs.dds.DDSException:
			print ("%s is not a valid image file." % file)
			raise ImageViewerError

		return image




class TextWidgetLayer(Layer):
	"""The absolute bottomest window."""

	is_event_handler = True

	def __init__(self, r=0, g=0, b=0, a=255, width=100, height=100):
		print("INIT >>> TextWidgetLayer.init() ")
		self.color = (r,g,b,a)
		self.width = width
		self.height = height

		super(TextWidgetLayer, self).__init__()




class FileInfoLayer(Layer):

	is_event_handler = False

	def __init__(self, text='', position=(0, 0), **kwargs):
		print("INIT >>> FileInfoLayer.init() ")
		super(FileInfoLayer, self).__init__()
		self.model = None
		self.background = cocos.layer.util_layers.ColorLayer(0, 0, 0, 128, 1000, 30)
		self.label = Label(
			"Label1", x=10, y=10,
			font_name='Gill Sans',
			font_size=10,
		    color=(250, 250, 250, 255),
		    anchor_x = "left",
		    anchor_y = "baseline",
		    multiline = False
		)

		self.add(self.background, name="background")
		self.add(self.label, name="label")


	def on_slideshow_model_update(self, model):
		print("FileInfoLayer.ON_SLIDESOW_MODEL_UPDATE")
		self.model = model
		self.label.element.text = self.text
		print("FileInfoLayer: %s" % self.text)

	def on_draw(self):
		self.background.draw()
		self.label.draw()

	@property
	def text(self):
		if self.model is None:
			return ''
		else:
			return '%d / %d: %s' % \
		        (self.model.current_id+1, self.model.total_files,
		        self.model.current_file)





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

class SlideshowController(object):
	"""controller for slideshow interactions"""

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

		# window resizing
		elif symbol in [pyglet.window.key.BRACKETLEFT,
		                pyglet.window.key.BRACKETRIGHT]:
			win = director.window
			if symbol == pyglet.window.key.BRACKETLEFT:
				win.width =  int(max(200, win.width * 0.9))
				win.height = int(max(150, win.height * 0.9))
			elif symbol == pyglet.window.key.BRACKETRIGHT:
				win.width =  (min(1200,win.width * 1.1))
				win.height = (min(850, win.height * 1.1))

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



class SingleImageScene(Scene):

	def __init__(self, *children):
		"""Creates a Scene with layers and / or scenes."""
		super(SingleImageScene, self).__init__(*children)


class Controller():

	def __init__(self, folder):
		director.init(
			width=800, height=600, caption="Image Viewer", fullscreen=False,
		    do_not_scale=True, resizable=True
		)

		bg = BackgroundLayer(0, 0, 0, 255, width=800, height=600)
		img = ImageLayer()
		info = FileInfoLayer()

		self.scene = SingleImageScene()
		self.scene.add(bg,   z=1, name = "bg")
		self.scene.add(img,  z=4, name = "img")
		self.scene.add(info, z=9, name = "info")
		self.scene.push_all_handlers()


		self.slideshowController = SlideshowController(folder)
		self.slideshowController.add_model_update_handlers(
			[bg, img, info]
		)
		director.window.push_handlers(self.slideshowController)
		director.window.push_handlers(img)


		print ("INIT >>> SingleImageScene.init()")



	def run(self):
		director.run(self.scene)


def main():
	controller = Controller('/Volumes/Proteus/virtualbox/_share/bru')
	controller.run()


if __name__ == '__main__':
	main()

