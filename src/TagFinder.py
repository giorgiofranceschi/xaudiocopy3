#!/usr/bin/python -tt
# -*- coding: utf-8 -*-
#
# X Audio Copy - GTK and GNOME application for ripping CD-Audio and encoding in lossy audio format.
# Copyright 2010 Giorgio Franceschi
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA

import time

import gi
from gi.repository import GObject
try:
	gi.require_version('Gst', '1.0')
	from gi.repository import Gst
except:
	print("GStreamer not available")
	sys.exit(1)


### Classe che legge i tag da un file audio ###
class TagFinder:

	# Costruttore della classe
	def __init__(self, uri):

		self.__uri = uri
		self.__taglist = {}

		Gst.init(None)
		self.pipe = Gst.Pipeline()

		#filesource = Gst.element_factory_make("filesrc", "filesource")
		#filesource.set_property("location", self.__location)
		filesource = Gst.Element.make_from_uri(Gst.URIType.SRC, self.__uri, "filesrc")

		decoder = Gst.ElementFactory.make("decodebin", "decoder")
		decoder.connect("pad-added", self.on_pad)
		self.pipe.add(filesource)
		self.pipe.add(decoder)
		#Gst.element_link_many(filesource, decoder)
		filesource.link(decoder)

		self.converter = Gst.ElementFactory.make("audioconvert", "converter")
		fakesink = Gst.ElementFactory.make("fakesink", "sink")
		self.pipe.add(self.converter)
		self.pipe.add(fakesink)
		#Gst.element_link_many(self.converter, fakesink)
		self.converter.link(fakesink)

		self.bus = self.pipe.get_bus()
		self.bus.add_signal_watch()
		self.bus.connect("message::eos", self.on_eos)
		self.bus.connect("message::error", self.on_error)
		self.bus.connect("message::async_done", self.on_async_done)
		self.bus.connect("message::tag", self.on_tag)

		self.pipe.set_state(Gst.State.PLAYING)
		self.mainloop = GObject.MainLoop()
		self.mainloop.run()

	def on_pad(self, dbin, pad):
		try:
			pad.link(self.converter.get_pad("sink"))
		except:
			pass

	def on_eos(self, bus, message):
		# Ricava la durata del brano
		while 1:
			try:
				self.__duration = float(self.pipe.query_duration(Gst.FORMAT_TIME)[0])/Gst.SECOND
				print "Duration from Gst.query_duration: ", self.__duration
				break
			except:
				# Aspetta per completare la query
				time.sleep(0.01)

		self.pipe.set_state(Gst.State.NULL)
		self.mainloop.quit()

	def on_async_done(self, bus, message):
		# Ricava la durata del brano
		while 1:
			try:
				self.__duration = float(self.pipe.query_duration(Gst.FORMAT_TIME)[0])/Gst.SECOND
				print "Duration from Gst.query_duration: ", self.__duration
				break
			except:
				# Aspetta per completare la query
				time.sleep(0.01)

		self.pipe.set_state(Gst.State.NULL)
		self.mainloop.quit()

	def on_tag(self, bus, message):
		gst_taglist = message.parse_tag()
		for key in gst_taglist.keys():
			if not ((key == "image") or (key == "preview-image")):
				print '%s = %s' % (key, gst_taglist[key])
			else:
				print key
			if not (key in self.__taglist.keys()):
				self.__taglist[key] = gst_taglist[key]
			
	def on_error(self, bus, message):
		self.pipe.set_state(Gst.State.NULL)
		err, debug = message.parse_error()
		print "Error: %s" % err, debug
		self.mainloop.quit()

	#Restituisce i tag letti
	def get_tags(self):

		if self.__taglist:
			return self.__taglist
		else:
			return None
	# Restituisce la durata in secondi
	def get_duration(self):

		try:
			return self.__duration
		except:
			return None


### Test ###
#tf=TagFinder("cdda://01")
tf=TagFinder("file:///mnt/VboxCondivisa/Musica/01 - Chega de saudade.mp3")
