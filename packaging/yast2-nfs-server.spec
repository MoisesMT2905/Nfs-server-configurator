Name:           yast2-nfs-server
Version:        1.0.0
Release:        1%{?dist}
Summary:        YaST2 NFS Server Configuration Tool
License:        MIT
URL:            https://github.com/MoisesMT2905/Nfs-server-configurator
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  systemd-rpm-macros

Requires:       python3 >= 3.8
Requires:       python3-gobject
Requires:       python3-pydbus
Requires:       gtk3
Requires:       polkit
Requires:       nfs-utils
Requires:       systemd

%description
YaST2-inspired NFS server configuration tool with graphical interface.
Provides a privileged D-Bus helper for non-root users to configure
NFS exports with polkit authorization.

%prep
%setup -q

%build
# Python package, no compilation needed

%install
# Create directory structure
mkdir -p %{buildroot}%{_datadir}/%{name}
mkdir -p %{buildroot}%{_libexecdir}
mkdir -p %{buildroot}%{_unitdir}
mkdir -p %{buildroot}%{_datadir}/polkit-1/actions
mkdir -p %{buildroot}%{_bindir}

# Install Python modules
cp -r src %{buildroot}%{_datadir}/%{name}/
cp main.py %{buildroot}%{_datadir}/%{name}/

# Install privileged helper
install -m 755 src/priv_helper/helper.py %{buildroot}%{_libexecdir}/yast2-nfs-server-helper

# Install systemd unit
install -m 644 packaging/yast2-nfs-helper.service %{buildroot}%{_unitdir}/

# Install polkit policy
install -m 644 packaging/org.yast2.nfshelper.policy %{buildroot}%{_datadir}/polkit-1/actions/

# Install launcher script
cat > %{buildroot}%{_bindir}/yast2-nfs-server <<'EOF'
#!/bin/bash
cd %{_datadir}/%{name}
exec python3 main.py "$@"
EOF
chmod 755 %{buildroot}%{_bindir}/yast2-nfs-server

%pre
# Create backup directory for exports if it doesn't exist
if [ ! -d /etc/exports.backup ]; then
    mkdir -p /etc/exports.backup
fi

%post
# Reload systemd daemon
%systemd_post yast2-nfs-helper.service

# Enable and start the helper service
if [ $1 -eq 1 ]; then
    # First installation
    systemctl daemon-reload
    systemctl enable yast2-nfs-helper.service
    systemctl start yast2-nfs-helper.service
fi

%preun
# Stop and disable service on uninstall
%systemd_preun yast2-nfs-helper.service

%postun
# Cleanup on uninstall
%systemd_postun_with_restart yast2-nfs-helper.service

%files
%license LICENSE
%doc README.md
%{_datadir}/%{name}/
%{_libexecdir}/yast2-nfs-server-helper
%{_unitdir}/yast2-nfs-helper.service
%{_datadir}/polkit-1/actions/org.yast2.nfshelper.policy
%{_bindir}/yast2-nfs-server

%changelog
* Tue Nov 12 2024 Copilot <copilot@github.com> - 1.0.0-1
- Initial package with D-Bus helper and polkit integration
- GTK3 graphical interface for NFS configuration
- Privileged helper for non-root users
- Systemd service integration
