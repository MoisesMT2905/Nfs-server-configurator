Name:           yast2-nfs-server
Version:        1.0.0
Release:        1%{?dist}
Summary:        YaST2 NFS Server Configurator

License:        MIT
URL:            https://github.com/MoisesMT2905/Nfs-server-configurator
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
Requires:       python3
Requires:       python3-gobject
Requires:       python3-dbus
Requires:       gtk3
Requires:       nfs-utils
Requires:       polkit
Requires:       systemd

%description
YaST2-inspired NFS Server Configurator with graphical interface.
Provides secure configuration of NFS exports using D-Bus and polkit
for privilege escalation.

%prep
%setup -q

%build
# No build needed for Python

%install
rm -rf %{buildroot}

# Install main application
mkdir -p %{buildroot}%{_datadir}/yast2-nfs-server
cp -r src %{buildroot}%{_datadir}/yast2-nfs-server/
cp main.py %{buildroot}%{_datadir}/yast2-nfs-server/
cp requirements.txt %{buildroot}%{_datadir}/yast2-nfs-server/
cp README.md %{buildroot}%{_datadir}/yast2-nfs-server/

# Install D-Bus helper
mkdir -p %{buildroot}%{_libexecdir}
install -m 0755 src/priv_helper/helper.py %{buildroot}%{_libexecdir}/yast2-nfs-helper

# Install polkit policy
mkdir -p %{buildroot}%{_datadir}/polkit-1/actions
install -m 0644 packaging/org.yast2.nfshelper.policy %{buildroot}%{_datadir}/polkit-1/actions/

# Install systemd service
mkdir -p %{buildroot}%{_unitdir}
install -m 0644 packaging/yast2-nfs-helper.service %{buildroot}%{_unitdir}/

# Install D-Bus service file
mkdir -p %{buildroot}%{_datadir}/dbus-1/system-services
cat > %{buildroot}%{_datadir}/dbus-1/system-services/org.yast2.NFSHelper.service << EOF
[D-BUS Service]
Name=org.yast2.NFSHelper
Exec=/usr/libexec/yast2-nfs-helper
User=root
SystemdService=yast2-nfs-helper.service
EOF

# Install D-Bus configuration
mkdir -p %{buildroot}%{_sysconfdir}/dbus-1/system.d
cat > %{buildroot}%{_sysconfdir}/dbus-1/system.d/org.yast2.NFSHelper.conf << EOF
<!DOCTYPE busconfig PUBLIC
 "-//freedesktop//DTD D-BUS Bus Configuration 1.0//EN"
 "http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">
<busconfig>
  <policy user="root">
    <allow own="org.yast2.NFSHelper"/>
    <allow send_destination="org.yast2.NFSHelper"/>
  </policy>
  
  <policy context="default">
    <allow send_destination="org.yast2.NFSHelper"
           send_interface="org.yast2.NFSHelper"/>
  </policy>
</busconfig>
EOF

# Create launcher script
mkdir -p %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/yast2-nfs-server << EOF
#!/bin/bash
cd %{_datadir}/yast2-nfs-server
exec python3 main.py "\$@"
EOF
chmod 0755 %{buildroot}%{_bindir}/yast2-nfs-server

%files
%doc README.md
%{_datadir}/yast2-nfs-server/
%{_libexecdir}/yast2-nfs-helper
%{_datadir}/polkit-1/actions/org.yast2.nfshelper.policy
%{_unitdir}/yast2-nfs-helper.service
%{_datadir}/dbus-1/system-services/org.yast2.NFSHelper.service
%config(noreplace) %{_sysconfdir}/dbus-1/system.d/org.yast2.NFSHelper.conf
%{_bindir}/yast2-nfs-server

%post
# Reload D-Bus configuration
if [ -x /usr/bin/dbus-send ]; then
    /usr/bin/dbus-send --system --type=method_call \
        --dest=org.freedesktop.DBus / \
        org.freedesktop.DBus.ReloadConfig || :
fi

# Enable and start the service
%systemd_post yast2-nfs-helper.service
if [ $1 -eq 1 ]; then
    # First installation
    /usr/bin/systemctl enable yast2-nfs-helper.service >/dev/null 2>&1 || :
    /usr/bin/systemctl start yast2-nfs-helper.service >/dev/null 2>&1 || :
fi

%preun
%systemd_preun yast2-nfs-helper.service

%postun
%systemd_postun_with_restart yast2-nfs-helper.service

# Reload D-Bus configuration
if [ $1 -eq 0 ]; then
    if [ -x /usr/bin/dbus-send ]; then
        /usr/bin/dbus-send --system --type=method_call \
            --dest=org.freedesktop.DBus / \
            org.freedesktop.DBus.ReloadConfig || :
    fi
fi

%changelog
* Wed Nov 12 2025 Development Team <dev@example.com> - 1.0.0-1
- Initial release
- D-Bus privileged helper with polkit integration
- GTK3 graphical interface
- Comprehensive test suite
- CI/CD integration
