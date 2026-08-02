#!/usr/bin/env python3
"""Fail-closed, candidate-bound, non-force Git publication helper (stdlib only)."""
from __future__ import annotations
import argparse, hashlib, json, os, re, stat, subprocess, time, tomllib
from pathlib import Path
from urllib.parse import urlsplit

HEX=re.compile(r"[0-9a-f]{64}\Z"); OID=re.compile(r"[0-9a-f]{40,64}\Z")
PK={"schema_version","auto_push_default","doctor_on_start","allow_force_push","require_reviewer_ship","require_passed_checks","require_secret_scan","require_attribution","require_existing_upstream","require_fresh_veto_evidence"}; TRUE=PK-{"schema_version","allow_force_push"}
AK={"schema_version","candidate_oid","base_oid","tree_oid","parent_oid","branch","remote","ref","remote_url_sha256","patch_sha256","evidence_sha256","policy_sha256","project_policy_sha256","paths_sha256","created_at","expires_at","attempt"}
RK={"schema_version","state","candidate_oid","ref","remote_url_sha256","authorization_sha256","attempt","completed_at"}
def refuse(_=""): raise SystemExit(1)
def canon(x): return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def sha(b): return hashlib.sha256(b).hexdigest()
def git(repo,*args,raw=False,soft=False):
 p=subprocess.run(["git","-C",str(repo),*args],capture_output=True)
 if p.returncode and not soft: refuse()
 return p if soft else (p.stdout if raw else p.stdout.decode("utf-8","strict").strip())
def read_file(p,mode=None):
 try:
  fd=os.open(p,os.O_RDONLY|getattr(os,"O_NOFOLLOW",0)); st=os.fstat(fd)
  if not stat.S_ISREG(st.st_mode) or mode is not None and stat.S_IMODE(st.st_mode)!=mode: raise OSError
  with os.fdopen(fd,"rb") as f:return f.read()
 except OSError: refuse()
def load(p,mode=None):
 try:return json.loads(read_file(p,mode))
 except Exception:refuse()
def exact_state(p,expected):
 x=load(p,0o600)
 if not isinstance(x,dict) or set(x)!=set(expected) or any(x[k]!=v for k,v in expected.items() if k!="completed_at") or "completed_at" in expected and (not isinstance(x["completed_at"],int) or isinstance(x["completed_at"],bool)):refuse()
 return x
def mkdir(p):
 if p.exists() and (p.is_symlink() or not p.is_dir()):refuse()
 p.mkdir(parents=True,exist_ok=True,mode=0o700);os.chmod(p,0o700);return p
def exact_dir(p):
 try:st=p.lstat()
 except OSError:refuse()
 if p.is_symlink() or not stat.S_ISDIR(st.st_mode) or stat.S_IMODE(st.st_mode)!=0o700:refuse()
 return p
def write_new(p,b):
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,"O_NOFOLLOW",0),0o600)
 try:
  while b:n=os.write(fd,b);b=b[n:]
  os.fsync(fd)
 finally:os.close(fd)
 dfd=os.open(p.parent,os.O_RDONLY)
 try:os.fsync(dfd)
 finally:os.close(dfd)
def common(repo):
 p=Path(git(repo,"rev-parse","--git-common-dir"));return (p if p.is_absolute() else repo/p).resolve()
def policy(p,optional=False):
 if optional and not os.path.lexists(p):return None
 b=read_file(p,0o600)
 try:x=tomllib.loads(b.decode())
 except Exception:refuse()
 if set(x)!=PK or x.get("schema_version")!=1 or x.get("allow_force_push") is not False or any(x.get(k) is not True for k in TRUE):refuse()
 return sha(b)
def valid_remote_name(value):
 return isinstance(value,str) and bool(re.fullmatch(r"[A-Za-z0-9._/-]+",value)) and value!="." and not value.startswith("-") and ".." not in value and not value.endswith("/")
def push_endpoint(repo,remote,soft=False):
 p=git(repo,"remote","get-url","--push","--all",remote,raw=True,soft=True)
 if p.returncode:
  if soft:return None
  refuse()
 try:value=p.stdout.decode("utf-8","strict")
 except UnicodeDecodeError:
  if soft:return None
  refuse()
 lines=value.splitlines()
 endpoint=lines[0] if len(lines)==1 else ""
 try:parsed=urlsplit(endpoint) if endpoint else None
 except ValueError:
  if soft:return None
  refuse()
 credential_http=bool(parsed and parsed.scheme.lower() in ("http","https") and (parsed.username is not None or parsed.password is not None))
 if len(lines)!=1 or not endpoint or endpoint.startswith("-") or value not in (endpoint,endpoint+"\n") or any(ord(c)<32 or ord(c)==127 for c in endpoint) or credential_http:
  if soft:return None
  refuse()
 return endpoint
