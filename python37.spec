# ==================
# Top-level metadata
# ==================

%global pybasever 3.7

# pybasever without the dot:
%global pyshortver 37

Name: python%{pyshortver}
Summary:  Version %{pybasever} of the Python interpreter
URL: https://www.python.org/


# Second alpha
%global prerel a4

#  WARNING  When rebasing to a new Python version,
#           remember to update the python3-docs package as well
Version: %{pybasever}.0
Release: 0.3.%{?prerel}%{?dist}
License: Python


# ==================================
# Conditionals controlling the build
# ==================================

# Note that the bcond macros are named for the CLI option they create.
# "%%bcond_without" means "ENABLE by default and create a --without option"


# Flat package, i.e. python36, python37, python38 for tox etc.
# warning: changes some other defaults
# in Fedora, never turn this on for the python3 package
# and always keep it on for python37 etc.
# WARNING: This does not change the package name and summary above
%bcond_without flatpackage


# Expensive optimizations (mainly, profile-guided optimizations)
%ifarch %{ix86} x86_64
%bcond_without optimizations
%else
# On some architectures, the optimized build takes tens of hours, possibly
# longer than Koji's 24-hour timeout. Disable optimizations here.
%bcond_with optimizations
%endif

# Run the test suite in %%check
%bcond_without tests

# Ability to reuse RPM-installed pip using rewheel
%if %{with flatpackage}
%bcond_with rewheel
%else
%bcond_without rewheel
%endif

# Extra build for debugging the interpreter or C-API extensions
# (the -debug subpackages)
%if %{with flatpackage}
%bcond_with debug_build
%else
%bcond_without debug_build
%endif

# Support for the GDB debugger
%bcond_without gdb_hooks

# Support for systemtap instrumentation
%bcond_with systemtap

# The dbm.gnu module (key-value database)
%bcond_without gdbm

# Main interpreter loop optimization
%bcond_without computed_gotos

# Support for the Valgrind debugger/profiler
%ifnarch s390 %{mips} riscv64
%bcond_without valgrind
%else
# Some arches don't have valgrind, disable support for it there.
%bcond_with valgrind
%endif


# ==================================
# Notes from bootstraping Python 3.6
# ==================================
#
# New Python major version (3.X) break ABI and bytecode compatibility,
# so all packages depending on it need to be rebuilt.
#
# Due to a dependency cycle between Python, gdb, rpm, pip, setuptools, wheel,
# and other packages, this isn't straightforward.
# Build in the following order:
#
# 1. At the same time:
#     - gdb without python support (add %%global _without_python 1 on top of
#       gdb's SPEC file)
#     - python-rpm-generators with bootstrapping_python set to 1
#       (this can be done also during step 2., but should be done before 3.)
# 2. python3 without rewheel (use %%bcond_with rewheel instead of
#     %%bcond_without)
# 3. At the same time:
#     - gdb with python support (remove %%global _without_python 1 on top of
#       gdb's SPEC file)
#     - python-rpm-generators with bootstrapping_python set to 0
#       (this can be done at any later step without negative effects)
# 4. rpm
# 5. python-setuptools with bootstrap set to 1
# 6. python-pip with build_wheel set to 0
# 7. python-wheel with %%bcond_without bootstrap
# 8. python-setuptools with bootstrap set to 0 and also with_check set to 0
# 9. python-pip with build_wheel set to 1
# 10. pyparsing
# 11. python3 with rewheel
#
# Then the most important packages have to be built, in dependency order.
# These were:
#   python-sphinx, pytest, python-requests, cloud-init, dnf, anaconda, abrt
#
# After these have been built, a targeted rebuild should be done for the rest.


# =====================
# General global macros
# =====================

%global pylibdir %{_libdir}/python%{pybasever}
%global dynload_dir %{pylibdir}/lib-dynload

# ABIFLAGS, LDVERSION and SOABI are in the upstream configure.ac
# See PEP 3149 for some background: http://www.python.org/dev/peps/pep-3149/
%global ABIFLAGS_optimized m
%global ABIFLAGS_debug     dm

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
#	foo/__pycache__/bar.cpython-%%{pyshortver}.opt-2.pyc
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

# For multilib support, files that are different between 32- and 64-bit arches
# need different filenames. Use "64" or "32" according to the word size.
# Currently, the best way to determine an architecture's word size happens to
# be checking %%{_lib}.
%if "%{_lib}" == "lib64"
%global wordsize 64
%else
%global wordsize 32
%endif


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
BuildRequires: glibc-devel
BuildRequires: gmp-devel
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
BuildRequires: sqlite-devel
BuildRequires: gdb

%if %{with systemtap}
BuildRequires: systemtap-devel
BuildRequires: systemtap-sdt-devel
%global tapsetdir      /usr/share/systemtap/tapset
%endif

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

%if %{with rewheel}
BuildRequires: python3-setuptools
BuildRequires: python3-pip
%endif


# =======================
# Source code and patches
# =======================

Source: https://www.python.org/ftp/python/%{version}/Python-%{version}%{prerel}.tar.xz

