{pkgs}: {
  deps = [
    pkgs.ffmpeg-full
    pkgs.libsndfile
    pkgs.portaudio
    pkgs.xsimd
    pkgs.pkg-config
    pkgs.libxcrypt
    pkgs.re2
    pkgs.oneDNN
    pkgs.postgresql
    pkgs.openssl
  ];
}
