%global ver 3.0.10
%global rev 33601

Name:           firebird
Version:        %{ver}.%{rev}
Release:        2
Summary:        SQL relational database management system
License:        Interbase
URL:            http://www.firebirdsql.org/

Source0:        https://github.com/FirebirdSQL/firebird/releases/download/v%{ver}/Firebird-%{ver}.%{rev}-0.tar.bz2
Source1:        firebird-logrotate
Source2:        firebird.conf
Source3:        fb_config

Patch0000:      add-pkgconfig-files.patch
Patch0001:      Provide-sized-global-delete-operators-when-compiled.patch
Patch0002:      obsolete-syslogd.target.patch
Patch0003:      honour-buildflags.patch
Patch0004:      no-copy-from-icu.patch
Patch0005:      cloop-honour-build-flags.patch
Patch0007:      0001-Port-to-RISC-V-64-bit-riscv64.patch

BuildRequires:  autoconf automake libtommath-devel libtool make ncurses-devel libicu-devel
BuildRequires:  libedit-devel gcc-c++ libstdc++-static systemd-units chrpath zlib-devel procmail
BuildRequires:  chrpath gcc_secure

Requires(post): systemd-units
Requires(preun):systemd-units
Requires(postun):systemd-units
Requires:       logrotate

Provides:       firebird-utils = %{version}-%{release} libfbclient2 = %{version}-%{release} libib-util = %{version}-%{release}
Obsoletes:      firebird-utils < %{version}-%{release} libfbclient2 < %{version}-%{release} libib-util < %{version}-%{release}
Obsoletes:      firebird-arch < 3.0 firebird-filesystem < 3.0 firebird-classic-common < 3.0 firebird-classic < 3.0
Obsoletes:      firebird-superclassic < 3.0 firebird-superserver < 3.0 firebird-libfbclient < 3.0 firebird-libfbembed < 3.0
Conflicts:      firebird-arch < 3.0 firebird-filesystem < 3.0 firebird-classic-common < 3.0 firebird-classic < 3.0
Conflicts:      firebird-superclassic < 3.0 firebird-superserver < 3.0 firebird-libfbclient < 3.0

%description
Firebird is an open-source SQL relational database management system that
runs on Linux, Microsoft Windows, macOS and several Unix platforms.
Firebird works excellently under concurrency. It has high performance,
and powerful language support for stored procedures and triggers.
This package also contains utility functions used by User-Defined Functions (UDF)
for memory management etc and shared client library for Firebird SQL server.

%package        devel
Requires:       firebird = %{version}-%{release} pkgconfig
Summary:        UDF support library for Firebird SQL server
Provides:       libfbclient2-devel = %{version}-%{release} firebird-examples = %{version}-%{release}
Obsoletes:      libfbclient2-devel < %{version}-%{release} firebird-examples < %{version}-%{release}

%description    devel
This package is needed for development of client applications and user
defined functions (UDF) for Firebird SQL server. It also contains development
files for Firebird SQL server client library.

%package        help
Summary:        Documentation for Firebird SQL server
BuildArch:      noarch
Provides:       firebird-doc = %{version}-%{release}
Obsoletes:      firebird-doc < %{version}-%{release}

%description    help
Documentation for Firebird SQL server.

%prep
%autosetup -n Firebird-%{ver}.%{rev}-0 -p1

