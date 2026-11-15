{ lib, stdenv, fetchFromGitHub, kernel, kernelModuleMakeFlags ? [ ] }:

stdenv.mkDerivation {
  pname = "react-drm-t1-kernel";
  version = "0-b9b1cae-${kernel.version}";
  src = fetchFromGitHub {
    owner = "dev-muhammad-adel";
    repo = "react-drm-for-touchbar";
    rev = "b9b1cae3f039dc1d64afefdc1a40955815902526";
    hash = "sha256-z2NG0hLDyOJ0FyzFI5cJe+NdX1DeKttqGndnsS+P+nk=";
  };
  sourceRoot = "source/system/t1-touchbar-display";
  nativeBuildInputs = kernel.moduleBuildDependencies;
  hardeningDisable = [ "pic" ];
  # Linux 7.3 renamed the DRM atomic transaction passed to plane helpers.
  # Follow the matching in-tree appletbdrm signatures; do not cast pointers or
  # suppress the compiler's type checks.
  postPatch = lib.optionalString (lib.versionAtLeast kernel.version "7.3") ''
    substituteInPlace appletbdrm.c \
      --replace-fail 'struct drm_atomic_state' 'struct drm_atomic_commit'
  '';
  buildPhase = ''
    make -C ${kernel.dev}/lib/modules/${kernel.modDirVersion}/build \
      M="$PWD" ${lib.escapeShellArgs kernelModuleMakeFlags} modules
  '';
  installPhase = ''
    for name in apple_dfr_cfgsel appletbdrm apple_ibridge; do
      install -Dm644 "$name.ko" "$out/lib/modules/${kernel.modDirVersion}/updates/$name.ko"
    done
  '';
  meta = {
    description = "Experimental T1 full-pixel Touch Bar driver set, mutually exclusive with Pomona";
    homepage = "https://github.com/dev-muhammad-adel/react-drm-for-touchbar";
    license = lib.licenses.gpl2Only;
    platforms = [ "x86_64-linux" ];
  };
}
