# -*- coding: utf-8 -*-

"""
utils for gromoteur.
"""
from sys import platform
import os,  ctypes


if platform.startswith("win"):
	os.environ["BROWSER"] = 'firefox'
	os.environ["DISPLAY"] = 'firefox'


def get_free_space(folder):
	""" Return folder/drive free space (in bytes)
	"""

	if platform.startswith("linux"):
		s = os.statvfs(folder)
		return s.f_bsize * s.f_bavail / 1048576
	elif platform.startswith("win"):
			free_bytes = ctypes.c_ulonglong(0)
			ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(folder), None, None, ctypes.pointer(free_bytes))
			return free_bytes.value/(1024*1024.0)

def fileSize(filename):
	try:
		return round(os.path.getsize(filename)/(1024*1024.0), 1)
	except:
		return 0.0

