# encoding: utf-8
"""
operational/__init__.py

Created by Thomas Mangin on 2013-09-01.
Copyright (c) 2009-2013 Exa Networks. All rights reserved.
"""

from struct import pack,unpack

from exabgp.protocol.family import AFI,SAFI
from exabgp.bgp.message.open.routerid import RouterID
from exabgp.bgp.message import Message

# =================================================================== Operational

MAX_ADVISORY = 2048  # 2K

class Type (int):
	def pack (self):
		return pack('!H',self)

	def extract (self):
		return [pack('!H',self)]

	def __len__ (self):
		return 2

	def __str__ (self):
		pass

class OperationalType:
	PRI  = 0x00  # 00: Prefix Reachability Indicators
	# ADVISE
	ADM  = 0x01  # 01: Advisory Demand Message
	ASM  = 0x02  # 02: Advisory Static Message
	# STATE
	RPCQ = 0x03  # 03: Reachable Prefix Count Request
	RPCP = 0x04  # 04: Reachable Prefix Count Reply
	APCQ = 0x05  # 05: Adj-Rib-Out Prefix Count Request
	APCP = 0x06  # 06: Adj-Rib-Out Prefix Count Reply
	LPCQ = 0x07  # 07: BGP Loc-Rib Prefix Count Request
	LPCP = 0x08  # 08: BGP Loc-Rib Prefix Count Reply
	SSQ  = 0x09  # 09: Simple State Request
	# DUMP
	DUP  = 0x0A  # 10: Dropped Update Prefixes
	MUP  = 0x0B  # 11: Malformed Update Prefixes
	MUD  = 0x0C  # 12: Malformed Update Dump
	SSP  = 0x0D  # 13: Simple State Response
	# CONTROL
	MP   = 0xFFFE  # 65534: Max Permitted
	NS   = 0xFFFF  # 65535: Not Satisfied

class Operational (Message):
	TYPE = chr(0x06)  # next free Message Type, as IANA did not assign one yet.

	def __init__ (self,what,data):
		self.what = Type(what)
		self.data = data

	def message (self):
		return self._message("%s%s%s" % (
			self.what.pack(),
			pack('!H',len(self.data)),
			self.data
		))

	def __str__ (self):
		return self.extensive()

	def extensive (self):
		return 'operational %s' % self.name

class OperationalFamily (Operational):
	def __init__ (self,what,afi,safi,data=''):
		self.afi = AFI(afi)
		self.safi = SAFI(afi)
		Operational.__init__(
			self,what,
			'%s%s%s' % (self.afi.pack(),self.safi.pack(),data)
		)

	def family (self):
		return (self.afi,self.safi)

class SequencedOperationalFamily (OperationalFamily):
	__sequence_number = 0

	def _sequence (self):
		self.__sequence_number +=1
		return self.__sequence_number

	def __init__ (self,what,afi,safi,routerid,sequence=None,data=''):
		self.routerid = routerid
		self.routerid = RouterID(routerid)
		self.sequence = self._sequence() if sequence is None else sequence
		OperationalFamily.__init__(
			self,what,
			afi,safi,
			'%s%s%s' % (self.routerid.pack(),pack('!H',self.sequence),data)
		)

class NS:
	MALFORMED   = 0x01  # Request TLV Malformed
	UNSUPPORTED = 0x02  # TLV Unsupported for this neighbor
	MAXIMUM     = 0x03  # Max query frequency exceeded
	PROHIBITED  = 0x04  # Administratively prohibited
	BUSY        = 0x05  # Busy
	NOTFOUND    = 0x06  # Not Found

	class _NS (OperationalFamily):
		def __init__ (self,afi,safi,sequence):
			OperationalFamily.__init__(
				self,
				OperationalType.NS,
				afi,safi,
				'%s%s' % (sequence,self.ERROR_SUBCODE)
			)

		def extensive (self):
			return 'operational NS %s %s/%s' % (self.name,self.afi,self.safi)


	class Malformed (_NS):
		name = 'NS malformed'
		ERROR_SUBCODE = '\x00\x01'  # pack('!H',MALFORMED)

	class Unsupported (_NS):
		name = 'NS unsupported'
		ERROR_SUBCODE = '\x00\x02'  # pack('!H',UNSUPPORTED)

	class Maximum (_NS):
		name = 'NS maximum'
		ERROR_SUBCODE = '\x00\x03'  # pack('!H',MAXIMUM)

	class Prohibited (_NS):
		name = 'NS prohibited'
		ERROR_SUBCODE = '\x00\x04'  # pack('!H',PROHIBITED)

	class Busy (_NS):
		name = 'NS busy'
		ERROR_SUBCODE = '\x00\x05'  # pack('!H',BUSY)

	class NotFound (_NS):
		name = 'NS notfound'
		ERROR_SUBCODE = '\x00\x06'  # pack('!H',NOTFOUND)


