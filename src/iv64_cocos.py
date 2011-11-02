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
import sys
import os
import os.path
import pyglet.gl

import cocos


### Exceptions ----------------------------------------------------------------


class ImageViewerError(Exception):
	def __init__(self, msg):
		self.msg = msg
	def __str__(self):
		return repr(self.msg)


class ImageLoadFileIOError(ImageViewerError): pass
class FontUnavailableError(ImageViewerError): pass
class InvalidFolderError(ImageViewerError): pass




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

#	@property
#	def playing(self):
#		return self._playing
#
#	def play(self):
#		"""Schedule and start auto-advance to next slide"""
#		print("play args:")
#		print(args)
#		pyglet.clock.schedule_once( self.play_next,
#									self._autonext_interval_msec)
#		# instead of using interval schedules, it just callls the same
#		# function repeated so if the system is backed up it won't create
#		# additional problems
#		self._playing = True
#
#	def stop(self):
#		"""Stop animation"""
#		pyglet.clock.unschedule(self.play_next)
#		self._playing = False
#
#	def play_next(self):
#		"""auto advance to next"""
#		print("plext_next() args:")
#		print(args)
#		self.next()
#		self.play()
#
#	def toggle_play(self):
#		"""toggle playing and not playing states"""
#		if self._playing:
#			self.stop()
#			self._playing = False
#		else:
#			self.play()
#			self._playing = True
#
#	def change_play_interval(self, msec):
#		"""change the time interval between advances"""
#		msec = max(msec, 500)   # at least 500msec
#		msec = min(10000, msec) # at most 10s
#		self.stop()
#		self._autonext_interval_msec = msec
#		self.start()


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


class SlideshowView(cocos.scene.Scene):
	"""The main scene: where a single image is displayed at any given time,
	showing its metadata and allowing the user to control the animation
	manually all allows the scene to play with them automatically.."""


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

		if fit_type == FitType.ScaleFitFull:
			x_scale = target_w / origin_w
			y_scale = target_h / origin_h

		elif fit_type == FitType.ScaleFitAspectFit:
			if target_aspect > orig_aspect:
				x_scale = y_scale = target_h / orig_h
			else:
				y_scale = x_scale = target_w / orig_w

		elif fit_type == FitType.ScaleFitAspectFill:
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

	def on_resize(self, target):
		if isinstance(target, width, height):
			
	def draw(self):
		gl.glPushMatrix()
		self.transform()
		# ... draw ..
		gl.glPopMatrix()

	