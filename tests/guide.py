"""Order recipe and guidance regression on local and actual published origins.
All saved progress belongs to disposable test browser contexts.
"""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE=os.environ.get('BASE_URL','http://127.0.0.1:8765/').rstrip('/')+'/'
OUT=Path(os.environ.get('RESULT_DIR','test-results'))/'guide'
OUT.mkdir(parents=True,exist_ok=True)
checks=[]

def check(name,ok,detail=''):
    checks.append({'test':name,'result':'passed' if ok else 'failed','detail':detail})
    if not ok:raise AssertionError(name+': '+str(detail))

def state(page):
    # normalize() reorders discovery-map keys. Compare every saved value and
    # array position exactly, without treating object property order as progress.
    return json.dumps(page.evaluate('S'),sort_keys=True,ensure_ascii=False)

def fixture(page):
    page.evaluate("""()=>{
      closeRecipe(false);closeAlbum();guidedOrder=null;clearTimeout(hintTimer);
      const base=freshState();base.daily=S.daily;base.auto=false;base.autoStory=false;
      base.coins=1234;base.repair=3;base.story=4;base.warehouse={shell1:2,drink10:1};
      base.board=Array(36).fill(null);base.board[0]='gen_cafe';base.board[5]='gen_sea';
      ['fish1','fish1','shell1','shell1'].forEach((id,i)=>base.board[6+i]=id);
      base.orders=Array.from({length:8},(_,i)=>({title:'注文'+i,wants:[{id:i===0?'shell2':i===1?'drink3':'fish4',n:1}],coin:20,star:1,xp:1}));
      normalize(base);undoState=null;setView('game');saveNow();
    }""")

def tap(page,i):
    box=page.locator(f'.cell[data-i="{i}"]').bounding_box()
    page.touchscreen.tap(box['x']+box['width']/2,box['y']+box['height']/2)