# Supply an RPM macro "py_byte_compile" for the python3-devel subpackage
# to enable specfiles to selectively byte-compile individual files and paths
# with different Python runtimes as necessary:
Source3: macros.pybytecompile%{pybasever}

# Systemtap tapset to make it easier to use the systemtap static probes
# (actually a template; LIBRARY_PATH will get fixed up during install)
# Written by dmalcolm; not yet sent upstream
Source5: libpython.stp

# Example systemtap script using the tapset
# Written by wcohen, mjw, dmalcolm; not yet sent upstream
Source6: systemtap-example.stp

# Another example systemtap script that uses the tapset
# Written by dmalcolm; not yet sent upstream
Source7: pyfuntop.stp

# A simple script to check timestamps of bytecode files
# Run in check section with Python that is currently being built
# Written by bkabrda
Source8: check-pyc-and-pyo-timestamps.py

# Backward compatible no-op macro for system-python
# Remove in Fedora 29
Source9: macros.systempython

# Desktop menu entry for idle3
Source10: idle3.desktop

# AppData file for idle3
Source11: idle3.appdata.xml

# 00001 #
# Fixup distutils/unixccompiler.py to remove standard library path from rpath:
# Was Patch0 in ivazquez' python3000 specfile:
Patch1:         00001-rpath.patch

# 00055 #
# Systemtap support: add statically-defined probe points
# Patch sent upstream as http://bugs.python.org/issue14776
# with some subsequent reworking to cope with LANG=C in an rpmbuild
# (where sys.getfilesystemencoding() == 'ascii')
Patch55: 00055-systemtap.patch

# 00102 #
# Change the various install paths to use /usr/lib64/ instead or /usr/lib
# Only used when "%{_lib}" == "lib64"
# Not yet sent upstream.
Patch102: 00102-lib64.patch

# 00111 #
# Patch the Makefile.pre.in so that the generated Makefile doesn't try to build
# a libpythonMAJOR.MINOR.a
# See https://bugzilla.redhat.com/show_bug.cgi?id=556092
# Downstream only: not appropriate for upstream
Patch111: 00111-no-static-lib.patch

# 00132 #
# Add non-standard hooks to unittest for use in the "check" phase below, when
# running selftests within the build:
#   @unittest._skipInRpmBuild(reason)
# for tests that hang or fail intermittently within the build environment, and:
#   @unittest._expectedFailureInRpmBuild
# for tests that always fail within the build environment
#
# The hooks only take effect if WITHIN_PYTHON_RPM_BUILD is set in the
# environment, which we set manually in the appropriate portion of the "check"
# phase below (and which potentially other python-* rpms could set, to reuse
# these unittest hooks in their own "check" phases)
Patch132: 00132-add-rpmbuild-hooks-to-unittest.patch

# 00155 #
# Avoid allocating thunks in ctypes unless absolutely necessary, to avoid
# generating SELinux denials on "import ctypes" and "import uuid" when
# embedding Python within httpd
# See https://bugzilla.redhat.com/show_bug.cgi?id=814391
Patch155: 00155-avoid-ctypes-thunks.patch

# 00160 #
# Python 3.3 added os.SEEK_DATA and os.SEEK_HOLE, which may be present in the
# header files in the build chroot, but may not be supported in the running
# kernel, hence we disable this test in an rpm build.
# Adding these was upstream issue http://bugs.python.org/issue10142
# Not yet sent upstream
Patch160: 00160-disable-test_fs_holes-in-rpm-build.patch

# 00163 #
# Some tests within test_socket fail intermittently when run inside Koji;
# disable them using unittest._skipInRpmBuild
# Not yet sent upstream
Patch163: 00163-disable-parts-of-test_socket-in-rpm-build.patch

# 00170 #
# In debug builds, try to print repr() when a C-level assert fails in the
# garbage collector (typically indicating a reference-counting error
# somewhere else e.g in an extension module)
# The new macros/functions within gcmodule.c are hidden to avoid exposing
# them within the extension API.
# Sent upstream: http://bugs.python.org/issue9263
# See https://bugzilla.redhat.com/show_bug.cgi?id=614680
Patch170: 00170-gc-assertions.patch

# 00178 #
# Don't duplicate various FLAGS in sysconfig values
# http://bugs.python.org/issue17679
# Does not affect python2 AFAICS (different sysconfig values initialization)
Patch178: 00178-dont-duplicate-flags-in-sysconfig.patch

# 00189 #
# Add the rewheel module, allowing to recreate wheels from already installed
# ones
# https://github.com/bkabrda/rewheel
Patch189: 00189-add-rewheel-module.patch

# 00205 #
# LIBPL variable in makefile takes LIBPL from configure.ac
# but the LIBPL variable defined there doesn't respect libdir macro
Patch205: 00205-make-libpl-respect-lib64.patch

# 00251
# Set values of prefix and exec_prefix in distutils install command
# to /usr/local if executable is /usr/bin/python* and RPM build
# is not detected to make pip and distutils install into separate location
# Fedora Change: https://fedoraproject.org/wiki/Changes/Making_sudo_pip_safe
Patch251: 00251-change-user-install-location.patch

