try{(function(){
if(self.__acpUI)return;self.__acpUI=true;
var s=document.createElement("style");
s.textContent=[
".acp-file-search{padding:4px 8px}",
".acp-file-search input{width:100%;font-size:13px;padding:4px 8px;border-radius:4px;outline:none}",
".acp-breadcrumb{display:flex;gap:2px;padding:4px 8px;font-size:12px;opacity:.7;flex-wrap:wrap}",
".acp-breadcrumb span{padding:2px 4px}",
".acp-error-toast{position:fixed;bottom:16px;left:16px;right:16px;background:#dc2626;color:#fff;padding:12px 16px;border-radius:8px;font-size:13px;z-index:9999}",
".acp-search-hidden{display:none!important}",
"body.acp-hide-thinking .acp-thinking-block{display:none!important}",
".acp-resize-handle{cursor:col-resize;width:5px;flex-shrink:0;background:transparent;z-index:10;position:relative;margin-left:-2px}",
".acp-resize-handle:hover{background:#3b82f6}",
".acp-tc{max-height:300px!important;overflow-y:auto!important;scrollbar-width:thin}",
"body.acp-expand-tools .acp-tc{max-height:none!important;overflow:visible!important}"
].join("\n");
document.head.appendChild(s);
function safe(fn){try{fn()}catch(e){}}
safe(function(){
var oa=WebSocket.prototype.addEventListener;
WebSocket.prototype.addEventListener=function(t,l,o){oa.call(this,t,l,o);if(t==="message")oa.call(this,"message",function(e){try{var d=JSON.parse(e.data);if(d&&d.type==="error"&&d.payload&&d.payload.message){var x=document.querySelector(".acp-error-toast");if(x)x.remove();var el=document.createElement("div");el.className="acp-error-toast";el.textContent=d.payload.message;var dm=document.createElement("span");dm.textContent=" \u2715";dm.style.cssText="margin-left:auto;cursor:pointer;opacity:.7;padding:4px";dm.onclick=function(){el.remove()};el.appendChild(dm);document.body.appendChild(el);setTimeout(function(){if(el.parentNode)el.remove()},8000)}}catch(e){}});};
})();
setInterval(function(){safe(function(){
/* === ACP UI ENHANCEMENT (v2 - no .acp-sidebar dependency) === */
/* Feature 0: Auto-open permission/confirmation dialogs (before popover guard) */
try{
document.querySelectorAll('[data-state="closed"]').forEach(function(el){
var txt=el.textContent||"";
if(txt.indexOf("Awaiting Approval")>=0||txt.indexOf("Permission Required")>=0){
var trig=el.querySelector('button');
if(trig){trig.click()}
}
});
}catch(e0){}
/* Feature 6: Lock working directory to P:\ (runs before popover guard — connection form is always visible) */
try{
var wdInput=document.getElementById("working-dir");
if(wdInput&&!wdInput.dataset.acpLocked){
wdInput.dataset.acpLocked="1";
wdInput.readOnly=true;
wdInput.style.opacity="0.6";
wdInput.style.cursor="default";
var ns=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,"value").set;
ns.call(wdInput,"P:\\");
wdInput.dispatchEvent(new Event("input",{bubbles:true}));
var lbl=wdInput.closest("div").parentElement.querySelector("label");
if(lbl){var optSpan=lbl.querySelector("span");if(optSpan){optSpan.textContent="(locked to P:\\)"}}
}
}catch(e5){}
/* Feature 7: Proxy-down detector — polls /health when disconnected, shows instructions */
try{
if(!window.__acpProxyCheck){
window.__acpProxyCheck=true;
var acpBanner=null;
function acpCheckProxy(){
var isDown=false;
var spans=document.querySelectorAll("span");
for(var i=0;i<spans.length;i++){
var t=spans[i].textContent.trim();
if(t==="Disconnected"||t==="Error"){isDown=true;break}
}
if(!isDown){if(acpBanner){acpBanner.remove();acpBanner=null}return}
if(acpBanner)return;
fetch("http://localhost:9315/health",{method:"GET",signal:AbortSignal.timeout?AbortSignal.timeout(1500):undefined}).then(function(r){return r.json()}).then(function(d){
acpBanner=document.createElement("div");
acpBanner.style.cssText="position:fixed;top:0;left:0;right:0;z-index:99999;padding:12px 16px;background:#dc2626;color:#fff;font-size:13px;line-height:1.5;font-family:system-ui,sans-serif;box-shadow:0 2px 8px rgba(0,0,0,.3)";
acpBanner.innerHTML="<b>⚠ Proxy running but unhealthy.</b><br>Try the Restart Proxy (⏻) button in the status bar.";
document.body.prepend(acpBanner)
}).catch(function(){
acpBanner=document.createElement("div");
acpBanner.id="acp-proxy-down";
acpBanner.style.cssText="position:fixed;top:0;left:0;right:0;z-index:99999;padding:12px 16px;background:#dc2626;color:#fff;font-size:13px;line-height:1.5;font-family:system-ui,sans-serif;box-shadow:0 2px 8px rgba(0,0,0,.3)";
acpBanner.innerHTML="<b>⚠ Proxy not running.</b> Nothing is listening on port 9315.<br>To start it, run this in a terminal:<br><code style='background:rgba(0,0,0,.3);padding:2px 6px;border-radius:3px;font-family:monospace'>& \"C:\\Users\\brsth\\chrome-acp\\start-proxy.bat\"</code>";
document.body.prepend(acpBanner)
})
}
setInterval(acpCheckProxy,3000);
acpCheckProxy()
}
}catch(e7){}
/* Feature 8: Header control buttons next to theme toggle (CONSOLIDATED 2026-07-31).
   Replaces old Feature 8 (theme-toggle, broken querySelector) AND Feature 1 (status-bar).
   Anchor: find theme toggle by its sr-only "Toggle theme" TEXT so other
   dropdown-menu-trigger buttons (model picker etc.) don't hijack a first-match.
   Insert buttons as siblings of the theme-toggle wrapper, in the header flex row. */
try{
var themeBtn=null;
var triggers=document.querySelectorAll('button[data-slot="dropdown-menu-trigger"]');
for(var ti=0;ti<triggers.length;ti++){var sr=triggers[ti].querySelector('span.sr-only');if(sr&&((sr.textContent||"").indexOf("Toggle theme")>=0)){themeBtn=triggers[ti];break}}
if(themeBtn){
var wrapDiv=themeBtn.parentElement;
var row=wrapDiv?wrapDiv.parentElement:null;
if(row&&!row.querySelector('[data-acp-ctrl]')){
var mkBtn=function(title,svgPath,onClick,opacity){
var b=document.createElement("button");b.type="button";b.title=title;b.className=themeBtn.className;
b.innerHTML='<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide h-4 w-4" aria-hidden="true">'+svgPath+'</svg>';
b.style.opacity=opacity===false?"0.4":"1";b.dataset.acpCtrl="1";b.onclick=onClick;return b};
var rb=mkBtn("Reload extension",'<path d="M3 12a9 9 0 0 1 15-6.7L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-15 6.7L3 16"/><path d="M3 21v-5h5"/>',function(){try{chrome.runtime.reload()}catch(e){location.reload()}});
var rpb=mkBtn("Restart proxy",'<path d="M12 2v10"/><path d="M18.4 6.6a9 9 0 1 1-12.77.04"/>',function(){rpb.style.opacity="0.4";rpb.title="Restarting...";fetch("http://localhost:9315/restart-proxy",{method:"POST"}).then(function(){setTimeout(function(){try{chrome.runtime.reload()}catch(e){location.reload()}},2500)}).catch(function(){try{chrome.runtime.reload()}catch(e){location.reload()}})});
var stb=mkBtn("Toggle tool calls",'<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>',function(){var v=localStorage.getItem("acp_st")==="0"?"1":"0";localStorage.setItem("acp_st",v);stb.style.opacity=v==="0"?"0.4":"1";document.querySelectorAll(".acp-tc").forEach(function(e){e.style.display=v==="0"?"none":""})},localStorage.getItem("acp_st")!=="0");
var thb=mkBtn("Toggle thinking",'<path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>',function(){var v=localStorage.getItem("acp_th")==="0"?"1":"0";localStorage.setItem("acp_th",v);thb.style.opacity=v==="0"?"0.4":"1";document.body.classList.toggle("acp-hide-thinking",v==="0")},localStorage.getItem("acp_th")!=="0");
var etb=mkBtn("Expand tool results",'<path d="M8 3H5a2 2 0 0 0-2 2v3"/><path d="M21 8V5a2 2 0 0 0-2-2h-3"/><path d="M3 16v3a2 2 0 0 0 2 2h3"/><path d="M16 21h3a2 2 0 0 0 2-2v-3"/>',function(){var ex=!document.body.classList.contains("acp-expand-tools");document.body.classList.toggle("acp-expand-tools",ex);localStorage.setItem("acp_et",ex?"1":"0");etb.style.opacity=ex?"1":"0.4"},localStorage.getItem("acp_et")==="1");
[rb,rpb,stb,thb,etb].forEach(function(b){row.insertBefore(b,wrapDiv)});
}
}
}catch(e8){console.warn("ACP header buttons:",e8&&e8.message)}
/* Feature 1: removed 2026-07-31 — consolidated into Feature 8 above. */
var po=document.querySelector('[data-state="open"][role="listbox"],[data-radix-popper-content-wrapper]');
if(po)return;
/* Feature 2: File search in file tree */
try{
var fl=document.querySelector(".acp-file-tree");
if(!fl){var candidates=document.querySelectorAll('[role="tabpanel"] .overflow-auto,[data-state="active"][role="tabpanel"] .overflow-auto');for(var ci=0;ci<candidates.length;ci++){if(candidates[ci].querySelectorAll("button").length>3){fl=candidates[ci];fl.classList.add("acp-file-tree");break}}}
if(fl&&!document.querySelector(".acp-file-search")){var sd=document.createElement("div");sd.className="acp-file-search";var ip=document.createElement("input");ip.type="text";ip.placeholder="Filter...";ip.oninput=function(){var q=this.value.toLowerCase();fl.querySelectorAll("button").forEach(function(b){b.classList.toggle("acp-search-hidden",q!==""&&b.textContent.toLowerCase().indexOf(q)<0)})};sd.appendChild(ip);fl.parentNode.insertBefore(sd,fl)}
}catch(e3){console.error("ACP file search failed:",e3)}
/* Feature 3: Tool call tagging + thinking hide (document-level) */
try{
document.body.classList.toggle("acp-hide-thinking",localStorage.getItem("acp_th")==="0");
document.body.classList.toggle("acp-expand-tools",localStorage.getItem("acp_et")==="1");
var ts=localStorage.getItem("acp_st")==="0";
document.querySelectorAll("div[class*=border][class*=rounded]").forEach(function(d){var t=d.textContent||"";if(t.match(/browser_|Completed|Tool call/i)){d.classList.add("acp-tc");d.style.display=ts?"none":""}})
}catch(e4){console.error("ACP tool-call tagging failed:",e4)}
/* === END ACP UI ENHANCEMENT === */})},800);
})();
}catch(e){console.error("ACP UI injection failed:",e)}