%build
export CFLAGS="%{optflags} -fno-strict-aliasing"
export CXXFLAGS="${CFLAGS} -fno-delete-null-pointer-checks"
NOCONFIGURE=1 ./autogen.sh
%configure --prefix=%{_prefix}  --disable-binreloc --with-system-editline --with-fbbin=%{_bindir} \
    --with-fbsbin=%{_sbindir} --with-fbconf=%{_sysconfdir}/firebird --with-fblib=%{_libdir} \
    --with-fbinclude=%{_includedir}/firebird --with-fbdoc=%{_defaultdocdir}/firebird \
    --with-fbudf=%{_libdir}/firebird/udf --with-fbsample=%{_defaultdocdir}/firebird/sample \
    --with-fbsample-db=%{_localstatedir}/lib/firebird/data/ --with-fbhelp=%{_localstatedir}/lib/firebird/system/ \
    --with-fbintl=%{_libdir}/firebird/intl --with-fbmisc=%{_datadir}/firebird/misc \
    --with-fbsecure-db=%{_localstatedir}/lib/firebird/secdb/ --with-fbmsg=%{_localstatedir}/lib/firebird/system/ \
    --with-fblog=%{_localstatedir}/log/firebird --with-fbglock=%{_var}/run/firebird \
    --with-fbplugins=%{_libdir}/firebird/plugins

%make_build
cd gen
make -f Makefile.install buildRoot
chmod -R u+w buildroot%{_docdir}/firebird


