'use strict';
const $ = id => document.getElementById(id);
const state = {titles:[],user:null,library:{},progress:{},tab:'home',genre:'All films'};
let toastTimer, playing = null, lastSaved = 0, authRegister = false, pendingAction = null;
const esc = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function api(path, method='GET', body, keepalive=false) {
  const r = await fetch('/api/'+path, {method, credentials:'same-origin', headers:{'Content-Type':'application/json'}, body:body===undefined?undefined:JSON.stringify(body), keepalive});
  const data = await r.json();
  if (!r.ok) {const e = new Error(data.error || 'Request failed'); e.status=r.status; throw e;}
  return data;
}
function notify(message) {$('toast').textContent=message; $('toast').hidden=false; clearTimeout(toastTimer); toastTimer=setTimeout(()=>$('toast').hidden=true,4500);}
function updateAccount() {$('account').textContent=state.user ? state.user+' · Sign out' : 'Sign in ↗'; $('list-count').textContent=Object.values(state.library).filter(Boolean).length;}
function showDialog(html, player=false) {closeDialog(); $('dialog').className=player?'player-dialog':''; $('dialog').innerHTML='<button class="close" aria-label="Close dialog">×</button>'+html; $('dialog').querySelector('.close').onclick=closeDialog; $('dialog').showModal(); document.body.classList.add('modal-open');}
function closeDialog() {
  const video=$('video');
  if(video && playing){persist(playing,video.ended?0:Math.floor(video.currentTime),true);video.pause();}
  playing=null; if($('dialog').open)$('dialog').close(); $('dialog').innerHTML=''; document.body.classList.remove('modal-open'); render();
}
function setTab(tab){state.tab=tab;state.genre='All films';render();if(tab!=='home')$('heading').scrollIntoView({behavior:'smooth',block:'start'});}
function render(){
  updateAccount();
  const q=$('search').value.trim().toLowerCase();
  $('hero').hidden=state.tab!=='home'||!!q;
  document.querySelectorAll('[data-tab]').forEach(b=>{b.classList.toggle('active',b.dataset.tab===state.tab);b.setAttribute('aria-current',b.dataset.tab===state.tab?'page':'false');});
  const names={home:'The collection',explore:'Explore all films',list:'My List',continue:'Continue watching'};
  $('heading').textContent=q?'Search results':names[state.tab];
  $('subtitle').textContent=state.tab==='list'?'Your stories, ready when you are.':state.tab==='continue'?'Pick up where the story left off.':'Six little reasons to press play.';
  const genres=['All films',...new Set(state.titles.map(t=>t.genre))];
  $('filters').innerHTML=genres.map(g=>`<button class="chip ${g===state.genre?'selected':''}" aria-pressed="${g===state.genre}">${esc(g)}</button>`).join('');
  $('filters').querySelectorAll('button').forEach(b=>b.onclick=()=>{state.genre=b.textContent;render();});
  let list=state.titles.filter(t=>(t.name+' '+t.genre+' '+t.description).toLowerCase().includes(q)&&(state.genre==='All films'||t.genre===state.genre));
  if(state.tab==='list')list=list.filter(t=>state.library[t.id]);
  if(state.tab==='continue')list=list.filter(t=>state.progress[t.id]>0);
  $('status').textContent=!state.user&&['list','continue'].includes(state.tab)?'Sign in to see your saved stories.':list.length?'':'No films here yet. Try another filter or add a film to your list.';
  $('cards').innerHTML=list.map(t=>`<article class="card"><div class="poster"><img src="${esc(t.poster)}" alt="${esc(t.name)} original landscape artwork" loading="lazy"><span class="poster-tag">${esc(t.genre.toUpperCase())}</span><button class="poster-play" data-play="${t.id}" aria-label="Play ${esc(t.name)}"><span class="play-circle">▶</span></button><span class="duration">${esc(t.duration)}</span></div><div class="card-info"><div><h3>${esc(t.name)}</h3><div class="card-meta">${t.year} &nbsp;·&nbsp; ${esc(t.genre)} &nbsp;·&nbsp; Short film</div></div><button class="save ${state.library[t.id]?'saved':''}" data-save="${t.id}" aria-label="${state.library[t.id]?'Remove':'Save'} ${esc(t.name)}" aria-pressed="${!!state.library[t.id]}">${state.library[t.id]?'✓':'+'}</button></div><p class="description">${esc(t.description)}</p>${state.progress[t.id]>0?`<p class="resume">↻ Resume from ${formatTime(state.progress[t.id])}</p>`:''}</article>`).join('');
  $('cards').querySelectorAll('[data-play]').forEach(b=>b.onclick=()=>play(b.dataset.play));
  $('cards').querySelectorAll('[data-save]').forEach(b=>b.onclick=()=>save(b.dataset.save,b));
}
const formatTime=s=>Math.floor(s/60)+':'+String(s%60).padStart(2,'0');
async function loadLibrary(){const data=await api('library');state.library=data.library;state.progress=data.progress;}
function auth(register=false, after=null){authRegister=register;if(after)pendingAction=after;
  showDialog(`<p class="eyebrow">WELCOME TO STREAMVAULT</p><h2>${register?'Your next story starts here.':'Good to see you.'}</h2><p class="muted">${register?'Create an account to save films and resume watching.':'Sign in to your personal collection.'}</p><form id="auth-form"><label for="username">Username</label><input id="username" name="username" autocomplete="username" required minlength="3" maxlength="32" pattern="[A-Za-z0-9_]+"><label for="password">Password</label><input id="password" name="password" type="password" autocomplete="${register?'new-password':'current-password'}" required minlength="8" maxlength="128"><p id="form-error" role="alert"></p><button class="button primary wide" type="submit">${register?'Create account':'Sign in'} ↗</button></form><button class="switch" id="auth-switch">${register?'Already a member? Sign in':'New here? Create an account'}</button>`);
  $('auth-switch').onclick=()=>auth(!authRegister);
  $('auth-form').onsubmit=async e=>{e.preventDefault();const button=e.target.querySelector('button');button.disabled=true;$('form-error').textContent='';try{const data={username:$('username').value,password:$('password').value};if(authRegister)await api('register','POST',data);state.user=(await api('login','POST',data)).user;await loadLibrary();closeDialog();render();notify('Welcome, '+state.user);const action=pendingAction;pendingAction=null;if(action)await action();}catch(err){if($('form-error'))$('form-error').textContent=err.message;}finally{button.disabled=false;}};
}
async function save(id,button){if(!state.user){auth(false,()=>save(id));return;}if(button)button.disabled=true;try{const saved=!state.library[id];await api('library','POST',{id,saved});state.library[id]=saved;render();notify(saved?'Added to My List':'Removed from My List');}catch(e){if(e.status===401){state.user=null;auth(false,()=>save(id));}else notify(e.message);}finally{if(button)button.disabled=false;}}
async function play(id){
  if(!state.user){auth(false,()=>play(id));return;}
  try{const data=await api('play/'+id);const title=state.titles.find(t=>t.id===id);
    showDialog(`<p class="eyebrow">NOW PLAYING</p><h2>${esc(title.name)}</h2><video id="video" controls playsinline preload="metadata"></video><p class="muted">${esc(title.description)}</p><p id="player-error" role="alert" class="muted"></p>`,true);
    playing=id;lastSaved=Date.now();const video=$('video');video.src=data.url;
    video.onloadedmetadata=()=>{if(state.progress[id])video.currentTime=Math.min(state.progress[id],Math.max(0,video.duration-1));video.play().catch(()=>{});};
    video.ontimeupdate=()=>{if(Date.now()-lastSaved>10000){lastSaved=Date.now();persist(id,Math.floor(video.currentTime));}};
    video.onpause=()=>{if(playing===id)persist(id,video.ended?0:Math.floor(video.currentTime));};
    video.onended=()=>persist(id,0);
    video.onerror=()=>{$('player-error').textContent='Playback could not start. Check the uploaded file uses MP4 with H.264 video and AAC audio, then reopen the film.';};
  }catch(e){if(e.status===401){state.user=null;auth(false,()=>play(id));}else notify(e.message);}
}
async function persist(id,seconds,keepalive=false){if(!state.user)return;state.progress[id]=seconds;try{await api('progress','POST',{id,seconds},keepalive);}catch(e){if(!keepalive)notify('Progress could not be saved. '+e.message);}}
$('account').onclick=()=>{if(!state.user){pendingAction=null;auth();return;}showDialog('<h2>See you next time.</h2><p class="muted">Your list and viewing progress will be waiting for you.</p><button id="signout" class="button primary wide">Sign out</button>');$('signout').onclick=async()=>{try{await api('logout','POST',{});state.user=null;state.library={};state.progress={};pendingAction=null;closeDialog();render();notify('Signed out');}catch(e){notify(e.message);}};};
$('dialog').addEventListener('cancel',e=>{e.preventDefault();pendingAction=null;closeDialog();});
document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>setTab(b.dataset.tab));
$('search').oninput=render;$('featured-play').onclick=()=>play('sintel');$('browse').onclick=()=>setTab('explore');
document.addEventListener('visibilitychange',()=>{const v=$('video');if(document.hidden&&v&&playing)persist(playing,v.ended?0:Math.floor(v.currentTime),true);});
(async()=>{try{state.titles=(await api('catalog')).titles;state.user=(await api('me')).user;if(state.user)await loadLibrary();render();}catch(e){$('status').textContent='Unable to load StreamVault. '+e.message;}})();
