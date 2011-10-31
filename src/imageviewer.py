#!/usr/bin/env python
# encoding: utf-8
"""
imageviewer: Slideshow viewer based on pygame and PIL

Created by See-ming Lee on 2011-10-28.
Copyright (c) 2011 See-ming Lee. All rights reserved.
"""
__author__ = 'See-ming Lee'
__email__ = 'seeminglee@gmail.com'

import os
import pygame
from pygame.locals import *
from PIL import Image
import string
import random
import re
import sys

class ImageViewerError(Exception): pass
class ImageLoadFileIOError(ImageViewerError): pass
class FontUnavailableError(ImageViewerError): pass


def loadImage(fullname=None):
	"""Load image and return image object and its rect"""
	try:
		image = pygame.image.load(fullname)
		if image.get_alpha is None:
			image = image.convert()
		else:
			image = image.convert_alpha()
	except pygame.error, message:
		print 'Cannot load image:', fullname
		# raise SystemExit, message
		raise ImageLoadFileIOError, message
	return image, image.get_rect()


class ImageUtil(object):
	"""Utility functions for images: mainly for PIL"""

	@staticmethod
	def toPIL(image):
		"""convert a pygame image to a PIL image"""
		raw = pygame.image.tostring(image, "RGBX")
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


class ImageView(pygame.sprite.Sprite):
	"""Container of a single image as a sprite"""

	def __init__(self, filename=None):
		"""initialize with the image filename"""
		pygame.sprite.Sprite.__init__(self)
		self.alpha = 0
		self.bg_color = (0, 0, 0)
		self.filename = None
		self.original_image = None
		self.original_rect = None
		self.image = None
		self.rect = None
		self.imagenow = None
		self.imagetgt = None
		self.set_filename(filename)

	def set_filename(self, filename):
		if filename is not None and os.path.exists(filename):
			if self.alpha < 255 and self.image is not None:
				self.image = self.imagetgt
				self.image.set_alpha(255)
				self.alpha = 255
			self.filename = filename
			self.original_image, self.original_rect = loadImage(filename)
			self.update()

	def update(self):
		"""Update drawing"""
		if self.filename is not None:
			self.rect = winrect = self.get_window_rect()

			if self.alpha == 0:
				image, self.rect = self.fit_to_window(self.original_image,
											self.original_rect,
											winrect)
				self.imagetgt = self.padded_image(image, winrect.size, self.bg_color)
				if self.image is None:
					self.image = pygame.Surface(winrect.size)
				self.alpha += 5
			elif self.alpha < 255:
				self.imagetgt.set_alpha(self.alpha)
				self.image.blit(self.imagetgt, (0,0))
				self.alpha += 5
				if self.alpha >= 255:
					self.alpha = 255
			else:
				self.imagetgt.set_alpha(255)
				self.image = self.imagetgt
				self.alpha = 0


	@staticmethod
	def get_window_rect():
		return pygame.display.get_surface().get_rect()

	@staticmethod
	def fit_to_window(inimage, inrect, winrect):
		"""return scaled image and scaled rect which fits the window"""
		scaled = inrect.fit(winrect)
		image = pygame.transform.smoothscale(inimage, scaled.size)
		image = image.convert()
		rect = Rect((0,0), scaled.size)
		return image, rect

	@staticmethod
	def padded_image(image, size, bgcolor):
		"""return image padded with background color to fill the entire window"""
		surf = pygame.Surface(size).convert()
		surf.fill(bgcolor)
		surf.blit(image, (0, 0))
		return surf



