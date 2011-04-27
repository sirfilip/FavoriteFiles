#!/usr/bin/env python

#  Copyright (C) 2007 Jesse Jaggars
#  Author: Jesse Jaggars <jhjaggars@t_gmail_com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys, re
from xml.dom import minidom
from optparse import OptionParser

class VimParser:
  NAME_REGEX = re.compile('^let .*colors_name\s*=\s*"(\w+)"$')
  found_name = None
  
  mapping = {
    "normal"     : "text",
    "cursor"     : "cursor",
    "cursorline" : "current-line",
    "search"     : "search-match",
    "comment"    : "def:comment",
    "constant"   : "def:constant",
    "identifier" : "def:identifier",
    "preproc"    : "def:preprocessor",
    "error"      : "def:error",
    "string"     : "def:string",
    "number"     : "def:number",
    "function"   : "def:function",
    "boolean"    : "def:boolean",
    "special"    : "def:specials",
    "type"       : "def:type",
    "statement"  : "def:statement",
    "keyword"    : "def:keyword",
    "matchparen" : "bracket-match",
    "diffdelete" : "diff:removed-line",
    "diffadd"    : "diff:added-line",
    "diffchange" : "diff:changed-line",
    "linenr"     : "line-numbers"
  }

  def __init__(self, options):
    self.options = options
    
  def parse_pair(self,pair):
    if pair[1].lower() == "none":
        return None
    if pair[0] == 'guibg':
      return {"background":pair[1]}
    elif pair[0] == 'guifg':
      return {"foreground":pair[1]}
    # this rule is used to do bold, underline, reverse or italics
    elif pair[0] == 'gui' and pair[1].lower() != 'none':
      return {pair[1]:"true"}
    else:
      return None
      
  def parse_vim_line(self,line):
    parts = line.split()
    rObj = None
    namematch = None
    
    if len(parts) < 1:
      return None
    if parts[0] == 'let':
      namematch = self.NAME_REGEX.match(line.strip())
    if namematch:
      self.found_name = namematch.groups()[0]
    if parts[0] == "hi" or parts[0] == "highlight":
      if parts[1].lower() in self.mapping:
        rObj = {"name":self.mapping[parts[1].lower()]}
        for i in parts[2:]:
          attr = self.parse_pair(i.split('='))
          if attr != None:
            rObj.update(attr)
      return rObj
    else:
      return None
    
  def parse_vim(self,f):
    out = []
    try:
      for line in f:
        rule = self.parse_vim_line(line)
        if rule != None and len(rule) > 1:
          out.append(rule)
      return self.build_xml(out)
    except Exception, e:
      sys.stderr.write("Error: parse_vim: %s" % e)

  def build_xml(self,styles):
    # build the document
    document = minidom.Document()
    # build the root element and append to the document
    root = document.createElement('style-scheme')
    # set the name attrib
    if self.options.name:
      root.setAttribute('name',self.options.name)
      root.setAttribute('id',self.options.name.lower())
    elif self.found_name != None:
      root.setAttribute('name',self.found_name.capitalize())
      root.setAttribute('id', self.found_name)
    else:
      root.setAttribute('name','Unknown')
      root.setAttribute('id', 'unknown')
    # set the version attrib
    if self.options.version:
      root.setAttribute('version', self.options.version)
    else:
      root.setAttribute('version', '1.0')
    document.appendChild(root)
    # append the author
    author = document.createElement('author')
    if self.options.author:
      author.appendChild( document.createTextNode(self.options.author) )
    root.appendChild( author )
    # append the description
    description = document.createElement('_description')
    if self.options.description:
      description.appendChild(
        document.createTextNode(self.options.description) )
    elif self.found_name != None:
      description.appendChild(
        document.createTextNode(
          "%s theme" % self.found_name.capitalize() ) )
    root.appendChild( description )
    # append the styles
    for s in styles:
      fg = None
      bg = None
      
      elem = document.createElement('style')
      elem.setAttribute('name',s["name"])
      if 'foreground' in s:
        fg = s["foreground"]
        if fg[0] != '#':
          fg = "#%s" % fg
        elem.setAttribute('foreground', fg)
      if 'background' in s:
        bg = s["background"]
        if bg[0] != '#':
          bg = "#%s" % bg
        elem.setAttribute('background', bg)
      # sometimes styles use fg and bg to copy colors
      try:
        if bg == "#fg":
          elem.setAttribute('background', fg)
      except:
        pass
      try:
        if fg == "#bg":
          elem.setAttribute('foreground', bg)
      except:
        pass
      for x in ('bold','italic','underline','reverse'):
        if x in s:
          elem.setAttribute(x,s[x])
            
      root.appendChild(elem)
     
    return document.toprettyxml()
  
if __name__ == "__main__":
  usage = "Usage: %prog [options] < in.vim > out.xml"
  optParser = OptionParser(usage=usage)
  optParser.add_option("-a", "--author", dest="author",
                  help="specify the author", metavar="AUTHOR")
  optParser.add_option("-v", "--version", dest="version",
                  help="specify the version", metavar="VERSION")
  optParser.add_option("-n", "--name", dest="name",
                  help="specify the name of the theme", metavar="NAME")
  optParser.add_option("-d", "--description", dest="description",
                  help="specify the description", metavar="DESCRIPTION")
  (options, args) = optParser.parse_args()
  
  vimparser = VimParser(options)
  print vimparser.parse_vim(sys.stdin)
