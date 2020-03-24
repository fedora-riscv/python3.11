# ==================
# Top-level metadata
# ==================

%global pybasever 3.9

# pybasever without the dot:
%global pyshortver 39

Name: python%{pyshortver}
Summary: Version %{pybasever} of the Python interpreter
URL: https://www.python.org/

#  WARNING  When rebasing to a new Python version,
#           remember to update the python3-docs package as well
%global general_version %{pybasever}.0
%global prerel a5
%global upstream_version %{general_version}%{?prerel}
Version: %{general_version}%{?prerel:~%{prerel}}
Release: 1%{?dist}
License: Python


# ==================================
# Conditionals controlling the build
# ==================================

# Note that the bcond macros are named for the CLI option they create.
# "%%bcond_without" means "ENABLE by default and create a --without option"


# Flat package, i.e. python36, python37, python38 for tox etc.
# WARNING: This also influences the main_python bcond below.
# in Fedora, never turn this on for the python3 package
# and always keep it on for python37 etc.
# WARNING: This does not change the package name and summary above.
%bcond_without flatpackage

# Main Python, i.e. whether this is the main Python version in the distribution
# that owns /usr/bin/python3 and other unique paths
# Default: if this is a flatpackage -> it is not the main Python
%if %{with flatpackage}
%bcond_with main_python
%else
%bcond_without main_python
%endif

# When bootstrapping python3, we need to build setuptools.
# but setuptools BR python3-devel and that brings in python3-rpm-generators;
# python3-rpm-generators needs python3-setuptools, so we cannot have it yet.
#
# Procedure: https://fedoraproject.org/wiki/SIGs/Python/UpgradingPython
#
#   IMPORTANT: When bootstrapping, it's very likely the wheels for pip and
#   setuptools are not available. Turn off the rpmwheels bcond until
#   the two packages are built with wheels to get around the issue.
%bcond_with bootstrap

# Whether to use RPM build wheels from the python-{pip,setuptools}-wheel package
# Uses upstream bundled prebuilt wheels otherwise
%bcond_without rpmwheels

# Expensive optimizations (mainly, profile-guided optimizations)
%bcond_without optimizations

# https://fedoraproject.org/wiki/Changes/PythonNoSemanticInterpositionSpeedup
%bcond_without no_semantic_interposition

# Run the test suite in %%check
%bcond_without tests

# Extra build for debugging the interpreter or C-API extensions
# (the -debug subpackages)
%if %{with flatpackage}
%bcond_with debug_build
%else
%bcond_without debug_build
%endif

# Support for the GDB debugger
%bcond_without gdb_hooks

# The dbm.gnu module (key-value database)
%bcond_without gdbm

# Main interpreter loop optimization
%bcond_without computed_gotos

# Support for the Valgrind debugger/profiler
%ifarch %{valgrind_arches}
%bcond_without valgrind
%else
%bcond_with valgrind
%endif


# =====================
# General global macros
# =====================

%global pylibdir %{_libdir}/python%{pybasever}
%global dynload_dir %{pylibdir}/lib-dynload

# ABIFLAGS, LDVERSION and SOABI are in the upstream configure.ac
# See PEP 3149 for some background: http://www.python.org/dev/peps/pep-3149/
%global ABIFLAGS_optimized %{nil}
%global ABIFLAGS_debug     d

%global LDVERSION_optimized %{pybasever}%{ABIFLAGS_optimized}
%global LDVERSION_debug     %{pybasever}%{ABIFLAGS_debug}

%global SOABI_optimized cpython-%{pyshortver}%{ABIFLAGS_optimized}-%{_arch}-linux%{_gnu}
%global SOABI_debug     cpython-%{pyshortver}%{ABIFLAGS_debug}-%{_arch}-linux%{_gnu}

# All bytecode files are in a __pycache__ subdirectory, with a name
# reflecting the version of the bytecode.
# See PEP 3147: http://www.python.org/dev/peps/pep-3147/
# For example,
#   foo/bar.py
# has bytecode at:
#   foo/__pycache__/bar.cpython-%%{pyshortver}.pyc
#   foo/__pycache__/bar.cpython-%%{pyshortver}.opt-1.pyc
#   foo/__pycache__/bar.cpython-%%{pyshortver}.opt-2.pyc
%global bytecode_suffixes .cpython-%{pyshortver}*.pyc

# Python's configure script defines SOVERSION, and this is used in the Makefile
# to determine INSTSONAME, the name of the libpython DSO:
#   LDLIBRARY='libpython$(VERSION).so'
#   INSTSONAME="$LDLIBRARY".$SOVERSION
# We mirror this here in order to make it easier to add the -gdb.py hooks.
# (if these get out of sync, the payload of the libs subpackage will fail
# and halt the build)
%global py_SOVERSION 1.0
%global py_INSTSONAME_optimized libpython%{LDVERSION_optimized}.so.%{py_SOVERSION}
%global py_INSTSONAME_debug     libpython%{LDVERSION_debug}.so.%{py_SOVERSION}

# Disable automatic bytecompilation. The python3 binary is not yet be
# available in /usr/bin when Python is built. Also, the bytecompilation fails
# on files that test invalid syntax.
%undefine py_auto_byte_compile


# =======================
# Build-time requirements
# =======================

# (keep this list alphabetized)

BuildRequires: autoconf
BuildRequires: bluez-libs-devel
BuildRequires: bzip2
BuildRequires: bzip2-devel
BuildRequires: desktop-file-utils
BuildRequires: expat-devel

BuildRequires: findutils
BuildRequires: gcc-c++
%if %{with gdbm}
BuildRequires: gdbm-devel
%endif
BuildRequires: glibc-all-langpacks
BuildRequires: glibc-devel
BuildRequires: gmp-devel
BuildRequires: gnupg2
BuildRequires: libappstream-glib
BuildRequires: libffi-devel
BuildRequires: libnsl2-devel
BuildRequires: libtirpc-devel
BuildRequires: libGL-devel
BuildRequires: libuuid-devel
BuildRequires: libX11-devel
BuildRequires: ncurses-devel

BuildRequires: openssl-devel
BuildRequires: pkgconfig
BuildRequires: readline-devel
BuildRequires: redhat-rpm-config >= 127
BuildRequires: sqlite-devel
BuildRequires: gdb

BuildRequires: tar
BuildRequires: tcl-devel
BuildRequires: tix-devel
BuildRequires: tk-devel

%if %{with valgrind}
BuildRequires: valgrind-devel
%endif

BuildRequires: xz-devel
BuildRequires: zlib-devel

BuildRequires: /usr/bin/dtrace

# workaround http://bugs.python.org/issue19804 (test_uuid requires ifconfig)
BuildRequires: /usr/sbin/ifconfig

# For %%python_provide
BuildRequires: python-rpm-macros

%if %{with rpmwheels}
BuildRequires: python-setuptools-wheel
BuildRequires: python-pip-wheel
%endif

%if %{without bootstrap}
# for make regen-all and distutils.tests.test_bdist_rpm
BuildRequires: python%{pyshortver}
%endif

# =======================
# Source code and patches
# =======================

Source0: %{url}ftp/python/%{general_version}/Python-%{upstream_version}.tar.xz
Source1: %{url}ftp/python/%{general_version}/Python-%{upstream_version}.tar.xz.asc
Source2: %{url}static/files/pubkeys.txt

# A simple script to check timestamps of bytecode files
# Run in check section with Python that is currently being built
# Originally written by bkabrda
Source8: check-pyc-timestamps.py

# Desktop menu entry for idle3
Source10: idle3.desktop

# AppData file for idle3
Source11: idle3.appdata.xml

# 00001 #
# Fixup distutils/unixccompiler.py to remove standard library path from rpath:
# Was Patch0 in ivazquez' python3000 specfile:
Patch1:         00001-rpath.patch

# 00111 #
# Patch the Makefile.pre.in so that the generated Makefile doesn't try to build
# a libpythonMAJOR.MINOR.a
# See https://bugzilla.redhat.com/show_bug.cgi?id=556092
# Downstream only: not appropriate for upstream
Patch111: 00111-no-static-lib.patch

# 00189 #
# Instead of bundled wheels, use our RPM packaged wheels from
# /usr/share/python-wheels
# Downstream only: upstream bundles
# We might eventually pursuit upstream support, but it's low prio
Patch189: 00189-use-rpm-wheels.patch

