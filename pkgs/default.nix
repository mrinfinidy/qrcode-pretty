{ lib, pkgs, ... }:

pkgs.python3Packages.buildPythonApplication {
  pname = "qrcode-pretty";
  version = "1.1.0";
  src = ./..;
  doCheck = true;
  pyproject = true;

  nativeBuildInputs = [
    pkgs.python3Packages.hatchling
  ];

  nativeCheckInputs = [
    pkgs.python3Packages.pytest
  ];

  checkPhase = ''
    runHook preCheck
    pytest tests/
    runHook postCheck
  '';

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