# 00264 #
# test_pass_by_value was added in Python 3.6.1 and on aarch64
# it is catching an error that was there, but wasn't tested before.
# Therefore skipping the test on aarch64 until fixed upstream.
# Reported upstream: http://bugs.python.org/issue29804
Patch264: 00264-skip-test-failing-on-aarch64.patch

# 00273 #
# Skip test_float_with_comma, which fails in Koji with UnicodeDecodeError
# See https://bugzilla.redhat.com/show_bug.cgi?id=1484497
Patch273: 00273-skip-float-test.patch

# 00274 #
# Upstream uses Debian-style architecture naming. Change to match Fedora.
Patch274: 00274-fix-arch-names.patch

# 00289 #
# Fix the compilation of the nis module, as glibc removed the
# interfaces related to Sun RPC and they are now provided
# by libtirpc and libnsl2.
# See: https://fedoraproject.org/wiki/Changes/SunRPCRemoval
# and https://fedoraproject.org/wiki/Changes/NISIPv6
# Fixed upstream: https://bugs.python.org/issue32521
Patch289: 00289-fix-nis-compilation.patch

# (New patches go here ^^^)
#
# When adding new patches to "python" and "python3" in Fedora, EL, etc.,
# please try to keep the patch numbers in-sync between all specfiles.
#
# More information, and a patch number catalog, is at:
#
#     https://fedoraproject.org/wiki/SIGs/Python/PythonPatches


# ==========================================
# Descriptions, and metadata for subpackages
# ==========================================

%if %{without flatpackage}

# Packages with Python modules in standard locations automatically
# depend on python(abi). Provide that here.
Provides: python(abi) = %{pybasever}

# For backward compatibility only, remove in F29:
Provides: system-python(abi) = %{pybasever}
Provides: system-python = %{version}-%{release}
Provides: system-python%{?_isa} = %{version}-%{release}
Obsoletes: system-python < %{version}-%{release}

Requires: %{name}-libs%{?_isa} = %{version}-%{release}

# In order to support multiple Python interpreters for development purposes,
# packages with with the naming scheme flatpackage (e.g. python35) exist for
# non-default versions of Python 3.
# For consistency, and to keep the upgrade path clean, we Provide/Obsolete
# these names here.
Provides: python%{pyshortver} = %{version}-%{release}
# Note that using Obsoletes without package version is not standard practice.
# Here we assert that *any* version of the system's default interpreter is
# preferable to an "extra" interpreter. For example, python3-3.6.1 will
# replace python36-3.6.2.
Obsoletes: python%{pyshortver}

# Shall be removed in Fedora 31
# The release is bumped to 20, so we can do f27 platform-python updates
# If the release in f27 ever goes >= 20, raise it here
# If platform-python is ever reintroduced, make it higher version than this:
%global platpyver 3.6.2-20
Obsoletes: platform-python < %{platpyver}

%if %{with rewheel}
Requires: python3-setuptools
Requires: python3-pip
%endif

# The description used both for the SRPM and the main `python3` subpackage:
%description
Python is an accessible, high-level, dynamically typed, interpreted programming
language, designed with an emphasis on code readibility.
It includes an extensive standard library, and has a vast ecosystem of
third-party libraries.

The ${name} package provides the "python3" executable: the reference
interpreter for the Python language, version 3.
The majority of its standard library is provided in the %{name}-libs package,
which should be installed automatically along with %{name}.
The remaining parts of the Python standard library are broken out into the
%{name}-tkinter and %{name}-test packages, which may need to be installed
separately.

Documentation for Python is provided in the %{name}-docs package.

Packages containing additional libraries for Python are generally named with
the "%{name}-" prefix.


%package libs
Summary:        Python runtime libraries

# The "enum" module is included in the standard library.
# Provide an upgrade path from the external library.
Provides: python3-enum34 = 1.0.4-5%{?dist}
Obsoletes: python3-enum34 < 1.0.4-5%{?dist}

# Python 3 built with glibc >= 2.24.90-26 needs to require it
# See https://bugzilla.redhat.com/show_bug.cgi?id=1410644
Requires: glibc%{?_isa} >= 2.24.90-26

# For backward compatibility only, remove in F29:
Provides: system-python-libs = %{version}-%{release}
Provides: system-python-libs%{?_isa} = %{version}-%{release}
Obsoletes: system-python-libs < %{version}-%{release}

# Shall be removed in Fedora 31
Obsoletes: platform-python-libs < %{platpyver}
Obsoletes: platform-python-libs-devel < %{platpyver}

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
Requires: python-rpm-macros
Requires: python3-rpm-macros
Requires: python3-rpm-generators

# https://bugzilla.redhat.com/show_bug.cgi?id=1217376
# https://bugzilla.redhat.com/show_bug.cgi?id=1496757
# https://bugzilla.redhat.com/show_bug.cgi?id=1218294
# TODO change to a specific subpackage once available (#1218294)
Requires: redhat-rpm-config

Conflicts: %{name} < %{version}-%{release}

# Shall be removed in Fedora 31
Obsoletes: platform-python-devel < %{platpyver}