# 00251
# Set values of prefix and exec_prefix in distutils install command
# to /usr/local if executable is /usr/bin/python* and RPM build
# is not detected to make pip and distutils install into separate location
# Fedora Change: https://fedoraproject.org/wiki/Changes/Making_sudo_pip_safe
# Downstream only: Awaiting resources to work on upstream PEP
Patch251: 00251-change-user-install-location.patch

# 00274 #
# Upstream uses Debian-style architecture naming. Change to match Fedora.
Patch274: 00274-fix-arch-names.patch

# 00328 #
# Restore pyc to TIMESTAMP invalidation mode as default in rpmbubild
# See https://src.fedoraproject.org/rpms/redhat-rpm-config/pull-request/57#comment-27426
# Downstream only: only used when building RPM packages
# Ideally, we should talk to upstream and explain why we don't want this
Patch328: 00328-pyc-timestamp-invalidation-mode.patch

# (New patches go here ^^^)
#
# When adding new patches to "python" and "python3" in Fedora, EL, etc.,
# please try to keep the patch numbers in-sync between all specfiles.
#
# More information, and a patch number catalog, is at:
#
#     https://fedoraproject.org/wiki/SIGs/Python/PythonPatches
#
# The patches are stored and rebased at:
#
#     https://github.com/fedora-python/cpython


# ==========================================
# Descriptions, and metadata for subpackages
# ==========================================

# People might want to dnf install pythonX.Y instead of pythonXY;
# we enable this in both flat and nonflat package.
Provides: python%{pybasever} = %{version}-%{release}

%if %{without flatpackage}

# Packages with Python modules in standard locations automatically
# depend on python(abi). Provide that here.
Provides: python(abi) = %{pybasever}

Requires: %{name}-libs%{?_isa} = %{version}-%{release}

# In order to support multiple Python interpreters for development purposes,
# packages with the naming scheme flatpackage (e.g. python35) exist for
# non-default versions of Python 3.
# For consistency, and to keep the upgrade path clean, we Provide/Obsolete
# these names here.
Provides: python%{pyshortver} = %{version}-%{release}
# Note that using Obsoletes without package version is not standard practice.
# Here we assert that *any* version of the system's default interpreter is
# preferable to an "extra" interpreter. For example, python3-3.6.1 will
# replace python36-3.6.2.
Obsoletes: python%{pyshortver}

%if %{with main_python}
# https://fedoraproject.org/wiki/Changes/Move_usr_bin_python_into_separate_package
# https://fedoraproject.org/wiki/Changes/Python_means_Python3
# We recommend /usr/bin/python so users get it by default
# Versioned recommends are problematic, and we know that the package requires
# python3 back with fixed version, so we just use the path here:
Recommends: %{_bindir}/python
%endif

# In Fedora 31, /usr/bin/pydoc was moved here from Python 2.
# Ideally we'd have an explicit conflict with "/usr/bin/pydoc < 3",
# but file provides aren't versioned and the file moved across packages.
# Instead, we rely on the conflict in python3-libs.

# Previously, this was required for our rewheel patch to work.
# This is technically no longer needed, but we keep it recommended
# for the developer experience.
Recommends: python3-setuptools
Recommends: python3-pip

# This prevents ALL subpackages built from this spec to require
# /usr/bin/python3*. Granularity per subpackage is impossible.
# It's intended for the libs package not to drag in the interpreter, see
# https://bugzilla.redhat.com/show_bug.cgi?id=1547131
# All others require %%{name} anyway.
%global __requires_exclude ^/usr/bin/python3


# The description used both for the SRPM and the main `python3` subpackage:
%description
Python is an accessible, high-level, dynamically typed, interpreted programming
language, designed with an emphasis on code readability.
It includes an extensive standard library, and has a vast ecosystem of
third-party libraries.

The %{name} package provides the "python3" executable: the reference
interpreter for the Python language, version 3.
The majority of its standard library is provided in the %{name}-libs package,
which should be installed automatically along with %{name}.
The remaining parts of the Python standard library are broken out into the
%{name}-tkinter and %{name}-test packages, which may need to be installed
separately.

Documentation for Python is provided in the %{name}-docs package.

Packages containing additional libraries for Python are generally named with
the "%{name}-" prefix.


%if %{with main_python}
# https://fedoraproject.org/wiki/Changes/Move_usr_bin_python_into_separate_package
# https://fedoraproject.org/wiki/Changes/Python_means_Python3
%package -n python-unversioned-command
Summary: The "python" command that runs Python 3
BuildArch: noarch

# In theory this could require any python3 version
Requires: python3 == %{version}-%{release}
# But since we want to provide versioned python, we require exact version
Provides: python = %{version}-%{release}
# This also save us an explicit conflict for older python3 builds

%description -n python-unversioned-command
This package contains /usr/bin/python - the "python" command that runs Python 3.

%endif # with main_python


%package libs
Summary:        Python runtime libraries

%if %{with rpmwheels}
Requires: python-setuptools-wheel
Requires: python-pip-wheel
%else
Provides: bundled(python3-pip) = 19.2.3
Provides: bundled(python3-setuptools) = 41.2.0
%endif

%{?python_provide:%python_provide python3-libs}

# There are files in the standard library that have python shebang.
# We've filtered the automatic requirement out so libs are installable without
# the main package. This however makes it pulled in by default.
# See https://bugzilla.redhat.com/show_bug.cgi?id=1547131
Recommends: %{name}%{?_isa} = %{version}-%{release}

# tkinter is part of the standard library,
# but it is torn out to save an unwanted dependency on tk and X11.
# we recommend it when tk is already installed (for better UX)
Recommends: (%{name}-tkinter%{?_isa} = %{version}-%{release} if tk%{?_isa})

# https://fedoraproject.org/wiki/Changes/Move_usr_bin_python_into_separate_package
# In Fedora 31, several "unversioned" files like /usr/bin/pydoc and all the
# "unversioned" provides were moved from python2 to python3.
# So, newer python3 packages need to conflict with old Python 2 builds that
# still provided unversioned Python.
# Since all python packages, new and old, have versioned requires on
# python?-libs, we do it here:
Conflicts: python-libs < 3
# (We explicitly conflict with python-libs and not python2-libs, so only the
# old Python 2 builds that still provided unversioned Python are handled.)


%description libs
This package contains runtime libraries for use by Python:
- the majority of the Python standard library
- a dynamically linked library for use by applications that embed Python as
  a scripting language, and by the main "python3" executable


%package devel
Summary: Libraries and header files needed for Python development
Requires: %{name} = %{version}-%{release}
Requires: %{name}-libs%{?_isa} = %{version}-%{release}
BuildRequires: python-rpm-macros
# The RPM related dependencies bring nothing to a non-RPM Python developer
# But we want them when packages BuildRequire python3-devel
Requires: (python-rpm-macros if rpm-build)
Requires: (python3-rpm-macros if rpm-build)

%if %{without bootstrap}
# This is not "API" (packages that need setuptools should still BuildRequire it)
# However some packages apparently can build both with and without setuptools
# producing egg-info as file or directory (depending on setuptools presence).
# Directory-to-file updates are problematic in RPM, so we ensure setuptools is
# installed when -devel is required.
# See https://bugzilla.redhat.com/show_bug.cgi?id=1623914
# See https://fedoraproject.org/wiki/Packaging:Directory_Replacement
Requires: (python3-setuptools if rpm-build)

Requires: (python3-rpm-generators if rpm-build)
%endif

%{?python_provide:%python_provide python3-devel}

Provides: %{name}-2to3 = %{version}-%{release}
Provides: 2to3 = %{version}-%{release}

Conflicts: %{name} < %{version}-%{release}

# In Fedora 31, several "unversioned" files were moved here from Python 2:
# pygettext.py, msgfmt.py, python-config, python.pc
Conflicts: python-devel < 3

%description devel
This package contains the header files and configuration needed to compile
Python extension modules (typically written in C or C++), to embed Python
into other programs, and to make binary distributions for Python libraries.

It also contains the necessary macros to build RPM packages with Python modules
and 2to3 tool, an automatic source converter from Python 2.X.


%package idle
Summary: A basic graphical development environment for Python
Requires: %{name} = %{version}-%{release}
Requires: %{name}-tkinter = %{version}-%{release}

Provides: idle3 = %{version}-%{release}
Provides: idle = %{version}-%{release}

Provides: %{name}-tools = %{version}-%{release}
Provides: %{name}-tools%{?_isa} = %{version}-%{release}
Obsoletes: %{name}-tools < %{version}-%{release}

