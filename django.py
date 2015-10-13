#!/usr/bin/env python

import subprocess
from waflib.Build import BuildContext

"""
Build scripts for django websites.

Example:

    def options(ctx):
        ctx.load('django')

    def configure(ctx):
        ctx.load('django')
        ctx.env.DJANGO_PYTHON_PACKAGES.extend(['sorl-thumbnail', 'boto', 'django-storages', ...])

    def build(ctx):
        ctx.load('django')

    def runserver(ctx):
        ctx.load('django')

"""

def options(ctx):
    ctx.add_option('--django-production', action='store_true', help='Use production settings for django')
    ctx.add_option('--django-root', action='store', default='src',
                   help='Path to root directory for django apps (default: src)')

def configure(ctx):
    ctx.find_program('virtualenv')

    ctx.env.DJANGO_ROOT = ctx.options.django_root
    ctx.env.DJANGO_PYTHON_PACKAGES = ['django']
    ctx.env.DJANGO_PRODUCTION = ctx.options.django_production
    if ctx.options.django_production:
        ctx.env.DJANGO_SETTINGS = 'main.prodsettings'
    else:
        ctx.env.DJANGO_SETTINGS = 'main.devsettings'

    src = ctx.path.find_node(ctx.env.DJANGO_ROOT)

    ctx.env.DJANGO_APPS = []
    for app in src.listdir():
        app = src.find_dir(app)
        if app is not None:
            ctx.env.DJANGO_APPS.append(app.name)

    ctx.recurse(['src/'+app for app in ctx.env.DJANGO_APPS])

def post(ctx):
    if ctx.cmd == 'install':

        import os
        env_path = os.path.join(ctx.env.PREFIX, 'env')
        if not os.path.exists(env_path):
            os.makedirs(env_path)
            ctx.exec_command(
                '%s env --system-site-packages --always-copy --python=python2.7' % ' '.join(ctx.env.VIRTUALENV),
                cwd=ctx.env.PREFIX)
            pip = 'env/bin/pip'
            ctx.exec_command('%s install --upgrade pip' % pip, cwd=ctx.env.PREFIX)
            ctx.exec_command('%s install %s' % (pip, ' '.join(ctx.env.DJANGO_PYTHON_PACKAGES)), cwd=ctx.env.PREFIX)

        if ctx.env.DJANGO_PRODUCTION:
            ctx.exec_command('echo "" > error.log', cwd=ctx.env.PREFIX)
            ctx.exec_command('chgrp www-data error.log', cwd=ctx.env.PREFIX)
            ctx.exec_command('chmod g+w error.log', cwd=ctx.env.PREFIX)

        manage = 'env/bin/python %s/manage.py' % ctx.env.PREFIX
        settings = '--settings %s' % ctx.env.DJANGO_SETTINGS

        ctx.exec_command('%s makemigrations %s' % (manage, settings), cwd=ctx.env.PREFIX)
        ctx.exec_command('%s migrate %s' % (manage, settings), cwd=ctx.env.PREFIX)
        for data in ctx.path.find_dir('data').listdir():
            data = os.path.join(ctx.path.find_dir('data').abspath(), data)
            ctx.exec_command('%s loaddata %s %s' % (manage, data, settings), cwd=ctx.env.PREFIX)
        if ctx.env.DJANGO_PRODUCTION:
            ctx.exec_command('%s collectstatic %s --noinput' % (manage, settings), cwd=ctx.env.PREFIX)

        deploy = ''
        if ctx.env.DJANGO_PRODUCTION:
            deploy = ' --deploy'
        ctx.exec_command('%s check %s %s' % (manage, settings, deploy), cwd=ctx.env.PREFIX)

        if ctx.env.DJANGO_PRODUCTION:
            ctx.exec_command('sudo service apache2 reload')

def build(ctx):
    ctx.add_post_fun(post)
    src = ctx.path.find_dir(ctx.env.DJANGO_ROOT)

    ctx.recurse(['src/'+app for app in ctx.env.DJANGO_APPS])

    ctx.install_files('${PREFIX}', src.ant_glob('**/*(.py|.html|.css|.js)'), cwd=src, relative_trick=True)

    ctx.install_files('${PREFIX}', ['secret-key.txt'])
    if ctx.env.DJANGO_PRODUCTION:
        ctx.install_files('${PREFIX}', ['db-password.txt', 'aws-credentials.txt'])

class RunServerContext(BuildContext):
    cmd = 'runserver'
    fun = 'runserver'

def runserver(ctx):
    if ctx.env.DJANGO_PRODUCTION:
        # error
        pass
    cmd = ('env/bin/python', 'manage.py', 'runserver', '--settings', ctx.env.DJANGO_SETTINGS)
    subprocess.Popen(cmd, cwd=ctx.env.PREFIX).wait()
