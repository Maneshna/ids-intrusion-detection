const $=s=>document.querySelector(s),out=$("#out"),PS=25;let rows=[],page=0,onlyAtk=false,tmr;
function go(id){["dash","pred","expl"].forEach(k=>$("#"+k).classList.toggle("hide",k!==id));
 document.querySelectorAll(".nav").forEach(b=>b.dataset.go===id?b.setAttribute("aria-current","page"):b.removeAttribute("aria-current"));
 try{location.hash=id}catch(e){}}
document.querySelectorAll(".nav").forEach(b=>b.onclick=()=>go(b.dataset.go));
$("#th").onclick=()=>{const d=document.documentElement,dk=matchMedia("(prefers-color-scheme:dark)").matches,c=d.dataset.theme||(dk?"dark":"light");d.dataset.theme=c==="dark"?"light":"dark"};
$("#ask").onkeydown=e=>{if(e.key==="Enter")go("expl")};
// funnel
const F=[["Flows analyzed",65200,"65.2k","var(--blue)","flows scanned"],["Flagged anomalous",18900,"18.9k","var(--blue)","flagged · 29% of flows"],["Predicted attacks",12800,"12.8k","var(--red)","attacks · 68% of flagged"],["High confidence",11600,"11.6k","var(--red)","above 90% confidence · 91%"]];
const fun=$("#fun"),tip=$("#tip");
F.forEach((f,i)=>{const h=Math.max(f[1]/65200*100,14),nx=F[i+1]?Math.max(F[i+1][1]/65200*100,14):h,d=((h-nx)/h*100);
 const c=document.createElement("div");c.className="col"+(i===2?" on":"");c.tabIndex=0;
 c.innerHTML=`<div class="t">${f[0]}</div><div class="v">${f[2]}</div><div class="plot"><div class="bar" style="--c:${f[3]};--d:${d}%;height:${h}%"></div></div>`;
 const show=()=>{fun.querySelectorAll(".col").forEach(x=>x.classList.remove("on"));c.classList.add("on");const r=c.getBoundingClientRect(),p=fun.getBoundingClientRect();
  tip.textContent=f[2]+" "+f[4];tip.style.left=(r.left-p.left+r.width/2+fun.offsetLeft)+"px";tip.style.top=(fun.offsetTop+110)+"px";tip.style.opacity=1};
 c.onmouseenter=show;c.onfocus=show;c.onmouseleave=()=>tip.style.opacity=0;fun.appendChild(c)});
// step line
(()=>{const v=[30,30,24,24,36,30,30,18,18,24,12,12,18,12,12],w=280/v.length;let d="M0 "+v[0];
 v.forEach((y,i)=>{d+=` L${i*w} ${y+10} L${(i+1)*w} ${y+10}`});d=d.replace("M0 "+v[0],"M0 "+(v[0]+10));
 $("#step").innerHTML=`<defs><pattern id="h" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="6" stroke="var(--amber)" stroke-opacity=".35" stroke-width="2"/></pattern></defs><path d="${d} L280 70 L0 70Z" fill="url(#h)"/><path d="${d}" fill="none" stroke="var(--amber)" stroke-width="2"/>`})();