# In Fedora 31, /usr/bin/idle was moved here from Python 2.
Conflicts: python-tools < 3

%{?python_provide:%python_provide python3-idle}

%description idle
IDLE is Python’s Integrated Development and Learning Environment.

IDLE has the following features: Python shell window (interactive
interpreter) with colorizing of code input, output, and error messages;
multi-window text editor with multiple undo, Python colorizing,
smart indent, call tips, auto completion, and other features;
search within any window, replace within editor windows, and
search through multiple files (grep); debugger with persistent
breakpoints, stepping, and viewing of global and local namespaces;
configuration, browsers, and other dialogs.


%package tkinter
Summary: A GUI toolkit for Python
Requires: %{name} = %{version}-%{release}

%{?python_provide:%python_provide python3-tkinter}

%description tkinter
The Tkinter (Tk interface) library is a graphical user interface toolkit for
the Python programming language.


%package test
Summary: The self-test suite for the main python3 package
Requires: %{name} = %{version}-%{release}
Requires: %{name}-libs%{?_isa} = %{version}-%{release}

%{?python_provide:%python_provide python3-test}

%description test
The self-test suite for the Python interpreter.

This is only useful to test Python itself. For testing general Python code,
you should use the unittest module from %{name}-libs, or a library such as
%{name}-pytest or %{name}-nose.


%if %{with debug_build}
%package debug
Summary: Debug version of the Python runtime

# The debug build is an all-in-one package version of the regular build, and
# shares the same .py/.pyc files and directories as the regular build. Hence
# we depend on all of the subpackages of the regular build:
Requires: %{name}%{?_isa} = %{version}-%{release}
Requires: %{name}-libs%{?_isa} = %{version}-%{release}
Requires: %{name}-devel%{?_isa} = %{version}-%{release}
Requires: %{name}-test%{?_isa} = %{version}-%{release}
Requires: %{name}-tkinter%{?_isa} = %{version}-%{release}
Requires: %{name}-idle%{?_isa} = %{version}-%{release}

# In Fedora 31, /usr/bin/python-debug was moved here from Python 2.
Conflicts: python-debug < 3

%{?python_provide:%python_provide python3-debug}

%description debug
python3-debug provides a version of the Python runtime with numerous debugging
features enabled, aimed at advanced Python users such as developers of Python
extension modules.

This version uses more memory and will be slower than the regular Python build,
but is useful for tracking down reference-counting issues and other bugs.

The debug build shares installation directories with the standard Python
runtime. Python modules -- source (.py), bytecode (.pyc), and C-API extensions
(.cpython*.so) -- are compatible between this and the standard version
of Python.

The debug runtime additionally supports debug builds of C-API extensions
(with the "d" ABI flag) for debugging issues in those extensions.
%endif # with debug_build

%else  # with flatpackage

# We'll not provide this, on purpose
# No package in Fedora shall ever depend on flatpackage via this
%global __requires_exclude ^python\\(abi\\) = 3\\..$
%global __provides_exclude ^python\\(abi\\) = 3\\..$

%if %{with rpmwheels}
Requires: python-setuptools-wheel
Requires: python-pip-wheel
%else
Provides: bundled(python3-pip) = 19.2.3
Provides: bundled(python3-setuptools) = 41.2.0
%endif

# The description for the flat package
%description
Python %{pybasever} package for developers.

This package exists to allow developers to test their code against a newer
version of Python. This is not a full Python stack and if you wish to run
your applications with Python %{pybasever}, update your Fedora to a newer
version once Python %{pybasever} is stable.

%endif # with flatpackage

# ======================================================
# The prep phase of the build:
# ======================================================

%prep
%gpgverify -k2 -s1 -d0
%setup -q -n Python-%{upstream_version}
# Remove all exe files to ensure we are not shipping prebuilt binaries
# note that those are only used to create Microsoft Windows installers
# and that functionality is broken on Linux anyway
find -name '*.exe' -print -delete

# Remove bundled libraries to ensure that we're using the system copy.
rm -r Modules/expat

#
# Apply patches:
#
%patch1 -p1
%patch111 -p1

