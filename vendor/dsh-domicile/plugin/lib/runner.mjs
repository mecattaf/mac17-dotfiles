import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
const runner = fileURLToPath(new URL('../python/tool_runner.py', import.meta.url));
const MAX = 2 * 1024 * 1024 + 65536;
const CODES = new Set(['ok','invalid-arguments','desktop-not-allowed','unavailable','invalid-reply','workspace-not-found','wrong-desktop','locked-or-unavailable','epoch-changed','stale-revision','not-ready','cancelled']);

export function runQuery(config, request, signal) {
  const fail = code => ({desktop:request.desktop,code,resultJson:null});
  if (signal.aborted) return Promise.resolve(fail('cancelled'));
  return new Promise(resolve => {
    let output=[], size=0, reason, settled=false, killTimer, pendingFinish;
    const child = spawn(config.python, ['-I',runner], {stdio:['pipe','pipe','pipe'],detached:true,env:{PATH:'/run/current-system/sw/bin:/usr/bin:/bin',HOME:process.env.HOME,LANG:'C.UTF-8'}});
    const stop = code => {
      reason ??= code;
      if (child.pid) {
        try {process.kill(-child.pid,'SIGTERM');} catch (error) {if(error.code !== 'ESRCH') reason='unavailable';}
        killTimer ??= setTimeout(() => {
          try {process.kill(-child.pid,'SIGKILL');} catch {}
          killTimer=undefined;pendingFinish?.();
        },250);
      }
    };
    const abort=()=>stop('cancelled');
    const timer=setTimeout(()=>stop('unavailable'),11000);
    const finish=value=>{
      if(settled)return;
      // A parent may close its pipes before an owned SSH descendant exits.
      // Finish cancellation only after the group escalation has run.
      if(reason && killTimer){pendingFinish=()=>finish(value);return;}
      settled=true;clearTimeout(timer);signal.removeEventListener('abort',abort);resolve(value);
    };
    signal.addEventListener('abort',abort,{once:true});
    if(signal.aborted)abort();
    child.on('error',()=>finish(fail('unavailable')));
    child.stdin.on('error',()=>{});
    // Never expose SSH/native stderr to the model. The fixed runner emits only
    // bounded status codes; retained integration logs describe failures.
    child.stderr.resume();
    child.stdout.on('data',bytes=>{size+=bytes.length;if(size>MAX)stop('invalid-reply');else output.push(bytes);});
    child.on('close',code=>{
      if(reason || code !== 0)return finish(fail(reason ?? 'unavailable'));
      try {
        const value=JSON.parse(Buffer.concat(output).toString('utf8'));
        if(!value || Object.keys(value).sort().join(',')!=='code,desktop,resultJson' || value.desktop!==request.desktop || !CODES.has(value.code) || (value.code==='ok' ? typeof value.resultJson!=='string' : value.resultJson!==null))throw Error('invalid runner envelope');
        finish(value);
      } catch {finish(fail('invalid-reply'));}
    });
    child.stdin.end(JSON.stringify({registry:config.registry,request}));
  });
}
