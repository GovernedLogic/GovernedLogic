(function () {
  "use strict";
  const experience=document.querySelector(".origin-experience");
  const stage=experience&&experience.querySelector(".origin-stage");
  const baseline=stage&&stage.querySelector("#origin-canvas");
  if(!experience||!stage||!baseline||stage.dataset.originEffectsV05==="ready")return;

  const TAU=Math.PI*2, STORY_SECONDS=22, LOOP_COUNT=3;
  const reduceMotion=window.matchMedia("(prefers-reduced-motion: reduce)");
  const mobileQuery=window.matchMedia("(max-width: 720px)");
  const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
  const mix=(a,b,t)=>a+(b-a)*t;
  const smooth=(a,b,v)=>{const t=clamp((v-a)/Math.max(.00001,b-a),0,1);return t*t*(3-2*t);};
  const ease=v=>1-Math.pow(1-clamp(v,0,1),3);
  const rnd=seed=>{const x=Math.sin(seed*12.9898+78.233)*43758.5453;return x-Math.floor(x);};

  function layer(name,z){
    const c=document.createElement("canvas");
    c.className="origin-effects-v05 "+name;c.setAttribute("aria-hidden","true");
    Object.assign(c.style,{position:"absolute",inset:"0",width:"100%",height:"100%",pointerEvents:"none",zIndex:String(z)});
    return c;
  }
  const back=layer("origin-effects-v05-back",0),front=layer("origin-effects-v05-front",2);
  const center=stage.querySelector("#origin-center");
  stage.insertBefore(back,baseline);stage.insertBefore(front,center||null);
  const b=back.getContext("2d",{alpha:true,desynchronized:true}),f=front.getContext("2d",{alpha:true,desynchronized:true});
  if(!b||!f){back.remove();front.remove();return;}
  stage.dataset.originEffectsV05="ready";

  let w=1,h=1,dpr=1,progress=0,gather=0,last=0,raf=0,autoplay=true,visible=true,top=0,scrollDistance=1,particles=[];

  function makeParticles(count){
    const out=[];for(let i=0;i<count;i++)out.push({a:rnd(i+11)*TAU,r:mix(.22,.98,Math.sqrt(rnd(i+37))),z:mix(-.9,.72,rnd(i+83)),s:mix(.45,1.15,rnd(i+121)),p:rnd(i+199)*TAU,speed:mix(.45,1.08,rnd(i+271))});return out;
  }
  function getGather(){return clamp((window.scrollY-top)/scrollDistance,0,1);}
  function resize(){
    const rect=experience.getBoundingClientRect();w=Math.max(1,stage.clientWidth);h=Math.max(1,stage.clientHeight);
    dpr=Math.min(window.devicePixelRatio||1,mobileQuery.matches ? 1.25:1.65);
    [back,front].forEach(c=>{c.width=Math.round(w*dpr);c.height=Math.round(h*dpr);c.style.width=w+"px";c.style.height=h+"px";});
    [b,f].forEach(c=>c.setTransform(dpr,0,0,dpr,0,0));
    top=window.scrollY+rect.top;scrollDistance=Math.max(1,rect.height-stage.clientHeight);
    particles=makeParticles(mobileQuery.matches ? 36:78);gather=getGather();render(progress,gather);
  }
  function clear(){[b,f].forEach(c=>{c.setTransform(dpr,0,0,dpr,0,0);c.clearRect(0,0,w,h);});}
  function project(x,y,z,rx=.12,ry=-.08,rz=0){
    const cx=Math.cos(rx),sx=Math.sin(rx),cy=Math.cos(ry),sy=Math.sin(ry),cz=Math.cos(rz),sz=Math.sin(rz);
    const y1=y*cx-z*sx,z1=y*sx+z*cx,x2=x*cy+z1*sy,z2=-x*sy+z1*cy,x3=x2*cz-y1*sz,y3=x2*sz+y1*cz;
    const cam=Math.max(480,Math.min(w,h)*1.14),p=clamp(cam/Math.max(100,cam-z2),.38,2.2);
    return{x:w/2+x3*p,y:h/2+y3*p,z:z2,p};
  }
  function dot(ctx,x,y,r,alpha,color){
    if(alpha<=.002)return;ctx.save();ctx.globalCompositeOperation="lighter";ctx.fillStyle="rgba("+color+","+alpha.toFixed(4)+")";ctx.shadowColor="rgba("+color+","+(alpha*.72).toFixed(4)+")";ctx.shadowBlur=7;ctx.beginPath();ctx.arc(x,y,r,0,TAU);ctx.fill();ctx.restore();
  }
  function drawParticles(v,g){
    const ge=ease(smooth(.02,.98,g)),scale=mix(1,.045,ge),field=Math.min(w,h)*(mobileQuery.matches ? .82:.75),fade=mix(1,.18,ge),rot=v*.24+ge*TAU*.72,align=smooth(.31,.56,v),dissolve=smooth(.65,.84,v);
    const loopR=Math.min(w,h)*(mobileQuery.matches ? .11:.105)*scale,spacing=loopR*1.7,alignedStart=Math.floor(particles.length*.42),alignedTotal=particles.length-alignedStart;
    particles.forEach((q,i)=>{
      const reveal=smooth(.06+rnd(i+9)*.08,.22+rnd(i+9)*.08,v);let x=Math.cos(q.a+rot*q.speed)*q.r*field*scale,y=Math.sin(q.a+rot*q.speed)*q.r*field*.72*scale,z=(q.z*Math.min(w,h)*.42+Math.sin(q.p+v*TAU*.35)*12)*mix(1,.16,ge);
      if(i>=alignedStart){const n=i-alignedStart,loop=Math.min(2,Math.floor((n/alignedTotal)*LOOP_COUNT)),a=(n/Math.max(1,alignedTotal/LOOP_COUNT))*TAU;const tx=(loop-1)*spacing+Math.cos(a)*loopR,ty=Math.sin(a)*loopR,tz=Math.sin(a)*loopR*.62*(loop%2?-1:1);x=mix(x,tx,align);y=mix(y,ty,align);z=mix(z,tz,align);}
      const pt=project(x,y,z,.12,-.07,rot*.18),ctx=pt.z>0?f:b,a=reveal*fade*mix(.38,.72,rnd(i+401))*mix(1,.45,dissolve);
      dot(ctx,pt.x,pt.y,q.s*mix(.65,1.55,clamp((pt.z/Math.min(w,h)+.5),0,1)),a,"226,242,255");
    });
  }
  function traceArc(ctx,cx,cy,r,start,amount,alpha,color,width,glow){
    if(amount<=0)return null;const end=start+TAU*clamp(amount,0,1);ctx.save();ctx.lineCap="round";ctx.lineWidth=width;ctx.strokeStyle="rgba("+color+","+alpha.toFixed(4)+")";ctx.shadowColor="rgba("+color+","+(alpha*.65).toFixed(4)+")";ctx.shadowBlur=glow;ctx.beginPath();ctx.arc(cx,cy,r,start,end,false);ctx.stroke();ctx.restore();return{x:cx+Math.cos(end)*r,y:cy+Math.sin(end)*r};
  }
  function leader(pt,alpha){
    if(!pt||alpha<=.002)return;const R=mobileQuery.matches ? 12:17,g=f.createRadialGradient(pt.x,pt.y,0,pt.x,pt.y,R);g.addColorStop(0,"rgba(255,255,255,"+alpha.toFixed(3)+")");g.addColorStop(.2,"rgba(213,240,255,"+(alpha*.9).toFixed(3)+")");g.addColorStop(.5,"rgba(155,110,255,"+(alpha*.55).toFixed(3)+")");g.addColorStop(1,"rgba(95,55,205,0)");f.save();f.globalCompositeOperation="lighter";f.fillStyle=g;f.beginPath();f.arc(pt.x,pt.y,R,0,TAU);f.fill();f.fillStyle="rgba(255,255,255,"+alpha.toFixed(3)+")";f.beginPath();f.arc(pt.x,pt.y,mobileQuery.matches ? 1.5:2,0,TAU);f.fill();f.restore();
  }
  function drawSeed(v,g){
    const alpha=smooth(.25,.42,v)*(1-smooth(.62,.82,v))*(1-smooth(.08,.98,g)*.82);if(alpha<=.002)return;
    const R=Math.min(w,h)*(mobileQuery.matches ? .067:.078)*mix(1,.08,ease(g)),total=smooth(.28,.57,v)*7;let lead=null;
    for(let i=0;i<7;i++){const amount=clamp(total-i,0,1);if(amount<=0)continue;const a=i===0?0:((i-1)/6)*TAU,cx=w/2+(i===0?0:Math.cos(a)*R),cy=h/2+(i===0?0:Math.sin(a)*R);lead=traceArc(b,cx,cy,R,-Math.PI/2,amount,alpha*.18,"190,221,242",mobileQuery.matches ? .55:.72,3);}
    if(total<6.98)leader(lead,alpha*.62);
  }
  function drawLoops(v,g){
    const appear=smooth(.39,.48,v),dissolve=smooth(.67,.82,v),ge=ease(g),alpha=appear*(1-dissolve*.94)*mix(1,.1,smooth(.04,.94,g));if(alpha<=.002)return;
    const R=Math.min(w,h)*(mobileQuery.matches ? .115:.105)*mix(1,.055,ge),spacing=R*1.72,total=(reduceMotion.matches?1:smooth(.40,.67,v))*LOOP_COUNT;let lead=null;
    for(let i=0;i<LOOP_COUNT;i++){const amount=clamp(total-i,0,1);if(amount<=0)continue;const cx=w/2+(i-1)*spacing,cy=h/2,start=i%2===0?0:Math.PI,ctx=i===1?f:b;traceArc(ctx,cx,cy,R,start,amount,alpha*.34,"17,51,87",mobileQuery.matches ? 3:4.6,0);traceArc(ctx,cx,cy,R,start,amount,alpha*.82,"217,238,252",mobileQuery.matches ? 1.15:1.8,mobileQuery.matches ? 5:8);lead={x:cx+Math.cos(start+TAU*amount)*R,y:cy+Math.sin(start+TAU*amount)*R};}
    if(total<LOOP_COUNT-.01)leader(lead,appear*mix(1,.15,dissolve));
  }
  function drawNetwork(v,g){
    const form=smooth(.68,.88,v),ge=ease(smooth(.02,.98,g)),alpha=form*mix(1,.16,smooth(.05,.96,g));if(alpha<=.002)return;
    const R=Math.min(w,h)*(mobileQuery.matches ? .16:.19)*mix(1,.055,ge),D=R*.58,rot=v*.85+ge*.32,raw=[[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1],[0,0,-1.55],[0,0,1.55]];
    const nodes=raw.map((q,i)=>{const jitter=1-form,ph=i*1.73+v*TAU*.45;return project(q[0]*R*.72+Math.cos(ph)*R*.34*jitter,q[1]*R*.72+Math.sin(ph*1.13)*R*.34*jitter,q[2]*D+Math.sin(ph*.77)*D*.45*jitter,.42+v*.08,-.28+v*.06,rot);});
    const edges=[[0,1],[1,2],[2,3],[3,0],[4,5],[5,6],[6,7],[7,4],[0,4],[1,5],[2,6],[3,7],[8,0],[8,1],[8,2],[8,3],[9,4],[9,5],[9,6],[9,7]];
    edges.forEach((e,i)=>{const a=nodes[e[0]],z=nodes[e[1]],ctx=((a.z+z.z)/2)>0?f:b,birth=smooth(.69+(i%6)*.01,.88+(i%6)*.006,v);ctx.save();ctx.lineWidth=mobileQuery.matches ? .48:.68;ctx.strokeStyle="rgba(125,171,255,"+(alpha*birth*.28).toFixed(4)+")";ctx.shadowColor="rgba(155,112,255,"+(alpha*birth*.32).toFixed(4)+")";ctx.shadowBlur=5;ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(z.x,z.y);ctx.stroke();ctx.restore();});
    nodes.forEach((p,i)=>dot(p.z>0?f:b,p.x,p.y,mobileQuery.matches ? .85:1.2,alpha*smooth(.68+(i%5)*.018,.84+(i%5)*.012,v)*.82,"235,247,255"));
    const cloudCount=mobileQuery.matches ? 48:110,rr=R*1.45;for(let i=0;i<cloudCount;i++){const a=i*2.399963+v*(.8+(i%7)*.035),r=rr*(.48+.52*rnd(i+901)),x=w/2+Math.cos(a)*r,y=h/2+Math.sin(a)*r*.72;dot(i%3===0?f:b,x,y,mobileQuery.matches ? .38:.55,alpha*smooth(.66,.85,v)*.3,"205,232,255");}
  }
  function render(v,g){clear();drawParticles(v,g);drawSeed(v,g);drawLoops(v,g);drawNetwork(v,g);}
  function wake(){if(!raf&&visible&&!reduceMotion.matches){last=0;raf=requestAnimationFrame(frame);}}
  function frame(now){raf=0;if(!visible||reduceMotion.matches)return;const dt=last?Math.min(.05,(now-last)/1000):0;last=now;if(autoplay){progress=clamp(progress+dt/STORY_SECONDS,0,1);if(progress>=1)autoplay=false;}render(progress,gather);if(autoplay)raf=requestAnimationFrame(frame);}
  function onScroll(){const n=getGather();if(Math.abs(n-gather)>.0005){gather=n;render(progress,gather);}}
  function reduced(){autoplay=false;progress=1;gather=getGather();render(progress,gather);}
  addEventListener("scroll",onScroll,{passive:true});addEventListener("resize",()=>requestAnimationFrame(resize),{passive:true});document.addEventListener("visibilitychange",()=>{visible=!document.hidden;if(visible)wake();});
  if("IntersectionObserver" in window)new IntersectionObserver(e=>{visible=!!(e[0]&&e[0].isIntersecting);if(visible)wake();},{threshold:.01}).observe(experience);
  if(reduceMotion.addEventListener)reduceMotion.addEventListener("change",()=>reduceMotion.matches?reduced():wake());
  resize();gather=getGather();if(reduceMotion.matches)reduced();else if(gather>.001){autoplay=false;progress=1;render(progress,gather);}else wake();
})();