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
    vars = ['EXPORT_WIDTH', 'EXPORT_HEIGHT']

    def run(self):
        opts = []
        if 'EXPORT_WIDTH' in self.env:
            opts.append('--export-width=%d' % self.env.EXPORT_WIDTH)
        if 'EXPORT_HEIGHT' in self.env:
            opts.append('--export-height=%d' % self.env.EXPORT_HEIGHT)
        self.outputs[0].parent.mkdir()
        cmd = self.env.INKSCAPE + \
              ['--export-%s=%s' % (self.outputs[0].suffix()[1:], self.outputs[0].abspath()),
               self.inputs[0].abspath()] + opts
        out = self.generator.bld.cmd_and_log(cmd, output=waflib.Context.STDOUT, quiet=waflib.Context.BOTH)
        if Logs.verbose > 2:
            Logs.info(out)

@TaskGen.extension('.svg')
def process_inkscape(self, source):
    if hasattr(self, 'width'):
        self.env.EXPORT_WIDTH = self.width
    if hasattr(self, 'height'):
        self.env.EXPORT_HEIGHT = self.height
    target = self.bld.path.get_bld().make_node(self.target)
    task = self.create_task('inkscape', src=source, tgt=target)
    if self.install_path:
        self.bld.install_files(self.install_path, task.outputs)
