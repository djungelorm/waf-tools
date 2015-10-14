#!/usr/bin/env python

import waflib
from waflib import TaskGen, Task, Logs

"""
Integrate inkscape for image conversion into the build system.

Example:

    def configure(ctx):
        ctx.load('inkscape')

    def build(ctx):
        ctx(source='image.svg', target='image.png', width=200, height=400)
        ctx(source='image2.svg', target='image2.jpg')

"""

def configure(ctx):
    ctx.find_program('inkscape')

class inkscape(Task.Task):
    shell = True
    color = 'BLUE'

    def run(self):
        opts = []
        if self.width:
            opts.append('--export-width=%d' % self.width)
        if self.height:
            opts.append('--export-height=%d' % self.height)
        cmd = self.env.INKSCAPE + \
              ['--export-%s=%s' % (self.outputs[0].suffix()[1:], self.outputs[0].abspath()),
               self.inputs[0].abspath()] + opts
        self.outputs[0].parent.mkdir()
        out = self.generator.bld.cmd_and_log(cmd, output=waflib.Context.STDOUT, quiet=waflib.Context.BOTH)
        if Logs.verbose > 2:
            Logs.info(out)

    def __str__(self):
        node = self.inputs[0]
        src = node.path_from(node.ctx.launch_node())
        node = self.outputs[0]
        tgt = node.path_from(node.ctx.launch_node())
        dimensions = ''
        if self.width and self.height:
            dimensions = ' (width: %d px, height: %d px)' % (self.width, self.height)
        elif self.width:
            dimensions = ' (width: %d px)' % self.width
        elif self.height:
            dimensions = ' (height: %d px)' % self.height
        return '%s -> %s%s' % (src, tgt, dimensions)

@TaskGen.extension('.svg')
def process_inkscape(self, source):
    if isinstance(self.target, str):
        target = self.path.find_or_declare(self.target)
    else:
        target = self.target
    task = self.create_task('inkscape', src=source, tgt=target)
    task.width = getattr(self, 'width', None)
    task.height = getattr(self, 'height', None)