class Advisory:
	class _Advisory (OperationalFamily):
		def extensive (self):
			return 'operational %s afi %s safi %s "%s"' % (self.name,self.afi,self.safi,self.data)

	class ADM (_Advisory):
		name = 'ADM'

		def __init__ (self,afi,safi,utf8):
			if len(utf8) > MAX_ADVISORY:
				utf8 = utf8[:MAX_ADVISORY-3] + '...'
			OperationalFamily.__init__(
				self,OperationalType.ADM,
				afi,safi,
				utf8.encode('utf-8')
			)

	class ASM (_Advisory):
		name = 'ASM'

		def __init__ (self,afi,safi,utf8):
			if len(utf8) > MAX_ADVISORY:
				utf8 = utf8[:MAX_ADVISORY-3] + '...'
			OperationalFamily.__init__(
				self,OperationalType.ASM,
				afi,safi,
				utf8.encode('utf-8')
			)

# a = Advisory.ADM(1,1,'string 1')
# print a.extensive()
# b = Advisory.ASM(1,1,'string 2')
# print b.extensive()


class State:
	class RPCQ (SequencedOperationalFamily):
		name = 'RPCQ'

		def __init__ (self,afi,safi,routerid,sequence):
			SequencedOperationalFamily.__init__(
				self,OperationalType.RPCQ,
				afi,safi,
				routerid,sequence
			)

		def extensive (self):
			return 'operational %s afi %s safi %s router-id %s sequence %d' % (self.name,self.afi,self.safi,self.routerid,self.sequence)

	class RPCP (SequencedOperationalFamily):
		name = 'RPCP'

		def __init__ (self,afi,safi,routerid,sequence,count):
			self.count = count
			SequencedOperationalFamily.__init__(
				self,OperationalType.RPCP,
				afi,safi,
				routerid,sequence,
				pack('!L',count)
			)

		def extensive (self):
			return 'operational %s afi %s safi %s router-id %s sequence %d count %d' % (self.name,self.afi,self.safi,self.routerid,self.sequence,self.count)

# c = State.RPCQ(1,1,'82.219.0.1',10)
# print c.extensive()
# d = State.RPCP(1,1,'82.219.0.1',10,10000)
# print d.extensive()

class Dump:
	pass


def OperationalFactory (data):
	what = Type(unpack('!H',data[0:2])[0])
	length = unpack('!H',data[2:4])[0]

	if what == OperationalType.ADM:
		afi = unpack('!H',data[4:6])[0]
		safi = ord(data[6])
		data = data[7:length+4]
		return Advisory.ADM(afi,safi,data)
	elif what == OperationalType.ASM:
		afi = unpack('!H',data[4:6])[0]
		safi = ord(data[6])
		data = data[7:length+4]
		return Advisory.ASM(afi,safi,data)
	elif what == OperationalType.RPCQ:
		afi = unpack('!H',data[4:6])[0]
		safi = ord(data[6])
		routerid = RouterID(unpack('!H',data[7:9])[0])
		sequence = unpack('!H',data[9:11])[0]
		return State.RPCQ(afi,safi,routerid,sequence)
	elif what == OperationalType.RPCP:
		afi = unpack('!H',data[4:6])[0]
		safi = ord(data[6])
		routerid = RouterID(unpack('!H',data[7:9])[0])
		sequence = unpack('!H',data[9:11])[0]
		count = unpack('!H',data[11:15])[0]
		return State.RPCQ(afi,safi,routerid,sequence,count)
	else:
		print 'ignoring ATM this kind of message'
