{pkgs}: {
  deps = [
    pkgs.postgresql
    pkgs.openssl
    pkgs.lsof
    pkgs.xsimd
    pkgs.pkg-config
    pkgs.libxcrypt
    pkgs.uv
  ];
}
