Name:           yast2-nfs-server
Version:        1.0.0
Release:        1%{?dist}
Summary:        YaST2 NFS Server Configuration Module
License:        MIT
URL:            https://github.com/MoisesMT2905/Nfs-server-configurator
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch

Requires:       python3 >= 3.8
Requires:       python3-gobject
Requires:       python3-pydbus
Requires:       polkit
Requires:       nfs-utils
Requires:       gtk3
Requires:       systemd

%description
YaST2 module for configuring NFS server exports with a graphical interface.
Includes a D-Bus privileged helper for secure non-root operation with polkit
authorization.

%prep
%setup -q

%build
# Nothing to build for Python

%install
# Create directory structure
install -d %{buildroot}%{_bindir}
install -d %{buildroot}%{_libexecdir}
install -d %{buildroot}%{_datadir}/%{name}
install -d %{buildroot}%{_datadir}/%{name}/src
install -d %{buildroot}%{_datadir}/%{name}/src/backend
install -d %{buildroot}%{_datadir}/%{name}/src/gui
install -d %{buildroot}%{_datadir}/%{name}/src/utils
install -d %{buildroot}%{_unitdir}
install -d %{buildroot}%{_datadir}/polkit-1/actions
install -d %{buildroot}%{_datadir}/dbus-1/system-services

# Install main application
install -m 755 main.py %{buildroot}%{_datadir}/%{name}/
install -m 644 src/backend/*.py %{buildroot}%{_datadir}/%{name}/src/backend/
install -m 644 src/gui/*.py %{buildroot}%{_datadir}/%{name}/src/gui/
install -m 644 src/utils/*.py %{buildroot}%{_datadir}/%{name}/src/utils/

# Install privileged helper
install -m 755 src/priv_helper/helper.py %{buildroot}%{_libexecdir}/yast2-nfs-server-helper

# Install systemd unit file
install -m 644 packaging/yast2-nfs-helper.service %{buildroot}%{_unitdir}/

# Install polkit policy
install -m 644 packaging/org.yast2.nfshelper.policy %{buildroot}%{_datadir}/polkit-1/actions/

# Create D-Bus service file
cat > %{buildroot}%{_datadir}/dbus-1/system-services/org.yast2.NFSHelper.service << EOF
[D-BUS Service]
Name=org.yast2.NFSHelper
Exec=%{_libexecdir}/yast2-nfs-server-helper
User=root
SystemdService=yast2-nfs-helper.service
EOF

# Create wrapper script in /usr/bin
cat > %{buildroot}%{_bindir}/yast2-nfs-server << EOF
#!/bin/bash
cd %{_datadir}/%{name}
exec python3 main.py "\$@"
EOF
chmod 755 %{buildroot}%{_bindir}/yast2-nfs-server

%post
%systemd_post yast2-nfs-helper.service
# Enable the service so it starts on boot
systemctl enable yast2-nfs-helper.service >/dev/null 2>&1 || :
# Reload D-Bus to recognize the new service
systemctl reload dbus.service >/dev/null 2>&1 || :

%preun
%systemd_preun yast2-nfs-helper.service

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
%{_datadir}/dbus-1/system-services/org.yast2.NFSHelper.service

%changelog
* Tue Nov 12 2024 YaST2 Development Team
- Initial release with D-Bus helper and polkit integration
- Graphical configuration interface
- Automated tests and CI