// dots
$("#dg").innerHTML=[3,4,5,7,4,2,1].map((n,i)=>`<div class="${i===3?"pk":""}">${"<i></i>".repeat(n)}</div>`).join("");
// predictions
function empty(){out.innerHTML='<div class="card empty"><h2>No file analyzed yet</h2><p>Upload a CSV of network flows to see which connections look like attacks.</p></div>'}
function loading(){out.innerHTML='<div class="card empty"><div class="spin"></div><b style="color:var(--ink)">Analyzing flows…</b><div class="cap">This usually takes a few seconds.</div><div class="pb"><i id="bar"></i></div></div>';requestAnimationFrame(()=>requestAnimationFrame(()=>{const b=$("#bar");if(b)b.style.width="92%"}))}
function error(m){out.innerHTML=`<div class="err" role="alert"><div style="flex:1"><b>Couldn’t read this file</b><div>${m}</div></div><button class="btn" id="retry">Try again</button></div>`;$("#retry").onclick=()=>{empty();$("#st").value=""}}
function gen(n,rate){let s=n*7919+13;const r=()=>(s=(s*1664525+1013904223)%4294967296)/4294967296;return Array.from({length:n},(_,i)=>{const a=r()<rate,c=a?.62+r()*.37:.7+r()*.3;return{i:i+1,atk:a,c,an:a?r()<.55:r()<.03}})}
function success(d){rows=d;page=0;onlyAtk=false;render()}
function render(){const A=rows.filter(r=>r.atk).length,N=rows.length;
 if(!A){out.innerHTML=`<div class="ok"><h2>All clear</h2><p>Analyzed ${N.toLocaleString()} flows and found no attacks. Every connection looks benign.</p><button class="btn" id="again" style="margin-top:14px">Analyze another file</button></div>`;$("#again").onclick=()=>{empty();$("#st").value=""};return}
 const L=onlyAtk?rows.filter(r=>r.atk):rows,P=Math.ceil(L.length/PS),sl=L.slice(page*PS,page*PS+PS);
 out.innerHTML=`<div class="strip"><span>Analyzed <b class="mono">${N.toLocaleString()}</b> flows</span><span class="lbl">→</span><span class="badge a">${A.toLocaleString()} attacks found</span><span class="badge b">${(N-A).toLocaleString()} benign</span></div>
 <div class="tools"><label class="sw"><input type="checkbox" id="fa" ${onlyAtk?"checked":""}><span></span>Show attacks only</label><span class="sp"></span><span class="cap" style="margin:0">Amber flag = unusual but unconfirmed</span></div>
 <div class="tw"><table><thead><tr><th>Flow #</th><th>Prediction</th><th>Confidence</th><th>Anomaly</th></tr></thead><tbody>${sl.map(r=>`<tr class="${r.atk?"atk":""}"><td class="n">${r.i.toLocaleString()}</td><td><span class="badge ${r.atk?"a":"b"}">${r.atk?"Attack":"Benign"}</span></td><td><div class="conf" style="--c:${r.atk?"var(--red)":"var(--green)"}"><i><b style="width:${r.c*100}%"></b></i>${(r.c*100).toFixed(1)}%</div></td><td>${r.an?'<span class="flag">⚠ Anomaly</span>':'<span class="dash">–</span>'}</td></tr>`).join("")}</tbody></table></div>
 <div class="pg"><span>Showing ${(page*PS+1).toLocaleString()}–${Math.min(page*PS+PS,L.length).toLocaleString()} of ${L.length.toLocaleString()}</span><div><button class="btn" id="pv" ${page===0?"disabled":""}>Previous</button><span>Page ${page+1} of ${P}</span><button class="btn" id="nx" ${page>=P-1?"disabled":""}>Next</button></div></div>`;
 $("#fa").onchange=e=>{onlyAtk=e.target.checked;page=0;render()};$("#pv").onclick=()=>{page--;render()};$("#nx").onclick=()=>{page++;render()}}
async function analyze(file){clearTimeout(tmr);loading();
 try{const fd=new FormData();fd.append("file",file);
  const r=await fetch("/api/predict",{method:"POST",body:fd}),j=await r.json();
  if(!r.ok)throw new Error(j.error||"Server error");
  $("#st").value="";success(j.rows)}
 catch(e){error(e.message==="Failed to fetch"?"Can’t reach the server. Start the backend and open http://127.0.0.1:5000.":e.message)}}
function handle(f){if(!f)return;
 if(!/\.csv$/i.test(f.name))return error(`“${f.name}” is not a CSV. Choose a file that ends in .csv.`);
 analyze(f)}
$("#choose").onclick=()=>$("#file").click();$("#file").onchange=e=>{handle(e.target.files[0]);e.target.value=""};
const dr=$("#drop");["dragenter","dragover"].forEach(v=>dr.addEventListener(v,e=>{e.preventDefault();dr.classList.add("over")}));["dragleave","drop"].forEach(v=>dr.addEventListener(v,e=>{e.preventDefault();dr.classList.remove("over")}));dr.addEventListener("drop",e=>handle(e.dataTransfer.files[0]));
$("#st").onchange=e=>{clearTimeout(tmr);go("pred");const v=e.target.value;if(v==="loading")loading();else if(v==="success")success(gen(5000,.0624));else if(v==="clear")success(gen(1200,0));else if(v==="error")error("“flows_march.txt” is not a CSV. Choose a file that ends in .csv.");else empty()};
empty();const h=(location.hash||"").slice(1);if(["dash","pred","expl"].includes(h))go(h);
