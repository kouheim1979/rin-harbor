"""Variable boards and the real five-second entry gesture, in disposable contexts.
Called by smoke.py for both local and published Chromium/WebKit release gates.
Can also run directly with BROWSERS=chromium SYSTEM_CHROMIUM=1.
"""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright


def saved(page):
    return json.dumps(page.evaluate('S'), sort_keys=True, ensure_ascii=False)


def inventory(page):
    return page.evaluate("""()=>({board:S.board.filter(Boolean).sort(),warehouse:S.warehouse,
        coins:S.coins,stars:S.stars,xp:S.xp,level:S.level,story:S.story,repair:S.repair,
        stats:S.stats,book:S.book,orders:S.orders,daily:S.daily})""")


def fixture(page):
    page.evaluate("""()=>{
        closeGeneratorSecret(false);closeRecipe(false);closeAlbum();cancelDrag();
        clearTimeout(hintTimer);clearTimeout(comboTimer);guidedOrder=null;
        normalize({...freshState(),daily:S.daily,auto:false,autoStory:false,
            sound:false,haptics:false,warehouse:{fish6:2,toy7:1},coins:1234,repair:2});
        selected=null;hintPair=[];undoState=null;setView('game');saveNow();
    }""")


def open_menu(page):
    page.evaluate("openGeneratorSecret('gen_cafe',document.querySelector('.cell.gen'))")


def choose_size(page, side):
    open_menu(page)
    page.locator('#generatorBoardSize').select_option(str(side))
    page.locator('#generatorSecretSave').click()
    page.wait_for_function('(n)=>S.board.length===n && !generatorSecretViewer.classList.contains("on")', arg=side*side)
    page.wait_for_function('(side)=>getComputedStyle(board).gridTemplateColumns.split(" ").length===side', arg=side)


