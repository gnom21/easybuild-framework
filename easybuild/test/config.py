##
# Copyright 2013 Ghent University
#
# This file is part of EasyBuild,
# originally created by the HPC team of Ghent University (http://ugent.be/hpc/en),
# with support of Ghent University (http://ugent.be/hpc),
# the Flemish Supercomputer Centre (VSC) (https://vscentrum.be/nl/en),
# the Hercules foundation (http://www.herculesstichting.be/in_English)
# and the Department of Economy, Science and Innovation (EWI) (http://www.ewi-vlaanderen.be/en).
#
# http://github.com/hpcugent/easybuild
#
# EasyBuild is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation v2.
#
# EasyBuild is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with EasyBuild.  If not, see <http://www.gnu.org/licenses/>.
##
"""
Unit tests for EasyBuild configuration.

@author: Kenneth Hoste (Ghent University)
"""
import os
import shutil
import tempfile
from unittest import TestCase, TestLoader
from unittest import main as unittestmain

import easybuild.tools.config as config
import easybuild.tools.options as eboptions
from easybuild.main import main
from easybuild.tools.config import build_path, source_path, install_path, get_repository, log_file_format
from easybuild.tools.config import get_build_log_path, ConfigurationVariables
from easybuild.tools.repository import FileRepository


