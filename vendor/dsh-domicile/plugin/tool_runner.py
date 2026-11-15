"""Fixed plugin bridge. Imports packaged reviewed query; never runs caller code."""
import json
from pathlib import Path
import re
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from query import query
from protocol import ProtocolError, workspace_query

def dispatch(payload):
    request = payload['request']
    desktop = request['desktop']
    def failure(code):return {'desktop':desktop,'code':code,'resultJson':None}
    if set(payload) != {'request','registry'} or not isinstance(request,dict):return failure('invalid-arguments')
    if request.get('operation') not in ('snapshot','workspace') or set(request)-{'operation','desktop','workspace','expected'}:return failure('invalid-arguments')
    if not isinstance(desktop,str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,63}',desktop):return failure('invalid-arguments')
    if desktop not in payload['registry'].get('desktops',{}):return failure('desktop-not-allowed')
    expected=request.get('expected')
    if expected is not None:
        if not isinstance(expected,dict) or set(expected)!={'epoch','revision'} or not isinstance(expected['epoch'],str) or not re.fullmatch(r'[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}',expected['epoch']) or type(expected['revision']) is not int or not 1<=expected['revision']<=9007199254740991:return failure('invalid-arguments')
        expected=(expected['epoch'],expected['revision'])
    if request['operation']=='workspace' and (not isinstance(request.get('workspace'),str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,64}',request['workspace'])):return failure('invalid-arguments')
    if request['operation']=='snapshot' and 'workspace' in request:return failure('invalid-arguments')
    try:
        reply=query(payload['registry'],desktop,expected=expected)
        if not reply['ok']:return failure(reply['error']['code'])
        if request['operation']=='workspace':
            if not any(w['name']==request['workspace'] for w in reply['snapshot']['workspaces']):return failure('workspace-not-found')
            reply=workspace_query(reply,request['workspace'])
        return {'desktop':desktop,'code':'ok','resultJson':json.dumps(reply,separators=(',',':'))}
    except ProtocolError as error:
        return failure('unavailable' if str(error)=='desktop transport unavailable; no fallback' else 'invalid-reply')
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError):return failure('unavailable')

if __name__=='__main__':
    try:
        raw=sys.stdin.buffer.read(65537)
        if len(raw)>65536:raise ValueError('oversized request')
        result=dispatch(json.loads(raw))
    except (ValueError,KeyError,TypeError):result={'desktop':'','code':'invalid-arguments','resultJson':None}
    print(json.dumps(result,separators=(',',':')))