def remote_oid(repo,endpoint,ref,soft=False):
 p=git(repo,"ls-remote","--refs",endpoint,ref,soft=True)
 if p.returncode:return "UNAVAILABLE" if soft else refuse()
 lines=p.stdout.splitlines()
 if not lines:return None
 try:o,r=lines[0].split(b"\t");o=o.decode("ascii");r=r.decode("ascii")
 except Exception:refuse()
 if len(lines)!=1 or r!=ref or not OID.fullmatch(o):refuse()
 return o
def sensitive(path):
 parts=path.lower().split("/");n=parts[-1];exact={".git",".agent-work","__pycache__",".pytest_cache",".mypy_cache","memory","policy.toml","push-authorizations","push-journal","push-receipts","credentials","secrets"}
 return any(x in exact for x in parts) or n.startswith(".env") or any(x in n for x in ("secret","credential","token","private_key")) or Path(n).suffix in {".pem",".key",".p12",".pfx",".crt",".cer"}
def evidence(p,head,patch,paths,allow_stale_veto=False):
 b=read_file(p)
 try:e=json.loads(b)
 except Exception:refuse()
 keys={"schema_version","candidate_oid","patch_digest","checks","secret_scan","attribution","qa","reviewer","fresh_veto"}
 if set(e)!=keys or e["schema_version"]!=1 or e["candidate_oid"]!=head or e["patch_digest"]!=patch:refuse()
 hx=lambda x:isinstance(x,str) and bool(HEX.fullmatch(x))
 c=e["checks"]
 if not isinstance(c,list) or not c or any(not isinstance(z,dict) or set(z)!={"name","status","digest"} or not isinstance(z["name"],str) or not z["name"] or z["status"]!="passed" or not hx(z["digest"]) for z in c):refuse()
 s=e["secret_scan"]; pd=sha(canon(paths))
 if not isinstance(s,dict) or set(s)!={"status","candidate_oid","patch_digest","paths_sha256","digest"} or s["status"]!="passed" or s["candidate_oid"]!=head or s["patch_digest"]!=patch or s["paths_sha256"]!=pd or not hx(s["digest"]):refuse()
 a=e["attribution"]
 if not isinstance(a,dict) or set(a)!={"candidate_oid","patch_digest","paths","paths_sha256","digest"} or a["candidate_oid"]!=head or a["patch_digest"]!=patch or a["paths"]!=paths or a["paths_sha256"]!=pd or not hx(a["digest"]):refuse()
 for k,v in (("qa","pass"),("reviewer","ship")):
  z=e[k]; req={"verdict","candidate_oid","patch_digest","digest"}|({"independent"} if k=="reviewer" else set())
  if not isinstance(z,dict) or set(z)!=req or z["verdict"]!=v or z["candidate_oid"]!=head or z["patch_digest"]!=patch or not hx(z["digest"]) or k=="reviewer" and z["independent"] is not True:refuse()
 v=e["fresh_veto"];now=int(time.time())
 if not isinstance(v,dict) or set(v)!={"status","candidate_oid","patch_digest","checked_at","digest"} or v["status"]!="clear" or v["candidate_oid"]!=head or v["patch_digest"]!=patch or not hx(v["digest"]) or not isinstance(v["checked_at"],int) or v["checked_at"]>now or not allow_stale_veto and now-v["checked_at"]>900:refuse()
 return sha(b)
