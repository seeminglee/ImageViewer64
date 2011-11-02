#!/usr/bin/env python
# encoding: utf-8
"""
Cocos_lessons_2

Created by See-ming Lee on 2011-11-01.
Copyright (c) 2011 See-ming Lee. All rights reserved.
"""
from cocos.actions.base_actions import Repeat, Reverse
from cocos.actions.interval_actions import ScaleBy

__author__ = 'See-ming Lee'
__email__ = 'seeminglee@gmail.com'


import cocos
import cocos.actions


class HelloWorld(cocos.layer.ColorLayer):
	def __init__(self):
		super( HelloWorld, self).__init__(64, 64, 224, 255)

	label = cocos.text.Label('Hello, World!',
		font_name='PT Sans',
		font_size=32, anchor_x='center', anchor_y='center')
	label.position = 320, 240
	self.add(label)

	sprite = cocos.sprite.Sprite('resources/grossini.png')
	sprite.position = 320, 240
	sprite.scale = 3
	self.add(sprite, z=1)
	scale = ScaleBy(3, duration=2)

#	label.do( Repeat( scale + Reverse( sale )))

def main():
	pass


if __name__ == '__main__':
	main()

