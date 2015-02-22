#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  ypkg.py
#  
#  Copyright 2015 Ikey Doherty <ikey@evolve-os.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
import sys

sys.path.append("/usr/share/ypkg")

import build
import packageit
import subprocess
import shlex
import sanity
from sanity import sane
import os
import shutil

def main():
    if len(sys.argv) < 2:
        print "Not enough arguments"
        return 1

    fpath = sys.argv[1]
    if not os.path.exists(fpath):
        print "%s does not exist.." % fpath
        return 1
    if not fpath.endswith("package.yml"):
        print "Unnecessarily anal warning: File is not named package.yml"
        return 1

    if not sane(fpath): # then y made for linoox
        return 1

    pspec = build.BuildPrefix + "/%s.xml" % sanity.name
    actions = build.BuildPrefix + "/actions.py"

    build.BuildDir += "/%s" % sanity.name
    build.InstallDir += "/%s" % sanity.name

    insList = list()
    if sanity.buildDeps:
        for dep in sanity.buildDeps:
            if not sanity._idb.has_package(dep) and dep not in insList:
                insList.append(dep)
    if len(insList) > 0:
        cmd = "eopkg install %s" % (" ".join(insList))
        if not build.LeRoot:
            cmd = "sudo %s" % cmd
        if "--force" in sys.argv:
            cmd += " -y"
        print "\nInstalling build dependencies...."
        ret = subprocess.call(shlex.split(cmd))
        if ret != 0:
            return ret

    build.cleanup()
    sources = sanity.get_sources()
    tars = build.fetch_source(sources)
    build.extract(tars)

    try:
        build.build(fpath)
        if sanity.emul32:
            print "Rebuilding for 32-bit"
            build.emul32 = True
            build.build(fpath)
    except Exception, e:
        print "Build failure: %s" % e
        return 1

    packageit.packageit(fpath, build.InstallDir, pspec)
    f = open(actions, "w")
    tmpl = """
from pisi.actionsapi import pisitools

def install():
    pisitools.insinto("/", "%s/*")
""" % build.InstallDir


    f.writelines(tmpl)
    f.close()

    cmd = "eopkg build --ignore-dependency --ignore-safety %s" % pspec
    if not build.LeRoot:
        cmd = "sudo %s" % cmd
    ret = subprocess.call(shlex.split(cmd), shell=False)
    if ret != 0:
        print "Failed to build package"
        return ret

    try:
        shutil.copy(pspec, "%s/pspec.xml" % os.getcwd())
    except:
        print "Unable to copy pspec.xml to current directory!"
        return 1
    
    return 0    

if __name__ == "__main__":
    sys.exit(main())