%description devel
This package contains the header files and configuration needed to compile
Python extension modules (typically written in C or C++), to embed Python
into other programs, and to make binary distributions for Python libraries.

It also contains the necessary macros to build RPM packages with Python modules.


%package tools
Summary: A collection of tools included with Python including 2to3 and idle
Requires: %{name} = %{version}-%{release}
Requires: %{name}-tkinter = %{version}-%{release}

Provides: %{name}-2to3 = %{version}-%{release}
Provides: %{name}-idle = %{version}-%{release}
Provides: 2to3 = %{version}-%{release}
Provides: idle3 = %{version}-%{release}

# https://bugzilla.redhat.com/show_bug.cgi?id=1111275
# /usr/bin/2to3 was moved from here
# TODO Remove in Fedora 29
Conflicts: python2-tools < 2.7.13-17
Conflicts: python-tools < 2.7.13-17

# Shall be removed in Fedora 31
Obsoletes: platform-python-tools < %{platpyver}

%description tools
This package contains several tools included with Python, including:
- 2to3, an automatic source converter from Python 2.X
- idle, a basic graphical development environment


%package tkinter
Summary: A GUI toolkit for Python
Requires: %{name} = %{version}-%{release}

# Shall be removed in Fedora 31
Obsoletes: platform-python-tkinter < %{platpyver}

%description tkinter
The Tkinter (Tk interface) library is a graphical user interface toolkit for
the Python programming language.


%package test
Summary: The self-test suite for the main python3 package
Requires: %{name} = %{version}-%{release}
Requires: %{name}-tools = %{version}-%{release}

# Shall be removed in Fedora 31
Obsoletes: platform-python-test < %{platpyver}

%description test
The self-test suite for the Python interpreter.

This is only useful to test Python itself. For testing general Python code,
you should use the unittest module from %{name}-libs, or a library such as
${name}-pytest or ${name}-nose.


%if %{with debug_build}
%package debug
Summary: Debug version of the Python runtime

# The debug build is an all-in-one package version of the regular build, and
# shares the same .py/.pyc files and directories as the regular build.  Hence
# we depend on all of the subpackages of the regular build:
Requires: %{name}%{?_isa} = %{version}-%{release}
Requires: %{name}-libs%{?_isa} = %{version}-%{release}
Requires: %{name}-devel%{?_isa} = %{version}-%{release}
Requires: %{name}-test%{?_isa} = %{version}-%{release}
Requires: %{name}-tkinter%{?_isa} = %{version}-%{release}
Requires: %{name}-tools%{?_isa} = %{version}-%{release}

%description debug
python3-debug provides a version of the Python runtime with numerous debugging
features enabled, aimed at advanced Python users such as developers of Python
extension modules.

This version uses more memory and will be slower than the regular Python build,
but is useful for tracking down reference-counting issues and other bugs.

The bytecode format is unchanged, so that .pyc files are compatible between
this and the standard version of Python, but the debugging features mean that
C/C++ extension modules are ABI-incompatible and must be built for each version
separately.

The debug build shares installation directories with the standard Python
runtime, so that .py and .pyc files can be shared.
Compiled extension modules use a special ABI flag ("d") in the filename,
so extensions for both verisons can co-exist in the same directory.
%endif # with debug_build

%else  # with flatpackage

Requires: redhat-rpm-config

# We'll not provide this, on purpose
# No package in Fedora shall ever depend on flatpackage via this
%global __requires_exclude ^python\\(abi\\) = 3\\..$
%global __provides_exclude ^python\\(abi\\) = 3\\..$

# We keep those inside on purpose
Provides: bundled(python3-pip) = 9.0.1
Provides: bundled(python3-setuptools) = 28.8.0

# The descripton for the flat flatpackage package
%description
This package exists to allow developers to test their code against an newer
version of Python. This is not a full Python stack and if you wish to run
your applications with Python %{pybasever}, update your Fedora to a newer
version once Python %{pybasever} is stable.

%endif # with flatpackage

# ======================================================
# The prep phase of the build:
# ======================================================

%prep
%setup -q -n Python-%{version}%{?prerel}

%if %{with systemtap}
# Provide an example of usage of the tapset:
cp -a %{SOURCE6} .
cp -a %{SOURCE7} .
%endif # with systemtap

# Remove bundled libraries to ensure that we're using the system copy.
rm -r Modules/expat

%if %{with rewheel}
%global pip_version 9.0.1
sed -r -i s/'_PIP_VERSION = "[0-9.]+"'/'_PIP_VERSION = "%{pip_version}"'/ Lib/ensurepip/__init__.py
%endif

#
# Apply patches:
#
%patch1 -p1

%if %{with systemtap}
%patch55 -p1 -b .systemtap
%endif

%if "%{_lib}" == "lib64"
%patch102 -p1
%endif
%patch111 -p1
%patch132 -p1
%patch155 -p1
%patch160 -p1
%patch163 -p1
%patch170 -p1
%patch178 -p1

%if %{with rewheel}
%patch189 -p1
%endif

%patch205 -p1
%patch251 -p1

%ifarch aarch64
%patch264 -p1
%endif

