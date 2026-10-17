"""Temporary QA-only loopback HTTP relay over Docker exec stdio (no Docker ports).
No external URL, host file mount, ROS endpoint or device is exposed to the container.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import base64,json,subprocess,sys,threading
exec_lock=threading.Lock()
asset_cache={}
asset_paths={"/","/p0.js","/p1.js","/app.js","/styles.css","/favicon.svg"}
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):self.forward()
 def do_POST(self):self.forward()
 def log_message(self,*args):pass
 def forward(self):
  if self.headers.get('Host') not in ('127.0.0.1:8773','localhost:8773'):
   self.send_error(403);return
  origin=self.headers.get('Origin')
  if origin and origin not in ('http://127.0.0.1:8773','http://localhost:8773'):
   self.send_error(403);return
  length=int(self.headers.get('Content-Length','0'))
  if not 0<=length<=8192:self.send_error(413);return
  body=self.rfile.read(length)
  request=dict(method=self.command,path=self.path,body=base64.b64encode(body).decode(),content_type=self.headers.get('Content-Type'))
  code='''import base64,http.client,json,sys
r=json.load(sys.stdin); c=http.client.HTTPConnection("127.0.0.1",8769,timeout=3)
h={"Content-Type":r["content_type"]} if r["content_type"] else {}
c.request(r["method"],r["path"],body=base64.b64decode(r["body"]),headers=h)
x=c.getresponse();print(json.dumps({"status":x.status,"headers":x.getheaders(),"body":base64.b64encode(x.read()).decode()}));c.close()
'''
  try:
   with exec_lock:
    reply=asset_cache.get(self.path) if self.command=='GET' else None
    if reply is None:
     run=subprocess.run(['/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe','exec','-i','mtc-webui-p1-20261013','python3','-c',code],input=json.dumps(request),capture_output=True,text=True,timeout=5)
     if run.returncode:raise RuntimeError(run.stderr)
     reply=json.loads(run.stdout)
     if self.command=='GET' and self.path in asset_paths and reply['status']==200:asset_cache[self.path]=reply
   self.send_response(reply['status'])
   for name,value in reply['headers']:
    if name.lower() not in ('server','date','connection'):self.send_header(name,value)
   self.end_headers();self.wfile.write(base64.b64decode(reply['body']))
  except Exception as error:
   print(type(error).__name__, str(error), flush=True)
   self.send_error(502,'Isolated UI unavailable')
if __name__=='__main__':
 with ThreadingHTTPServer(('127.0.0.1',8773),Handler) as server:
  print('QA relay: http://127.0.0.1:8773 -> docker exec stdio -> container loopback:8769',flush=True)
  try:server.serve_forever()
  except KeyboardInterrupt:pass
