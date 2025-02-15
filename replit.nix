{pkgs}: {
  deps = [
    pkgs.lsof
    pkgs.xsimd
    pkgs.pkg-config
    pkgs.libxcrypt
    pkgs.uv
  ];
}
