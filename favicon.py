import os

def options(ctx):
    ctx.load('inkscape')

def configure(ctx):
    ctx.load('inkscape')
    ctx.find_program('convert')

def build_favicon(ctx, source='favicon.svg', install_to=None):
    sourcedir = os.path.dirname(source)
    ico_sizes = [16,32,48]
    extra_sizes = [144,152]
    for size in ico_sizes + extra_sizes:
        ctx(
            source = source,
            target = os.path.join(sourcedir, 'favicon-%d.png' % size),
            width = size, height = size)
    ctx(
        rule = '${CONVERT} ${SRC} ${TGT}',
        source = [os.path.join(sourcedir, 'favicon-%d.png' % size) for size in ico_sizes],
        target = os.path.join(sourcedir, 'favicon.ico'))

    if install_to:
        ctx.install_files(install_to, [os.path.join(sourcedir, 'favicon-%d.png' % size) for size in extra_sizes])
        ctx.install_files(install_to, os.path.join(sourcedir, 'favicon.ico'))
