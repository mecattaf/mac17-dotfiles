import { readFileSync } from 'node:fs';
import { isAbsolute } from 'node:path';
import { runQuery } from './runner.mjs';

export const name = 'dsh-domicile';
export const inject = ['tools'];
export const TOOL_NAMES = Object.freeze(['domicile_snapshot', 'domicile_workspace']);
const epochPattern = /^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/;
export const CODES = Object.freeze(['ok', 'invalid-arguments', 'desktop-not-allowed', 'unavailable', 'invalid-reply', 'workspace-not-found', 'wrong-desktop', 'locked-or-unavailable', 'epoch-changed', 'stale-revision', 'not-ready', 'cancelled']);
export const failure = (desktop, code) => ({desktop, code, resultJson: null});
const object = (properties, required = Object.keys(properties)) => ({type:'object', additionalProperties:false, required, properties});
const outputSchema = object({desktop:{type:'string'}, code:{type:'string',enum:CODES}, resultJson:{oneOf:[{type:'string'},{type:'null'}]}});

function validArguments(args, workspace, desktops) {
  if (!args || typeof args !== 'object' || Array.isArray(args)) return 'invalid-arguments';
  const keys = ['desktop', ...(workspace ? ['workspace'] : []), 'expected'];
  if (Object.keys(args).some(k => !keys.includes(k)) || typeof args.desktop !== 'string') return 'invalid-arguments';
  if (!desktops.includes(args.desktop)) return 'desktop-not-allowed';
  if (workspace && (typeof args.workspace !== 'string' || !/^[A-Za-z0-9_.-]{1,64}$/.test(args.workspace))) return 'invalid-arguments';
  if (args.expected !== undefined) {
    const e = args.expected;
    if (!e || typeof e !== 'object' || Array.isArray(e) || Object.keys(e).sort().join(',') !== 'epoch,revision' || !epochPattern.test(e.epoch) || !Number.isSafeInteger(e.revision) || e.revision < 1) return 'invalid-arguments';
  }
}

export function createTools(config, execute = runQuery) {
  if (!config || typeof config.python !== 'string' || !isAbsolute(config.python)) throw Error('dsh-domicile requires an explicit Python executable');
  const registry = structuredClone(config.registry);
  const desktops = Object.keys(registry?.desktops ?? {});
  if (!desktops.length || desktops.length > 32 || desktops.some(d => !/^[a-z][a-z0-9-]{0,63}$/.test(d))) throw Error('dsh-domicile requires an explicit desktop allowlist');
  // Snapshot the trusted configuration once; model arguments never select a
  // program, registry file, remote address, native command or transport route.
  const runtime = Object.freeze({python:config.python, registry});
  return TOOL_NAMES.map((toolName, index) => {
    const workspace = index === 1;
    const properties = {desktop:{type:'string',enum:desktops}, ...(workspace ? {workspace:{type:'string'}} : {}), expected:object({epoch:{type:'string'},revision:{type:'integer'}})};
    return {
      name:toolName,
      description:`Read ${workspace ? 'one actual workspace tree and its enclosed windows' : 'the actual Imagine desktop workspace trees, outputs and window identities'} on an explicitly selected allowed desktop. Read-only; excludes titles, URLs and contents. Supply expected epoch and revision together to reject stale references. Lock, restart or unavailable transport fails; never infer missing windows from failure. Container paths are valid only at the returned epoch and revision.`,
      parameters:object(properties, ['desktop', ...(workspace ? ['workspace'] : [])]),
      output:{schema:outputSchema, render:(_args, value) => [{type:'text',text:value.code === 'ok' ? value.resultJson : JSON.stringify({ok:false,desktop:value.desktop,error:{code:value.code}})}]},
      timeoutMs:12000,
      // Remain exclusive: the native hook bounds concurrent atomic writers.
      async execute(args, exec) {
        const code = validArguments(args, workspace, desktops);
        if (code) return failure(typeof args?.desktop === 'string' && desktops.includes(args.desktop) ? args.desktop : '', code);
        if (exec.signal.aborted) return failure(args.desktop, 'cancelled');
        return execute(runtime, {operation:workspace ? 'workspace' : 'snapshot', ...args}, exec.signal);
      },
      presentCall:() => ({card:'generic',title:workspace ? 'Read Imagine workspace' : 'Read Imagine desktop',kind:'read'}),
    };
  });
}

export function apply(ctx, config) {
  if (!config || typeof config.registryPath !== 'string' || !isAbsolute(config.registryPath)) throw Error('dsh-domicile requires an explicit registry path');
  const bytes = readFileSync(config.registryPath);
  if (bytes.length > 65536) throw Error('dsh-domicile registry exceeds limit');
  const tools = createTools({python:config.python,registry:JSON.parse(bytes.toString('utf8'))});
  for (const tool of tools) ctx.effect(() => ctx.tools.register(tool), `dsh-domicile: ${tool.name}`);
}
