{ lib, stdenv, fetchFromGitHub, kernel, kernelModuleMakeFlags ? [ ] }:

assert lib.versionAtLeast kernel.version "6.17";
stdenv.mkDerivation {
  pname = "snd-hda-macbookpro";
  version = "0-1931615-${kernel.version}";
  src = fetchFromGitHub {
    owner = "davidjo";
    repo = "snd_hda_macbookpro";
    rev = "1931615d723899f64b352e9e7ed2368c21c49728";
    hash = "sha256-lpzhaw57AyWO/Kcwc7lhI7ZbW4l6WFYG0saWOjcRmPk=";
  };
  nativeBuildInputs = kernel.moduleBuildDependencies;
  hardeningDisable = [ "pic" ];

  # Take both public and private HDA source from the SAME selected NixOS kernel.
  # Never download the running distribution's nearest upstream version at boot.
  postUnpack = ''
    mkdir selected-kernel
    tar -xf ${kernel.src} --directory selected-kernel --strip-components=1 --wildcards '*/sound/hda/*'
  '';
  postPatch = ''
    mkdir -p hda/codecs/cirrus hda/codecs/side-codecs hda/common
    for file in \
      codecs/cirrus/cs8409.c codecs/cirrus/cs8409.h codecs/cirrus/cs8409-tables.c \
      codecs/generic.h codecs/side-codecs/hda_component.h \
      common/hda_local.h common/hda_auto_parser.h common/hda_jack.h; do
      cp "../selected-kernel/sound/hda/$file" "hda/$file"
    done
    # The upstream checkout also contains an old copy of cs8409.h. Never
    # overwrite the selected kernel's header with it: newer kernels add Dell
    # component fields that their own cs8409.c still needs. Only Apple helper
    # headers are inputs to the community patch.
    cp patch_cirrus/cirrus_apple.h patch_cirrus/patch_cirrus_*.h hda/codecs/cirrus/
    (cd hda && patch -p1 < ../patch_cs8409.c.diff && patch -p1 < ../patch_cs8409.h.diff)
    cat > hda/codecs/cirrus/Kbuild <<'EOF'
    ccflags-y += -I$(src)/../../common -DAPPLE_PINSENSE_FIXUP -DAPPLE_CODECS -Wno-unused-variable -Wno-unused-function
    snd-hda-codec-cs8409-y := cs8409.o cs8409-tables.o
    obj-m += snd-hda-codec-cs8409.o
    EOF
  '';
  buildPhase = ''
    runHook preBuild
    make -C ${kernel.dev}/lib/modules/${kernel.modDirVersion}/build \
      M="$PWD/hda/codecs/cirrus" ${lib.escapeShellArgs kernelModuleMakeFlags} modules
    runHook postBuild
  '';
  installPhase = ''
    install -Dm644 hda/codecs/cirrus/snd-hda-codec-cs8409.ko \
      "$out/lib/modules/${kernel.modDirVersion}/updates/snd-hda-codec-cs8409.ko"
    install -Dm644 LICENSE "$out/share/doc/snd-hda-macbookpro/LICENSE"
  '';
  meta = {
    description = "CS8409 Apple amplifier and headset support built for the selected NixOS kernel";
    homepage = "https://github.com/davidjo/snd_hda_macbookpro";
    license = lib.licenses.gpl2Only;
    platforms = [ "x86_64-linux" ];
  };
}