%patch273 -p1
%patch274 -p1
%patch289 -p1


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
export CFLAGS="$RPM_OPT_FLAGS -D_GNU_SOURCE -fPIC -fwrapv"
export CXXFLAGS="$RPM_OPT_FLAGS -D_GNU_SOURCE -fPIC -fwrapv"
export CPPFLAGS="$(pkg-config --cflags-only-I libffi)"
export OPT="$RPM_OPT_FLAGS -D_GNU_SOURCE -fPIC -fwrapv"
export LINKCC="gcc"
export CFLAGS="$CFLAGS $(pkg-config --cflags openssl)"
export LDFLAGS="$RPM_LD_FLAGS -g $(pkg-config --libs-only-L openssl)"

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

%configure \
  --enable-ipv6 \
  --enable-shared \
  --with-computed-gotos=%{computed_gotos_flag} \
  --with-dbmliborder=gdbm:ndbm:bdb \
  --with-system-expat \
  --with-system-ffi \
  --enable-loadable-sqlite-extensions \
  --with-dtrace \
  --with-lto \
%if %{with systemtap}
  --with-systemtap \
%endif
%if %{with valgrind}
  --with-valgrind \
%endif
  $ExtraConfigArgs \
  %{nil}

  # Invoke the build
  make EXTRA_CFLAGS="$CFLAGS $MoreCFlags" %{?_smp_mflags}

  popd
  echo FINISHED: BUILD OF PYTHON FOR CONFIGURATION: $ConfName
}

# Call the above to build each configuration.

%if %{with debug_build}
BuildPython debug \
  "--without-ensurepip --with-pydebug" \
  "-O0"
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
DirHoldingGdbPy=%{_prefix}/lib/debug/%{_libdir}
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
%global _pyconfig_h pyconfig-%{wordsize}.h

# Use a common function to do an install for all our configurations:
InstallPython() {

  ConfName=$1
  PyInstSoName=$2
  MoreCFlags=$3
  LDVersion=$4
  Postfix=$5

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

  # Systemtap hooks
%if %{with systemtap}
  mkdir -p %{buildroot}%{tapsetdir}
  sed \
     -e "s|LIBRARY_PATH|%{_libdir}/${PyInstSoName}|" \
     -e 's|"python3"|"python3${Postfix}"|' \
     %{_sourcedir}/libpython.stp \
     > %{buildroot}%{tapsetdir}/libpython%{pybasever}${Postfix}-%{wordsize}.stp
%endif # with systemtap

  echo FINISHED: INSTALL OF PYTHON FOR CONFIGURATION: $ConfName
}

# Install the "debug" build first; any common files will be overridden with
# later builds
%if %{with debug_build}
InstallPython debug \
  %{py_INSTSONAME_debug} \
  -O0 \
  %{LDVERSION_debug} \
  -debug
%endif # with debug_build

# Now the optimized build:
InstallPython optimized \
  %{py_INSTSONAME_optimized} \
  "" \
  %{LDVERSION_optimized} \
  ""

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

%if %{without flatpackage}
# add idle3 to menu
install -D -m 0644 Lib/idlelib/Icons/idle_16.png %{buildroot}%{_datadir}/icons/hicolor/16x16/apps/idle3.png
install -D -m 0644 Lib/idlelib/Icons/idle_32.png %{buildroot}%{_datadir}/icons/hicolor/32x32/apps/idle3.png
install -D -m 0644 Lib/idlelib/Icons/idle_48.png %{buildroot}%{_datadir}/icons/hicolor/48x48/apps/idle3.png
desktop-file-install --dir=%{buildroot}%{_datadir}/applications %{SOURCE10}

# Install and validate appdata file
mkdir -p %{buildroot}%{_datadir}/appdata
cp -a %{SOURCE11} %{buildroot}%{_datadir}/appdata
appstream-util validate-relax --nonet %{buildroot}%{_datadir}/appdata/idle3.appdata.xml
%endif

# Development tools
install -m755 -d %{buildroot}%{pylibdir}/Tools
install Tools/README %{buildroot}%{pylibdir}/Tools/
cp -ar Tools/freeze %{buildroot}%{pylibdir}/Tools/
cp -ar Tools/i18n %{buildroot}%{pylibdir}/Tools/
cp -ar Tools/pynche %{buildroot}%{pylibdir}/Tools/
cp -ar Tools/scripts %{buildroot}%{pylibdir}/Tools/

# Documentation tools
install -m755 -d %{buildroot}%{pylibdir}/Doc
cp -ar Doc/tools %{buildroot}%{pylibdir}/Doc/

# Demo scripts
cp -ar Tools/demo %{buildroot}%{pylibdir}/Tools/

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

