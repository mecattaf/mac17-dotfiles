{ writeShellApplication, coreutils, util-linux, jq }:
writeShellApplication {
  name = "mac17-usb-backup";
  runtimeInputs = [ coreutils util-linux jq ];
  text = builtins.readFile ./mount-usb-backup.sh;
}
