{ lib, pkgs, ... }:

pkgs.python3Packages.buildPythonApplication {
  pname = "qrcode-pretty";
  version = "1.1.0";
  src = ./..;
  doCheck = false;
  pyproject = true;

  nativeBuildInputs = [
    pkgs.python3Packages.hatchling
  ];

  propagatedBuildInputs = [
    pkgs.python3Packages.qrcode
    pkgs.python3Packages.pillow
  ];

  makeWrapperArgs = [
    "--set DEFAULT_IMAGE ${./../assets/default.png}"
  ];

  meta = with lib; {
    homepage = "https://github.com/mrinfinidy/qrcode-pretty";
    description = "A tool which generates pretty QR codes";
    license = licenses.mit;
  };
}
