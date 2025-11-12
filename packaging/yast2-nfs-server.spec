Name:           yast2-nfs-server
Version:        1.0.0
Release:        1%{?dist}
Summary:        YaST2 NFS Server Configurator with GUI and privileged helper
License:        MIT
URL:            https://github.com/MoisesMT2905/Nfs-server-configurator
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch

# Runtime dependencies
Requires:       python3 >= 3.8
Requires:       python3-gobject
Requires:       python3-pydbus
Requires:       gtk3
Requires:       polkit
Requires:       polkit-tools
Requires:       nfs-utils
Requires:       systemd

# Build dependencies
BuildRequires:  python3-devel
BuildRequires:  systemd-rpm-macros

%description
Graphical NFS server configuration tool inspired by YaST2.
Features GUI for managing NFS exports, D-Bus helper service
with polkit authentication for privileged operations, and
comprehensive validation of NFS options.

%prep
%setup -q

%build
# Nothing to build for Python

%install
# Create directory structure
install -d %{buildroot}%{_datadir}/%{name}
install -d %{buildroot}%{_datadir}/%{name}/src
install -d %{buildroot}%{_libexecdir}
install -d %{buildroot}%{_unitdir}
install -d %{buildroot}%{_datadir}/polkit-1/actions

# Install Python modules
cp -r src/* %{buildroot}%{_datadir}/%{name}/src/
install -m 0755 main.py %{buildroot}%{_datadir}/%{name}/

# Install helper as libexec
install -m 0755 src/priv_helper/helper.py %{buildroot}%{_libexecdir}/yast2-nfs-server-helper

# Install systemd unit
install -m 0644 packaging/yast2-nfs-helper.service %{buildroot}%{_unitdir}/

# Install polkit policy
install -m 0644 packaging/org.yast2.nfshelper.policy %{buildroot}%{_datadir}/polkit-1/actions/

# Create wrapper script
cat > %{buildroot}%{_bindir}/yast2-nfs-server <<EOF
#!/bin/bash
cd %{_datadir}/%{name}
exec python3 main.py "\$@"
EOF
chmod 0755 %{buildroot}%{_bindir}/yast2-nfs-server

%post
%systemd_post yast2-nfs-helper.service
# Reload systemd and enable service
systemctl daemon-reload || true
systemctl enable --now yast2-nfs-helper.service || true

%preun
%systemd_preun yast2-nfs-helper.service
# Stop and disable service before uninstall
systemctl disable --now yast2-nfs-helper.service || true

%postun
%systemd_postun_with_restart yast2-nfs-helper.service

%files
%license LICENSE
%doc README.md
%{_bindir}/yast2-nfs-server
%{_datadir}/%{name}/
%{_libexecdir}/yast2-nfs-server-helper
%{_unitdir}/yast2-nfs-helper.service
%{_datadir}/polkit-1/actions/org.yast2.nfshelper.policy

%changelog
* Wed Nov 12 2025 NFS Configurator Team <team@example.com> - 1.0.0-1
- Initial release
- Added D-Bus helper with polkit authentication
- Added GUI with GTK3
- Added comprehensive NFS options (13 options)
- Added systemd service integration
- Added validation and security features