# Switch all shebangs to refer to the specific Python version.
# This currently only covers files matching ^[a-zA-Z0-9_]+\.py$,
# so handle files named using other naming scheme separately.
LD_LIBRARY_PATH=./build/optimized ./build/optimized/python \
  Tools/scripts/pathfix.py \
  -i "%{_bindir}/python%{pybasever}" \
  %{buildroot} %{buildroot}%{pylibdir}/Tools/scripts/*-*.py \
  %{buildroot}%{pylibdir}/Tools/pynche/{pynche,pynche.pyw}
# not covered, also redundant and useless:
rm %{buildroot}%{pylibdir}/Tools/scripts/{2to3,idle3,pydoc3,pyvenv}


# Move pathfix.py to bindir
# See https://github.com/fedora-python/python-rpm-porting/issues/24
mv %{buildroot}%{pylibdir}/Tools/scripts/pathfix.py %{buildroot}%{_bindir}/


# Remove shebang lines from .py files that aren't executable, and
# remove executability from .py files that don't have a shebang line:
find %{buildroot} -name \*.py \
  \( \( \! -perm /u+x,g+x,o+x -exec sed -e '/^#!/Q 0' -e 'Q 1' {} \; \
  -print -exec sed -i '1d' {} \; \) -o \( \
  -perm /u+x,g+x,o+x ! -exec grep -m 1 -q '^#!' {} \; \
  -exec chmod a-x {} \; \) \)

# Remove executable flag from files that shouldn't have it:
chmod a-x \
  %{buildroot}%{pylibdir}/Tools/README

# Get rid of DOS batch files:
find %{buildroot} -name \*.bat -exec rm {} \;

# Get rid of backup files:
find %{buildroot}/ -name "*~" -exec rm -f {} \;
find . -name "*~" -exec rm -f {} \;

# Get rid of a stray copy of the license:
rm %{buildroot}%{pylibdir}/LICENSE.txt

# Do bytecompilation with the newly installed interpreter.
# This is similar to the script in macros.pybytecompile
# compile *.pyc
find %{buildroot} -type f -a -name "*.py" -print0 | \
    LD_LIBRARY_PATH="%{buildroot}%{dynload_dir}/:%{buildroot}%{_libdir}" \
    PYTHONPATH="%{buildroot}%{_libdir}/python%{pybasever} %{buildroot}%{_libdir}/python%{pybasever}/site-packages" \
    xargs -0 %{buildroot}%{_bindir}/python%{pybasever} -O -c 'import py_compile, sys; [py_compile.compile(f, dfile=f.partition("%{buildroot}")[2], optimize=opt) for opt in range(3) for f in sys.argv[1:]]' || :

# Since we have pathfix.py in bindir, this is created, but we don't want it
rm -rf %{buildroot}%{_bindir}/__pycache__

# Fixup permissions for shared libraries from non-standard 555 to standard 755:
find %{buildroot} -perm 555 -exec chmod 755 {} \;

# Install macros for rpm:
mkdir -p %{buildroot}/%{_rpmconfigdir}/macros.d/
install -m 644 %{SOURCE3} %{buildroot}/%{_rpmconfigdir}/macros.d/
%if %{without flatpackage}
install -m 644 %{SOURCE9} %{buildroot}/%{_rpmconfigdir}/macros.d/
%endif

# Create "/usr/bin/python3-debug", a symlink to the python3 debug binary, to
# avoid the user having to know the precise version and ABI flags.
# See e.g. https://bugzilla.redhat.com/show_bug.cgi?id=676748
%if %{with debug_build} && %{without flatpackage}
ln -s \
  %{_bindir}/python%{LDVERSION_debug} \
  %{buildroot}%{_bindir}/python3-debug
%endif

# System Python: Link the executable to libexec
# This is for backwards compatibility only and should be removed in Fedora 29
%if %{without flatpackage}
mkdir -p %{buildroot}%{_libexecdir}
ln -s %{_bindir}/python%{pybasever} %{buildroot}%{_libexecdir}/system-python
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

# There's no point of having this, as decided in
# https://bugzilla.redhat.com/show_bug.cgi?id=1111275
rm %{buildroot}%{_bindir}/2to3-%{pybasever}

%if %{with flatpackage}
# Remove stuff that would conflict with python3 package
rm %{buildroot}%{_bindir}/python3
rm %{buildroot}%{_bindir}/pydoc3
rm %{buildroot}%{_bindir}/pathfix.py
rm %{buildroot}%{_bindir}/idle3
rm %{buildroot}%{_bindir}/python3-*
rm %{buildroot}%{_bindir}/pyvenv
rm %{buildroot}%{_bindir}/2to3
rm %{buildroot}%{_libdir}/libpython3.so
rm %{buildroot}%{_mandir}/man1/python3.1*
rm %{buildroot}%{_libdir}/pkgconfig/python3.pc
%endif


# ======================================================
# Running the upstream test suite
# ======================================================

# For ppc64 we need a larger stack than default
# See https://bugzilla.redhat.com/show_bug.cgi?id=1292462
%ifarch %{power64}
  ulimit -a
  ulimit -s 16384
%endif


topdir=$(pwd)
CheckPython() {
  ConfName=$1
  ConfDir=$(pwd)/build/$ConfName

  echo STARTING: CHECKING OF PYTHON FOR CONFIGURATION: $ConfName

  # Note that we're running the tests using the version of the code in the
  # builddir, not in the buildroot.

  # Run the upstream test suite, setting "WITHIN_PYTHON_RPM_BUILD" so that the
  # our non-standard decorators take effect on the relevant tests:
  #   @unittest._skipInRpmBuild(reason)
  #   @unittest._expectedFailureInRpmBuild
  # test_faulthandler.test_register_chain currently fails on ppc64le and
  #   aarch64, see upstream bug http://bugs.python.org/issue21131
  WITHIN_PYTHON_RPM_BUILD= \
  LD_LIBRARY_PATH=$ConfDir $ConfDir/python -m test.regrtest \
    -wW --slowest --findleaks \
    -x test_distutils \
    -x test_bdist_rpm \
    %ifarch ppc64le aarch64
    -x test_faulthandler \
    %endif
    %ifarch %{mips64}
    -x test_ctypes \
    %endif
    %ifarch %{power64} s390 s390x armv7hl aarch64 %{mips}
    -x test_gdb
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


# ======================================================
# Scriptlets
# ======================================================

%if %{without flatpackage}

%post libs -p /sbin/ldconfig

%postun libs -p /sbin/ldconfig

%posttrans
/usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :

%endif


%post
%if %{with flatpackage}
/sbin/ldconfig
%else
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :
%endif

%postun
%if %{with flatpackage}
/sbin/ldconfig
%else
if [ $1 -eq 0 ] ; then
    /bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null
    /usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :
fi
%endif

%files
%defattr(-, root, root)
%license LICENSE
%doc README.rst

%if %{without flatpackage}
%{_bindir}/pydoc*
%{_bindir}/python3
%{_bindir}/pyvenv
# Remove in Fedora 29:
%{_libexecdir}/system-python
%else
%{_bindir}/pydoc%{pybasever}
%endif

%{_bindir}/python%{pybasever}
%{_bindir}/python%{pybasever}m
%{_bindir}/pyvenv-%{pybasever}
%{_mandir}/*/*