%install
chmod u+rw,a+rx gen/buildroot/usr/include/firebird/firebird/impl
cp -r gen/buildroot/* ${RPM_BUILD_ROOT}/
install -d ${RPM_BUILD_ROOT}%{_libdir}/pkgconfig
cp -v gen/install/misc/*.pc ${RPM_BUILD_ROOT}%{_libdir}/pkgconfig/

cd ${RPM_BUILD_ROOT}
rm -vf .%{_sbindir}/*.sh && mv -v .%{_sbindir}/fb_config .%{_libdir}/
install -pm 0755 %{SOURCE3} %{buildroot}%{_sbindir}/fb_config
rm -vf .%{_includedir}/firebird/perf.h .%{_includedir}/*.h .%{_libdir}/libicu*.so
chmod -R u+w .%{_docdir}/firebird
rm -vf .%{_datadir}/firebird/misc/{firebird.init.*,firebird.xinetd,rc.config.firebird}
mv -v .%{_sysconfdir}/firebird/{README,WhatsNew} .%{_docdir}/firebird/
mv -v .%{_sysconfdir}/firebird/{IDPLicense,IPLicense}.txt .%{_docdir}/firebird/
mv -v .%{_bindir}/gstat{,-fb} && mv -v .%{_bindir}/isql{,-fb}

install -d .%{_localstatedir}/log/firebird .%{_sysconfdir}/logrotate.d
echo 1 > .%{_localstatedir}/log/firebird/firebird.log
sed "s@firebird.log@%{_localstatedir}/log/firebird/firebird.log@g" %{SOURCE1} > .%{_sysconfdir}/logrotate.d/firebird

install -d .%{_tmpfilesdir} && cp %{SOURCE2} .%{_tmpfilesdir}/

install -d .%{_unitdir}
cp .%{_datadir}/firebird/misc/firebird-superserver.service .%{_unitdir}/firebird-superserver.service

# remove rpath info
for ff in $(find %{buildroot}/ -executable -type f -exec file '{}' ';' | grep "\<ELF\>" | awk -F ':' '{print $1}')
do
        if [ ! -u "$ff" ]; then
                if [ -w "$ff" ]; then
                        chrpath -d $ff
                fi
        fi
done

# add rpath path /usr/lib/systemd in ld.so.cond.d
mkdir -p %{buildroot}%{_sysconfdir}/ld.so.conf.d
echo "/usr/lib/systemd" > %{buildroot}%{_sysconfdir}/ld.so.conf.d/%{name}-%{_arch}.conf


%pre

getent group firebird || /usr/sbin/groupadd -r firebird
getent passwd firebird >/dev/null || /usr/sbin/useradd -d / -g firebird -s /sbin/nologin -r firebird


oldLine=$(grep "^gds_db" /etc/services)
if [ -z "$oldLine" ]; then
    echo "gds_db 3050/tcp  # Firebird SQL Database Remote Protocol" >> /etc/services
fi


%post
/sbin/ldconfig
systemd-tmpfiles --create  %{_tmpfilesdir}/firebird.conf
%systemd_post firebird-superserver.service


%postun
/sbin/ldconfig
%systemd_postun_with_restart firebird-superserver.service


%preun
%systemd_preun firebird-superserver.service


%files
%{_docdir}/firebird/IDPLicense.txt
%{_docdir}/firebird/IPLicense.txt
%{_sbindir}/firebird
%{_sbindir}/fbguard
%{_sbindir}/fb_lock_print
%dir %{_sysconfdir}/firebird
%config(noreplace) %{_sysconfdir}/firebird/*.conf
%dir %{_libdir}/firebird
%dir %{_datadir}/firebird
%{_libdir}/firebird/*
%{_datadir}/firebird/misc

%dir %{_localstatedir}/lib/firebird
%dir %attr(0700,firebird,firebird) %{_localstatedir}/lib/firebird/secdb
%dir %attr(0700,firebird,firebird) %{_localstatedir}/lib/firebird/data
%dir %attr(0755,firebird,firebird) %{_localstatedir}/lib/firebird/system
%attr(0600,firebird,firebird) %config(noreplace) %{_localstatedir}/lib/firebird/secdb/security3.fdb
%attr(0644,firebird,firebird) %{_localstatedir}/lib/firebird/system/help.fdb
%attr(0644,firebird,firebird) %{_localstatedir}/lib/firebird/system/firebird.msg
%ghost %dir %attr(0775,firebird,firebird) %{_var}/run/firebird
%ghost %attr(0644,firebird,firebird) %{_var}/run/firebird/fb_guard
%attr(0644,root,root) %{_tmpfilesdir}/firebird.conf
%dir %{_localstatedir}/log/firebird
%config(noreplace) %attr(0664,firebird,firebird)  %{_localstatedir}/log/firebird/firebird.log
%config(noreplace) %attr(0644,root,root) %{_sysconfdir}/logrotate.d/firebird
%config(noreplace) %{_sysconfdir}/ld.so.conf.d/%{name}-%{_arch}.conf

%defattr(0755,root,root,0755)
%{_unitdir}/firebird-superserver.service
%{_libdir}/libfbclient.so.*
%{_libdir}/libib_util.so
%{_bindir}/*

%files          devel
%{_includedir}/firebird
%{_libdir}/fb_config
%{_sbindir}/fb_config
%{_libdir}/libfbclient.so
%{_libdir}/pkgconfig/fbclient.pc
%{_docdir}/firebird/sample
%attr(0600,firebird,firebird) %{_localstatedir}/lib/firebird/data/employee.fdb

%files          help
%{_docdir}/firebird
%exclude %{_docdir}/firebird/sample
%exclude %{_docdir}/firebird/IDPLicense.txt
%exclude %{_docdir}/firebird/IPLicense.txt

%changelog
* Thu Mar 2 2023 dillon chen <dillon.chen@gmail.com> - 3.0.10.33601-2
- add -fPIE in honour-buildflags.patch

* Thu Sep 1 2022 Funda Wang <fundawang@yeah.net> - 3.0.10.33601-1
- New version 3.0.10

* Tue Aug 30 2022 dillon chen<dillon.chen@gmail.com> - 3.0.3.32900-10
- put correct source as /usr/sbin/fb_config

* Mon Mar 7 2022 yaoxin <yaoxin30@huawei.com> - 3.0.3.32900-9
- Fix failed to parse pid from pid file

* Fri Sep 10 2021 bzhaoop <bzhaojyathousandy@gmail.com> - 3.0.3.32900-8
- Del rpath in some binaries for firebird.

* Thu Feb 25 2021 huanghaitao <huanghaitao8@huawei.com> - 3.0.3.32900-7
- Fix login shell to /sbin/nologin

* Mon Jan 13 2020 openEuler Buildteam <buildteam@openeuler.org> - 3.0.3.32900-6
- Type:bugfix
- Id:NA
- SUG:NA
- DESC:remove the libtermcap-devel in buildrequires

* Mon Dec 2 2019 lihao <lihao129@huawei.com> - 3.0.3.32900-5
- Package Init