%if %{with rpmwheels}
%patch189 -p1
rm Lib/ensurepip/_bundled/*.whl
%endif

%patch251 -p1
%patch274 -p1
%patch328 -p1


# Remove files that should be generated by the build
# (This is after patching, so that we can use patches directly from upstream)
rm configure pyconfig.h.in


# ======================================================
# Configuring and building the code:
# ======================================================

%build

# Regenerate the configure script and pyconfig.h.in
autoconf
autoheader

# Remember the current directory (which has sources and the configure script),
# so we can refer to it after we "cd" elsewhere.
topdir=$(pwd)

# Get proper option names from bconds
%if %{with computed_gotos}
%global computed_gotos_flag yes
%else
%global computed_gotos_flag no
%endif

%if %{with optimizations}
%global optimizations_flag "--enable-optimizations"
%else
%global optimizations_flag "--disable-optimizations"
%endif

# Set common compiler/linker flags
# We utilize the %%extension_...flags macros here so users building C/C++
# extensions with our python won't get all the compiler/linker flags used
# in Fedora RPMs.
# Standard library built here will still use the %%build_...flags,
# Fedora packages utilizing %%py3_build will use them as well
# https://fedoraproject.org/wiki/Changes/Python_Extension_Flags
export CFLAGS="%{extension_cflags} -D_GNU_SOURCE -fPIC -fwrapv"
export CFLAGS_NODIST="%{build_cflags} -D_GNU_SOURCE -fPIC -fwrapv%{?with_no_semantic_interposition: -fno-semantic-interposition}"
export CXXFLAGS="%{extension_cxxflags} -D_GNU_SOURCE -fPIC -fwrapv"
export CPPFLAGS="$(pkg-config --cflags-only-I libffi)"
export OPT="%{extension_cflags} -D_GNU_SOURCE -fPIC -fwrapv"
export LINKCC="gcc"
export CFLAGS="$CFLAGS $(pkg-config --cflags openssl)"
export LDFLAGS="%{extension_ldflags} -g $(pkg-config --libs-only-L openssl)"
export LDFLAGS_NODIST="%{build_ldflags}%{?with_no_semantic_interposition: -fno-semantic-interposition} -g $(pkg-config --libs-only-L openssl)"

# We can build several different configurations of Python: regular and debug.
# Define a common function that does one build:
BuildPython() {
  ConfName=$1
  ExtraConfigArgs=$2
  MoreCFlags=$3

  # Each build is done in its own directory
  ConfDir=build/$ConfName
  echo STARTING: BUILD OF PYTHON FOR CONFIGURATION: $ConfName
  mkdir -p $ConfDir
  pushd $ConfDir

  # Normally, %%configure looks for the "configure" script in the current
  # directory.
  # Since we changed directories, we need to tell %%configure where to look.
  %global _configure $topdir/configure

  # A workaround for https://bugs.python.org/issue39761
  export DFLAGS=" "

%configure \
  --with-platlibdir=%{_lib} \
  --enable-ipv6 \
  --enable-shared \
  --with-computed-gotos=%{computed_gotos_flag} \
  --with-dbmliborder=gdbm:ndbm:bdb \
  --with-system-expat \
  --with-system-ffi \
  --enable-loadable-sqlite-extensions \
  --with-dtrace \
  --with-lto \
  --with-ssl-default-suites=openssl \
%if %{with valgrind}
  --with-valgrind \
%endif
  $ExtraConfigArgs \
  %{nil}

%global flags_override EXTRA_CFLAGS="$MoreCFlags" CFLAGS_NODIST="$CFLAGS_NODIST $MoreCFlags"

%if %{without bootstrap}
  # Regenerate generated files (needs python3)
  %make_build %{flags_override} regen-all PYTHON_FOR_REGEN="python%{pybasever}"
%endif

  # Invoke the build
  %make_build %{flags_override}

  popd
  echo FINISHED: BUILD OF PYTHON FOR CONFIGURATION: $ConfName
}

# Call the above to build each configuration.

%if %{with debug_build}
BuildPython debug \
  "--without-ensurepip --with-pydebug" \
  "-Og"
%endif # with debug_build

BuildPython optimized \
  "--without-ensurepip %{optimizations_flag}" \
  ""

# ======================================================
# Installing the built code:
# ======================================================

%install

# As in %%build, remember the current directory
topdir=$(pwd)

# We install a collection of hooks for gdb that make it easier to debug
# executables linked against libpython3* (such as /usr/bin/python3 itself)
#
# These hooks are implemented in Python itself (though they are for the version
# of python that gdb is linked with)
#
# gdb-archer looks for them in the same path as the ELF file or its .debug
# file, with a -gdb.py suffix.
# We put them next to the debug file, because ldconfig would complain if
# it found non-library files directly in /usr/lib/
# (see https://bugzilla.redhat.com/show_bug.cgi?id=562980)
#
# We'll put these files in the debuginfo package by installing them to e.g.:
#  /usr/lib/debug/usr/lib/libpython3.2.so.1.0.debug-gdb.py
# (note that the debug path is /usr/lib/debug for both 32/64 bit)
#
# See https://fedoraproject.org/wiki/Features/EasierPythonDebugging for more
# information

%if %{with gdb_hooks}
DirHoldingGdbPy=%{_usr}/lib/debug/%{_libdir}
mkdir -p %{buildroot}$DirHoldingGdbPy
%endif # with gdb_hooks

# Multilib support for pyconfig.h
# 32- and 64-bit versions of pyconfig.h are different. For multilib support
# (making it possible to install 32- and 64-bit versions simultaneously),
# we need to install them under different filenames, and to make the common
# "pyconfig.h" include the right file based on architecture.
# See https://bugzilla.redhat.com/show_bug.cgi?id=192747
# Filanames are defined here:
%global _pyconfig32_h pyconfig-32.h
%global _pyconfig64_h pyconfig-64.h
%global _pyconfig_h pyconfig-%{__isa_bits}.h

# Use a common function to do an install for all our configurations:
InstallPython() {

  ConfName=$1
  PyInstSoName=$2
  MoreCFlags=$3
  LDVersion=$4

  # Switch to the directory with this configuration's built files
  ConfDir=build/$ConfName
  echo STARTING: INSTALL OF PYTHON FOR CONFIGURATION: $ConfName
  mkdir -p $ConfDir
  pushd $ConfDir

  make \
    DESTDIR=%{buildroot} \
    INSTALL="install -p" \
    EXTRA_CFLAGS="$MoreCFlags" \
    install

  popd

%if %{with gdb_hooks}
  # See comment on $DirHoldingGdbPy above
  PathOfGdbPy=$DirHoldingGdbPy/$PyInstSoName-%{version}-%{release}.%{_arch}.debug-gdb.py
  cp Tools/gdb/libpython.py %{buildroot}$PathOfGdbPy
%endif # with gdb_hooks

  # Rename the -devel script that differs on different arches to arch specific name
  mv %{buildroot}%{_bindir}/python${LDVersion}-{,`uname -m`-}config
  echo -e '#!/bin/sh\nexec `dirname $0`/python'${LDVersion}'-`uname -m`-config "$@"' > \
    %{buildroot}%{_bindir}/python${LDVersion}-config
  echo '[ $? -eq 127 ] && echo "Could not find python'${LDVersion}'-`uname -m`-config. Look around to see available arches." >&2' >> \
    %{buildroot}%{_bindir}/python${LDVersion}-config
    chmod +x %{buildroot}%{_bindir}/python${LDVersion}-config

  # Make python3-devel multilib-ready
  mv %{buildroot}%{_includedir}/python${LDVersion}/pyconfig.h \
     %{buildroot}%{_includedir}/python${LDVersion}/%{_pyconfig_h}
  cat > %{buildroot}%{_includedir}/python${LDVersion}/pyconfig.h << EOF
#include <bits/wordsize.h>

#if __WORDSIZE == 32
#include "%{_pyconfig32_h}"
#elif __WORDSIZE == 64
#include "%{_pyconfig64_h}"
#else
#error "Unknown word size"
#endif
EOF

  echo FINISHED: INSTALL OF PYTHON FOR CONFIGURATION: $ConfName
}

# Install the "debug" build first; any common files will be overridden with
# later builds
%if %{with debug_build}
InstallPython debug \
  %{py_INSTSONAME_debug} \
  -O0 \
  %{LDVERSION_debug}
%endif # with debug_build

# Now the optimized build:
InstallPython optimized \
  %{py_INSTSONAME_optimized} \
  "" \
  %{LDVERSION_optimized}

# Install directories for additional packages
install -d -m 0755 %{buildroot}%{pylibdir}/site-packages/__pycache__
%if "%{_lib}" == "lib64"
# The 64-bit version needs to create "site-packages" in /usr/lib/ (for
# pure-Python modules) as well as in /usr/lib64/ (for packages with extension
# modules).
# Note that rpmlint will complain about hardcoded library path;
# this is intentional.
install -d -m 0755 %{buildroot}%{_prefix}/lib/python%{pybasever}/site-packages/__pycache__
%endif

%if %{with main_python}
# add idle3 to menu
install -D -m 0644 Lib/idlelib/Icons/idle_16.png %{buildroot}%{_datadir}/icons/hicolor/16x16/apps/idle3.png
install -D -m 0644 Lib/idlelib/Icons/idle_32.png %{buildroot}%{_datadir}/icons/hicolor/32x32/apps/idle3.png
install -D -m 0644 Lib/idlelib/Icons/idle_48.png %{buildroot}%{_datadir}/icons/hicolor/48x48/apps/idle3.png
desktop-file-install --dir=%{buildroot}%{_datadir}/applications %{SOURCE10}

# Install and validate appdata file
mkdir -p %{buildroot}%{_metainfodir}
cp -a %{SOURCE11} %{buildroot}%{_metainfodir}
appstream-util validate-relax --nonet %{buildroot}%{_metainfodir}/idle3.appdata.xml
%endif

# Make sure distutils looks at the right pyconfig.h file
# See https://bugzilla.redhat.com/show_bug.cgi?id=201434
# Similar for sysconfig: sysconfig.get_config_h_filename tries to locate
# pyconfig.h so it can be parsed, and needs to do this at runtime in site.py
# when python starts up (see https://bugzilla.redhat.com/show_bug.cgi?id=653058)
#
# Split this out so it goes directly to the pyconfig-32.h/pyconfig-64.h
# variants:
sed -i -e "s/'pyconfig.h'/'%{_pyconfig_h}'/" \
  %{buildroot}%{pylibdir}/distutils/sysconfig.py \
  %{buildroot}%{pylibdir}/sysconfig.py

# Install pathfix.py to bindir
# See https://github.com/fedora-python/python-rpm-porting/issues/24
cp -p Tools/scripts/pathfix.py %{buildroot}%{_bindir}/

# Install i18n tools to bindir
# They are also in python2, so we version them
# https://bugzilla.redhat.com/show_bug.cgi?id=1571474
for tool in pygettext msgfmt; do
  cp -p Tools/i18n/${tool}.py %{buildroot}%{_bindir}/${tool}%{pybasever}.py
  ln -s ${tool}%{pybasever}.py %{buildroot}%{_bindir}/${tool}3.py
done

# Switch all shebangs to refer to the specific Python version.
# This currently only covers files matching ^[a-zA-Z0-9_]+\.py$,
# so handle files named using other naming scheme separately.
LD_LIBRARY_PATH=./build/optimized ./build/optimized/python \
  Tools/scripts/pathfix.py \
  -i "%{_bindir}/python%{pybasever}" -pn \
  %{buildroot} \
  %{buildroot}%{_bindir}/*%{pybasever}.py \
  %{?with_gdb_hooks:%{buildroot}$DirHoldingGdbPy/*.py}

# Remove shebang lines from .py files that aren't executable, and
# remove executability from .py files that don't have a shebang line:
find %{buildroot} -name \*.py \
  \( \( \! -perm /u+x,g+x,o+x -exec sed -e '/^#!/Q 0' -e 'Q 1' {} \; \
  -print -exec sed -i '1d' {} \; \) -o \( \
  -perm /u+x,g+x,o+x ! -exec grep -m 1 -q '^#!' {} \; \
  -exec chmod a-x {} \; \) \)

# Get rid of DOS batch files:
find %{buildroot} -name \*.bat -exec rm {} \;

# Get rid of backup files:
find %{buildroot}/ -name "*~" -exec rm -f {} \;
find . -name "*~" -exec rm -f {} \;

# Do bytecompilation with the newly installed interpreter.
# This is similar to the script in macros.pybytecompile
# compile *.pyc
# Python CMD line options:
# -s - don't add user site directory to sys.path
# -B - don't write .pyc files on import
# Compileall2 CMD line options:
# -f - force rebuild even if timestamps are up to date
# -o - optimization levels to run compilation with
# -s - part of path to left-strip from path to source file (buildroot)
# -p - path to add as prefix to path to source file (/ to make it absolute)
# --hardlink-dupes - hardlink different optimization level pycs together if identical (saves space)
LD_LIBRARY_PATH="%{buildroot}%{dynload_dir}/:%{buildroot}%{_libdir}" \
PYTHONPATH="%{_rpmconfigdir}/redhat" %{buildroot}%{_bindir}/python%{pybasever} -s -B -m \
compileall2 -f %{_smp_mflags} -o 0 -o 1 -o 2 -s %{buildroot} -p / %{buildroot} --hardlink-dupes || :

# Turn this BRP off, it is done by compileall2 --hardlink-dupes above
%global __brp_python_hardlink %{nil}

# Since we have pathfix.py in bindir, this is created, but we don't want it
rm -rf %{buildroot}%{_bindir}/__pycache__

# Fixup permissions for shared libraries from non-standard 555 to standard 755:
find %{buildroot} -perm 555 -exec chmod 755 {} \;

# Create "/usr/bin/python3-debug", a symlink to the python3 debug binary, to
# avoid the user having to know the precise version and ABI flags.
# See e.g. https://bugzilla.redhat.com/show_bug.cgi?id=676748
%if %{with debug_build} && %{with main_python}
ln -s \
  %{_bindir}/python%{LDVERSION_debug} \
  %{buildroot}%{_bindir}/python3-debug
%endif

# There's 2to3-X.X executable and 2to3 soft link to it.
# No reason to have both, so keep only 2to3 as an executable.
# See https://bugzilla.redhat.com/show_bug.cgi?id=1111275
mv %{buildroot}%{_bindir}/2to3-%{pybasever} %{buildroot}%{_bindir}/2to3

%if %{without main_python}
# Remove stuff that would conflict with python3 package
rm %{buildroot}%{_bindir}/python3
rm %{buildroot}%{_bindir}/pydoc3
rm %{buildroot}%{_bindir}/pathfix.py
rm %{buildroot}%{_bindir}/pygettext3.py
rm %{buildroot}%{_bindir}/msgfmt3.py
rm %{buildroot}%{_bindir}/idle3
rm %{buildroot}%{_bindir}/python3-*
rm %{buildroot}%{_bindir}/2to3
rm %{buildroot}%{_libdir}/libpython3.so
rm %{buildroot}%{_mandir}/man1/python3.1*
rm %{buildroot}%{_libdir}/pkgconfig/python3.pc
rm %{buildroot}%{_libdir}/pkgconfig/python3-embed.pc
%else
# Link the unversioned stuff
# https://fedoraproject.org/wiki/Changes/Python_means_Python3
ln -s ./python3 %{buildroot}%{_bindir}/python
ln -s ./pydoc3 %{buildroot}%{_bindir}/pydoc
ln -s ./pygettext3.py %{buildroot}%{_bindir}/pygettext.py
ln -s ./msgfmt3.py %{buildroot}%{_bindir}/msgfmt.py
ln -s ./idle3 %{buildroot}%{_bindir}/idle
ln -s ./python3-config %{buildroot}%{_bindir}/python-config
ln -s ./python3.1 %{buildroot}%{_mandir}/man1/python.1
ln -s ./python3.pc %{buildroot}%{_libdir}/pkgconfig/python.pc
%if %{with debug_build}
ln -s ./python3-debug %{buildroot}%{_bindir}/python-debug
%endif
%endif


# ======================================================
# Checks for packaging issues
# ======================================================

%check

# first of all, check timestamps of bytecode files
find %{buildroot} -type f -a -name "*.py" -print0 | \
    LD_LIBRARY_PATH="%{buildroot}%{dynload_dir}/:%{buildroot}%{_libdir}" \
    PYTHONPATH="%{buildroot}%{_libdir}/python%{pybasever} %{buildroot}%{_libdir}/python%{pybasever}/site-packages" \
    xargs -0 %{buildroot}%{_bindir}/python%{pybasever} %{SOURCE8}

# Ensure that the curses module was linked against libncursesw.so, rather than
# libncurses.so
# See https://bugzilla.redhat.com/show_bug.cgi?id=539917
ldd %{buildroot}/%{dynload_dir}/_curses*.so \
    | grep curses \
    | grep libncurses.so && (echo "_curses.so linked against libncurses.so" ; exit 1)

# Ensure that the debug modules are linked against the debug libpython, and
# likewise for the optimized modules and libpython:
for Module in %{buildroot}/%{dynload_dir}/*.so ; do
    case $Module in
    *.%{SOABI_debug})
        ldd $Module | grep %{py_INSTSONAME_optimized} &&
            (echo Debug module $Module linked against optimized %{py_INSTSONAME_optimized} ; exit 1)

        ;;
    *.%{SOABI_optimized})
        ldd $Module | grep %{py_INSTSONAME_debug} &&
            (echo Optimized module $Module linked against debug %{py_INSTSONAME_debug} ; exit 1)
        ;;
    esac
done


# ======================================================
# Running the upstream test suite
# ======================================================

topdir=$(pwd)
CheckPython() {
  ConfName=$1
  ConfDir=$(pwd)/build/$ConfName

  # Fedora sets explicit minimum/maximum TLS versions.
  # Python's test suite assumes that the minimum/maximum version is set to
  # a magic marker. We workaround the test problem by setting:
  export OPENSSL_CONF=/non-existing-file
  # https://bugzilla.redhat.com/show_bug.cgi?id=1618753
  # https://bugzilla.redhat.com/show_bug.cgi?id=1778357
  # https://bugs.python.org/issue35045
  # https://bugs.python.org/issue38815

  echo STARTING: CHECKING OF PYTHON FOR CONFIGURATION: $ConfName

  # Note that we're running the tests using the version of the code in the
  # builddir, not in the buildroot.

  # Show some info, helpful for debugging test failures
  LD_LIBRARY_PATH=$ConfDir $ConfDir/python -m test.pythoninfo

  # Run the upstream test suite
  # --timeout=1800: kill test running for longer than 30 minutes
  # test_gdb skipped on s390x:
  #   https://bugzilla.redhat.com/show_bug.cgi?id=1678277
  # test_gdb skipped everywhere:
  #   https://bugzilla.redhat.com/show_bug.cgi?id=1734327
  # test_distutils
  #   distutils.tests.test_bdist_rpm tests fail when bootstraping the Python
  #   package: rpmbuild requires /usr/bin/pythonX.Y to be installed
  LD_LIBRARY_PATH=$ConfDir $ConfDir/python -m test.regrtest \
    -wW --slowest -j0 --timeout=1800 \
    %if %{with bootstrap}
    -x test_distutils \
    %endif
    -x test_gdb \
    %ifarch %{mips64}
    -x test_ctypes \
    %endif

  echo FINISHED: CHECKING OF PYTHON FOR CONFIGURATION: $ConfName

}

%if %{with tests}

# Check each of the configurations:
%if %{with debug_build}
CheckPython debug
%endif # with debug_build
CheckPython optimized

%endif # with tests


%files
%doc README.rst

%if %{with main_python}
%{_bindir}/pydoc*
%{_bindir}/python3
%else
%{_bindir}/pydoc%{pybasever}
%endif

%{_bindir}/python%{pybasever}
%{_bindir}/python%{LDVERSION_optimized}
%{_mandir}/*/*3*