class FileInfo(pygame.sprite.Sprite):
	"""Meta information about the file"""

	def __init__(self, filename='', index=None, total=None):
		"""initialization. optionally add name of file"""
		pygame.sprite.Sprite.__init__(self)
		self.bg_height = 20
		self.font = pygame.font.Font(pygame.font.match_font('Helvetica'), 12)
		self.fg_color = (50, 50, 50)
		self.bg_color = (250, 250, 250)
		self.image = None
		self.rect = None
		self.visible = True
		# set meta calls update directly. So put this last
		self.set_meta(filename, index, total)

	def update(self):
		"""display current meta"""
		if self.visible:
			info = self.info()
			text = self.font.render(info, 1, self.bg_color, self.fg_color)
			textpos = text.get_rect(left=5, bottom=self.bg_height-3)
			self.image = pygame.Surface((text.get_width()+10, self.bg_height))
			self.image.fill(self.fg_color)
			self.image.blit(text, textpos)
			self.image.set_alpha(255)
			self.screen = pygame.display.get_surface()
			self.rect = pygame.Rect((0, 0), self.image.get_size())
			self.rect.bottomleft = (0, self.screen.get_height()+1)
		else:
			self.image.set_alpha(0)

	def toggle_visibility(self):
		"""show / hide the meta info"""
		self.visible = not self.visible

	def set_meta(self, filename='', index=None, total=None):
		"""set the filename and other meta info
		@filename name of the file, string
		index     position of the file among files, integer
		total     total number of files, integer"""
		self.set_filename(filename)
		self.index = index
		self.total = total
		self.update()

	def set_filename(self, filename=''):
		"""set the filename"""
		self.filename = os.path.abspath(filename)

	def _wackytest(self):
		"""for testing only. ignore"""
		word = ''
		for i in range(random.randrange(24,37)):
			word += random.choice(string.letters)
		self.filename = word

	def info(self):
		"""Return completed info in this format:
		[n/total]: filename """
		text = ''
		if self.index is not None and self.total is not None:
			text += '[%d/%d]: ' % (self.index+1, self.total) #display info is 1-based
		text += self.filename
		return text

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
		return self._abspath(self.allfiles)

	def images(self):
		"""Return all image files contained in folder"""
		return self._abspath(self.imagefiles)

	def jpgs(self):
		"""Return list of jpegs"""
		return self._abspath([f for f in self.allfiles if FileType.is_jpg.search(f)])

	def gifs(self):
		"""Return list of gifs only"""
		return self._abspath([f for f in self.allfiles if FileType.is_gif.search(f)])

	def pngs(self):
		"""Return list of gifs only"""
		return self._abspath([f for f in self.allfiles if FileType.is_png.search(f)])

	def _abspath(self, files=None):
		"""Return a list of files with absolute paths"""
		if files is None:
			files = self.allfiles
		return [os.path.join(self.path, f) for f in files]


