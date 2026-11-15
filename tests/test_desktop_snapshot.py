import copy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
SDK = '8115d932b41be551ca7769fc2e89e323e5692c8c'
os.environ.setdefault('DSH_DOMICILE_PAYLOAD', str(REPO/'vendor/dsh-domicile'))
SPEC=importlib.util.spec_from_file_location('local_snapshot',REPO/'scripts/mac17-desktop-snapshot.py')
module=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(module)

class LocalSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.home=Path(self.tmp.name)
        self.directory=self.home/'.config/dsh-domicile';self.directory.mkdir(parents=True,mode=0o700)
        self.config={'desktopId':'tarek-mac17','runtimeDirectory':f'/run/user/{os.getuid()}',
            'domicileBinary':'/nix/store/fixture-domicile/bin/domicile','imagineSource':'/nix/store/fixture-imagine-source',
            'sdkSource':SDK,'replyRoot':'.local/state/dsh-domicile/replies'}
        self.path=self.directory/'client.json';self.path.write_text(json.dumps(self.config));self.path.chmod(0o600)
        self.environment=patch.dict(os.environ,{
            'DSH_DOMICILE_RUNTIME_UID':str(os.getuid()),'DSH_DOMICILE_DESKTOP_ID':'tarek-mac17',
            'DSH_DOMICILE_BINARY':self.config['domicileBinary'],'DSH_DOMICILE_IMAGINE_SOURCE':self.config['imagineSource'],
            'DSH_DOMICILE_SDK_SOURCE':SDK})
        self.environment.start();self.patched_home=patch.object(module.Path,'home',return_value=self.home);self.patched_home.start()
    def tearDown(self):
        self.patched_home.stop();self.environment.stop();self.tmp.cleanup()
    def reply(self):
        return {'ok':True,'source':{'sdk':SDK,'imagine':self.config['imagineSource']},
            'epoch':'4c760009-19ae-4dfa-860a-4e5c44e7181f','revision':2,'snapshot':{'workspaces':[{'name':'1'}]}}
    def test_correct_private_config_is_accepted(self):
        self.assertEqual(module.read_config(),self.config)
    def test_world_readable_config_is_rejected(self):
        self.path.chmod(0o644)
        with self.assertRaises(module.ProtocolError):module.read_config()
    def test_config_symlink_is_rejected(self):
        self.path.unlink();self.path.symlink_to(self.home/'elsewhere')
        with self.assertRaises(OSError):module.read_config()
    def test_owner_identity_mismatch_is_rejected(self):
        with patch.object(module.os,'getuid',return_value=os.getuid()+1):
            with self.assertRaises(module.ProtocolError):module.read_config()
    def test_unreviewed_binary_cannot_redirect_the_client(self):
        self.config['domicileBinary']='/bin/sh';self.path.write_text(json.dumps(self.config))
        with self.assertRaises(module.ProtocolError):module.read_config()
    def test_wrong_desktop_never_reaches_transport(self):
        with patch.object(module,'native_request') as send:
            with self.assertRaises(module.ProtocolError):module.query('someone-else')
            send.assert_not_called()
    def test_source_mismatch_fails_without_relabeling(self):
        reply=self.reply();reply['source']['sdk']='0'*40
        with patch.object(module,'native_request',return_value=reply):
            with self.assertRaises(module.ProtocolError):module.query('tarek-mac17')
    def test_stale_reply_is_rejected(self):
        with patch.object(module,'native_request',return_value=self.reply()):
            with self.assertRaises(module.ProtocolError):module.query('tarek-mac17',expected=('4c760009-19ae-4dfa-860a-4e5c44e7181f',1))
    def test_invalid_expected_identity_never_reaches_transport(self):
        with patch.object(module,'native_request') as send:
            with self.assertRaises(module.ProtocolError):module.query('tarek-mac17',expected=('bad',1))
            send.assert_not_called()
    def test_lock_failure_remains_failure(self):
        reply=self.reply();reply['ok']=False;reply.pop('snapshot');reply['error']={'code':'locked-or-unavailable'}
        with patch.object(module,'native_request',return_value=reply):
            result=module.query('tarek-mac17');self.assertFalse(result['ok']);self.assertNotIn('snapshot',result)

if __name__=='__main__':unittest.main()