def validate(repo,wp,ep,require_remote_base=True,base_override=None,recovery=False):
 if git(repo,"status","--porcelain=v1","-z",raw=True):refuse()
 branch=git(repo,"symbolic-ref","--short","HEAD");remote=git(repo,"config","--get",f"branch.{branch}.remote");ref=git(repo,"config","--get",f"branch.{branch}.merge")
 if not valid_remote_name(remote) or not re.fullmatch(r"refs/heads/[A-Za-z0-9._/-]+",ref or "") or ".." in ref or ref.endswith("/"):refuse()
 tracking=git(repo,"rev-parse","--symbolic-full-name","@{upstream}")
 if tracking!=f"refs/remotes/{remote}/{ref.removeprefix('refs/heads/')}":refuse()
 head=git(repo,"rev-parse","HEAD");tracking_oid=git(repo,"rev-parse","@{upstream}");base=base_override or tracking_oid
 if base_override is not None and tracking_oid not in (base_override,head):refuse()
 if git(repo,"rev-list","--count",f"{base}..{head}")!="1" or git(repo,"rev-list","--count",f"{head}..{base}")!="0" or git(repo,"diff","--check",f"{base}..{head}",soft=True).returncode:refuse()
 endpoint=push_endpoint(repo,remote)
 if require_remote_base and remote_oid(repo,endpoint,ref)!=base:refuse()
 raw=git(repo,"diff","--name-only","-z",f"{base}..{head}",raw=True)
 if not raw.endswith(b"\0"):refuse()
 try:paths=raw[:-1].decode("utf-8","strict").split("\0")
 except Exception:refuse()
 if not paths or any(not x or x.startswith("/") or ".." in Path(x).parts or sensitive(x) for x in paths):refuse()
 patch=sha(git(repo,"diff","--binary",f"{base}..{head}",raw=True));root=common(repo)
 return {"schema_version":1,"candidate_oid":head,"base_oid":base,"tree_oid":git(repo,"rev-parse",head+"^{tree}"),"parent_oid":git(repo,"rev-parse",head+"^"),"branch":git(repo,"symbolic-ref","--short","HEAD"),"remote":remote,"ref":ref,"remote_url_sha256":sha(endpoint.encode()),"patch_sha256":patch,"evidence_sha256":evidence(ep,head,patch,paths,recovery),"policy_sha256":policy(wp),"project_policy_sha256":policy(root/"agent/policy.toml",True),"paths_sha256":sha(canon(paths))}
def receipt(a,h,state):return {"schema_version":1,"state":state,"candidate_oid":a["candidate_oid"],"ref":a["ref"],"remote_url_sha256":a["remote_url_sha256"],"authorization_sha256":h,"attempt":a["attempt"],"completed_at":int(time.time())}
def ensure_receipt(p,a,h,state):
 expected=receipt(a,h,state)
 if p.exists() or os.path.lexists(p):exact_state(p,expected)
 else:write_new(p,canon(expected))
def reconcile(repo,a,h,ds,captured_endpoint=None):
 endpoint=captured_endpoint if captured_endpoint is not None else push_endpoint(repo,a["remote"],True)
 o="UNAVAILABLE" if endpoint is None or sha(endpoint.encode())!=a["remote_url_sha256"] else remote_oid(repo,endpoint,a["ref"],True)
 if o==a["candidate_oid"]:
  p=ds["push-receipts"]/(h+".json")
  ensure_receipt(p,a,h,"success")
  return "success"
 if o==a["base_oid"]:
  p=ds["push-receipts"]/(h+".absent.json")
  ensure_receipt(p,a,h,"absent")
  return "absent"
 p=ds["push-receipts"]/(a["candidate_oid"]+".unknown.json")
 ensure_receipt(p,a,h,"unknown")
 return "unknown"
