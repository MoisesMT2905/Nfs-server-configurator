Name:           yast2-nfs-server
Version:        1.0.0
Release:        1%{?dist}
Summary:        YaST2 NFS Server Configurator with GUI

License:        MIT
URL:            https://github.com/MoisesMT2905/Nfs-server-configurator
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch

Requires:       python3 >= 3.8
Requires:       python3-gobject
Requires:       python3-dbus
Requires:       gtk3
Requires:       nfs-utils
Requires:       polkit
Requires:       systemd

BuildRequires:  python3-devel
BuildRequires:  systemd-rpm-macros

%description
A graphical NFS server configurator inspired by YaST2. Provides an intuitive
interface for managing NFS exports with advanced permission options. Includes
a privileged D-Bus helper with polkit integration to allow non-root users
to configure NFS exports after authentication.

%prep
%setup -q

%build
# Nothing to build - pure Python

%install
# Create directory structure
install -d %{buildroot}%{_bindir}
install -d %{buildroot}%{_libexecdir}
install -d %{buildroot}%{python3_sitelib}/yast2_nfs
install -d %{buildroot}%{_datadir}/polkit-1/actions
install -d %{buildroot}%{_datadir}/dbus-1/system.d
install -d %{buildroot}%{_unitdir}

# Install main application
install -m 755 main.py %{buildroot}%{_bindir}/yast2-nfs-server

# Install Python modules
cp -r src/* %{buildroot}%{python3_sitelib}/yast2_nfs/

# Install privileged helper
install -m 755 src/priv_helper/helper.py %{buildroot}%{_libexecdir}/yast2-nfs-helper

# Install polkit policy
install -m 644 packaging/org.yast2.nfshelper.policy %{buildroot}%{_datadir}/polkit-1/actions/

# Install D-Bus service config
install -m 644 packaging/org.yast2.NFSHelper.conf %{buildroot}%{_datadir}/dbus-1/system.d/

# Install systemd unit
install -m 644 packaging/yast2-nfs-helper.service %{buildroot}%{_unitdir}/

%post
# Reload systemd and D-Bus
%systemd_post yast2-nfs-helper.service
dbus-send --system --type=method_call --dest=org.freedesktop.DBus / org.freedesktop.DBus.ReloadConfig || true

%preun
%systemd_preun yast2-nfs-helper.service

%postun
%systemd_postun_with_restart yast2-nfs-helper.service

%files
%license LICENSE
%doc README.md
%{_bindir}/yast2-nfs-server
%{_libexecdir}/yast2-nfs-helper
%{python3_sitelib}/yast2_nfs/
%{_datadir}/polkit-1/actions/org.yast2.nfshelper.policy
%{_datadir}/dbus-1/system.d/org.yast2.NFSHelper.conf
%{_unitdir}/yast2-nfs-helper.service

%changelog
* Wed Nov 12 2025 NFS Configurator Team <dev@example.com> - 1.0.0-1
- Initial release
- Add D-Bus privileged helper with polkit integration
- Add GUI for NFS export configuration
- Add comprehensive validation and error handling
- Add pytest test suite
- Add CI/CD with GitHub Actions
