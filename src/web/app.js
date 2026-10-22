(function(){
  "use strict";
  var $=function(s,r){return (r||document).querySelector(s)}, $$=function(s,r){return Array.prototype.slice.call((r||document).querySelectorAll(s))};

  /* ---------- tabs ---------- */
  var tabs=$$('.tab'), panels=$$('.panel');
  function show(id,push){
    var ok=false;
    tabs.forEach(function(t){var on=t.dataset.tab===id; if(on)ok=true; t.setAttribute('aria-selected',on); t.tabIndex=on?0:-1;});
    if(!ok)return show(tabs[0].dataset.tab,push);
    panels.forEach(function(p){p.hidden=(p.id!=='panel-'+id)});
    if(push){try{history.replaceState(null,'','#'+id)}catch(e){}}
    var t=$('.tab[data-tab="'+id+'"]'); if(t&&t.scrollIntoView){try{t.scrollIntoView({block:'nearest',inline:'center'})}catch(e){}}
    var n=$('nav.tabs'); if(n&&window.scrollY>n.offsetTop){window.scrollTo(0,n.offsetTop)}
  }
  tabs.forEach(function(t,i){
    t.addEventListener('click',function(){show(t.dataset.tab,true)});
    t.addEventListener('keydown',function(e){
      var j=null; if(e.key==='ArrowRight')j=(i+1)%tabs.length; if(e.key==='ArrowLeft')j=(i-1+tabs.length)%tabs.length;
      if(e.key==='Home')j=0; if(e.key==='End')j=tabs.length-1;
      if(j!==null){e.preventDefault();tabs[j].focus();show(tabs[j].dataset.tab,true)}
    });
  });
  $$('[data-goto]').forEach(function(a){a.addEventListener('click',function(e){e.preventDefault();show(a.dataset.goto,true)})});
  show((location.hash||'').slice(1)||tabs[0].dataset.tab,false);
  window.addEventListener('hashchange',function(){show((location.hash||'').slice(1),false)});

  /* ---------- tooltips ---------- */
  var tip=document.createElement('div'); tip.id='tip'; tip.setAttribute('role','status'); document.body.appendChild(tip);
  function place(x,y){var w=tip.offsetWidth,h=tip.offsetHeight; var l=Math.min(Math.max(8,x+12),window.innerWidth-w-8); var t=y-h-14; if(t<8)t=y+18; tip.style.left=l+'px'; tip.style.top=t+'px'}
  document.addEventListener('mouseover',function(e){var el=e.target.closest&&e.target.closest('[data-tip]'); if(!el)return; tip.textContent=el.getAttribute('data-tip'); tip.classList.add('on'); place(e.clientX,e.clientY)});
  document.addEventListener('mousemove',function(e){if(tip.classList.contains('on'))place(e.clientX,e.clientY)});
  document.addEventListener('mouseout',function(e){var el=e.target.closest&&e.target.closest('[data-tip]'); if(el)tip.classList.remove('on')});
  document.addEventListener('focusin',function(e){var el=e.target.closest&&e.target.closest('[data-tip]'); if(!el)return; var r=el.getBoundingClientRect(); tip.textContent=el.getAttribute('data-tip'); tip.classList.add('on'); place(r.left+r.width/2,r.top)});
  document.addEventListener('focusout',function(){tip.classList.remove('on')});

  /* ---------- exact binomial bounds (same maths as evidence.py) ---------- */
  function binCdf(k,n,p){
    if(p<=0)return 1; if(p>=1)return k>=n?1:0;
    var lp=Math.log(p), lq=Math.log1p(-p), lc=0, s=0;
    for(var i=0;i<=k;i++){ if(i>0)lc+=Math.log((n-i+1)/i); s+=Math.exp(lc+i*lp+(n-i)*lq); }
    return Math.min(1,s);
  }
  function cpUpper(k,n,conf){
    if(k>=n)return 1; var a=1-conf, lo=0, hi=1;
    for(var it=0;it<90;it++){var m=(lo+hi)/2; if(binCdf(k,n,m)>a)lo=m; else hi=m}
    return (lo+hi)/2;
  }
  function nNeeded(target,k,conf){
    if(target>=1)return k+1;
    if(k===0)return Math.ceil(Math.log(1-conf)/Math.log(1-target));
    var lo=k+1, hi=Math.max(lo*2,Math.ceil(k/target)*2);
    while(cpUpper(k,hi,conf)>target)hi*=2;
    while(lo<hi){var m=Math.floor((lo+hi)/2); if(cpUpper(k,m,conf)<=target)hi=m; else lo=m+1}
    return lo;
  }
  window.EvidenceMath={cpUpper:cpUpper,nNeeded:nNeeded};
  var pct=function(x,d){return (x*100).toFixed(d===undefined?2:d)+'%'};
  var fmt=function(x){return Math.round(x).toLocaleString('en-US')};

  var c=$('#calc');
  if(c){
    var f={n:$('#c-n'),k:$('#c-k'),conf:$('#c-conf'),t:$('#c-t'),s:$('#c-s'),sv:$('#c-sv')};
    var o={big:$('#o-big'),txt:$('#o-txt'),need:$('#o-need'),needtxt:$('#o-needtxt')};
    var run=function(){
      var n=Math.max(1,Math.floor(+f.n.value||1)), k=Math.max(0,Math.floor(+f.k.value||0)), conf=+f.conf.value, t=Math.min(50,Math.max(0.01,+f.t.value||1))/100, s=(+f.s.value)/100;
      f.sv.textContent=Math.round(s*100)+'%';
      if(k>n){o.big.textContent='n/a';o.txt.textContent='Flagged answers cannot exceed reviews.';return}
      var u=cpUpper(k,n,conf), uTrue=Math.min(1,u/s);
      o.big.textContent=pct(uTrue);
      o.txt.innerHTML='With <b>'+k+'</b> flagged in <b>'+fmt(n)+'</b> reviews, the unsafe rate is at most <b>'+pct(uTrue)+'</b> at '+Math.round(conf*100)+'% confidence'+(s<1?' (reviewers assumed to catch '+Math.round(s*100)+'% of unsafe answers)':'')+'. On 1,000 answers to families, that is up to <b>'+fmt(uTrue*1000)+'</b> unsafe ones you have not seen.';
      var need=nNeeded(t*s,k,conf);
      o.need.textContent=fmt(need);
      o.needtxt.innerHTML='reviews needed to show the rate is at most <b>'+pct(t,2)+'</b> with up to <b>'+k+'</b> flagged'+(need>n?' &mdash; <b>'+fmt(need-n)+'</b> more than you have done.':' &mdash; you are past that point.');
    };
    ['input','change'].forEach(function(ev){c.addEventListener(ev,run)}); run();
  }

  var cap=$('#cap');
  if(cap){
    var h=$('#k-h'), m=$('#k-m'), out=$('#k-out');
    var runc=function(){
      var H=Math.max(0.5,+h.value||1), M=Math.max(1,+m.value||1), perWeek=H*60/M;
      var rows=[[0.01,'1%'],[0.005,'0.5%'],[0.001,'0.1%']].map(function(r){var n=nNeeded(r[0],0,0.95);return '<tr><td>at most '+r[1]+'</td><td class="n">'+fmt(n)+'</td><td class="n">'+(n/perWeek).toFixed(1)+' weeks</td></tr>'}).join('');
      out.innerHTML='<p><b>'+fmt(perWeek)+'</b> reviews a week from '+H+' reviewer-hours at '+M+' minutes each.</p><table class="tbl"><thead><tr><th>To show the unsafe rate is</th><th class="n">Clean reviews</th><th class="n">Time at this pace</th></tr></thead><tbody>'+rows+'</tbody></table><p class="hint">Per risk tier, not pooled, with zero flags. Add canary items and a second reviewer and the hours go up.</p>';
    };
    ['input','change'].forEach(function(ev){cap.addEventListener(ev,runc)}); runc();
  }

  /* ---------- router demo ---------- */
  var d=$('#demo');
  if(d&&window.Router&&window.RULES){
    var R=Router.load(window.RULES), box=$('#d-in'), v=$('#d-out');
    var info={
      1:['Tier 1 · Urgent','Show the crisis card now: 911, 988 and the SAMHSA helpline. No AI-written text. Alert the on-call human and log it.','t1'],
      2:['Tier 2 · Clinical question','Answer only from clinician-approved cards. If no card fits, hand off to a human helpline. No free-form AI text.','t2'],
      3:['Tier 3 · Family support','The AI may assemble an answer from approved sources and must cite them. A sample is reviewed afterwards.','t3'],
      4:['Tier 4 · Outside this service','Decline kindly and point to where to go. Nothing is generated.','t4']
    };
    var go=function(){
      var txt=box.value.trim();
      if(!txt){v.className='verdict t4';v.innerHTML='<div class="t">Type a message</div><div class="path">Try one of the examples. The Spanish and misspelled ones are there to show where this rule set fails.</div>';return}
      var r=Router.routeV2(txt,R), i=info[r.tier];
      v.className='verdict '+i[2];
      var none=r.why[0].indexOf('default')===0;
      v.innerHTML='<div class="t">'+i[0]+'</div><div class="path">'+i[1]+(none?' <b>No rule recognised this message.</b> In the planned design, a message the router cannot read shows the crisis card and a human route instead of a decline.':'')+'</div><ul>'+r.why.map(function(w){return '<li>'+w.replace(/&/g,'&amp;').replace(/</g,'&lt;')+'</li>'}).join('')+'</ul><div class="banner">Whatever the tier, every screen keeps &ldquo;Emergency? Call 911. In crisis? Call or text 988.&rdquo; in view.</div>';
    };
    box.addEventListener('input',go);
    $$('.chips button',d).forEach(function(b){b.addEventListener('click',function(){box.value=b.getAttribute('data-q');go();box.focus()})});
    box.value=''; go();
  }

  /* ---------- segmented toggles ---------- */
  $$('.seg').forEach(function(sg){
    var btns=$$('button',sg);
    btns.forEach(function(b){b.addEventListener('click',function(){
      btns.forEach(function(x){x.setAttribute('aria-pressed',x===b)});
      $$('[data-group="'+sg.dataset.for+'"]').forEach(function(g){g.hidden=(g.dataset.key!==b.dataset.key)});
    })});
  });

  /* ---------- code blocks ---------- */
  $$('.codeblock').forEach(function(cb){
    var pre=$('pre',cb), name=cb.dataset.name;
    var copy=$('[data-act=copy]',cb), dl=$('[data-act=dl]',cb);
    if(copy)copy.addEventListener('click',function(){
      var done=function(){copy.textContent='Copied';setTimeout(function(){copy.textContent='Copy'},1400)};
      try{navigator.clipboard.writeText(pre.textContent).then(done,function(){sel(pre)})}catch(e){sel(pre)}
    });
    if(dl)dl.addEventListener('click',function(){
      try{var b=new Blob([pre.textContent],{type:'text/plain'}),a=document.createElement('a');a.href=URL.createObjectURL(b);a.download=name;document.body.appendChild(a);a.click();a.remove()}catch(e){}
    });
  });
  function sel(el){try{var r=document.createRange();r.selectNodeContents(el);var s=getSelection();s.removeAllRanges();s.addRange(r)}catch(e){}}
})();