def parse_auth(path,auth_dir,provided_sha=None,allow_expired=False):
 if not path.is_absolute() or path.parent!=auth_dir or path.is_symlink() or ".." in path.parts:refuse()
 b=read_file(path,0o600);h=sha(b)
 if provided_sha is not None and provided_sha!=h:refuse()
 try:a=json.loads(b)
 except Exception:refuse()
 digests=("remote_url_sha256","patch_sha256","evidence_sha256","policy_sha256","paths_sha256")
 ints=("created_at","expires_at","attempt","schema_version")
 if not isinstance(a,dict) or set(a)!=AK or any(not isinstance(a[k],int) or isinstance(a[k],bool) for k in ints):refuse()
 if a["schema_version"]!=1 or a["attempt"] not in (1,2) or a["expires_at"]-a["created_at"]!=900 or a["created_at"]>int(time.time()) or not allow_expired and a["expires_at"]<int(time.time()):refuse()
 if any(not isinstance(a[k],str) or not OID.fullmatch(a[k]) for k in ("candidate_oid","base_oid","tree_oid","parent_oid")) or any(not isinstance(a[k],str) or not HEX.fullmatch(a[k]) for k in digests):refuse()
 if a["project_policy_sha256"] is not None and (not isinstance(a["project_policy_sha256"],str) or not HEX.fullmatch(a["project_policy_sha256"])):refuse()
 if not isinstance(a["branch"],str) or not re.fullmatch(r"[A-Za-z0-9._/-]+",a["branch"]) or ".." in a["branch"] or not valid_remote_name(a["remote"]) or not isinstance(a["ref"],str) or not re.fullmatch(r"refs/heads/[A-Za-z0-9._/-]+",a["ref"]) or ".." in a["ref"]:refuse()
 if path.name!=f"{a['candidate_oid']}-{a['attempt']}-{h}.json":refuse()
 return a,b,h
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);sp=p.add_subparsers(dest="cmd",required=True)
 for name in ("check","execute"):
  q=sp.add_parser(name,allow_abbrev=False)
  for x in ("repo","policy","evidence"):q.add_argument("--"+x,required=True)
  if name=="execute":q.add_argument("--authorization",required=True);q.add_argument("--authorization-sha256",required=True)
 n=p.parse_args();repo=Path(n.repo).resolve();root=common(repo)
 if n.cmd=="check":
  cur=validate(repo,Path(n.policy),Path(n.evidence))
  state=mkdir(root/"agent");ds={x:mkdir(state/x) for x in ("push-authorizations","push-journal","push-receipts")}
  if list(ds["push-receipts"].glob("*.unknown.json")):refuse()
  prior=list(ds["push-authorizations"].glob(cur["candidate_oid"]+"-*.json"))
  if not prior:attempt=1
  elif len(prior)==1:
   old,_,old_h=parse_auth(prior[0],ds["push-authorizations"],allow_expired=True)
   if old["attempt"]!=1:refuse()
   exact_state(ds["push-journal"]/(old_h+".json"),{"schema_version":1,"state":"started","authorization_sha256":old_h,"attempt":1})
   exact_state(ds["push-receipts"]/(old_h+".absent.json"),receipt(old,old_h,"absent"))
   attempt=2
  else:refuse()
  now=int(time.time());a=cur|{"created_at":now,"expires_at":now+900,"attempt":attempt};b=canon(a);h=sha(b);path=ds["push-authorizations"]/(f"{a['candidate_oid']}-{attempt}-{h}.json");write_new(path,b);print(canon({"authorization":str(path),"sha256":h,"attempt":attempt}).decode());return
 state=exact_dir(root/"agent");ds={x:exact_dir(state/x) for x in ("push-authorizations","push-journal","push-receipts")}
 if list(ds["push-receipts"].glob("*.unknown.json")):refuse()
 ap=Path(n.authorization);a,b,h=parse_auth(ap,ds["push-authorizations"],n.authorization_sha256,True)
 rp=ds["push-receipts"]/(h+".json")
 if rp.exists() or os.path.lexists(rp):
  exact_state(rp,receipt(a,h,"success"));cur=validate(repo,Path(n.policy),Path(n.evidence),False,a["base_oid"],True)
  endpoint=push_endpoint(repo,a["remote"])
  if any(a.get(k)!=v for k,v in cur.items()) or sha(endpoint.encode())!=a["remote_url_sha256"] or remote_oid(repo,endpoint,a["ref"])!=a["candidate_oid"]:refuse()
  print(canon({"status":"success","idempotent":True}).decode());return
 jp=ds["push-journal"]/(h+".json")
 if jp.exists() or os.path.lexists(jp):
  exact_state(jp,{"schema_version":1,"state":"started","authorization_sha256":h,"attempt":a["attempt"]});endpoint=push_endpoint(repo,a["remote"],True)
  if endpoint is None or sha(endpoint.encode())!=a["remote_url_sha256"]:reconcile(repo,a,h,ds);refuse()
  cur=validate(repo,Path(n.policy),Path(n.evidence),False,a["base_oid"],True)
  if any(a.get(k)!=v for k,v in cur.items()):refuse()
  if reconcile(repo,a,h,ds)=="success":print(canon({"status":"success","idempotent":True}).decode());return
  refuse()
 cur=validate(repo,Path(n.policy),Path(n.evidence))
 if a["expires_at"]<int(time.time()):refuse()
 if any(a.get(k)!=v for k,v in cur.items()):refuse()
 if (ds["push-receipts"]/(h+".absent.json")).exists():refuse()
 captured=push_endpoint(repo,a["remote"])
 if sha(captured.encode())!=a["remote_url_sha256"] or remote_oid(repo,captured,a["ref"])!=a["base_oid"]:refuse()
 write_new(jp,canon({"schema_version":1,"state":"started","authorization_sha256":h,"attempt":a["attempt"]}))
 subprocess.run(["git","-C",str(repo),"push","--",captured,f"{a['candidate_oid']}:{a['ref']}"],capture_output=True)
 if reconcile(repo,a,h,ds,captured)=="success":print(canon({"status":"success","idempotent":False}).decode());return
 refuse()
if __name__=="__main__":main()
