(()=>{
const qs=s=>document.querySelector(s),qsa=s=>[...document.querySelectorAll(s)],scenes=qsa('.scene'),meter=qs('#meter'),menu=qs('#menuPanel'),reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
let scene=0,started=true,timer=null,audioOn=false,mouse={x:.5,y:.5,tx:.5,ty:.5};
const durations=[20000,24000,24000,26000,26000,26000,22000],accents=['#168CFA','#8D78FF','#168CFA','#8D78FF','#168CFA','#8D78FF','#168CFA'];
scenes.forEach((s,i)=>{const b=document.createElement('button');b.type='button';b.setAttribute('aria-label','Go to scene '+(i+1));if(i===0)b.classList.add('on');b.addEventListener('click',e=>{e.stopPropagation();setScene(i,true)});meter.appendChild(b)});
function update(){scenes.forEach((s,i)=>{const on=i===scene;s.classList.toggle('active',on);s.setAttribute('aria-hidden',on?'false':'true');if('inert'in s)s.inert=!on});[...meter.children].forEach((m,i)=>m.classList.toggle('on',i===scene));document.documentElement.style.setProperty('--accent',accents[scene]);if(audioOn)ramp(scene<2?.3:.22)}
function setScene(n,user=false){scene=(n+scenes.length)%scenes.length;const run=()=>update();if(document.startViewTransition&&started&&user&&!reduced)document.startViewTransition(run);else run();if(started)schedule()}
function schedule(){clearTimeout(timer);if(reduced||menu.classList.contains('show'))return;timer=setTimeout(()=>setScene(scene+1,false),durations[scene]||8000)}
function toggleMenu(force){const show=typeof force==='boolean'?force:!menu.classList.contains('show');menu.classList.toggle('show',show);qs('#menuBtn').setAttribute('aria-expanded',String(show));if(show){clearTimeout(timer);menu.querySelector('a')?.focus()}else if(started)schedule()}
document.addEventListener('keydown',e=>{if(e.key==='Escape'){toggleMenu(false);return}if(e.key.toLowerCase()==='m'){e.preventDefault();toggleMenu();return}if(menu.classList.contains('show'))return;if(e.key==='ArrowRight'||e.key===' '){e.preventDefault();setScene(scene+1,true)}if(e.key==='ArrowLeft'){e.preventDefault();setScene(scene-1,true)}});
qs('#menuBtn').addEventListener('click',e=>{e.stopPropagation();toggleMenu()});menu.addEventListener('click',e=>e.stopPropagation());
document.addEventListener('click',e=>{if(!started||menu.classList.contains('show')||e.target.closest('a,button,#menuPanel'))return;setScene(scene+1,true)});
let ac=null,master=null,tones=[];
function setupAudio(){if(ac||!(window.AudioContext||window.webkitAudioContext))return;ac=new(window.AudioContext||window.webkitAudioContext)();master=ac.createGain();master.gain.value=.0001;master.connect(ac.destination);[55,82.41,110,164.81].forEach((f,i)=>{const o=ac.createOscillator(),g=ac.createGain();o.type=i%2?'sine':'triangle';o.frequency.value=f;g.gain.value=.026/(i+1);o.connect(g);g.connect(master);o.start();tones.push({o,g})});const lfo=ac.createOscillator(),lg=ac.createGain();lfo.frequency.value=.075;lg.gain.value=7;lfo.connect(lg);lg.connect(tones[2].o.detune);lfo.start();audioOn=true;ramp(.28);qs('#soundBtn').textContent='Sound on'}
function ramp(v){if(!ac||!master)return;master.gain.cancelScheduledValues(ac.currentTime);master.gain.linearRampToValueAtTime(.045*v,ac.currentTime+.75)}
async function toggleSound(){if(!ac){setupAudio();if(ac?.state==='suspended')await ac.resume();return}audioOn=!audioOn;master.gain.cancelScheduledValues(ac.currentTime);master.gain.linearRampToValueAtTime(audioOn?.012:.0001,ac.currentTime+.4);qs('#soundBtn').textContent=audioOn?'Sound on':'Sound off'}
qs('#soundBtn').addEventListener('click',e=>{e.stopPropagation();toggleSound()});
document.addEventListener('pointermove',e=>{mouse.tx=e.clientX/innerWidth;mouse.ty=1-e.clientY/innerHeight});
const pc=qs('#particles'),ctx=pc.getContext('2d'),pts=[],count=reduced?0:(innerWidth<720?84:138);for(let i=0;i<count;i++)pts.push({x:Math.random()*innerWidth,y:Math.random()*innerHeight,vx:(Math.random()-.5)*.22,vy:(Math.random()-.5)*.22,z:.35+Math.random()*.8});
function resizeParticles(){const d=Math.min(devicePixelRatio||1,1.7);pc.width=innerWidth*d;pc.height=innerHeight*d;pc.style.width=innerWidth+'px';pc.style.height=innerHeight+'px';ctx.setTransform(d,0,0,d,0,0)}addEventListener('resize',resizeParticles);resizeParticles();
function particles(){if(reduced)return;ctx.clearRect(0,0,innerWidth,innerHeight);for(let i=0;i<pts.length;i++){const a=pts[i];let dx=a.x-mouse.tx*innerWidth,dy=a.y-(1-mouse.ty)*innerHeight,dd=Math.hypot(dx,dy)||1;if(dd<170){a.vx+=dx/dd*.005;a.vy+=dy/dd*.005}a.x+=a.vx*a.z;a.y+=a.vy*a.z;if(a.x<0)a.x=innerWidth;if(a.x>innerWidth)a.x=0;if(a.y<0)a.y=innerHeight;if(a.y>innerHeight)a.y=0;a.vx*=.998;a.vy*=.998;for(let j=i+1;j<pts.length;j++){const b=pts[j],x=a.x-b.x,y=a.y-b.y,d2=x*x+y*y;if(d2<6400){const al=(1-Math.sqrt(d2)/80)*.075;ctx.strokeStyle=i%2===0?'rgba(22,140,250,'+al+')':'rgba(141,120,255,'+al+')';ctx.lineWidth=.5;ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke()}}const alpha=.24+a.z*.3;if(i%17===0)ctx.fillStyle='rgba(0,255,65,.42)';else if(i%3===0)ctx.fillStyle='rgba(141,120,255,'+alpha+')';else if(i%3===1)ctx.fillStyle='rgba(22,140,250,'+alpha+')';else ctx.fillStyle='rgba(255,255,255,'+alpha+')';if(i%5===0){const w=1.2+a.z*1.8,h=.7+a.z*.8;ctx.fillRect(a.x-w/2,a.y-h/2,w,h)}else{ctx.beginPath();ctx.arc(a.x,a.y,.45+a.z*.78,0,7);ctx.fill()}}requestAnimationFrame(particles)}if(!reduced)requestAnimationFrame(particles);

// Living light field. Decorative only; semantic content remains DOM text.
const glc=qs('#gl'),gl=glc&&glc.getContext&&glc.getContext('webgl2',{antialias:false,alpha:false});
if(gl&&!reduced){
  const vs='#version 300 es\nprecision highp float;in vec2 p;void main(){gl_Position=vec4(p,0.,1.);}';
  const fs='#version 300 es\nprecision highp float;out vec4 o;uniform vec2 r;uniform float t;float h(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}float n(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(h(i),h(i+vec2(1,0)),f.x),mix(h(i+vec2(0,1)),h(i+vec2(1)),f.x),f.y);}void main(){vec2 u=(gl_FragCoord.xy-.5*r)/min(r.x,r.y);float q=n(u*2.2+vec2(t*.035,-t*.026));float d=length(u);float a=atan(u.y,u.x);float ring=.018/(abs(d-(.30+.045*sin(t*.16+a*4.)))+.028);float beam=pow(max(0.,cos(a*3.+t*.11+sin(d*7.))),9.);vec3 c=vec3(.004,.008,.02)+vec3(.086,.55,.98)*(q*q*.24)+vec3(.55,.47,1.)*ring*.12+vec3(0.,1.,.255)*beam*.012;c*=1.-smoothstep(.55,1.05,d)*.8;o=vec4(pow(c,vec3(.86)),1.);}';
  const sh=(type,src)=>{const x=gl.createShader(type);gl.shaderSource(x,src);gl.compileShader(x);return gl.getShaderParameter(x,gl.COMPILE_STATUS)?x:null};
  const v=sh(gl.VERTEX_SHADER,vs),f=sh(gl.FRAGMENT_SHADER,fs);
  if(v&&f){
    const p=gl.createProgram();gl.attachShader(p,v);gl.attachShader(p,f);gl.linkProgram(p);gl.useProgram(p);
    const b=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,b);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,3,-1,-1,3]),gl.STATIC_DRAW);
    const l=gl.getAttribLocation(p,'p');gl.enableVertexAttribArray(l);gl.vertexAttribPointer(l,2,gl.FLOAT,false,0,0);
    const ur=gl.getUniformLocation(p,'r'),ut=gl.getUniformLocation(p,'t');
    const rg=()=>{const d=Math.min(devicePixelRatio||1,1.5);glc.width=innerWidth*d;glc.height=innerHeight*d;gl.viewport(0,0,glc.width,glc.height)};addEventListener('resize',rg);rg();
    const draw=now=>{gl.uniform2f(ur,glc.width,glc.height);gl.uniform1f(ut,now*.001);gl.drawArrays(gl.TRIANGLES,0,3);requestAnimationFrame(draw)};requestAnimationFrame(draw);
  }
}

update();
schedule();
})();