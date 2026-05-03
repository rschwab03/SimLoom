{
  description = "SimLoom — multi-rate C++/Python simulation framework";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

  outputs = { self, nixpkgs }:
    let
      systems     = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f system);
    in {
      devShells = forAllSystems (system:
        let pkgs = nixpkgs.legacyPackages.${system};
        in {
          default = pkgs.mkShell {
            packages = with pkgs; [
              cmake
              gcc
              gnumake
              python3
              doxygen
            ];

            shellHook = ''
              echo "SimLoom dev environment ready."
              echo "  ./build.sh   — compile all models"
              echo "  ./docs.sh    — generate HTML documentation"
              echo "  ./clean.sh   — remove all build artifacts"
            '';
          };
        }
      );
    };
}
