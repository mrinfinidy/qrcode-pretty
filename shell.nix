{
  pkgs ? import <nixpkgs> { },
}:

pkgs.mkShell {
  nativeBuildInputs = [
    pkgs.python313Packages.qrcode
    pkgs.python313Packages.pillow
  ];
}