%if %{without flatpackage}
%files libs
%defattr(-,root,root,-)
%license LICENSE
%doc README.rst
%endif

%dir %{pylibdir}
%dir %{dynload_dir}

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

%if %{without flatpackage}
%exclude %{pylibdir}/ensurepip/_bundled
%else
%dir %{pylibdir}/ensurepip/_bundled
%{pylibdir}/ensurepip/_bundled/*.whl
%endif

%if %{with rewheel}
%dir %{pylibdir}/ensurepip/rewheel/
%dir %{pylibdir}/ensurepip/rewheel/__pycache__/
%{pylibdir}/ensurepip/rewheel/*.py
%{pylibdir}/ensurepip/rewheel/__pycache__/*%{bytecode_suffixes}
%endif

%{pylibdir}/idlelib

%dir %{pylibdir}/test/
%dir %{pylibdir}/test/__pycache__/
%dir %{pylibdir}/test/support/
%dir %{pylibdir}/test/support/__pycache__/
%{pylibdir}/test/__init__.py
%{pylibdir}/test/__pycache__/__init__%{bytecode_suffixes}
%{pylibdir}/test/support/__init__.py
%{pylibdir}/test/support/__pycache__/__init__%{bytecode_suffixes}

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
%{dynload_dir}/_random.%{SOABI_optimized}.so
%{dynload_dir}/_socket.%{SOABI_optimized}.so
%{dynload_dir}/_sqlite3.%{SOABI_optimized}.so
%{dynload_dir}/_ssl.%{SOABI_optimized}.so
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
%{dynload_dir}/pyexpat.%{SOABI_optimized}.so
%{dynload_dir}/readline.%{SOABI_optimized}.so
%{dynload_dir}/resource.%{SOABI_optimized}.so
%{dynload_dir}/select.%{SOABI_optimized}.so
%{dynload_dir}/spwd.%{SOABI_optimized}.so
%{dynload_dir}/syslog.%{SOABI_optimized}.so
%{dynload_dir}/termios.%{SOABI_optimized}.so
#%{dynload_dir}/time.%{SOABI_optimized}.so
%{dynload_dir}/_testmultiphase.%{SOABI_optimized}.so
%{dynload_dir}/unicodedata.%{SOABI_optimized}.so
%{dynload_dir}/_uuid.%{SOABI_optimized}.so
%{dynload_dir}/xxlimited.%{SOABI_optimized}.so
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
%exclude %{pylibdir}/distutils/command/wininst-*.exe

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
%if %{without flatpackage}
%{_libdir}/libpython3.so
%endif
%if %{with systemtap}
%dir %(dirname %{tapsetdir})
%dir %{tapsetdir}
%{tapsetdir}/%{libpython_stp_optimized}
%doc systemtap-example.stp pyfuntop.stp
%endif


%if %{without flatpackage}
%files devel
%defattr(-,root,root)
%endif

%{pylibdir}/config-%{LDVERSION_optimized}-%{_arch}-linux%{_gnu}/*
%if %{without flatpackage}
%exclude %{pylibdir}/config-%{LDVERSION_optimized}-%{_arch}-linux%{_gnu}/Makefile
%exclude %{_includedir}/python%{LDVERSION_optimized}/%{_pyconfig_h}
%endif
%{pylibdir}/distutils/command/wininst-*.exe
%{_includedir}/python%{LDVERSION_optimized}/*.h
%doc Misc/README.valgrind Misc/valgrind-python.supp Misc/gdbinit

%if %{without flatpackage}
%{_bindir}/python3-config
%{_libdir}/pkgconfig/python3.pc
%{_rpmconfigdir}/macros.d/macros.systempython
%{_bindir}/pathfix.py
%endif

%{_bindir}/python%{pybasever}-config
%{_bindir}/python%{LDVERSION_optimized}-config
%{_bindir}/python%{LDVERSION_optimized}-*-config
%{_libdir}/libpython%{LDVERSION_optimized}.so
%{_libdir}/pkgconfig/python-%{LDVERSION_optimized}.pc
%{_libdir}/pkgconfig/python-%{pybasever}.pc
%{_rpmconfigdir}/macros.d/macros.pybytecompile%{pybasever}


%if %{without flatpackage}
%files tools
%defattr(-,root,root,755)

%{_bindir}/2to3
%{_bindir}/idle*
%else
%{_bindir}/idle%{pybasever}
%endif

%{pylibdir}/Tools
%doc %{pylibdir}/Doc
%if %{without flatpackage}
%{_datadir}/appdata/idle3.appdata.xml
%{_datadir}/applications/idle3.desktop
%{_datadir}/icons/hicolor/*/apps/idle3.*
%endif