def suite(browser_type):
    browser=browser_type.launch()
    ctx=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
    page=ctx.new_page();errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    prefix=browser_type.name+' '
    try:
        page.goto(BASE,wait_until='networkidle')
        page.wait_for_function("typeof RELEASE!=='undefined'&&RELEASE==='20260908-guide1'")
        fixture(page)
        before=state(page)
        chip=page.locator('#nextWants [data-recipe="shell2"]')
        check(prefix+'closest order selected from real ingredients',chip.count()==1)
        chip.click()
        check(prefix+'recipe dialog opens',page.locator('#recipeViewer.on').count()==1)
        check(prefix+'recipe has distinct predecessor and goal art',page.locator('#recipeFormula .itemArt').count()==3)
        check(prefix+'correct named merge rule','小さな貝を2つ' in page.locator('#recipeRule').inner_text())
        check(prefix+'correct generator','海辺のかご' in page.locator('#recipeSource').inner_text())
        check(prefix+'separate board and warehouse counts','盤面 2こ ・ 倉庫 2こ' in page.locator('#recipeSteps').inner_text())
        check(prefix+'recipe does not discover items or change saves',state(page)==before)
        check(prefix+'background blocked while reading',page.evaluate("document.querySelector('.app').inert&&document.getElementById('nav').inert"))
        page.locator('#recipeClose').press('Shift+Tab')
        check(prefix+'reverse tab stays in dialog',page.evaluate("document.activeElement.id==='recipeGuide'"))
        page.locator('#recipeGuide').press('Tab')
        check(prefix+'forward tab stays in dialog',page.evaluate("document.activeElement.id==='recipeClose'"))
        page.evaluate('renderGame()')
        page.locator('#recipeClose').press('Escape')
        check(prefix+'escape restores focus after board redraw',page.evaluate("document.activeElement.dataset.recipe==='shell2'&&!document.querySelector('.app').inert"))
        chip.click();page.locator('#recipeGuide').click()
        check(prefix+'goal and board agree',page.evaluate("view==='game'&&guidedOrder===S.orders[0]&&hintPair.length===2&&hintPair.every(i=>S.board[i]==='shell1')"))
        check(prefix+'hint only guides, without moving items',state(page)==before)
        page.locator('#nextWants [data-recipe="shell2"]').click();page.locator('#recipeAuto').click()
        check(prefix+'automatic target can be restored',page.evaluate('guidedOrder===null'))

        # Every order can be chosen; quick delivery must honor the displayed goal.
        page.locator('#nav [data-go="orders"]').click()
        page.locator('#orders [data-recipe="drink3"]').click();page.locator('#recipeGuide').click()
        check(prefix+'specific order can be targeted',page.evaluate("guidedOrder===S.orders[1]&&document.querySelector('#nextWants [data-recipe=drink3]')!==null"))
        check(prefix+'correct generator highlighted when missing materials',page.evaluate("hintPair.length===1&&S.board[hintPair[0]]==='gen_cafe'"))
        page.evaluate("S.board[12]='shell2';S.board[13]='drink3';normalize(S);guidedOrder=S.orders[1];renderGame()")
        before=state(page);page.locator('#quickTop').click()
        check(prefix+'deliver the displayed order, not another ready order',page.evaluate("S.board.includes('shell2')&&!S.board.includes('drink3')&&S.stats.delivered===1&&guidedOrder===null"))
        page.locator('#undo').click()
        check(prefix+'delivery undo restores the complete save',state(page)==before)

        fixture(page);before=state(page)
        page.locator('#nextWants [data-recipe="shell2"]').click();page.locator('#recipeWarehouse').click()
        check(prefix+'warehouse opens with relevant kind',page.evaluate("view==='warehouse'&&warehouseFilter==='shell'"))
        check(prefix+'warehouse navigation never withdraws or delivers',state(page)==before)
        check(prefix+'original stored artwork remains',page.locator('[data-stored-item="shell1"] .itemArt').count()==1)

        # Preserve a finished lower-level requirement while building a higher one.
        fixture(page)
        page.evaluate("""S.board=Array(36).fill(null);S.board[0]='gen_cafe';S.board[5]='gen_sea';
          ['drink2','drink2','drink1','drink1'].forEach((id,i)=>S.board[i+6]=id);
          S.orders[0]={title:'2種類の注文',wants:[{id:'drink2',n:1},{id:'drink3',n:1}],coin:30,star:1,xp:1};guidedOrder=S.orders[0];renderGame()""")
        page.locator('#hint').click()
        check(prefix+'protect exact items already required',page.evaluate("JSON.stringify(hintPair)==='[8,9]'"))
        tap(page,8);tap(page,9);page.locator('#hint').click()
        check(prefix+'follow-up hint reserves one finished item',page.evaluate("hintPair.length===2&&!hintPair.includes(6)&&hintPair.every(i=>S.board[i]==='drink2')"))
        pair=page.evaluate('hintPair');tap(page,pair[0]);tap(page,pair[1])
        check(prefix+'guided merges actually complete all requirements',page.evaluate("orderCan(S.orders[0])&&S.board[6]==='drink2'"))
        page.locator('#hint').click()
        check(prefix+'ready order suggests delivery instead of merging it away','お届け' in page.locator('#msg').inner_text())

        fixture(page)
        page.evaluate("S.orders[0].wants=[{id:'drink10',n:1}];guidedOrder=S.orders[0];renderGame()")
        for width,height in [(320,568),(390,844),(844,390),(1280,800)]:
            page.set_viewport_size({'width':width,'height':height})
            page.locator('#nextWants [data-recipe="drink10"]').click()
            check(prefix+f'{width}x{height} ten-level recipe',page.locator('#recipeSteps .recipeStep').count()==10)
            for selector in ('#recipeClose','#recipeGuide'):
                box=page.locator(selector).bounding_box()
                check(prefix+f'{width}x{height} {selector} visible and tappable',box['height']>=44 and box['x']>=0 and box['y']>=0 and box['x']+box['width']<=width+1 and box['y']+box['height']<=height+1,box)
            check(prefix+f'{width}x{height} no recipe overflow',page.locator('.recipePanel').evaluate('e=>e.scrollWidth<=e.clientWidth+1'))
            if width==390:page.screenshot(path=str(OUT/(browser_type.name+'-recipe.png')))
            page.locator('#recipeClose').click()
        page.set_viewport_size({'width':390,'height':844})
        fixture(page);page.emulate_media(reduced_motion='reduce');page.locator('#hint').click()
        check(prefix+'reduced motion keeps static useful hints',page.locator('.cell.hint').count()==2 and page.locator('.cell.hint').first.evaluate("e=>getComputedStyle(e).animationName==='none'"))
        page.screenshot(path=str(OUT/(browser_type.name+'-guided-board.png')))
        before=state(page)
        check(prefix+'invalid recipe rejected',page.evaluate("openRecipe('<script>',0)===false&&openRecipe('gen_cafe',0)===false&&openRecipe('shell2',999)===false"))
        check(prefix+'invalid recipe leaves state intact',state(page)==before)
        page.evaluate("guidedOrder=S.orders[0];saveNow()")
        page.reload(wait_until='networkidle');page.wait_for_function("typeof S!=='undefined'&&S!==null")
        check(prefix+'reload preserves inventory, story, repair and all progress',state(page)==before)
        check(prefix+'no guide schema added to old saves',page.evaluate("guidedOrder===null&&!Object.hasOwn(S,'guidedOrder')&&SAVE_KEY==='rin_harbor_save_v10'"))
        if browser_type.name=='chromium':
            page.wait_for_function('navigator.serviceWorker.controller!==null')
            ctx.set_offline(True)
            page.reload(wait_until='load');page.wait_for_function("typeof S!=='undefined'&&S!==null")
            page.locator('#startGame').click();page.locator('#nextWants [data-recipe="shell2"]').click()
            check(prefix+'recipe and art work after offline reload',page.locator('#recipeViewer.on .recipeStep .itemArt').count()==2)
            check(prefix+'offline guide preserves saved progress',state(page)==before)
        check(prefix+'no JavaScript errors',not errors,' | '.join(errors))
    finally:
        ctx.close();browser.close()

try:
    with sync_playwright() as p:
        for browser_type in (p.chromium,p.webkit):suite(browser_type)
finally:
    (OUT/'report.json').write_text(json.dumps({'base_url':BASE,'release':'20260908-guide1','checks':checks},ensure_ascii=False,indent=2))
    print('GUIDE:',sum(x['result']=='passed' for x in checks),'passed;',sum(x['result']=='failed' for x in checks),'failed')