%if %{with main_python}
%if %{without flatpackage}
%files -n python-unversioned-command
%endif
%{_bindir}/python
%{_mandir}/*/python.1*
%endif

%if %{without flatpackage}
%files libs
%doc README.rst
%endif

%dir %{pylibdir}
%dir %{dynload_dir}

%license %{pylibdir}/LICENSE.txt

%{pylibdir}/lib2to3
%if %{without flatpackage}
%exclude %{pylibdir}/lib2to3/tests
%endif

%dir %{pylibdir}/unittest/
%dir %{pylibdir}/unittest/__pycache__/
%{pylibdir}/unittest/*.py
%{pylibdir}/unittest/__pycache__/*%{bytecode_suffixes}

%dir %{pylibdir}/asyncio/
%dir %{pylibdir}/asyncio/__pycache__/
%{pylibdir}/asyncio/*.py
%{pylibdir}/asyncio/__pycache__/*%{bytecode_suffixes}

%dir %{pylibdir}/venv/
%dir %{pylibdir}/venv/__pycache__/
%{pylibdir}/venv/*.py
%{pylibdir}/venv/__pycache__/*%{bytecode_suffixes}
%{pylibdir}/venv/scripts

%{pylibdir}/wsgiref
%{pylibdir}/xmlrpc

%dir %{pylibdir}/ensurepip/
%dir %{pylibdir}/ensurepip/__pycache__/
%{pylibdir}/ensurepip/*.py
%{pylibdir}/ensurepip/__pycache__/*%{bytecode_suffixes}

%if %{with rpmwheels}
%exclude %{pylibdir}/ensurepip/_bundled
%else
%dir %{pylibdir}/ensurepip/_bundled
%{pylibdir}/ensurepip/_bundled/*.whl
%{pylibdir}/ensurepip/_bundled/__init__.py
%{pylibdir}/ensurepip/_bundled/__pycache__/*%{bytecode_suffixes}
%endif

%dir %{pylibdir}/concurrent/
%dir %{pylibdir}/concurrent/__pycache__/
%{pylibdir}/concurrent/*.py
%{pylibdir}/concurrent/__pycache__/*%{bytecode_suffixes}

%dir %{pylibdir}/concurrent/futures/
%dir %{pylibdir}/concurrent/futures/__pycache__/
%{pylibdir}/concurrent/futures/*.py
%{pylibdir}/concurrent/futures/__pycache__/*%{bytecode_suffixes}

%{pylibdir}/pydoc_data

%{dynload_dir}/_blake2.%{SOABI_optimized}.so
%{dynload_dir}/_md5.%{SOABI_optimized}.so
%{dynload_dir}/_sha1.%{SOABI_optimized}.so
%{dynload_dir}/_sha256.%{SOABI_optimized}.so
%{dynload_dir}/_sha3.%{SOABI_optimized}.so
%{dynload_dir}/_sha512.%{SOABI_optimized}.so

%{dynload_dir}/_asyncio.%{SOABI_optimized}.so
%{dynload_dir}/_bisect.%{SOABI_optimized}.so
%{dynload_dir}/_bz2.%{SOABI_optimized}.so
%{dynload_dir}/_codecs_cn.%{SOABI_optimized}.so
%{dynload_dir}/_codecs_hk.%{SOABI_optimized}.so
%{dynload_dir}/_codecs_iso2022.%{SOABI_optimized}.so
%{dynload_dir}/_codecs_jp.%{SOABI_optimized}.so
%{dynload_dir}/_codecs_kr.%{SOABI_optimized}.so
%{dynload_dir}/_codecs_tw.%{SOABI_optimized}.so
%{dynload_dir}/_contextvars.%{SOABI_optimized}.so
%{dynload_dir}/_crypt.%{SOABI_optimized}.so
%{dynload_dir}/_csv.%{SOABI_optimized}.so
%{dynload_dir}/_ctypes.%{SOABI_optimized}.so
%{dynload_dir}/_curses.%{SOABI_optimized}.so
%{dynload_dir}/_curses_panel.%{SOABI_optimized}.so
%{dynload_dir}/_dbm.%{SOABI_optimized}.so
%{dynload_dir}/_decimal.%{SOABI_optimized}.so
%{dynload_dir}/_elementtree.%{SOABI_optimized}.so
%if %{with gdbm}
%{dynload_dir}/_gdbm.%{SOABI_optimized}.so
%endif
%{dynload_dir}/_hashlib.%{SOABI_optimized}.so
%{dynload_dir}/_heapq.%{SOABI_optimized}.so
%{dynload_dir}/_json.%{SOABI_optimized}.so
%{dynload_dir}/_lsprof.%{SOABI_optimized}.so
%{dynload_dir}/_lzma.%{SOABI_optimized}.so
%{dynload_dir}/_multibytecodec.%{SOABI_optimized}.so
%{dynload_dir}/_multiprocessing.%{SOABI_optimized}.so
%{dynload_dir}/_opcode.%{SOABI_optimized}.so
%{dynload_dir}/_pickle.%{SOABI_optimized}.so
%{dynload_dir}/_posixsubprocess.%{SOABI_optimized}.so
%{dynload_dir}/_queue.%{SOABI_optimized}.so
%{dynload_dir}/_random.%{SOABI_optimized}.so
%{dynload_dir}/_socket.%{SOABI_optimized}.so
%{dynload_dir}/_sqlite3.%{SOABI_optimized}.so
%{dynload_dir}/_ssl.%{SOABI_optimized}.so
%{dynload_dir}/_statistics.%{SOABI_optimized}.so
%{dynload_dir}/_struct.%{SOABI_optimized}.so
%{dynload_dir}/array.%{SOABI_optimized}.so
%{dynload_dir}/audioop.%{SOABI_optimized}.so
%{dynload_dir}/binascii.%{SOABI_optimized}.so
%{dynload_dir}/cmath.%{SOABI_optimized}.so
%{dynload_dir}/_datetime.%{SOABI_optimized}.so
%{dynload_dir}/fcntl.%{SOABI_optimized}.so
%{dynload_dir}/grp.%{SOABI_optimized}.so
%{dynload_dir}/math.%{SOABI_optimized}.so
%{dynload_dir}/mmap.%{SOABI_optimized}.so
%{dynload_dir}/nis.%{SOABI_optimized}.so
%{dynload_dir}/ossaudiodev.%{SOABI_optimized}.so
%{dynload_dir}/parser.%{SOABI_optimized}.so
%{dynload_dir}/_posixshmem.%{SOABI_optimized}.so
%{dynload_dir}/pyexpat.%{SOABI_optimized}.so
%{dynload_dir}/readline.%{SOABI_optimized}.so
%{dynload_dir}/resource.%{SOABI_optimized}.so
%{dynload_dir}/select.%{SOABI_optimized}.so
%{dynload_dir}/spwd.%{SOABI_optimized}.so
%{dynload_dir}/syslog.%{SOABI_optimized}.so
%{dynload_dir}/termios.%{SOABI_optimized}.so
%{dynload_dir}/unicodedata.%{SOABI_optimized}.so
%{dynload_dir}/_uuid.%{SOABI_optimized}.so
%{dynload_dir}/xxlimited.%{SOABI_optimized}.so
%{dynload_dir}/_xxsubinterpreters.%{SOABI_optimized}.so
%{dynload_dir}/zlib.%{SOABI_optimized}.so

%dir %{pylibdir}/site-packages/
%dir %{pylibdir}/site-packages/__pycache__/
%{pylibdir}/site-packages/README.txt
%{pylibdir}/*.py
%dir %{pylibdir}/__pycache__/
%{pylibdir}/__pycache__/*%{bytecode_suffixes}

%dir %{pylibdir}/collections/
%dir %{pylibdir}/collections/__pycache__/
%{pylibdir}/collections/*.py
%{pylibdir}/collections/__pycache__/*%{bytecode_suffixes}

%dir %{pylibdir}/ctypes/
%dir %{pylibdir}/ctypes/__pycache__/
%{pylibdir}/ctypes/*.py
%{pylibdir}/ctypes/__pycache__/*%{bytecode_suffixes}
%{pylibdir}/ctypes/macholib

%{pylibdir}/curses

%dir %{pylibdir}/dbm/
%dir %{pylibdir}/dbm/__pycache__/
%{pylibdir}/dbm/*.py
%{pylibdir}/dbm/__pycache__/*%{bytecode_suffixes}

%dir %{pylibdir}/distutils/
%dir %{pylibdir}/distutils/__pycache__/
%{pylibdir}/distutils/*.py
%{pylibdir}/distutils/__pycache__/*%{bytecode_suffixes}
%{pylibdir}/distutils/README
%{pylibdir}/distutils/command

%dir %{pylibdir}/email/
%dir %{pylibdir}/email/__pycache__/
%{pylibdir}/email/*.py
%{pylibdir}/email/__pycache__/*%{bytecode_suffixes}
%{pylibdir}/email/mime
%doc %{pylibdir}/email/architecture.rst

%{pylibdir}/encodings

%{pylibdir}/html
%{pylibdir}/http

%dir %{pylibdir}/importlib/
%dir %{pylibdir}/importlib/__pycache__/
%{pylibdir}/importlib/*.py
%{pylibdir}/importlib/__pycache__/*%{bytecode_suffixes}

%dir %{pylibdir}/json/
%dir %{pylibdir}/json/__pycache__/
%{pylibdir}/json/*.py
%{pylibdir}/json/__pycache__/*%{bytecode_suffixes}

%{pylibdir}/logging
%{pylibdir}/multiprocessing

%dir %{pylibdir}/sqlite3/
%dir %{pylibdir}/sqlite3/__pycache__/
%{pylibdir}/sqlite3/*.py
%{pylibdir}/sqlite3/__pycache__/*%{bytecode_suffixes}

%if %{without flatpackage}
%exclude %{pylibdir}/turtle.py
%exclude %{pylibdir}/__pycache__/turtle*%{bytecode_suffixes}
%endif

%{pylibdir}/urllib
%{pylibdir}/xml

%if "%{_lib}" == "lib64"
%attr(0755,root,root) %dir %{_prefix}/lib/python%{pybasever}
%attr(0755,root,root) %dir %{_prefix}/lib/python%{pybasever}/site-packages
%attr(0755,root,root) %dir %{_prefix}/lib/python%{pybasever}/site-packages/__pycache__/
%endif

# "Makefile" and the config-32/64.h file are needed by
# distutils/sysconfig.py:_init_posix(), so we include them in the core
# package, along with their parent directories (bug 531901):
%dir %{pylibdir}/config-%{LDVERSION_optimized}-%{_arch}-linux%{_gnu}/
%{pylibdir}/config-%{LDVERSION_optimized}-%{_arch}-linux%{_gnu}/Makefile
%dir %{_includedir}/python%{LDVERSION_optimized}/
%{_includedir}/python%{LDVERSION_optimized}/%{_pyconfig_h}

%{_libdir}/%{py_INSTSONAME_optimized}
%if %{with main_python}
%{_libdir}/libpython3.so
%endif


%if %{without flatpackage}
%files devel
%endif

%if %{with main_python}
%{_bindir}/2to3
%endif

%{pylibdir}/config-%{LDVERSION_optimized}-%{_arch}-linux%{_gnu}/*
%if %{without flatpackage}
%exclude %{pylibdir}/config-%{LDVERSION_optimized}-%{_arch}-linux%{_gnu}/Makefile
%exclude %{_includedir}/python%{LDVERSION_optimized}/%{_pyconfig_h}
%endif
%{_includedir}/python%{LDVERSION_optimized}/*.h
%{_includedir}/python%{LDVERSION_optimized}/internal/
%{_includedir}/python%{LDVERSION_optimized}/cpython/
%doc Misc/README.valgrind Misc/valgrind-python.supp Misc/gdbinit

%if %{with main_python}
%{_bindir}/python3-config
%{_bindir}/python-config
%{_libdir}/pkgconfig/python3.pc
%{_libdir}/pkgconfig/python.pc
%{_libdir}/pkgconfig/python3-embed.pc
%{_bindir}/pathfix.py
%{_bindir}/pygettext3.py
%{_bindir}/pygettext.py
%{_bindir}/msgfmt3.py
%{_bindir}/msgfmt.py
%endif

%{_bindir}/pygettext%{pybasever}.py
%{_bindir}/msgfmt%{pybasever}.py

%{_bindir}/python%{pybasever}-config
%{_bindir}/python%{LDVERSION_optimized}-config
%{_bindir}/python%{LDVERSION_optimized}-*-config
%{_libdir}/libpython%{LDVERSION_optimized}.so
%{_libdir}/pkgconfig/python-%{LDVERSION_optimized}.pc
%{_libdir}/pkgconfig/python-%{LDVERSION_optimized}-embed.pc
%{_libdir}/pkgconfig/python-%{pybasever}.pc
%{_libdir}/pkgconfig/python-%{pybasever}-embed.pc


%if %{without flatpackage}
%files idle
%endif

%if %{with main_python}
%{_bindir}/idle*
%else
%{_bindir}/idle%{pybasever}
%endif

%{pylibdir}/idlelib

%if %{with main_python}
%{_metainfodir}/idle3.appdata.xml
%{_datadir}/applications/idle3.desktop
%{_datadir}/icons/hicolor/*/apps/idle3.*
%endif