%if %{without flatpackage}
%files tkinter
%defattr(-,root,root,755)
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
%defattr(-, root, root)
%endif

%{pylibdir}/ctypes/test
%{pylibdir}/distutils/tests
%{pylibdir}/sqlite3/test
%{pylibdir}/test
%{dynload_dir}/_ctypes_test.%{SOABI_optimized}.so
%{dynload_dir}/_testbuffer.%{SOABI_optimized}.so
%{dynload_dir}/_testcapi.%{SOABI_optimized}.so
%{dynload_dir}/_testimportmultiple.%{SOABI_optimized}.so
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
%defattr(-,root,root,-)
%{_bindir}/python3-debug
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
%{dynload_dir}/_random.%{SOABI_debug}.so
%{dynload_dir}/_socket.%{SOABI_debug}.so
%{dynload_dir}/_sqlite3.%{SOABI_debug}.so
%{dynload_dir}/_ssl.%{SOABI_debug}.so
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
%{dynload_dir}/pyexpat.%{SOABI_debug}.so
%{dynload_dir}/readline.%{SOABI_debug}.so
%{dynload_dir}/resource.%{SOABI_debug}.so
%{dynload_dir}/select.%{SOABI_debug}.so
%{dynload_dir}/spwd.%{SOABI_debug}.so
%{dynload_dir}/syslog.%{SOABI_debug}.so
%{dynload_dir}/termios.%{SOABI_debug}.so
#%{dynload_dir}/time.%{SOABI_debug}.so
%{dynload_dir}/_testmultiphase.%{SOABI_debug}.so
%{dynload_dir}/unicodedata.%{SOABI_debug}.so
%{dynload_dir}/_uuid.%{SOABI_debug}.so
%{dynload_dir}/_xxtestfuzz.%{SOABI_debug}.so
%{dynload_dir}/zlib.%{SOABI_debug}.so

# No need to split things out the "Makefile" and the config-32/64.h file as we
# do for the regular build above (bug 531901), since they're all in one package
# now; they're listed below, under "-devel":

%{_libdir}/%{py_INSTSONAME_debug}
%if %{with systemtap}
%dir %(dirname %{tapsetdir})
%dir %{tapsetdir}
%{tapsetdir}/%{libpython_stp_debug}
%endif

# Analog of the -devel subpackage's files:
%{pylibdir}/config-%{LDVERSION_debug}-%{_arch}-linux%{_gnu}
%{_includedir}/python%{LDVERSION_debug}
%{_bindir}/python%{LDVERSION_debug}-config
%{_bindir}/python%{LDVERSION_debug}-*-config
%{_libdir}/libpython%{LDVERSION_debug}.so
%{_libdir}/libpython%{LDVERSION_debug}.so.1.0
%{_libdir}/pkgconfig/python-%{LDVERSION_debug}.pc

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

%endif # with debug_build

# We put the debug-gdb.py file inside /usr/lib/debug to avoid noise from ldconfig
# See https://bugzilla.redhat.com/show_bug.cgi?id=562980
#
# The /usr/lib/rpm/redhat/macros defines %__debug_package to use
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
* Thu Jan 18 2018 Miro Hrončok <mhroncok@redhat.com> - 3.7.0-0.3.a4
- Remove /usr/bin/python37 (#1526129)

* Tue Jan 09 2018 Miro Hrončok <mhroncok@redhat.com> - 3.7.0-0.2.a4
- Update to 3.7.0 alpha 4
- Fix the compilation of the nis module

* Tue Nov 28 2017 Miro Hrončok <mhroncok@redhat.com> - 3.7.0-0.1.a2
- Update to 3.7.0 alpha 2
- Removed merged patches 262, 277, 279