class Queue(object):
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

	
def main(argv=None):
	folder=argv[1]
	# Initialise screen
	pygame.init()
	screen = pygame.display.set_mode((640, 480), pygame.RESIZABLE)
	pygame.display.set_caption('Image Viewer')

	# Fill background
	background = pygame.Surface(screen.get_size())
	background = background.convert()
	background.fill((0, 0, 0))

	# Initialise clock
	clock = pygame.time.Clock()


	# Initialise game objects
	folder = Folder(folder)
	queue = Queue(folder.images())

	fileinfo = FileInfo( filename=queue.current_file(),
	                     index=queue.current_index,
	                     total=queue.total_files() )
	fileinfo.update()

	imageview = ImageView(filename=queue.current_file())
	imageview.update()

	# Fill background
	backsprite = pygame.sprite.Sprite()
	rect = Rect((0,0),(1400,900))
	background = pygame.Surface(rect.size)
	background = background.convert()
	background.fill((0, 0, 0))
	backsprite.image = background
	backsprite.rect = rect

	allsprites = pygame.sprite.LayeredUpdates((backsprite, imageview, fileinfo))
	
	# Blit everything to screen
	screen.blit(background, (0, 0))
	allsprites.draw(screen)
	pygame.display.flip()
	

	# Fullscreen control
	is_fullscreen = False
	screen_size = (640, 480)

	def create_screen(size=(640, 480), is_fullscreen=False):
		if is_fullscreen:
			screen = pygame.display.set_mode((1400,900), pygame.FULLSCREEN)
		else:
			screen = pygame.display.set_mode(size, pygame.RESIZABLE)

	# reset screen
	def update_screen(screen):
		"""Reset display when screen is updated"""
		pygame.display.set_caption('Image Viewer')

		allsprites.update()
		allsprites.draw(screen)
		pygame.display.flip()

	# update screen
	update_screen(screen)


	# Event: auto-advance (aka slideshow)
	SLIDESHOW_NEXTIMAGE      = pygame.USEREVENT + 4
	slideshow_nextimage_evt  = pygame.event.Event(SLIDESHOW_NEXTIMAGE)
	SLIDESHOW_PREVIMAGE      = pygame.USEREVENT + 3
	slideshow_previmage_evt  = pygame.event.Event(SLIDESHOW_PREVIMAGE)
	SLIDESHOW_TOGGLEINFO     = pygame.USEREVENT + 2
	slideshow_toggleinfo_evt = pygame.event.Event(SLIDESHOW_TOGGLEINFO)
	slideshow_started = False

	# constants
	NUM_KEYS = [K_1, K_2, K_3, K_4, K_5, K_6, K_7, K_8, K_9, K_0]

	# so NUM_TIME[K_1] = 1000, NUM_TIME[K_6] = 7000
	NUM_TIME = dict([(v, (NUM_KEYS.index(v)+1)*1000) for v in NUM_KEYS ])

	slideshow_delay_time = 2000

	# Event loop
	while 1:
		# Make sure game doesn't run at more than 60 fps
		clock.tick(60)

		for event in pygame.event.get():

			# game quit
			if event.type == QUIT:
				return

			# WINDOW: resize
			elif event.type == VIDEORESIZE:
				screen_size = event.size
				create_screen(screen_size, is_fullscreen=False)

			# SLIDESHOW: next file
			elif event.type == SLIDESHOW_NEXTIMAGE:
				queue.next()
				fileinfo.set_meta( filename=queue.current_file(),
								   index=queue.current_index,
								   total=queue.total_files() )
				imageview.set_filename( filename=queue.current_file() )

			# SLIDESHOW: previous file
			elif event.type == SLIDESHOW_PREVIMAGE:
				queue.prev()
				fileinfo.set_meta( filename=queue.current_file(),
								   index=queue.current_index,
								   total=queue.total_files() )
				imageview.set_filename( filename=queue.current_file() )

			# SLIDESHOW: toggle info
			elif event.type == SLIDESHOW_TOGGLEINFO:
				fileinfo.toggle_visibility()
				fileinfo.update()

			# keyboard inputs
			elif event.type == KEYUP:

				# APP: exit
				if event.key == K_q:
					return

				# WINDOW: full screen toggle
				elif event.key == K_f:
					is_fullscreen = not is_fullscreen
					old_screen_size = pygame.display.get_surface().get_size()
					create_screen(is_fullscreen=is_fullscreen)

				# SLIDESHOW: forward
				elif event.key == K_RIGHT:
					pygame.event.post(slideshow_nextimage_evt)

				# SLIDESHOW: backward
				elif event.key == K_LEFT:
					pygame.event.post(slideshow_previmage_evt)

				# SLIDESHOW: Start / Stop
				elif event.key == K_SPACE or event.key == K_s:
					slideshow_started = not slideshow_started
					if slideshow_started:
						pygame.time.set_timer(SLIDESHOW_NEXTIMAGE, slideshow_delay_time)
					else:
						pygame.time.set_timer(SLIDESHOW_NEXTIMAGE, 0)

				# SLIDESHOW: toggle info
				elif event.key == K_i:
					pygame.event.post(slideshow_toggleinfo_evt)


				# SLIDESHOW: speed control: 1000-10000ms
				elif event.key in NUM_KEYS:
					pygame.time.set_timer(SLIDESHOW_NEXTIMAGE, 0)
					slideshow_delay_time = NUM_TIME[event.key]
					pygame.time.set_timer(SLIDESHOW_NEXTIMAGE, slideshow_delay_time)
					slideshow_started = True

				# SLIDESHOW: speed control: 500ms
				elif event.key == K_BACKQUOTE:
					pygame.time.set_timer(SLIDESHOW_NEXTIMAGE, 0)
					slideshow_delay_time = 500
					pygame.time.set_timer(SLIDESHOW_NEXTIMAGE, slideshow_delay_time)
					slideshow_started = True

		update_screen(screen)


if __name__ == '__main__':
	if len(sys.argv) < 2:
		main(['','/Volumes/Proteus/Pictures/test'])
	else:
		main(sys.argv)