%if %{without flatpackage}
%files tkinter
%endif

%{pylibdir}/tkinter
%if %{without flatpackage}
%exclude %{pylibdir}/tkinter/test
%endif
%{dynload_dir}/_tkinter.%{SOABI_optimized}.so
%{pylibdir}/turtle.py
%{pylibdir}/__pycache__/turtle*%{bytecode_suffixes}
%dir %{pylibdir}/turtledemo
%{pylibdir}/turtledemo/*.py
%{pylibdir}/turtledemo/*.cfg
%dir %{pylibdir}/turtledemo/__pycache__/
%{pylibdir}/turtledemo/__pycache__/*%{bytecode_suffixes}


%if %{without flatpackage}
%files test
%endif

%{pylibdir}/ctypes/test
%{pylibdir}/distutils/tests
%{pylibdir}/sqlite3/test
%{pylibdir}/test
%{dynload_dir}/_ctypes_test.%{SOABI_optimized}.so
%{dynload_dir}/_testbuffer.%{SOABI_optimized}.so
%{dynload_dir}/_testcapi.%{SOABI_optimized}.so
%{dynload_dir}/_testimportmultiple.%{SOABI_optimized}.so
%{dynload_dir}/_testinternalcapi.%{SOABI_optimized}.so
%{dynload_dir}/_testmultiphase.%{SOABI_optimized}.so
%{dynload_dir}/_xxtestfuzz.%{SOABI_optimized}.so
%{pylibdir}/lib2to3/tests
%{pylibdir}/tkinter/test
%{pylibdir}/unittest/test

# We don't bother splitting the debug build out into further subpackages:
# if you need it, you're probably a developer.

# Hence the manifest is the combination of analogous files in the manifests of
# all of the other subpackages

%if %{with debug_build}
%if %{without flatpackage}
%files debug
%endif

%if %{with main_python}
%{_bindir}/python3-debug
%{_bindir}/python-debug
%endif

# Analog of the core subpackage's files:
%{_bindir}/python%{LDVERSION_debug}

# Analog of the -libs subpackage's files:
# ...with debug builds of the built-in "extension" modules:

%{dynload_dir}/_blake2.%{SOABI_debug}.so
%{dynload_dir}/_md5.%{SOABI_debug}.so
%{dynload_dir}/_sha1.%{SOABI_debug}.so
%{dynload_dir}/_sha256.%{SOABI_debug}.so
%{dynload_dir}/_sha3.%{SOABI_debug}.so
%{dynload_dir}/_sha512.%{SOABI_debug}.so

%{dynload_dir}/_asyncio.%{SOABI_debug}.so
%{dynload_dir}/_bisect.%{SOABI_debug}.so
%{dynload_dir}/_bz2.%{SOABI_debug}.so
%{dynload_dir}/_codecs_cn.%{SOABI_debug}.so
%{dynload_dir}/_codecs_hk.%{SOABI_debug}.so
%{dynload_dir}/_codecs_iso2022.%{SOABI_debug}.so
%{dynload_dir}/_codecs_jp.%{SOABI_debug}.so
%{dynload_dir}/_codecs_kr.%{SOABI_debug}.so
%{dynload_dir}/_codecs_tw.%{SOABI_debug}.so
%{dynload_dir}/_contextvars.%{SOABI_debug}.so
%{dynload_dir}/_crypt.%{SOABI_debug}.so
%{dynload_dir}/_csv.%{SOABI_debug}.so
%{dynload_dir}/_ctypes.%{SOABI_debug}.so
%{dynload_dir}/_curses.%{SOABI_debug}.so
%{dynload_dir}/_curses_panel.%{SOABI_debug}.so
%{dynload_dir}/_dbm.%{SOABI_debug}.so
%{dynload_dir}/_decimal.%{SOABI_debug}.so
%{dynload_dir}/_elementtree.%{SOABI_debug}.so
%if %{with gdbm}
%{dynload_dir}/_gdbm.%{SOABI_debug}.so
%endif
%{dynload_dir}/_hashlib.%{SOABI_debug}.so
%{dynload_dir}/_heapq.%{SOABI_debug}.so
%{dynload_dir}/_json.%{SOABI_debug}.so
%{dynload_dir}/_lsprof.%{SOABI_debug}.so
%{dynload_dir}/_lzma.%{SOABI_debug}.so
%{dynload_dir}/_multibytecodec.%{SOABI_debug}.so
%{dynload_dir}/_multiprocessing.%{SOABI_debug}.so
%{dynload_dir}/_opcode.%{SOABI_debug}.so
%{dynload_dir}/_pickle.%{SOABI_debug}.so
%{dynload_dir}/_posixsubprocess.%{SOABI_debug}.so
%{dynload_dir}/_queue.%{SOABI_debug}.so
%{dynload_dir}/_random.%{SOABI_debug}.so
%{dynload_dir}/_socket.%{SOABI_debug}.so
%{dynload_dir}/_sqlite3.%{SOABI_debug}.so
%{dynload_dir}/_ssl.%{SOABI_debug}.so
%{dynload_dir}/_statistics.%{SOABI_debug}.so
%{dynload_dir}/_struct.%{SOABI_debug}.so
%{dynload_dir}/array.%{SOABI_debug}.so
%{dynload_dir}/audioop.%{SOABI_debug}.so
%{dynload_dir}/binascii.%{SOABI_debug}.so
%{dynload_dir}/cmath.%{SOABI_debug}.so
%{dynload_dir}/_datetime.%{SOABI_debug}.so
%{dynload_dir}/fcntl.%{SOABI_debug}.so
%{dynload_dir}/grp.%{SOABI_debug}.so
%{dynload_dir}/math.%{SOABI_debug}.so
%{dynload_dir}/mmap.%{SOABI_debug}.so
%{dynload_dir}/nis.%{SOABI_debug}.so
%{dynload_dir}/ossaudiodev.%{SOABI_debug}.so
%{dynload_dir}/parser.%{SOABI_debug}.so
%{dynload_dir}/_posixshmem.%{SOABI_debug}.so
%{dynload_dir}/pyexpat.%{SOABI_debug}.so
%{dynload_dir}/readline.%{SOABI_debug}.so
%{dynload_dir}/resource.%{SOABI_debug}.so
%{dynload_dir}/select.%{SOABI_debug}.so
%{dynload_dir}/spwd.%{SOABI_debug}.so
%{dynload_dir}/syslog.%{SOABI_debug}.so
%{dynload_dir}/termios.%{SOABI_debug}.so
%{dynload_dir}/unicodedata.%{SOABI_debug}.so
%{dynload_dir}/_uuid.%{SOABI_debug}.so
%{dynload_dir}/_xxsubinterpreters.%{SOABI_debug}.so
%{dynload_dir}/_xxtestfuzz.%{SOABI_debug}.so
%{dynload_dir}/zlib.%{SOABI_debug}.so

# No need to split things out the "Makefile" and the config-32/64.h file as we
# do for the regular build above (bug 531901), since they're all in one package
# now; they're listed below, under "-devel":

%{_libdir}/%{py_INSTSONAME_debug}

# Analog of the -devel subpackage's files:
%{pylibdir}/config-%{LDVERSION_debug}-%{_arch}-linux%{_gnu}
%{_includedir}/python%{LDVERSION_debug}
%{_bindir}/python%{LDVERSION_debug}-config
%{_bindir}/python%{LDVERSION_debug}-*-config
%{_libdir}/libpython%{LDVERSION_debug}.so
%{_libdir}/libpython%{LDVERSION_debug}.so.%{py_SOVERSION}
%{_libdir}/pkgconfig/python-%{LDVERSION_debug}.pc
%{_libdir}/pkgconfig/python-%{LDVERSION_debug}-embed.pc

# Analog of the -tools subpackage's files:
#  None for now; we could build precanned versions that have the appropriate
# shebang if needed

# Analog  of the tkinter subpackage's files:
%{dynload_dir}/_tkinter.%{SOABI_debug}.so

# Analog  of the -test subpackage's files:
%{dynload_dir}/_ctypes_test.%{SOABI_debug}.so
%{dynload_dir}/_testbuffer.%{SOABI_debug}.so
%{dynload_dir}/_testcapi.%{SOABI_debug}.so
%{dynload_dir}/_testimportmultiple.%{SOABI_debug}.so
%{dynload_dir}/_testinternalcapi.%{SOABI_debug}.so
%{dynload_dir}/_testmultiphase.%{SOABI_debug}.so

%endif # with debug_build

# We put the debug-gdb.py file inside /usr/lib/debug to avoid noise from ldconfig
# See https://bugzilla.redhat.com/show_bug.cgi?id=562980
#
# The /usr/lib/rpm/redhat/macros defines %%__debug_package to use
# debugfiles.list, and it appears that everything below /usr/lib/debug and
# (/usr/src/debug) gets added to this file (via LISTFILES) in
# /usr/lib/rpm/find-debuginfo.sh
#
# Hence by installing it below /usr/lib/debug we ensure it is added to the
# -debuginfo subpackage
# (if it doesn't, then the rpmbuild ought to fail since the debug-gdb.py
# payload file would be unpackaged)

# Workaround for https://bugzilla.redhat.com/show_bug.cgi?id=1476593
%undefine _debuginfo_subpackages

# ======================================================
# Finally, the changelog:
# ======================================================

%changelog
* Tue Mar 24 2020 Miro Hrončok <mhroncok@redhat.com> - 3.9.0~a5-1
- Update to Python 3.9.0a5

* Thu Feb 27 2020 Marcel Plch <mplch@redhat.com> - 3.9.0~a4-1
- Update to Python 3.9.0a4

* Tue Feb 11 2020 Miro Hrončok <mhroncok@redhat.com> - 3.9.0~a3-2
- Update the ensurepip module to work with setuptools >= 45

* Mon Jan 27 2020 Victor Stinner <vstinner@python.org> - 3.9.0~a3-1
- Update to Python 3.9.0a3

* Thu Dec 19 2019 Miro Hrončok <mhroncok@redhat.com> - 3.9.0~a2-1
- Rebased to Python 3.9.0a2

* Wed Dec 04 2019 Miro Hrončok <mhroncok@redhat.com> - 3.9.0~a1-3
- Build Python with -fno-semantic-interposition for better performance
- https://fedoraproject.org/wiki/Changes/PythonNoSemanticInterpositionSpeedup

* Thu Nov 28 2019 Miro Hrončok <mhroncok@redhat.com> - 3.9.0~a1-2
- Don't remove the test.test_tools module

* Wed Nov 20 2019 Miro Hrončok <mhroncok@redhat.com> - 3.9.0~a1-1
- Rebased to Python 3.9.0a1

* Mon Oct 14 2019 Miro Hrončok <mhroncok@redhat.com> - 3.8.0-1
- Update to Python 3.8.0 final

* Tue Oct 01 2019 Miro Hrončok <mhroncok@redhat.com> - 3.8.0~rc1-1
- Rebased to Python 3.8.0rc1

* Sat Aug 31 2019 Miro Hrončok <mhroncok@redhat.com> - 3.8.0~b4-1
- Rebased to Python 3.8.0b4
- Enable Profile-guided optimization for all arches, not just x86 (#1741015)

* Mon Jul 29 2019 Miro Hrončok <mhroncok@redhat.com> - 3.8.0~b3-1
- Update to 3.8.0b3

* Fri Jul 26 2019 Fedora Release Engineering <releng@fedoraproject.org> - 3.8.0~b2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Fri Jul 05 2019 Miro Hrončok <mhroncok@redhat.com> - 3.8.0~b2-1
- Update to 3.8.0b2

* Wed Jun 05 2019 Miro Hrončok <mhroncok@redhat.com> - 3.8.0~b1-1
- Update to 3.8.0b1

* Fri May 17 2019 Miro Hrončok <mhroncok@redhat.com> - 3.8.0~a4-2
- Remove a faulty patch that resulted in invalid value of
  distutils.sysconfig.get_config_var('LIBPL') (#1710767)

* Tue May 07 2019 Miro Hrončok <mhroncok@redhat.com> - 3.8.0~a4-1
- Update to 3.8.0a4

* Tue Mar 26 2019 Miro Hrončok <mhroncok@redhat.com> - 3.8.0~a3-1
- Update to 3.8.0a3

* Mon Feb 25 2019 Miro Hrončok <mhroncok@redhat.com> - 3.8.0~a2-1
- Update to 3.8.0a2

* Mon Feb 18 2019 Miro Hrončok <mhroncok@redhat.com> - 3.8.0~a1-3
- Reduced default build flags used to build extension modules
  https://fedoraproject.org/wiki/Changes/Python_Extension_Flags

* Sun Feb 17 2019 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 3.8.0~a1-2
- Rebuild for readline 8.0

* Tue Feb 05 2019 Miro Hrončok <mhroncok@redhat.com> - 3.8.0~a1-1
- Update to 3.8.0a1
