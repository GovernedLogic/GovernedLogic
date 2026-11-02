/* v14 (Paul 2026-11-01 22:34): treatise reading progress, contents drawer and current chapter; the article share row's
   Copy link button. No third-party scripts. Nothing animates: progress is a scroll-position readout. */
(function(){
  var body=document.body;body.classList.add('gl-js');
  var bar=document.querySelector('.gl-treatise-bar'),toc=document.getElementById('gl-toc');
  if(bar&&toc){
    var fill=bar.querySelector('.gl-progress>span'),btn=bar.querySelector('.gl-toc-toggle');
    var links=[].slice.call(toc.querySelectorAll('a[href^="#"]'));
    var secs=links.map(function(a){return document.getElementById(a.getAttribute('href').slice(1));});
    var article=document.querySelector('main article')||document.querySelector('main');
    function update(){
      var r=article.getBoundingClientRect(),h=r.height-innerHeight;
      var p=h>0?Math.min(1,Math.max(0,-r.top/h)):1;
      if(fill)fill.style.setProperty('--gl-read',p.toFixed(4));
      var cur=-1;secs.forEach(function(s,i){if(s&&s.getBoundingClientRect().top<innerHeight*0.35)cur=i;});
      links.forEach(function(a,i){if(i===cur)a.setAttribute('aria-current','true');else a.removeAttribute('aria-current');});
      body.style.setProperty('--gl-bar-bottom',Math.round(bar.getBoundingClientRect().bottom)+'px');
    }
    function close(){toc.classList.remove('gl-open');btn.setAttribute('aria-expanded','false');}
    btn.addEventListener('click',function(){var o=toc.classList.toggle('gl-open');btn.setAttribute('aria-expanded',o?'true':'false');update();});
    links.forEach(function(a){a.addEventListener('click',close);});
    document.addEventListener('keydown',function(e){if(e.key==='Escape')close();});
    addEventListener('scroll',update,{passive:true});addEventListener('resize',update);update();
  }
  var copy=document.querySelector('.gl-share .gl-copy');
  if(copy){
    var status=document.querySelector('.gl-share .gl-copied');
    copy.addEventListener('click',function(){
      var url=copy.getAttribute('data-url');
      function done(){if(status){status.textContent='Copied';setTimeout(function(){status.textContent='';},2500);}}
      if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(url).then(done,function(){});
      else{var t=document.createElement('textarea');t.value=url;t.setAttribute('readonly','');t.style.position='fixed';t.style.opacity='0';document.body.appendChild(t);t.select();try{document.execCommand('copy');done();}catch(e){}document.body.removeChild(t);}
    });
  }
})();
