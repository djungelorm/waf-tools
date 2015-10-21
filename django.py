#!/usr/bin/env python

import os
import random
import subprocess
from waflib import Context, Logs
from waflib.Build import BuildContext

"""
Build scripts for django websites.

Example:

    django_root = 'src'

    def options(ctx):
        ctx.load('django')

    def configure(ctx):
        ctx.load('django')
        ctx.env.DJANGO_PYTHON_PACKAGES.extend(['sorl-thumbnail', 'boto', 'django-storages', ...])

    def build(ctx):
        ctx.load('django')

        ctx(rule=ctx.tools('django').secret_key, target='secret-key.txt')

    def runserver(ctx):
        ctx.load('django')

"""

def options(ctx):
    group = ctx.add_option_group('Django options')
    group.add_option('--django-production', action='store_true',
                     help='Build django for use in a production environment')
    default_root = getattr(Context.g_module, 'django_root', 'src')
    group.add_option('--django-root', action='store', default=default_root,
                     help='Path to root directory where django apps are located [default: \'%s\']' % default_root)

def configure(ctx):
    ctx.env.DJANGO_ROOT = ctx.options.django_root
    root = ctx.path.find_node(ctx.env.DJANGO_ROOT)
    assert(root)
    ctx.msg('Checking for django root at \'%s\'' % ctx.env.DJANGO_ROOT, 'ok')

    ctx.env.DJANGO_PRODUCTION = ctx.options.django_production

    if 'DJANGO_PRODUCTION_SETTINGS' not in ctx.env:
        ctx.env.DJANGO_PRODUCTION_SETTINGS = 'main.settings'

    if 'DJANGO_DEVELOPMENT_SETTINGS' not in ctx.env:
        ctx.env.DJANGO_DEVELOPMENT_SETTINGS = 'main.devsettings'

    if ctx.env.DJANGO_PRODUCTION:
        ctx.env.DJANGO_SETTINGS = ctx.env.DJANGO_PRODUCTION_SETTINGS
    else:
        ctx.env.DJANGO_SETTINGS = ctx.env.DJANGO_DEVELOPMENT_SETTINGS

    ctx.env.DJANGO_APPS = []
    for app in root.listdir():
        app = root.find_dir(app)
        if app is not None:
            ctx.env.DJANGO_APPS.append(app.name)

    ctx.msg('Found django apps', ','.join(ctx.env.DJANGO_APPS))

    ctx.find_program('virtualenv')
    if 'DJANGO_PYTHON_PACKAGES' not in ctx.env:
        ctx.env.DJANGO_PYTHON_PACKAGES = ['django']

    ctx.recurse([root.find_dir(app).abspath() for app in ctx.env.DJANGO_APPS])

def post(ctx):
    if ctx.cmd == 'install':

        Logs.info('Setting up virtualenv')
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
            Logs.info('Setting up error log file')
            ctx.exec_command('echo "" > error.log', cwd=ctx.env.PREFIX)
            ctx.exec_command('chgrp www-data error.log', cwd=ctx.env.PREFIX)
            ctx.exec_command('chmod g+w error.log', cwd=ctx.env.PREFIX)

        manage = 'env/bin/python %s/manage.py' % ctx.env.PREFIX
        settings = '--settings %s' % ctx.env.DJANGO_SETTINGS

        Logs.info('Building migrations')
        ctx.exec_command('%s makemigrations %s' % (manage, settings), cwd=ctx.env.PREFIX)
        ctx.exec_command('%s migrate %s' % (manage, settings), cwd=ctx.env.PREFIX)

        Logs.info('Loading fixtures')
        for data in ctx.path.find_dir('data').listdir():
            data = os.path.join(ctx.path.find_dir('data').abspath(), data)
            ctx.exec_command('%s loaddata %s %s' % (manage, data, settings), cwd=ctx.env.PREFIX)

        if ctx.env.DJANGO_PRODUCTION:
            Logs.info('Collecting static files')
            ctx.exec_command('%s collectstatic %s --noinput' % (manage, settings), cwd=ctx.env.PREFIX)

        Logs.info('Checking django install')
        deploy = ''
        if ctx.env.DJANGO_PRODUCTION:
            deploy = ' --deploy'
        ctx.exec_command('%s check %s %s' % (manage, settings, deploy), cwd=ctx.env.PREFIX)

        if ctx.env.DJANGO_PRODUCTION:
            Logs.info('Reloading apache')
            ctx.exec_command('sudo service apache2 reload')

def build(ctx):
    ctx.add_post_fun(post)
    root = ctx.path.find_dir(ctx.env.DJANGO_ROOT)

    ctx.recurse([root.find_dir(app).abspath() for app in ctx.env.DJANGO_APPS])

    ctx.install_files('${PREFIX}', root.ant_glob('**/*(.py|.html|.css|.js)'), cwd=root, relative_trick=True)

def _generate_secret_key():
    length = 50
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
    return ''.join(random.choice(chars) for i in range(length))

def secret_key(task):
    tgt = task.outputs[0].abspath()
    with open(tgt, 'w') as f:
        f.write(_generate_secret_key() + '\n')
    return 0

class RunServerContext(BuildContext):
    cmd = 'runserver'
    fun = 'runserver'

def runserver(ctx):
    if ctx.env.DJANGO_PRODUCTION:
        ctx.fatal('Cannot run server locally with production settings')
    Logs.info('Running server')
    cmd = ('env/bin/python', 'manage.py', 'runserver', '--settings', ctx.env.DJANGO_SETTINGS)
    subprocess.Popen(cmd, cwd=ctx.env.PREFIX).wait()

def sorl_clear_thumbnails(ctx):
    Logs.info('Clearing the thumbnail cache')
    ctx.exec_command(
        'env/bin/python manage.py thumbnail clear --settings %s' % ctx.env.DJANGO_SETTINGS,
        cwd=ctx.env.PREFIX)
    import shutil, os.path
    cache_dir = os.path.join(ctx.env.PREFIX, 'media', 'cache')
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)
