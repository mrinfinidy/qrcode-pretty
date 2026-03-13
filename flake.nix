{
  description = "A tool which generates pretty QR codes";
  inputs.nixpkgs.url = "nixpkgs";

  outputs =
    {
      self,
      nixpkgs,
    }:
    let
      systems = [
        "x86_64-linux"
        "i686-linux"
        "x86_64-darwin"
        "aarch64-linux"
        "armv6l-linux"
        "armv7l-linux"
      ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f system);
    in
    {
      legacyPackages = forAllSystems (
        system:
        let
          pkgs = import nixpkgs {
            inherit system;
            config.allowUnfree = true;
          };
        in
        rec {
          qrcode-pretty = pkgs.callPackage ./pkgs { };
          default = qrcode-pretty;
        }
      );

      packages = forAllSystems (
        system: nixpkgs.lib.filterAttrs (_: v: nixpkgs.lib.isDerivation v) self.legacyPackages.${system}
      );

      devShells = forAllSystems (
        system:
        let
          pkgs = import nixpkgs {
            inherit system;
            config.allowUnfree = true;
          };
        in
        {
          default = pkgs.mkShell {
            inputsFrom = [ self.packages.${system}.qrcode-pretty ];
            nativeBuildInputs = [ pkgs.python3Packages.pytest ];
          };
        }
      );

      nixosModules = import ./modules;
    };
}
