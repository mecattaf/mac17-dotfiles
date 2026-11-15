# Postprocess the maintained NixOS hybrid ISO; retain its BIOS and EFI boot
# equipment and append an independent, initially empty writable FAT partition.
{ lib, runCommand, xorriso, dosfstools, mtools, coreutils, util-linux, python3
, baseIso, backupMiB ? 512, imageName ? "mac17-installer.iso"
}:
assert backupMiB >= 512;
assert lib.hasSuffix ".iso" imageName && builtins.baseNameOf imageName == imageName;
runCommand "mac17-usb-installer" {
  __structuredAttrs = true;
  nativeBuildInputs = [ xorriso dosfstools mtools coreutils util-linux python3 ];
  unsafeDiscardReferences.out = true;
  passthru = { inherit baseIso backupMiB; };
} ''
  set -euo pipefail
  export TZ=UTC SOURCE_DATE_EPOCH=946684800
  mkdir -p "$out/iso" "$out/nix-support" "$out/metadata"
  shopt -s nullglob
  images=(${baseIso}/iso/*.iso)
  if (( ''${#images[@]} != 1 )); then
    echo 'Expected exactly one uncompressed NixOS ISO' >&2; exit 1
  fi
  source_iso=''${images[0]}
  sfdisk --json "$source_iso" > "$out/metadata/source-layout.json"
  python3 - "$out/metadata/source-layout.json" <<'PY'
  import json,sys
  t=json.load(open(sys.argv[1]))['partitiontable']
  p=t['partitions']
  assert t['label']=='dos' and len(p)==2, 'Unexpected source hybrid layout'
  assert p[0]['type']=='0' and p[1]['type'].lower()=='ef', 'Unexpected boot partitions'
  PY
  truncate -s ${toString backupMiB}M backup.fat
  mkfs.fat -F 32 --invariant -i 4d313742 -n MAC17SAVE backup.fat
  printf 'mac17-usb-backup-v1\n' > marker
  cat > README.txt <<'README'
  This partition stores the Mac's Apple EFI/T1 firmware backup during installation.
  It starts empty and contains no personalized firmware in the downloadable image.
  Copy the saved backup somewhere safe before flashing or erasing this USB again.
  README
  touch -d @946684800 marker README.txt
  mcopy -m -i backup.fat marker ::/.mac17-backup
  mcopy -m -i backup.fat README.txt ::/README.txt
  fsck.fat -n backup.fat
  xorriso -indev "$source_iso" -outdev "$out/iso/${imageName}" \
    -boot_image any replay \
    -boot_image any gpt_disk_guid=volume_date_uuid \
    -append_partition 3 0x0c backup.fat -commit -end
  sfdisk --json "$out/iso/${imageName}" > "$out/metadata/layout.json"
  xorriso -indev "$out/iso/${imageName}" \
    -report_el_torito plain -report_system_area plain \
    > "$out/metadata/boot-layout.txt" 2>&1
  python3 - "$out/metadata/layout.json" "$out/iso/${imageName}" <<'PY'
  import json,sys,subprocess
  t=json.load(open(sys.argv[1]))['partitiontable']; p=t['partitions']
  assert t['label']=='dos' and len(p)==3, 'Unexpected output hybrid layout'
  assert p[1]['type'].lower()=='ef' and p[2]['type'].lower()=='c'
  assert p[2]['size']*t['sectorsize'] >= ${toString backupMiB}*1024*1024
  offset=p[2]['start']*t['sectorsize']
  got=subprocess.check_output(['mtype','-i',sys.argv[2]+'@@'+str(offset),'::/.mac17-backup'])
  assert got==b'mac17-usb-backup-v1\n', 'Backup partition marker absent'
  with open(sys.argv[2],'rb') as image:
      image.seek(16*2048+1)
      assert image.read(5)==b'CD001', 'Output is not an ISO9660 image'
  PY
  (cd "$out/iso"; sha256sum ${lib.escapeShellArg imageName} > SHA256SUMS)
  printf 'file iso %s\n' "$out/iso/${imageName}" > "$out/nix-support/hydra-build-products"
''