def run_board_size(browser, engine, url, check, output_dir):
    output_dir=Path(output_dir)/'board-size';output_dir.mkdir(parents=True,exist_ok=True)
    ctx=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,service_workers='allow')
    page=ctx.new_page();errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    def ok(name,condition,detail=''):
        check(engine+' board size: '+name,condition,detail)
    try:
        page.goto(url,wait_until='networkidle')
        page.wait_for_function("typeof S!=='undefined' && S!==null && typeof BUILD!=='undefined'")
        fixture(page)
        ok('legacy save remains 36 cells',page.evaluate('S.board.length===36 && boardSide()===6'))
        ok('five supported square boards',page.evaluate('JSON.stringify(BOARD_SIDES)')=='[4,5,6,7,8]')
        ok('secret hold remains exactly 5000 ms',page.evaluate('GENERATOR_SECRET_HOLD_MS===5000'))
        # Real pointer input, not a direct call to the hidden dialog.
        page.wait_for_function('board.clientWidth>100')
        gen=page.locator('.cell.gen').first
        b=gen.bounding_box();x=b['x']+b['width']/2;y=b['y']+b['height']/2
        page.mouse.move(x,y);before=saved(page);page.mouse.down()
        page.wait_for_timeout(4500)
        ok('hold has not fired at 4.5 seconds',page.locator('#generatorSecretViewer.on').count()==0)
        # Hint/combo timers can replace all board children during a hold.
        page.evaluate('renderGame()')
        page.wait_for_selector('#generatorSecretViewer.on',timeout=2000)
        page.mouse.up()
        ok('real five-second hold opens size selector',page.locator('#generatorBoardSize').is_visible())
        ok('long hold and release generate no item',saved(page)==before)
        ok('background inert during size selection',page.evaluate("document.querySelector('.app').inert&&nav.inert"))
        page.locator('#generatorSecretClose').press('Shift+Tab')
        ok('reverse tab trapped',page.evaluate("document.activeElement.id==='generatorSecretSave'"))
        page.locator('#generatorSecretSave').press('Tab')
        ok('forward tab trapped',page.evaluate("document.activeElement.id==='generatorSecretClose'"))
        page.locator('#generatorBoardSize').select_option('8')
        page.locator('#generatorSecretClose').click()
        ok('closing without save preserves board',saved(page)==before)
        # Navigation must cancel a pending secret timer as well as dragging.
        b=gen.bounding_box();page.mouse.move(b['x']+b['width']/2,b['y']+b['height']/2);page.mouse.down()
        page.evaluate("setView('home')");page.mouse.up()
        ok('navigation cancels unfinished hold',page.evaluate("generatorSecretHold===null&&drag===null"))
        fixture(page)
        seed=saved(page);items=inventory(page)
        choose_size(page,8)
        ok('64 real cells rendered',page.locator('#board .cell').count()==64)
        ok('expansion preserves all inventory and progress',inventory(page)==items)
        ok('expansion preserves existing indices',page.evaluate('S.board.slice(0,36)')==json.loads(seed)['board'])
        ok('first resize keeps a recovery backup',page.evaluate("JSON.parse(localStorage.getItem('rin_harbor_before_board_resize_v1')).board.length===36"))
        ok('accessible label follows dimensions','8行8列' in page.locator('#board').get_attribute('aria-label'))
        open_menu(page)
        ok('every menu shows current size',page.locator('#generatorBoardSize').input_value()=='8')
        page.locator('#generatorSecretClose').click()
        page.locator('#undo').click()
        ok('undo restores exact pre-resize save',saved(page)==seed)
        ok('undo restores rendered 36-cell grid',page.locator('#board .cell').count()==36)
        # No fixed upper bound at index 35: exercise actual last cells.
        choose_size(page,8)
        page.evaluate("S.board[62]='drink1';S.board[63]='drink1';S.book.drink1=1;renderGame();saveNow()")
        page.locator('.cell[data-i="62"]').tap();page.locator('.cell[data-i="63"]').tap()
        ok('merge in extended cells',page.evaluate("S.board[62]===null&&S.board[63]==='drink2'&&S.stats.merges===1"))
        page.locator('.cell[data-i="63"]').tap();page.locator('.cell[data-i="61"]').tap()
        ok('move in extended cells',page.evaluate("S.board[63]===null&&S.board[61]==='drink2'"))
        page.locator('#store').click()
        ok('deposit from extended cell',page.evaluate("S.board[61]===null&&S.warehouse.drink2===1"))
        page.evaluate("S.board=S.board.map((v,i)=>i===63?null:v||'shell10');setView('warehouse')")
        page.locator('[data-take="drink2"]').click()
        ok('warehouse uses last free cell',page.evaluate("S.board[63]==='drink2'&&!S.warehouse.drink2"))
        page.evaluate("S.board[60]=null;setView('game')")
        expected=inventory(page);page.locator('#sort').click()
        ok('sorting preserves every item beyond 35',inventory(page)==expected)
        page.evaluate("S.orders[0]={title:'端の注文',wants:[{id:'drink2',n:1}],coin:20,star:1,xp:1};guidedOrder=S.orders[0];renderGame()")
        page.locator('#quickTop').click()
        ok('delivery uses extended inventory',page.evaluate("!S.board.includes('drink2')&&S.stats.delivered===1"))
        before=saved(page);page.evaluate('cellTap(64);moveOrMerge(64,0);moveOrMerge(0,64)')
        ok('out-of-range input is inert',saved(page)==before)
        fixture(page);choose_size(page,8)
        page.locator('.cell[data-i="56"]').focus();page.keyboard.press('ArrowDown')
        ok('bottom edge retains keyboard focus',page.evaluate("document.activeElement.dataset.i==='56'"))
        page.keyboard.press('ArrowUp')
        ok('keyboard moves by eight columns',page.evaluate("document.activeElement.dataset.i==='48'"))
        page.locator('.cell[data-i="7"]').focus();page.keyboard.press('ArrowRight')
        ok('keyboard does not wrap row edge',page.evaluate("document.activeElement.dataset.i==='7'"))
        page.locator('.cell[data-i="63"]').focus();page.keyboard.press('ArrowLeft')
        ok('last row is keyboard reachable',page.evaluate("document.activeElement.dataset.i==='62'"))
        # Shrink safely, including an unlocked generator, without touching
        # warehouse capacity or rewards.
        page.evaluate("S.story=2;S.board[63]='gen_gift';S.board[62]='toy10';S.board[60]='drink2';S.book.gen_gift=1;S.book.toy10=1;S.book.drink2=1;S.stats.bestLevel=10;renderGame();saveNow()")
        before=saved(page);items=inventory(page)
        choose_size(page,4)
        ok('shrink renders 16 cells',page.locator('#board .cell').count()==16)
        ok('shrink preserves high-level items and generators',inventory(page)==items)
        ok('no truncated indices after shrink',page.evaluate("S.board.length===16&&S.board.includes('gen_gift')&&S.board.includes('toy10')"))
        page.locator('#undo').click()
        ok('shrink undo restores exact positions and save',saved(page)==before)
        page.evaluate("S.board=S.board.map(v=>v||'shell10');renderGame();saveNow()")
        before=saved(page);old_undo=page.evaluate('undoState');old_secret=page.evaluate('JSON.stringify(generatorSecret)')
        open_menu(page);page.locator('#generatorBoardSize').select_option('4')
        ok('overfull shrink disables save',page.locator('#generatorSecretSave').is_disabled())
        ok('overfull shrink explains required space','48こ分' in page.locator('#generatorBoardNote').inner_text())
        page.evaluate('applyGeneratorSecret()')
        ok('overfull shrink leaves save and undo untouched',saved(page)==before and page.evaluate('undoState')==old_undo)
        ok('rejected shrink does not save generator draft',page.evaluate('JSON.stringify(generatorSecret)')==old_secret)
        ok('rejected shrink keeps dialog open',page.locator('#generatorSecretViewer.on').count()==1)
        page.locator('#generatorSecretClose').click()
        for invalid in (0,3,9,6.5,'8',None):
            ok('invalid side rejected '+repr(invalid),not page.evaluate('(side)=>resizeBoard(side)',invalid) and saved(page)==before)
        # Actual localStorage and the user-facing JSON backup prompt, all sizes.
        for side in (4,5,6,7,8):
            fixture(page);choose_size(page,side)
            page.evaluate("S.board[S.board.length-1]='toy7';S.book.toy7=1;S.stats.bestLevel=Math.max(S.stats.bestLevel,7);saveNow()")
            before=saved(page)
            page.reload(wait_until='networkidle');page.wait_for_function("typeof S!=='undefined' && S!==null")
            ok(str(side)+'x'+str(side)+' reload preserves full save',saved(page)==before)
            page.evaluate("setView('book')")
            def dialog(d):d.accept(before if d.type=='prompt' else None)
            page.on('dialog',dialog);page.locator('#importSave').click();page.remove_listener('dialog',dialog)
            ok(str(side)+'x'+str(side)+' JSON import round trip',saved(page)==before)
        # Legacy 36-cell backup while 64 cells are active.
        legacy=json.loads(seed)
        def import_legacy(d):d.accept(json.dumps(legacy,ensure_ascii=False) if d.type=='prompt' else None)
        page.on('dialog',import_legacy);page.locator('#importSave').click();page.remove_listener('dialog',import_legacy)
        ok('legacy backup imports into expanded game',saved(page)==seed)
        page.evaluate('undo()')
        ok('backup import undo restores expanded game',page.evaluate('S.board.length===64'))
        invalid=json.loads(saved(page));invalid['board'].append(None)
        before=saved(page)
        def import_invalid(d):d.accept(json.dumps(invalid) if d.type=='prompt' else None)
        page.on('dialog',import_invalid);page.locator('#importSave').click();page.remove_listener('dialog',import_invalid)
        ok('malformed board import rejected without progress loss',saved(page)==before)
        fixture(page);choose_size(page,8)
        page.on('dialog',lambda d:d.accept());page.evaluate('resetGame()')
        ok('new game returns to legacy 36-cell default',page.evaluate('S.board.length===36&&view==="opening"'))
        for width,height in ((320,568),(375,667),(390,844),(430,932),(844,390),(1280,800)):
            page.set_viewport_size({'width':width,'height':height});fixture(page)
            for side in (4,5,6,7,8):
                choose_size(page,side);page.wait_for_timeout(60)
                d=page.locator('#board').evaluate("""e=>{const r=e.getBoundingClientRect(),s=document.getElementById('screenGame');return {
                    rows:getComputedStyle(e).gridTemplateRows.split(' ').length,cols:getComputedStyle(e).gridTemplateColumns.split(' ').length,
                    clipped:s.scrollWidth>s.clientWidth+1||document.documentElement.scrollWidth>innerWidth+1,
                    bottom:r.bottom,right:r.right,left:r.left,top:r.top,
                    inside:[...e.children].every(c=>{const b=c.getBoundingClientRect();return b.width>0&&b.height>0&&b.left>=r.left-1&&b.top>=r.top-1&&b.right<=r.right+1&&b.bottom<=r.bottom+1})}}""")
                ok(f'{width}x{height} {side}x{side} fits with real rows and columns',d['rows']==side and d['cols']==side and not d['clipped'] and d['inside'] and d['right']<=width+1 and d['bottom']<=height+1,d)
            open_menu(page)
            for sel in ('#generatorSecretClose','#generatorSecretSave','#generatorSecretReset'):
                b=page.locator(sel).bounding_box()
                ok(f'{width}x{height} {sel} reachable',b is not None and b['height']>=44 and b['x']>=0 and b['y']>=0 and b['x']+b['width']<=width+1 and b['y']+b['height']<=height+1,b)
            page.locator('#generatorSecretClose').click()
            if width==390:page.screenshot(path=str(output_dir/(engine+'-64-cells.png')))
        page.set_viewport_size({'width':390,'height':844});fixture(page);choose_size(page,8)
        open_menu(page)
        page.locator('#generatorSecretOptions label').filter(has=page.locator('input[value="drink1"]')).click()
        page.locator('#generatorSecretSave').click();before=saved(page)
        page.wait_for_function('navigator.serviceWorker.controller!==null')
        ok('current version has cached assets',page.evaluate("""async()=>{const c=await caches.open('rin-harbor-'+BUILD);return !!(await c.match(document.querySelector('script[src^="game.js"]').src))&&!!(await c.match(document.querySelector('link[rel="stylesheet"]').href))}"""))
        if engine=='chromium':
            ctx.set_offline(True);page.reload(wait_until='load');page.wait_for_function("typeof S!=='undefined' && S!==null")
            ok('64 cells and full save survive offline restart',saved(page)==before)
            ok('five second picker and selection survive offline restart',page.evaluate("GENERATOR_SECRET_HOLD_MS===5000&&generatorPool('gen_cafe').length===1&&generatorPool('gen_cafe')[0][0]==='drink1'"))
            page.locator('#startGame').click()
            ok('offline 64-cell board and eight-order rail',page.locator('#board .cell').count()==64 and page.locator('#nextWants .gameOrderMini').count()==8)
        ok('no JavaScript errors',not errors,errors)
    except Exception:
        try:page.screenshot(path=str(output_dir/(engine+'-failure.png')),timeout=5000)
        except Exception:pass
        raise
    finally:ctx.close()


if __name__=='__main__':
    checks=[]
    def check(name,condition,detail=''):
        checks.append({'test':name,'result':'passed' if condition else 'failed','detail':detail})
        if not condition:raise AssertionError(f'{name}: {detail}')
    out=Path(os.environ.get('RESULT_DIR','test-results'));out.mkdir(parents=True,exist_ok=True)
    try:
        with sync_playwright() as p:
            for engine in os.environ.get('BROWSERS','chromium,webkit').split(','):
                opts={'headless':True}
                if engine=='chromium' and os.environ.get('SYSTEM_CHROMIUM')=='1':
                    opts.update(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
                browser=getattr(p,engine).launch(**opts)
                try:run_board_size(browser,engine,os.environ.get('BASE_URL','http://127.0.0.1:8765/'),check,out)
                finally:browser.close()
    finally:
        (out/'board-size-report.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
        print('BOARD SIZE:',sum(c['result']=='passed' for c in checks),'passed;',sum(c['result']=='failed' for c in checks),'failed')
