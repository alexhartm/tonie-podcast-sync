{
  description = "tonie-podcast-sync - sync podcast episodes to creative tonies";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python310;
      in
      {
        devShells.default = pkgs.mkShell {
          name = "tonie-podcast-sync";

          buildInputs = [
            # Python
            python

            # Package management
            pkgs.uv

            # Development tools
            pkgs.ruff
            pkgs.pre-commit

            # Required for volume_adjustment feature
            pkgs.ffmpeg

            # For all-contributors CLI
            pkgs.nodejs
            pkgs.yarn
          ];

          shellHook = ''
            echo "🎧 tonie-podcast-sync development environment"
            echo ""
            echo "Python: $(python --version)"
            echo "uv: $(uv --version)"
            echo "ruff: $(ruff --version)"
            echo ""
            echo "Quick start:"
            echo "  uv sync                    # Install dependencies"
            echo "  uv pip install -e .[dev]   # Install in editable mode with dev deps"
            echo "  uv run pytest tests/       # Run tests"
            echo ""

            # Create venv if it doesn't exist
            if [ ! -d .venv ]; then
              echo "Creating virtual environment..."
              uv venv .venv
            fi

            # Activate venv
            source .venv/bin/activate
          '';

          # Set environment variables
          UV_PYTHON = "${python}/bin/python";
        };
      }
    );
}
