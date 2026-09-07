"""Test offline recovery by stopping the actual HTTP origin.

Playwright's WebKit set_offline() can abort the document before its service
worker gets a fetch event. Do not skip the offline assertions or catch a failed
navigation: remove the TCP origin instead, then perform a normal page reload.
The public-site suite still tests WebKit gameplay against BASE_URL; this one
uses the exact release files on an isolated localhost origin.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
import socket


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def test_origin_offline(browser, root, check, reload_page):
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(root)))
    server.daemon_threads = True
    port = server.server_port
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    context = browser.new_context(viewport={'width':390,'height':844}, is_mobile=True, has_touch=True)
    stopped = False
    label = 'webkit real-origin-outage '
    try:
        page = context.new_page()
        errors = []
        transport_errors = []
        def record_error(error):
            text = str(error)
            # WebKit emits this transport failure as a pageerror when the
            # deliberate uncached probe receives Response.error() from the SW.
            # Only this exact message AFTER confirmed origin shutdown is expected.
            # All JS exceptions and all errors while online remain test failures.
            if stopped and text == 'Response served by service worker is an error':
                transport_errors.append(text)
            else:
                errors.append(text)
        page.on('pageerror', record_error)
        page.goto(f'http://127.0.0.1:{port}/', wait_until='networkidle')
        page.wait_for_function("navigator.serviceWorker.controller!==null", timeout=60000)
        page.wait_for_function("document.getElementById('offlineStatus').textContent.includes('保存済み')||document.getElementById('offlineStatus').textContent.includes('新しい')", timeout=60000)
        page.evaluate("S.auto=false;S.autoStory=false;S.coins=2345;S.repair=5;saveNow()")
        keys = page.evaluate("async()=>{const c=await caches.open('rin-harbor-20260907-sea2');return (await c.keys()).map(r=>r.url)}")
        check(label+'app and art cached', len(keys)>=16)
        page.evaluate("caches.open('unrelated-app-sentinel')")
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)
        stopped = True
        try:
            connection = socket.create_connection(('127.0.0.1',port), timeout=1)
        except OSError:
            connection = None
        if connection:
            connection.close()
        check(label+'TCP origin unavailable', connection is None)
        check(label+'uncached fetch fails', page.evaluate("fetch('./__offline_probe__?t='+Date.now(),{cache:'no-store'}).then(()=>false,()=>true)"))
        reload_page(page)
        check(label+'new document retains progress', page.evaluate('S.coins===2345&&S.repair===5'))
        page.wait_for_function("document.getElementById('openingImage').naturalWidth>1000")
        check(label+'title art decoded', page.locator('#openingImage').evaluate('(e)=>e.complete&&e.naturalWidth>1000'))
        page.evaluate("setView('home')")
        page.wait_for_function("document.getElementById('homeShipImage').naturalWidth>1000")
        check(label+'harbor art decoded', page.locator('#homeShipImage').evaluate('(e)=>e.complete&&e.naturalWidth>1000'))
        for stage in range(6):
            page.evaluate('(n)=>openAlbum(n)', stage)
            page.wait_for_function("document.getElementById('viewerImg').complete&&document.getElementById('viewerImg').naturalWidth>1000")
            check(label+f'album scene {stage}', page.locator('#viewerImg').evaluate('(e)=>e.naturalWidth>1000'))
        check(label+'unrelated cache preserved', page.evaluate("caches.has('unrelated-app-sentinel')"))
        page.evaluate("closeAlbum();setView('game');S.coins=3456;saveNow()")
        reload_page(page)
        check(label+'second offline reload saves progress', page.evaluate('S.coins===3456&&S.repair===5'))
        check(label+'no JavaScript exceptions', not errors, errors)
        print(label+'expected transport errors: '+str(len(transport_errors)), flush=True)
    finally:
        context.close()
        if not stopped:
            server.shutdown()
            server.server_close()
            worker.join(timeout=5)