class ConfigTest(TestCase):
    """Test cases for EasyBuild configuration."""

    tmpdir = None

    def setUp(self):
        """Prepare for running a config test."""

        config.variables = ConfigurationVariables()
        self.tmpdir = tempfile.mkdtemp()
        for envvar in os.environ.keys():
            if envvar.startswith('EASYBUILD'):
                del os.environ[envvar]

    def tearDown(self):
        """Clean up after a config test."""
        try:
            shutil.rmtree(self.tmpdir)
        except OSError:
            err = None

    def configure(self, args = None):
        """(re)Configure."""
        eb_go = eboptions.parse_options(args = args)
        options = eb_go.options
        config.init(options, eb_go.get_options_by_section('config'))
        return eb_go.options.config

    def test_default_config(self):
        """Test default configuration."""

        self.configure(args = [])

        self.assertEqual(build_path(), os.path.join(os.path.expanduser('~'), '.local', 'easybuild', 'build'))
        self.assertEqual(source_path(), os.path.join(os.path.expanduser('~'), '.local', 'easybuild', 'sources'))
        self.assertEqual(install_path(), os.path.join(os.path.expanduser('~'), '.local', 'easybuild', 'software'))
        self.assertEqual(install_path(typ = 'mod'), os.path.join(os.path.expanduser('~'), '.local', 'easybuild', 'modules'))
        repo = get_repository()
        self.assertTrue(isinstance(repo, FileRepository))
        self.assertEqual(repo.repo, os.path.join(os.path.expanduser('~'), '.local', 'easybuild', 'ebfiles_repo'))
        self.assertEqual(log_file_format(return_directory = True), config.DEFAULT_LOGFILE_FORMAT[0])
        self.assertEqual(log_file_format(), config.DEFAULT_LOGFILE_FORMAT[1])
        self.assertEqual(get_build_log_path(), tempfile.gettempdir())

    def test_legacy_env_vars(self):
        """Test legacy environment variables."""

        # build path
        test_buildpath = os.path.join(self.tmpdir, 'build', 'path')
        os.environ['EASYBUILDBUILDPATH'] = test_buildpath
        self.configure(args = [])
        self.assertEqual(build_path(), test_buildpath)
        del os.environ['EASYBUILDBUILDPATH']

        # source path
        config.variables = ConfigurationVariables()
        test_sourcepath = os.path.join(self.tmpdir, 'source', 'path')
        os.environ['EASYBUILDSOURCEPATH'] = test_sourcepath
        self.configure(args = [])
        self.assertEqual(build_path(), os.path.join(os.path.expanduser('~'), '.local', 'easybuild', 'build'))
        self.assertEqual(source_path(), test_sourcepath)
        del os.environ['EASYBUILDSOURCEPATH']

        # install path
        config.variables = ConfigurationVariables()
        test_installpath = os.path.join(self.tmpdir, 'install', 'path')
        os.environ['EASYBUILDINSTALLPATH'] = test_installpath
        self.configure(args = [])
        self.assertEqual(source_path(), os.path.join(os.path.expanduser('~'), '.local', 'easybuild', 'sources'))
        self.assertEqual(install_path(), os.path.join(test_installpath, 'software'))
        self.assertEqual(install_path(typ = 'mod'), os.path.join(test_installpath, 'modules'))
        del os.environ['EASYBUILDINSTALLPATH']

        # prefix: should change build/install/source/repo paths
        config.variables = ConfigurationVariables()
        test_prefixpath = os.path.join(self.tmpdir, 'prefix', 'path')
        os.environ['EASYBUILDPREFIX'] = test_prefixpath
        self.configure(args = [])
        self.assertEqual(build_path(), os.path.join(test_prefixpath, 'build'))
        self.assertEqual(source_path(), os.path.join(test_prefixpath, 'sources'))
        self.assertEqual(install_path(), os.path.join(test_prefixpath, 'software'))
        self.assertEqual(install_path(typ = 'mod'), os.path.join(test_prefixpath, 'modules'))
        repo = get_repository()
        self.assertTrue(isinstance(repo, FileRepository))
        self.assertEqual(repo.repo, os.path.join(test_prefixpath, 'ebfiles_repo'))

        # build/source/install path overrides prefix
        config.variables = ConfigurationVariables()
        os.environ['EASYBUILDBUILDPATH'] = test_buildpath
        self.configure(args = [])
        self.assertEqual(build_path(), test_buildpath)
        self.assertEqual(source_path(), os.path.join(test_prefixpath, 'sources'))
        self.assertEqual(install_path(), os.path.join(test_prefixpath, 'software'))
        self.assertEqual(install_path(typ = 'mod'), os.path.join(test_prefixpath, 'modules'))
        repo = get_repository()
        self.assertTrue(isinstance(repo, FileRepository))
        self.assertEqual(repo.repo, os.path.join(test_prefixpath, 'ebfiles_repo'))
        del os.environ['EASYBUILDBUILDPATH']

        config.variables = ConfigurationVariables()
        os.environ['EASYBUILDSOURCEPATH'] = test_sourcepath
        self.configure(args = [])
        self.assertEqual(build_path(), os.path.join(test_prefixpath, 'build'))
        self.assertEqual(source_path(), test_sourcepath)
        self.assertEqual(install_path(), os.path.join(test_prefixpath, 'software'))
        self.assertEqual(install_path(typ = 'mod'), os.path.join(test_prefixpath, 'modules'))
        repo = get_repository()
        self.assertTrue(isinstance(repo, FileRepository))
        self.assertEqual(repo.repo, os.path.join(test_prefixpath, 'ebfiles_repo'))
        del os.environ['EASYBUILDSOURCEPATH']

        config.variables = ConfigurationVariables()
        os.environ['EASYBUILDINSTALLPATH'] = test_installpath
        self.configure(args = [])
        self.assertEqual(build_path(), os.path.join(test_prefixpath, 'build'))
        self.assertEqual(source_path(), os.path.join(test_prefixpath, 'sources'))
        self.assertEqual(install_path(), os.path.join(test_installpath, 'software'))
        self.assertEqual(install_path(typ = 'mod'), os.path.join(test_installpath, 'modules'))
        repo = get_repository()
        self.assertTrue(isinstance(repo, FileRepository))
        self.assertEqual(repo.repo, os.path.join(test_prefixpath, 'ebfiles_repo'))
        del os.environ['EASYBUILDINSTALLPATH']

        del os.environ['EASYBUILDPREFIX']

    def test_legacy_config_file(self):
        """Test finding/using legacy configuration files."""

        cfg_fn = self.configure(args = [])
        self.assertTrue(cfg_fn.endswith('easybuild/easybuild_config.py'))

        configtxt = """
build_path = '%(buildpath)s'
source_path = '%(sourcepath)s'
install_path = '%(installpath)s'
repository_path = '%(repopath)s'
repository = FileRepository(repository_path)
log_format = ('%(logdir)s', '%(logtmpl)s')
log_dir = '%(tmplogdir)s'
software_install_suffix = '%(softsuffix)s'
modules_install_suffix = '%(modsuffix)s'
"""

        buildpath = os.path.join(self.tmpdir, 'my', 'test', 'build', 'path')
        sourcepath = os.path.join(self.tmpdir, 'my', 'test', 'source', 'path')
        installpath = os.path.join(self.tmpdir, 'my', 'test', 'install', 'path')
        repopath = os.path.join(self.tmpdir, 'my', 'test', 'repo', 'path')
        logdir = 'somedir'
        logtmpl = 'test-eb-%(name)s%(version)s_date-%(date)s__time-%(time)s.log'
        tmplogdir = os.path.join(self.tmpdir, 'my', 'test', 'tmplogdir')
        softsuffix = 'myfavoritesoftware'
        modsuffix = 'modulesgohere'

        configdict = {
            'buildpath': buildpath,
            'sourcepath': sourcepath,
            'installpath': installpath,
            'repopath': repopath,
            'logdir': logdir,
            'logtmpl': logtmpl,
            'tmplogdir': tmplogdir,
            'softsuffix': softsuffix,
            'modsuffix': modsuffix
        }

        # create user config file on default location
        myconfigfile = os.path.join(self.tmpdir, '.easybuild', 'config.py')
        if not os.path.exists(os.path.dirname(myconfigfile)):
            os.makedirs(os.path.dirname(myconfigfile))
        f = open(myconfigfile, 'w')
        f.write(configtxt % configdict)
        f.close()

        # redefine home so we can test user config file on default location
        home = os.environ.get('HOME', None)
        os.environ['HOME'] = self.tmpdir
        config.variables = ConfigurationVariables()
        cfg_fn = self.configure(args = [])
        if home is not None:
            os.environ['HOME'] = home

        # check finding and use of config file
        self.assertEqual(cfg_fn, myconfigfile)
        self.assertEqual(build_path(), buildpath)
        self.assertEqual(source_path(), sourcepath)
        self.assertEqual(install_path(), os.path.join(installpath, softsuffix))
        self.assertEqual(install_path(typ = 'mod'), os.path.join(installpath, modsuffix))
        repo = get_repository()
        self.assertTrue(isinstance(repo, FileRepository))
        self.assertEqual(repo.repo, repopath)
        self.assertEqual(log_file_format(return_directory = True), logdir)
        self.assertEqual(log_file_format(), logtmpl)
        self.assertEqual(get_build_log_path(), tmplogdir)

        # redefine config file entries for proper testing below
        buildpath = os.path.join(self.tmpdir, 'my', 'custom', 'test', 'build', 'path')
        sourcepath = os.path.join(self.tmpdir, 'my', 'custom', 'test', 'source', 'path')
        installpath = os.path.join(self.tmpdir, 'my', 'custom', 'test', 'install', 'path')
        repopath = os.path.join(self.tmpdir, 'my', 'custom', 'test', 'repo', 'path')
        logdir = 'somedir_custom'
        logtmpl = 'test-custom-eb-%(name)_%(date)s%(time)s__%(version)s.log'
        tmplogdir = os.path.join(self.tmpdir, 'my', 'custom', 'test', 'tmplogdir')
        softsuffix = 'myfavoritesoftware_custom'
        modsuffix = 'modulesgohere_custom'

        configdict = {
            'buildpath': buildpath,
            'sourcepath': sourcepath,
            'installpath': installpath,
            'repopath': repopath,
            'logdir': logdir,
            'logtmpl': logtmpl,
            'tmplogdir': tmplogdir,
            'softsuffix': softsuffix,
            'modsuffix': modsuffix }

        # create custom config file, and point to it
        mycustomconfigfile = os.path.join(self.tmpdir, 'mycustomconfig.py')
        if not os.path.exists(os.path.dirname(mycustomconfigfile)):
            os.makedirs(os.path.dirname(mycustomconfigfile))
        f = open(mycustomconfigfile, 'w')
        f.write(configtxt % configdict)
        f.close()
        os.environ['EASYBUILDCONFIG'] = mycustomconfigfile

        # reconfigure
        config.variables = ConfigurationVariables()
        cfg_fn = self.configure(args = [])

        # verify configuration
        self.assertEqual(cfg_fn, mycustomconfigfile)
        self.assertEqual(build_path(), buildpath)
        self.assertEqual(source_path(), sourcepath)
        self.assertEqual(install_path(), os.path.join(installpath, softsuffix))
        self.assertEqual(install_path(typ = 'mod'), os.path.join(installpath, modsuffix))
        repo = get_repository()
        self.assertTrue(isinstance(repo, FileRepository))
        self.assertEqual(repo.repo, repopath)
        self.assertEqual(log_file_format(return_directory = True), logdir)
        self.assertEqual(log_file_format(), logtmpl)
        self.assertEqual(get_build_log_path(), tmplogdir)
        del os.environ['EASYBUILDCONFIG']


def suite():
    return TestLoader().loadTestsFromTestCase(ConfigTest)

if __name__ == '__main__':
    unittestmain()
