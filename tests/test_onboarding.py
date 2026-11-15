import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor

REPO=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('onboard',REPO/'scripts/mac17-onboarding.py')
onboard=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(onboard)

class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.environment=patch.dict(os.environ,{'XDG_STATE_HOME':self.tmp.name,'MAC17_JOURNEY':str(REPO/'onboarding/onboarding-journey.json')})
        self.environment.start()
    def tearDown(self):
        self.environment.stop();self.tmp.cleanup()
    def seed(self):
        with onboard.state_lock():
            value=onboard.state()
            for step in ('network','chrome'):
                value['steps'][step]={'status':'complete','evidence':'acknowledged'}
            onboard.save(value)
    def test_arbitrary_execution_and_extra_fields_are_rejected(self):
        for request in ({'op':'launch','action':'rm -rf ~'},{'op':'state','command':'secret'}, {'op':'launch','action':'chrome.open-profile','url':'https://invalid'}):
            with self.assertRaises(onboard.Refused):onboard.respond(request)
    def test_chrome_first_dependency_is_enforced(self):
        with self.assertRaises(onboard.Refused):onboard.respond({'op':'launch','action':'github.login'})
    def test_provider_output_is_not_reflected(self):
        self.seed()
        native=subprocess.CompletedProcess([],0,'You are logged in using SECRET-TOKEN','SECRET-STDERR')
        with patch.object(onboard,'run',return_value=native):
            reply=onboard.respond({'op':'probe','step':'cloudflare'})
        self.assertEqual(reply['state'],'ready')
        self.assertNotIn('SECRET',json.dumps(reply))
    def test_wrong_github_account_is_not_complete(self):
        self.seed()
        native=subprocess.CompletedProcess([],0,'someone-else\n','')
        with patch.object(onboard,'run',return_value=native):
            self.assertEqual(onboard.probe('github')['state'],'wrong-account')
            with self.assertRaises(onboard.Refused):onboard.record('github','complete')
    def test_github_invitation_is_required_after_account_login(self):
        self.seed()
        account=subprocess.CompletedProcess([],0,'tarekcmahmoud\n','')
        invitation=subprocess.CompletedProcess([],1,'','Not Found')
        with patch.object(onboard,'run',side_effect=[account,invitation]):
            self.assertEqual(onboard.probe('github')['state'],'invite-pending')
    def test_parallel_progress_writes_preserve_both_steps(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(lambda step:onboard.record(step,'deferred'),('hardware','network')))
        value=onboard.state()
        self.assertEqual(value['steps']['hardware']['status'],'deferred')
        self.assertEqual(value['steps']['network']['status'],'deferred')
        self.assertEqual((onboard.root()/'state.json').stat().st_mode&0o777,0o600)
    def test_reopening_cannot_start_duplicate_login(self):
        self.seed()
        with patch.object(onboard.subprocess,'Popen') as spawn:
            first=onboard.launch('cloudflare.login');second=onboard.launch('cloudflare.login')
        self.assertTrue(first['launched']);self.assertFalse(second['launched']);self.assertEqual(spawn.call_count,1)
    def test_state_symlink_is_not_followed(self):
        outside=Path(self.tmp.name)/'outside';outside.write_text('{"schema":1,"steps":{}}')
        (onboard.root()/'state.json').symlink_to(outside)
        with self.assertRaises(OSError):onboard.state()
    def test_finish_refuses_deferred_required_steps(self):
        onboard.record('hardware','deferred')
        with self.assertRaises(onboard.Refused):onboard.respond({'op':'finish'})
    def test_projection_contains_no_native_credentials(self):
        value=onboard.respond({'op':'state'})
        self.assertLess(len(json.dumps({'ok':True,'result':value}).encode()),15000)
        self.assertTrue(all(set(row)<= {'id','title','body','action','required','requires','completion','status','evidence','running'} for row in value['steps']))
    def test_free_ai_is_manual_reply_acknowledgement_and_claude_is_optional(self):
        self.assertEqual(onboard.probe('free-ai')['state'],'manual')
        self.assertFalse(onboard.step_for('claude')['required'])
        self.assertNotIn('claude',onboard.step_for('dsh')['requires'])
        self.assertIn('reply',onboard.step_for('free-ai')['completion']['text'])
    def test_optional_ai_accounts_do_not_block_finishing(self):
        with onboard.state_lock():
            value=onboard.state()
            for step in onboard.manifest()['steps']:
                if step['id']!='finish':
                    value['steps'][step['id']]={'status':'complete' if step.get('required') else 'deferred'}
            onboard.save(value)
        self.assertTrue(onboard.dependencies_ready(onboard.step_for('finish'),onboard.state()))
        self.assertEqual(onboard.respond({'op':'finish'})['visibility'],'complete')

if __name__=='__main__':unittest.main()
