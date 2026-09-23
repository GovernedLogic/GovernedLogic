/* A visual metaphor: dispersed tokens enter relation around a fixed referent. */
(()=>{
 'use strict';
 const scene=document.getElementById('origin'),canvas=document.getElementById('origin-canvas');
 const nav=document.querySelector('.chain-nav');
 if(!scene||!canvas)return;
 const ctx=canvas.getContext('2d');
 if(!ctx){document.documentElement.classList.remove('gl-intro');return;}
 const reduce=matchMedia('(prefers-reduced-motion: reduce)');
 const clamp=x=>Math.max(0,Math.min(1,x));
 const smooth=x=>{x=clamp(x);return x*x*(3-2*x);};
 const mix=(a,b,t)=>a+(b-a)*t;
 const words=['truth','logic','meaning','being','ground','reasoning','Logos','1','0','∴','→','α','Ω','intelligibility','obligation','intelligence'];
 let w=1,h=1,dpr=1,clock=reduce.matches?20:0,last=0,lastDraw=0,raf=0,active=false,paused=reduce.matches,arrival=0;
 let nodes=[],edges=[],dust=[],pointerX=0,pointerY=0,turnX=0,turnY=0,seed=971;
 const random=()=>{seed=(seed*16807)%2147483647;return(seed-1)/2147483646;};
 function makeField(){
  seed=971;const count=w<720?330:600;nodes=[];edges=[];dust=[];
  for(let i=0;i<count;i++){
   const y=1-2*(i+.5)/count,a=i*Math.PI*(3-Math.sqrt(5)),r=Math.sqrt(1-y*y),shell=.65+random()*.35;
   nodes.push({x:Math.cos(a)*r*shell,y:y*shell,z:Math.sin(a)*r*shell,word:words[i%words.length],size:.55+random()*1.5,label:i%5===0,gold:i%19===0,phase:random()*Math.PI*2});
  }
  // Preserve a sparse, connected topology as the field rotates.
  const pairs=new Set();
  nodes.forEach((p,i)=>{
   const closest=[];
   nodes.forEach((q,j)=>{if(i!==j){const d=(p.x-q.x)**2+(p.y-q.y)**2+(p.z-q.z)**2;closest.push([j,d]);}});
   closest.sort((a,b)=>a[1]-b[1]);
   closest.slice(0,3).forEach(([j])=>{const lo=Math.min(i,j),hi=Math.max(i,j),key=lo+':'+hi;if(!pairs.has(key)){pairs.add(key);edges.push([lo,hi]);}});
  });
  for(let i=0;i<(w<720?100:220);i++){const a=random()*Math.PI*2;dust.push({a,r:.15+random(),z:random(),v:.1+random()*.2,s:.3+random()});}
 }
 function resize(){
  const oldMobile=w<720;w=scene.clientWidth;h=scene.clientHeight;dpr=Math.min(devicePixelRatio||1,1.75);
  canvas.width=Math.round(w*dpr);canvas.height=Math.round(h*dpr);ctx.setTransform(dpr,0,0,dpr,0,0);
  if(!nodes.length||oldMobile!==(w<720))makeField();draw();
 }
 function stroke(x1,y1,x2,y2,color,width=1){ctx.strokeStyle=color;ctx.lineWidth=width;ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.stroke();}
 function draw(){
  const stops=[[0,0],[2,.65],[5,1.85],[8,3.6],[13,5.05],[14,6.8],[14.3,7.5],[20,10.5]];
  let t=10.5+(clock-20)*.65;
  if(clock<20){for(let i=1;i<stops.length;i++){if(clock<=stops[i][0]){const p=stops[i-1],q=stops[i];t=mix(p[1],q[1],(clock-p[0])/(q[0]-p[0]));break;}}}
  const cx=w*.5,cy=h*.5;
  const reveal=smooth((t-7.5)/2.8),aligned=smooth((t-3.6)/2.9),born=smooth((t-1.85)/.55);
  const radius=w<720?Math.min(w*.43,h*.3):Math.min(w*.34,h*.34),burst=1.72*(1-Math.exp(-3.7*Math.max(0,t-1.85)));
  const size=radius*mix(burst,1,aligned),spreadX=mix(1,w<720?1.06:1.64,reveal),flatten=mix(1,w<720?1.55:.76,reveal);
  const a=t*.12*aligned+turnX,b=.28+turnY,c=Math.cos(a),s=Math.sin(a),cb=Math.cos(b),sb=Math.sin(b);
  arrival=smooth((t-9.1)/1.4);scene.style.setProperty('--reveal',reveal.toFixed(4));scene.style.setProperty('--arrival',arrival.toFixed(4));
  scene.dataset.phase=clock<2?'black':clock<5?'point':clock<8?'burst':clock<14.3?'alignment':clock<20?'reveal':'settled';
  ctx.clearRect(0,0,w,h);
  if(t<.65)return;
  const star=smooth((t-.65)/.75),flash=Math.exp(-(((t-1.98)/.19)**2));
  // Light expands once. It does not strobe.
  const bloomRadius=mix(20,Math.min(w,h)*.49,born),bloom=ctx.createRadialGradient(cx,cy,0,cx,cy,bloomRadius);
  bloom.addColorStop(0,`rgba(108,194,255,${(.20*born+.30*flash)*star})`);
  bloom.addColorStop(.2,`rgba(34,104,196,${(.12*born+.16*flash)*(1-reveal*.5)})`);
  bloom.addColorStop(1,'rgba(0,0,0,0)');ctx.fillStyle=bloom;ctx.fillRect(0,0,w,h);
  if(born>0){
   // A deeper star field carries the burst out beyond the main graph.
   dust.forEach(p=>{
    const distance=(.3+p.r)*Math.max(w,h)*.53*mix(burst,.94,aligned),angle=p.a+t*p.v*.06*aligned;
    const x=cx+Math.cos(angle)*distance,y=cy+Math.sin(angle)*distance*.69;
    const alpha=born*(.16+p.z*.47)*(1-reveal*.2);ctx.fillStyle=`rgba(149,199,255,${alpha})`;ctx.beginPath();ctx.arc(x,y,p.s,0,Math.PI*2);ctx.fill();
    if(t<3.5)stroke(mix(cx,x,.91),mix(cy,y,.91),x,y,`rgba(117,176,255,${alpha*.42})`,.6);
   });
   const pts=nodes.map(p=>{
    const x=p.x*c+p.z*s,z=-p.x*s+p.z*c,y=p.y*cb-z*sb,depth=p.y*sb+z*cb;
    const perspective=3.6/(3.6-depth),xx=cx+x*size*spreadX*perspective,yy=cy+y*size*flatten*perspective;
    const imageH=(w<720?w*1.12:w)/2.4;
    const inWordmark=Math.abs(yy-cy)<imageH*.23&&Math.abs(xx-cx)<w*.455;
    const opacity=born*(.3+(.5+depth*.5)*.65)*(1-reveal*(inWordmark?.88:.12));
    return{x:xx,y:yy,z:depth,alpha:opacity,scale:perspective};
   });
   // Connections become visible as the scattered field settles into relation.
   const relational=smooth((t-3.2)/2.2),edgePulse=(t*.09)%1;
   for(let k=0;k<edges.length;k++){
    const [i,j]=edges[k],p=pts[i],q=pts[j],alpha=Math.min(p.alpha,q.alpha)*relational;
    if(alpha<.025)continue;
    const gold=nodes[i].gold,light=k%31===0;
    stroke(p.x,p.y,q.x,q.y,`rgba(${gold?'197,157,94':light?'149,146,244':'78,152,220'},${alpha*(light?.57:.29)})`,light?.85:.55);
    if(k%71===0&&relational>.5){const x=mix(p.x,q.x,edgePulse),y=mix(p.y,q.y,edgePulse);ctx.fillStyle=`rgba(196,226,255,${alpha})`;ctx.beginPath();ctx.arc(x,y,1.6,0,Math.PI*2);ctx.fill();}
   }
   for(let i=0;i<pts.length;i+=43){const p=pts[i];stroke(cx,cy,p.x,p.y,`rgba(186,162,224,${p.alpha*relational*.09})`,.65);}
   const sorted=pts.map((p,i)=>({...p,i})).sort((p,q)=>p.z-q.z);
   sorted.forEach(p=>{
    const n=nodes[p.i],r=n.size*p.scale,alpha=p.alpha;
    if(alpha<.03)return;
    ctx.fillStyle=`rgba(${n.gold?'246,209,135':'171,216,255'},${alpha})`;
    if(n.label&&p.z>-.45){ctx.font=`${Math.max(8,Math.min(13,9.1*p.scale))}px ui-monospace,monospace`;ctx.fillText(n.word,p.x+4,p.y-4);}
    if(p.z>.62&&p.i%7===0){ctx.shadowColor='#74bfff';ctx.shadowBlur=7;}
    ctx.beginPath();ctx.arc(p.x,p.y,r,0,Math.PI*2);ctx.fill();ctx.shadowBlur=0;
    if(t<3.4)stroke(mix(cx,p.x,.88),mix(cy,p.y,.88),p.x,p.y,`rgba(137,203,255,${alpha*.6})`,.8);
   });
  }
  // The brief seven-circle motif gives way to the sustained token network.
  const seedAlpha=smooth((t-5.05)/.5)*(1-smooth((t-6.1)/.7));
  if(seedAlpha>0){
   const r=Math.min(w,h)*.08;ctx.strokeStyle=`rgba(218,189,142,${seedAlpha*.40})`;ctx.lineWidth=.8;
   for(let i=-1;i<6;i++){const q=i*Math.PI/3,x=i<0?cx:cx+Math.cos(q)*r,y=i<0?cy:cy+Math.sin(q)*r;ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2*smooth((t-5.05)/.6));ctx.stroke();}
  }
  if(flash>.002){
   const shock=(t-1.7)*Math.min(w,h)*2.6;
   ctx.strokeStyle=`rgba(172,204,255,${flash*.22})`;ctx.lineWidth=1.4;ctx.beginPath();ctx.ellipse(cx,cy,Math.max(1,shock),Math.max(1,shock*.36),0,0,Math.PI*2);ctx.stroke();
  }
  // The reference point is invariant: the camera, field and phases never move it.
  const pulse=1+Math.sin(t*1.1)*.1,coreR=(12+born*13+flash*90)*pulse;
  const core=ctx.createRadialGradient(cx,cy,0,cx,cy,coreR);
  core.addColorStop(0,`rgba(255,255,255,${star})`);core.addColorStop(.07,`rgba(235,246,255,${star*.94})`);core.addColorStop(.2,`rgba(132,202,255,${star*.53})`);core.addColorStop(1,'rgba(66,129,255,0)');
  ctx.fillStyle=core;ctx.fillRect(cx-coreR,cy-coreR,coreR*2,coreR*2);
  ctx.fillStyle=`rgba(255,252,235,${star})`;ctx.beginPath();ctx.arc(cx,cy,1.35+flash*3.5,0,Math.PI*2);ctx.fill();
  if(born>0){const beam=ctx.createLinearGradient(cx-w*.37,cy,cx+w*.37,cy);beam.addColorStop(0,'#72baff00');beam.addColorStop(.45,`rgba(153,216,255,${born*.13})`);beam.addColorStop(.5,`rgba(232,245,255,${born*.75})`);beam.addColorStop(.55,`rgba(153,216,255,${born*.13})`);beam.addColorStop(1,'#72baff00');ctx.fillStyle=beam;ctx.fillRect(cx-w*.37,cy-.4,w*.74,.8);}
 }
 function loop(now){
  raf=0;if(paused||!active||document.hidden){last=0;return;}
  if(last)clock+=Math.max(0,(now-last)/1000);last=now;
  if(now-lastDraw>=(w<720?33:25)){turnX+=(pointerX-turnX)*.03;turnY+=(pointerY-turnY)*.03;draw();lastDraw=now;}
  raf=requestAnimationFrame(loop);
 }
 function run(){if(!raf&&!paused&&active&&!document.hidden){last=0;raf=requestAnimationFrame(loop);}}
 function setPaused(value){paused=value;document.documentElement.classList.toggle('motion-paused',paused);if(paused)draw();else run();}
 scene.addEventListener('pointermove',e=>{const r=scene.getBoundingClientRect();pointerX=((e.clientX-r.left)/w-.5)*.18;pointerY=((e.clientY-r.top)/h-.5)*.13;},{passive:true});
 scene.addEventListener('pointerleave',()=>{pointerX=pointerY=0;});
 reduce.addEventListener('change',e=>{if(e.matches)clock=20;setPaused(e.matches);draw();});
 document.addEventListener('visibilitychange',()=>{last=0;run();});
 const visibleScenes=new Set();
 const sceneObserver=new IntersectionObserver(entries=>{entries.forEach(e=>e.isIntersecting?visibleScenes.add(e.target):visibleScenes.delete(e.target));active=visibleScenes.has(scene);last=0;const hideNav=visibleScenes.size>0;nav?.classList.toggle('is-origin',hideNav);if(nav)nav.inert=hideNav;run();},{threshold:.08});
 sceneObserver.observe(scene);sceneObserver.observe(document.getElementById('architecture'));
 new ResizeObserver(resize).observe(scene);
 resize();setPaused(paused);document.documentElement.classList.add('gl-intro-ready');run();
 const copyButton=document.getElementById('copy-principles'),text=document.getElementById('governing-principles'),status=document.getElementById('copy-status');
 copyButton?.addEventListener('click',async()=>{try{await navigator.clipboard.writeText(text.value);status.textContent='Copied. Ready to use in your model.';copyButton.textContent='Copied ✓';}catch{text.focus();text.select();status.textContent='Text selected. Use your device’s Copy command.';}});
})();
