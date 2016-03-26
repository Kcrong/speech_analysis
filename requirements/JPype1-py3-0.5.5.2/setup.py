#!/usr/bin/python
# -- Content-Encoding: UTF-8 --
"""
jPype1-py3 installation script

Requires Visual C++ (Express) 2010 to be installed on Windows.

..

    Copyright 2013 Thomas Calmant

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

# Module version
__version_info__ = (0, 5, 5, 2)
__version__ = ".".join(str(x) for x in __version_info__)

# Documentation strings format
__docformat__ = "restructuredtext en"

# ------------------------------------------------------------------------------

import os
import sys
import platform
from glob import glob

try:
    from setuptools import setup
    from setuptools import Extension

except ImportError:
    from distutils.core import setup
    from distutils.core import Extension

# ------------------------------------------------------------------------------

if sys.version_info[0] < 3:
    print("This module can only be used with Python 3.")
    print("For a Python 2 version, see:\nhttps://github.com/originell/jpype")
    sys.exit(1)

# ------------------------------------------------------------------------------

class NoJDKError(Exception):
    """
    No JDK found
    """
    def __init__(self, possible_homes):
        """
        Sets up the exception message
        """
        Exception.__init__(self, "No JDK found")

        # Normalize possible homes -> always give an iterable or None
        if not possible_homes:
            self.possible_homes = []

        elif not isinstance(possible_homes, (list, tuple)):
            self.possible_homes = [possible_homes]

        else:
            self.possible_homes = possible_homes


class JDKFinder(object):
    """
    Base JDK installation finder
    """
    def __init__(self):
        """
        Sets up the basic configuration
        """
        self.configuration = {
          'include_dirs': [
                           os.path.join('src', 'native', 'common', 'include'),
                           os.path.join('src', 'native', 'python', 'include'),
                           ],
          'sources': self.find_sources()}


    def find_sources(self):
        """
        Sets up the list of files to be compiled
        """
        # Source folders
        common_dir = os.path.join("src", "native", "common")
        python_dir = os.path.join("src", "native", "python")

        # List all .cpp files in those folders
        cpp_files = []
        for folder in (common_dir, python_dir):
            for root, _, filenames in os.walk(folder):
                cpp_files.extend(os.path.join(root, filename)
                                 for filename in filenames
                                 if os.path.splitext(filename)[1] == '.cpp')

        return cpp_files


    def find_jdk_home(self):
        """
        Tries to locate a JDK home folder, according to the JAVA_HOME
        environment variable

        :return: The path to the JDK home
        :raise NoJDKError: No JDK found
        """
        java_home = os.getenv("JAVA_HOME")
        if self.check_jdk(java_home):
            return java_home

        raise NoJDKError(os.getenv("JAVA_HOME"))


    def check_homes(self, homes):
        """
        Checks if one the given folders is a JDK home, and returns it

        :param homes: A list of possible JDK homes
        :return: The first JDK home found, or None
        """
        for java_home in homes:
            java_home = self.check_jdk(os.path.realpath(java_home))
            if java_home is not None:
                # Valid path
                return java_home

        return None


    def check_jdk(self, java_home):
        """
        Checks if the given folder can be a JDK installation

        :param java_home: A possible JDK installation
        :return: The real folder path if it contains headers, else None
        """
        if not java_home:
            return

        # Possible JDK folder names
        possible_names = ('jdk', 'java', 'icedtea')

        # Construct the full path
        java_home = os.path.realpath(java_home)
        if not os.path.isdir(java_home):
            return

        # Lower-case content tests
        folder = os.path.basename(java_home).lower()

        # Consider it's a JDK if it has an 'include' folder
        # and if the folder name contains 'jdk' or 'java'
        for name in possible_names:
            if name in folder:
                include_path = os.path.join(java_home, 'include')
                if os.path.exists(include_path):
                    # Match
                    return java_home

# ------------------------------------------------------------------------------

class WindowsJDKFinder(JDKFinder):
    """
    Windows specific JDK Finder
    """
    def __init__(self):
        """
        Sets up the basic configuration

        :raise ValueError: No JDK installation found
        """
        # Basic configuration
        JDKFinder.__init__(self)
        self.configuration['libraries'] = ['Advapi32']
        self.configuration['define_macros'] = [('WIN32', 1)]
        self.configuration['extra_compile_args'] = ['/EHsc']

        # Look for the JDK home folder
        java_home = self.find_jdk_home()

        # Home-based configuration
        self.configuration['library_dirs'] = [os.path.join(java_home, 'lib'), ]
        self.configuration['include_dirs'] += [
            os.path.join(java_home, 'include'),
            os.path.join(java_home, 'include', 'win32')
        ]


    def find_jdk_home(self):
        """
        Tries to locate a JDK home folder, according to the JAVA_HOME
        environment variable, or to the Windows registry

        :return: The path to the JDK home
        :raise ValueError: No JDK installation found
        """
        visited_folders = []
        try:
            java_home = JDKFinder.find_jdk_home(self)
            # Found it
            return java_home

        except NoJDKError as ex:
            visited_folders.extend(ex.possible_homes)

        # Try from registry
        java_home = self._get_from_registry()
        if java_home and self.check_jdk(java_home):
            return java_home

        # Try with known locations
        # 64 bits (or 32 bits on 32 bits OS) JDK
        possible_homes = glob(os.path.join(os.environ['ProgramFiles'],
                                           "Java", "*"))

        try:
            # 32 bits (or none on 32 bits OS) JDK
            possible_homes += glob(os.path.join(os.environ['ProgramFiles(x86)'],
                                                "Java", "*"))
        except KeyError:
            # Environment variable doesn't exist on Windows 32 bits
            pass

        # Compute the real home folder
        java_home = self.check_homes(possible_homes)
        if java_home:
            return java_home

        else:
            visited_folders.extend(possible_homes)
            raise NoJDKError(visited_folders)


    def _get_from_registry(self):
        """
        Retrieves the path to the default Java installation stored in the
        Windows registry

        :return: The path found in the registry, or None
        """
        import winreg
        try:
            jreKey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r"SOFTWARE\JavaSoft\Java Runtime Environment")
            cv = winreg.QueryValueEx(jreKey, "CurrentVersion")
            versionKey = winreg.OpenKey(jreKey, cv[0])
            winreg.CloseKey(jreKey)

            cv = winreg.QueryValueEx(versionKey, "RuntimeLib")
            winreg.CloseKey(versionKey)

            return cv[0]

        except WindowsError:
            pass

        return None

# ------------------------------------------------------------------------------

class DarwinJDKFinder(JDKFinder):
    """
    Mac OS X specific JDK Finder
    """
    def __init__(self):
        """
        Sets up the basic configuration

        :raise ValueError: No JDK installation found
        """
        # Basic configuration
        JDKFinder.__init__(self)
        self.configuration['libraries'] = ['dl']
        self.configuration['define_macros'] = [('MACOSX', 1)]

        # Look for the JDK home folder
        java_home = self.find_jdk_home()

        # Home-based configuration
        self.configuration['library_dirs'] = [os.path.join(java_home, 'lib')]
        self.configuration['include_dirs'] += [
            os.path.join(java_home, 'include'),
            os.path.join(java_home, 'include', 'darwin'),
        ]


    def find_jdk_home(self):
        """
        Tries to locate a JDK home folder, according to the JAVA_HOME
        environment variable, or to the Windows registry

        :return: The path to the JDK home
        :raise ValueError: No JDK installation found
        """
        visited_folders = []
        try:
            java_home = JDKFinder.find_jdk_home(self)
            # Found it
            return java_home

        except NoJDKError as ex:
            visited_folders.extend(ex.possible_homes)

        # Changes according to:
        # http://stackoverflow.com/questions/8525193/cannot-install-jpype-on-os-x-lion-to-use-with-neo4j
        # and
        # http://blog.y3xz.com/post/5037243230/installing-jpype-on-mac-os-x
        osx = platform.mac_ver()[0][:4]

        # Seems like the installation folder for Java 7
        possible_homes = glob("/Library/Java/JavaVirtualMachines/*")

        if osx in ('10.7', '10.8'):
            # ... for Java 6
            possible_homes.append('/System/Library/Frameworks/' \
                                  'JavaVM.framework/Versions/Current/')

        elif osx == '10.6':
            # Previous Mac OS version
            possible_homes.append('/Developer/SDKs/MacOSX10.6.sdk/System/' \
                                  'Library/Frameworks/JavaVM.framework/' \
                                  'Versions/1.6.0/')

        else:
            # Other previous version
            possible_homes.append('/Library/Java/Home')

        # Compute the real home folder
        java_home = self.check_homes(possible_homes)
        if java_home:
            return java_home

        else:
            # No JDK found
            visited_folders.extend(possible_homes)
            raise NoJDKError(visited_folders)


    def check_jdk(self, java_home):
        """
        Checks if the given folder can be a JDK installation for Mac OS X

        :param java_home: A possible JDK installation
        :return: The real folder path if it contains headers, else None
        """
        if not java_home:
            return

        # Lower-case content tests
        folder = os.path.basename(java_home).lower()
        if 'jdk' not in folder:
            return

        # Construct the full path
        java_home = os.path.realpath(java_home)
        if not os.path.isdir(java_home):
            return

        # Mac OS specific sub path
        java_home = os.path.join(java_home, 'Contents', 'Home')
        if not os.path.isdir(java_home):
            return

        # Consider it's a JDK if it has an 'include' folder
        # and if the folder name contains 'jdk' or 'java'
        include_path = os.path.join(java_home, 'include')
        if os.path.exists(include_path):
            # Match
            return java_home


# ------------------------------------------------------------------------------

class LinuxJDKFinder(JDKFinder):
    """
    Linux specific JDK Finder
    """
    def __init__(self):
        """
        Sets up the basic configuration

        :raise ValueError: No JDK installation found
        """
        # Basic configuration
        JDKFinder.__init__(self)
        self.configuration['libraries'] = ['dl']

        # Look for the JDK home folder
        java_home = self.find_jdk_home()

        # Home-based configuration
        self.configuration['library_dirs'] = [os.path.join(java_home, 'lib')]
        self.configuration['include_dirs'] += [
            os.path.join(java_home, 'include'),
            os.path.join(java_home, 'include', 'linux'),
        ]


    def find_jdk_home(self):
        """
        Tries to locate a JDK home folder, according to the JAVA_HOME
        environment variable, or to the Windows registry

        :return: The path to the JDK home
        :raise ValueError: No JDK installation found
        """
        visited_folders = []
        try:
            java_home = JDKFinder.find_jdk_home(self)
            # Found it
            return java_home

        except NoJDKError as ex:
            visited_folders.extend(ex.possible_homes)

        # (Almost) standard in GNU/Linux
        possible_homes = glob('/usr/lib/jvm/*')

        # Sun/Oracle Java in some cases
        possible_homes += glob('/usr/java/*')

        # Compute the real home folder
        java_home = self.check_homes(possible_homes)
        if java_home:
            return java_home

        else:
            visited_folders.extend(possible_homes)
            raise NoJDKError(visited_folders)

# ------------------------------------------------------------------------------

try:
    if sys.platform == 'win32':
        config = WindowsJDKFinder()

    elif sys.platform == 'darwin':
        config = DarwinJDKFinder()

    else:
        config = LinuxJDKFinder()

except NoJDKError as ex:
    raise RuntimeError(
                "No Java/JDK could be found. I looked in the following "
                "directories:\n\n{0}\n\n"
                "Please check that you have it installed.\n\n"
                "If you have and the destination is not in the "
                "above list, please find out where your java's home is, "
                "set your JAVA_HOME environment variable to that path and "
                "retry the installation.\n"
                "If this still fails please open a ticket or create a "
                "pull request with a fix on github:\n"
                "https://github.com/tcalmant/jpype/"
                .format('\n'.join(ex.possible_homes)))

# ------------------------------------------------------------------------------

# Define the Python extension
jpypeLib = Extension(name="_jpype", **config.configuration)

# Setup the package
setup(
    name="JPype1-py3",
    version=__version__,
    description="Python-Java bridge. Fork of the jPype project by "
    "Steve Menard (http://jpype.sourceforge.net/), with the "
    "modifications applied by Luis Nell "
    "(https://github.com/originell/jpype)",
    long_description=open("README.rst").read(),
    license='License :: OSI Approved :: Apache Software License',
    author='Steve Menard',
    author_email='devilwolf@users.sourceforge.net',
    maintainer='Thomas Calmant',
    maintainer_email='thomas.calmant@gmail.com',
    url="http://github.com/tcalmant/jpype-py3/",
    platforms=[
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows :: Windows 7',
        'Operating System :: Microsoft :: Windows :: Windows Vista',
        'Operating System :: POSIX :: Linux',
    ],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Java',
        'Programming Language :: Python :: 3'
    ],
    packages=[
        "jpype", 'jpype.awt', 'jpype.awt.event',
        'jpypex', 'jpypex.swing'],
    package_dir={
        "jpype": os.path.join("src", "python", "jpype"),
        'jpypex': os.path.join("src", "python", "jpypex"),
    },
    ext_modules=[jpypeLib],
)
