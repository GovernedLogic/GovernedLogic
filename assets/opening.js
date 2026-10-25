/* Governed Logic opening. Native rendering; no bitmap identity or external dependency.
   GL_MARK_TRACE plays the mark. Set it to false for the Spirograph and Earth intro. */
const GL_MARK_TRACE = true;
(() => {
  'use strict';
  const TAU = Math.PI * 2;
  const EARTH_U_OFFSET=.02*TAU,EARTH_TILT_START=.05,EARTH_TILT_END=1.02;
  const clamp = x => Math.max(0, Math.min(1, x));
  const ease = x => { x = clamp(x); return x*x*x*(x*(x*6-15)+10); };
  const phase = (time,start,end) => ease((time-start)/(end-start));
  const wrapLongitude = x => ((x+Math.PI)%TAU+TAU)%TAU-Math.PI;
  // The pauses are part of the composition: release, organization, recognition.
  // Surface material arrives only after the same particles describe a globe.
  const TIMELINE = Object.freeze({
    pointStart:.75,
    starStart:1.55,
    starEnd:2.6,
    burstStart:2.35,
    burstEnd:3.75,
    orbitStart:3.1,
    orbitEnd:5.15,
    petalStart:4.75,
    petalEnd:6.2,
    greenStart:5.95,
    greenEnd:7.15,
    sphereStart:7.95,
    sphereEnd:10.05,
    centerFadeStart:8.05,
    centerFadeEnd:9.7,
    greenFadeStart:9.85,
    greenFadeEnd:11.55,
    materialStart:9.9,
    materialEnd:11.25,
    settleStart:11.05,
    settleEnd:13.55,
    environmentStart:12,
    environmentEnd:14.1,
    tokenFadeStart:11.85,
    tokenFadeEnd:13.65,
    identityStart:13.05,
    identityEnd:14.7,
    finalAt:15.1,
    deadline:16.1
  });
  const mix = (a,b,t) => a+(b-a)*t;
  const rand = n => { const x=Math.sin(n*127.1+311.7)*43758.5453123; return x-Math.floor(x); };
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  const siteCanvas = document.getElementById('siteCanvas');
  if (!siteCanvas) return;
  const context = siteCanvas.getContext('2d', {alpha:false});
  if (!context) return; // The semantic HTML identity is the no-canvas fallback.
  let width=0, height=0, dpr=1, intro=null, raf=0, deadline=0, finishTimer=0;
  const MATERIAL_HANDOFF_MS=420;
  const scene = document.createElement('canvas');
  const sceneCtx = scene.getContext('2d', {alpha:false});
  const atmosphere = document.createElement('canvas');
  const atmosphereCtx = atmosphere.getContext('2d', {alpha:false});
  if (!sceneCtx || !atmosphereCtx) return;
  let layout,materialReadyAt=null,materialHandoffRaf=0;
  const materialEarth=window.GLCreateEarth?.(beginMaterialHandoff);
  const fallbackSurface=document.createElement('canvas');
  const fallbackContext=fallbackSurface.getContext('2d');
  function materialBlend(now=performance.now()){return materialEarth?.ready&&materialReadyAt!==null?ease((now-materialReadyAt)/MATERIAL_HANDOFF_MS):0;}
  function beginMaterialHandoff(){materialReadyAt=performance.now();cancelAnimationFrame(materialHandoffRaf);materialHandoffRaf=requestAnimationFrame(drawMaterialHandoff);}
  function drawMaterialHandoff(now){
    if(!layout||!materialEarth?.ready){materialHandoffRaf=0;return;}
    backdrop(sceneCtx);context.drawImage(scene,0,0,width,height);
    if(materialBlend(now)<1)materialHandoffRaf=requestAnimationFrame(drawMaterialHandoff);else materialHandoffRaf=0;
  }
  function size(canvas, ctx) {
    canvas.width=Math.round(width*dpr);canvas.height=Math.round(height*dpr);
    ctx.setTransform(dpr,0,0,dpr,0,0);
  }
  function glow(ctx,x,y,r,color,strength=1) {
    if(r<=0 || strength<=0)return;
    const g=ctx.createRadialGradient(x,y,0,x,y,r);
    g.addColorStop(0,`rgba(${color},${strength})`);
    g.addColorStop(.09,`rgba(${color},${strength*.52})`);
    g.addColorStop(.35,`rgba(${color},${strength*.12})`);
    g.addColorStop(1,`rgba(${color},0)`);
    ctx.fillStyle=g;ctx.fillRect(x-r,y-r,r*2,r*2);
  }
  // Coarse geographic silhouettes establish Earth, rather than a generic sphere.
  const land = [
    [[-168,65],[-145,70],[-130,55],[-124,49],[-122,37],[-111,29],[-97,18],[-87,20],[-81,26],[-81,32],[-70,44],[-59,49],[-64,59],[-82,63],[-95,75],[-130,72]],
    [[-81,12],[-70,10],[-59,6],[-48,-1],[-35,-7],[-41,-23],[-51,-30],[-66,-55],[-74,-48],[-70,-30],[-81,-5]],
    [[-17,35],[0,37],[12,33],[34,30],[43,12],[51,11],[42,-4],[34,-13],[29,-31],[18,-35],[12,-18],[9,4],[-4,5],[-17,15]],
    [[-11,36],[-10,44],[1,50],[5,58],[20,71],[33,69],[42,56],[57,52],[68,57],[100,75],[140,71],[180,65],[160,52],[141,41],[126,40],[122,23],[107,4],[99,9],[80,8],[69,25],[52,13],[42,30],[28,41],[20,36]],
    [[112,-11],[132,-12],[142,-10],[153,-27],[146,-39],[131,-32],[114,-35]],
    [[-54,59],[-42,61],[-19,78],[-42,84],[-63,76]],
    [[47,-13],[50,-16],[47,-26],[43,-24]]
  ];
  function inLand(lon,lat) {
    return land.some(poly=>{let yes=false;for(let i=0,j=poly.length-1;i<poly.length;j=i++){
      const a=poly[i],b=poly[j];if((a[1]>lat)!==(b[1]>lat)&&lon<(b[0]-a[0])*(lat-a[1])/(b[1]-a[1])+a[0])yes=!yes;
    }return yes;});
  }
  // Procedural orthographic Earth surface, generated once from geographic silhouettes.
  const globeTexture=document.createElement('canvas');globeTexture.width=512;globeTexture.height=512;
  const textureContext=globeTexture.getContext('2d');
  if(!textureContext)return;
  const pixels=textureContext.createImageData(512,512);
  const fallbackTiltCos=Math.cos(EARTH_TILT_START),fallbackTiltSin=Math.sin(EARTH_TILT_START);
  for(let y=0;y<512;y++)for(let x=0;x<512;x++){
    const nx=(x-255.5)/256,ny=(255.5-y)/256,rr=nx*nx+ny*ny;
    if(rr>1)continue;
    const z=Math.sqrt(1-rr),materialY=ny*fallbackTiltCos-z*fallbackTiltSin,materialZ=ny*fallbackTiltSin+z*fallbackTiltCos;
    const lat=Math.asin(materialY),lon=wrapLongitude(Math.atan2(materialZ,nx)+EARTH_U_OFFSET);
    const landHere=inLand(lon*180/Math.PI,lat*180/Math.PI);
    const noise=(Math.sin(lon*83+Math.sin(lat*61)*2)+Math.sin(lat*137+lon*37)+Math.cos(lon*217-lat*151))/3;
    const light=.15+.85*Math.max(0,-nx*.22+ny*.55+z*.72);
    const clouds=Math.max(0,Math.sin(lon*14+lat*9+Math.sin(lat*21)*2)+Math.cos(lat*32-lon*8)-1.0)*.65;
    const base=landHere?[85+noise*20,101+noise*20,80+noise*16]:[12,43+noise*6,66+noise*10];
    const k=(y*512+x)*4;
    for(let c=0;c<3;c++)pixels.data[k+c]=mix(base[c],210,clouds)*light;
    pixels.data[k+3]=255;
  }
  textureContext.putImageData(pixels,0,0);
  function fallbackEarth(ctx,cx,cy,rx,ry,alpha=1) {
    ctx.save();ctx.globalAlpha*=alpha;
    ctx.drawImage(globeTexture,cx-rx,cy-ry,rx*2,ry*2);
    ctx.beginPath();ctx.ellipse(cx,cy,rx,ry,0,0,TAU);ctx.clip();
    const shade=ctx.createLinearGradient(0,cy-ry,0,cy+ry);
    shade.addColorStop(0,'#0000');shade.addColorStop(.32,'#0002');shade.addColorStop(.7,'#000b');shade.addColorStop(1,'#000');ctx.fillStyle=shade;ctx.fillRect(cx-rx,cy-ry,rx*2,ry*2);
    ctx.restore();ctx.save();ctx.globalAlpha*=alpha;
    ctx.strokeStyle='#88cfff66';ctx.lineWidth=1;ctx.beginPath();ctx.ellipse(cx,cy,rx,ry,0,Math.PI*1.03,Math.PI*1.97);ctx.stroke();
    glow(ctx,cx,cy-ry,rx*.35,'182,217,250',.45);
    glow(ctx,cx,cy-ry,rx*.13,'255,218,155',.8);ctx.restore();
  }
  function earth(ctx,cx,cy,r,cap=0,alpha=1){
    if(alpha<=0)return;
    ctx.save();ctx.globalAlpha*=alpha;
    const earthAlpha=ctx.globalAlpha,materialAmount=materialBlend();
    const materialSurface=materialAmount>0?materialEarth.render(width,height,dpr,cx,cy,r,cap,layout.scale):null;
    if(fallbackContext&&(!materialSurface||materialAmount<1)){
      if(fallbackSurface.width!==Math.round(width*dpr)||fallbackSurface.height!==Math.round(height*dpr))size(fallbackSurface,fallbackContext);
      const f=fallbackContext,s=layout.scale,top=cy-r;
      f.clearRect(0,0,width,height);fallbackEarth(f,cx,cy,r,r,1);
      f.globalCompositeOperation='destination-in';
      const vertical=f.createLinearGradient(0,top+28*s,0,top+148*s);
      vertical.addColorStop(0,'#fff');vertical.addColorStop(1,`rgba(255,255,255,${1-cap})`);
      f.fillStyle=vertical;f.fillRect(0,0,width,height);
      const horizontal=f.createLinearGradient(cx-700*s,0,cx+700*s,0);
      for(let i=0;i<=20;i++){const x=(i/20-.5)*1400;horizontal.addColorStop(i/20,`rgba(255,255,255,${mix(1,Math.exp(-Math.pow(Math.abs(x)/465,4)),cap)})`);}
      f.fillStyle=horizontal;f.fillRect(0,0,width,height);f.globalCompositeOperation='source-over';
      ctx.globalAlpha=earthAlpha*(materialSurface?1-materialAmount:1);
      ctx.drawImage(fallbackSurface,0,0,width,height);
    }
    if(materialSurface){ctx.globalAlpha=earthAlpha*materialAmount;ctx.drawImage(materialSurface,0,0,width,height);}
    ctx.globalAlpha=earthAlpha;
    const top=cy-r, s=layout.scale;
    // A sharp light core with restrained, directional bloom at the physical limb.
    glow(ctx,cx,top,50*s,'103,183,238',.48);
    glow(ctx,cx,top,16*s,'255,229,187',.88);
    ctx.strokeStyle='#fff5d6';ctx.lineWidth=Math.max(.6,s*.8);ctx.beginPath();ctx.moveTo(cx-27*s,top);ctx.lineTo(cx+27*s,top);ctx.stroke();
    ctx.restore();
  }
  function backdrop(ctx,withEarth=true) {
    const {cx,base,scale:s,earthY,earthR}=layout;
    if(window.GLMaterialEnvironment){window.GLMaterialEnvironment(ctx,{width,height,cx,base,scale:s});if(withEarth)earth(ctx,cx,earthY,earthR,1);return;}
    ctx.fillStyle='#000';ctx.fillRect(0,0,width,height);
    const sky=ctx.createRadialGradient(cx,base-380*s,0,cx,base-240*s,800*s);
    sky.addColorStop(0,'#152430');sky.addColorStop(.4,'#060c12');sky.addColorStop(1,'#000');ctx.fillStyle=sky;ctx.fillRect(0,0,width,height);
    ctx.save();ctx.globalCompositeOperation='screen';
    // Circuitry sits at the margins, never between the organizing particles.
    for(const side of [-1,1])for(let j=0;j<52;j++){
      const start=side<0?0:width, dir=-side, y=base+(-370+j*8)*s;
      const reach=(110+rand(j+73)*340)*s;
      ctx.strokeStyle=`rgba(29,143,208,${.07+rand(j+17)*.2})`;ctx.lineWidth=.65*s;
      ctx.beginPath();ctx.moveTo(start,y);let x=start+dir*reach*.3;ctx.lineTo(x,y);x+=dir*reach*.2;const dy=(j%2?1:-1)*16*s;ctx.lineTo(x,y+dy);x+=dir*reach*.3;ctx.lineTo(x,y+dy);x+=dir*reach*.2;ctx.lineTo(x,y+dy*2);ctx.stroke();
      ctx.strokeStyle='#47c9ff66';ctx.beginPath();ctx.arc(x,y+dy*2,1.4*s,0,TAU);ctx.stroke();
      if(j%8===0)glow(ctx,x,y+dy*2,17*s,'55,178,255',.7);
      for(let k=0;k<9;k++){ctx.fillStyle='#3b9fce30';ctx.fillRect(start+dir*(k*13+rand(j)*100)*s,y+5*s,2*s,2*s);}
    }
    const hy=base+165*s, floorY=base+218*s;
    glow(ctx,cx,hy,410*s,'17,111,172',.22);
    // Perspective floor: fine interrupted rings, radial traces and reflections.
    for(let j=0;j<35;j++){
      const rx=(50+j*j*1.25)*s,ry=rx*.113;
      ctx.strokeStyle=`rgba(77,166,207,${.06+rand(j+90)*.16})`;ctx.lineWidth=(j%6===0?.9:.45)*s;
      ctx.beginPath();ctx.ellipse(cx,floorY,rx,ry,0,0,TAU);ctx.stroke();
      for(let k=0;k<4;k++){
        const a=rand(j*8+k+404)*TAU;ctx.strokeStyle=`rgba(116,210,240,${.1+rand(j+k)*.3})`;ctx.beginPath();ctx.ellipse(cx,floorY,rx,ry,0,a,a+.05+rand(k+j)*.18);ctx.stroke();
      }
    }
    for(let j=-24;j<=24;j++){
      ctx.strokeStyle=j%5===0?'#438aaa38':'#32678520';ctx.lineWidth=.7*s;
      ctx.beginPath();ctx.moveTo(cx+j*7*s,hy);ctx.lineTo(cx+j*130*s,base+650*s);ctx.stroke();
    }
    for(let j=0;j<500;j++){
      const a=rand(j+710)*TAU,r=rand(j+72)*1070*s;
      const x=cx+Math.cos(a)*r,y=floorY+Math.sin(a)*r*.113;
      ctx.fillStyle=`rgba(138,212,247,${rand(j+106)*.5})`;ctx.fillRect(x,y,1.5*s,.8*s);
    }
    for(let j=0;j<13;j++){
      const y=floorY+j*j*1.3*s;glow(ctx,cx+(rand(j)-.5)*6*s,y,(14+j)*s,'96,206,255',.28*(1-j/14));
    }
    ctx.strokeStyle='#9eeaff77';ctx.lineWidth=s;ctx.beginPath();ctx.moveTo(cx,hy);ctx.lineTo(cx,base+430*s);ctx.stroke();
    glow(ctx,cx,floorY,85*s,'137,232,255',.66);
    ctx.restore();
    if(withEarth)earth(ctx,cx,earthY,earthR,1);
    // Fade the edges into the physical black field.
    const vignette=ctx.createRadialGradient(cx,base,150*s,cx,base,1100*s);
    vignette.addColorStop(0,'#0000');vignette.addColorStop(.65,'#0000');vignette.addColorStop(1,'#000b');ctx.fillStyle=vignette;ctx.fillRect(0,0,width,height);
  }
  function resize() {
    width=document.documentElement.clientWidth;height=siteCanvas.parentElement.clientHeight;dpr=Math.min(devicePixelRatio||1,2);
    const scale=width/1920,base=height*.5;
    layout={cx:width*.5,base,scale,earthY:base+1100*scale,earthR:1300*scale};
    size(siteCanvas,context);size(scene,sceneCtx);size(atmosphere,atmosphereCtx);backdrop(sceneCtx);backdrop(atmosphereCtx,false);
    context.drawImage(scene,0,0,width,height);
    if(intro)size(intro.canvas,intro.ctx);
  }
  function removeIntro() {
    cancelAnimationFrame(raf);clearTimeout(deadline);clearTimeout(finishTimer);
    if(intro){intro.element.remove();intro=null;}
    motion.removeEventListener('change',motionChanged);
    document.removeEventListener('visibilitychange',visibilityChanged);
  }
  function motionChanged(){if(motion.matches)removeIntro();}
  function visibilityChanged(){if(document.hidden)removeIntro();}
  addEventListener('resize',resize,{passive:true});
  try{resize();}catch{ return; }
  if(motion.matches || document.hidden)return;
  if(GL_MARK_TRACE)return;
  try {
    const count=Math.min(window.innerWidth,window.innerHeight)<=600?3360:5760;
    const loops=24,samples=count/loops;
    const particles=Array.from({length:count},(_,i)=>{
      const loop=i%loops,phi=loop/loops*TAU;
      const theta=(Math.floor(i/loops)+.5)/samples*TAU;
      // Twenty-four circles, each tangent to the center, reproduce the dense
      // interlocking radial mark. These are points on loops, never drawn lines.
      const sx=.5*(Math.cos(phi)+Math.cos(theta+phi));
      const sy=.5*(Math.sin(phi)+Math.sin(theta+phi));
      const a=Math.atan2(sy,sx),z=1-2*rand(i+4107),rho=Math.sqrt(1-z*z);
      const vx=Math.cos(a)*rho,vy=-Math.sin(a)*rho;
      // Assign the sphere on the same radial bearing as the petal point. The
      // transformation gains depth without particles crossing the whole image.
      const mx=vx,my=vy*fallbackTiltCos-z*fallbackTiltSin,mz=vy*fallbackTiltSin+z*fallbackTiltCos;
      const lat=Math.asin(my),lon=wrapLongitude(Math.atan2(mz,mx)+EARTH_U_OFFSET);
      return {a,r:rand(i+1),s:rand(i+999),c:rand(i+2048),sx,sy,mx,my,mz,
        dirX:Math.cos(a),dirY:Math.sin(a),deflect:.12*Math.sin(phi),
        orbitCos:Math.cos(theta+phi),orbitSin:Math.sin(theta+phi),
        phiCos:Math.cos(phi),phiSin:Math.sin(phi),
        orbitalRadius:.56+.23*Math.sin(phi*.5)**2,inclination:.28+.54*Math.abs(Math.sin(phi)),
        orbitDepth:Math.sqrt(1-(.28+.54*Math.abs(Math.sin(phi)))**2),
        land:inLand(lon*180/Math.PI,lat*180/Math.PI)};
    });
    const element=document.createElement('div');element.id='glIntro';element.setAttribute('aria-hidden','true');
    const canvas=document.createElement('canvas');canvas.className='intro-canvas';
    const ctx=canvas.getContext('2d',{alpha:false});if(!ctx)return;
    const identity=document.querySelector('#site .identity').cloneNode(true);
    identity.querySelectorAll('[id]').forEach(n=>n.id+='-intro');
    identity.querySelectorAll('[fill],[stroke],[filter]').forEach(n=>{for(const a of ['fill','stroke','filter']){const v=n.getAttribute(a);if(v?.startsWith('url(#'))n.setAttribute(a,v.replace(')', '-intro)'));}});
    element.append(canvas,identity);intro={element,canvas,ctx,identity};size(canvas,ctx);
    document.body.appendChild(element);
    // Independent safety deadline removes the overlay even after a rendering failure.
    deadline=setTimeout(removeIntro,TIMELINE.deadline*1000);
    motion.addEventListener('change',motionChanged);
    document.addEventListener('visibilitychange',visibilityChanged);
    const start=performance.now();
    const stages=[['black',0],['point',TIMELINE.pointStart],['star',TIMELINE.starStart],['release',TIMELINE.burstStart],['orbits',TIMELINE.orbitStart],['spirograph',TIMELINE.petalEnd],['green',TIMELINE.greenEnd],['globe',TIMELINE.sphereStart],['material',TIMELINE.materialStart],['horizon',TIMELINE.settleStart],['identity',TIMELINE.identityStart]];
    let stage='';
    function frame(now) {
      if(!intro)return;
      try {
        const t=(now-start)/1000;
        const currentStage=stages.findLast(item=>t>=item[1])?.[0]||'black';
        if(stage!==currentStage){stage=currentStage;element.dataset.stage=stage;}
        ctx.fillStyle='#000';ctx.fillRect(0,0,width,height);
        const u=Math.min(width,height),cx=width*.5,cy=height*.5;
        if(t>=TIMELINE.pointStart && t<TIMELINE.starEnd){
          const point=phase(t,TIMELINE.pointStart,TIMELINE.starStart),star=phase(t,TIMELINE.starStart,TIMELINE.starEnd);
          glow(ctx,cx,cy,u*(.006+.025*star),'218,239,255',(.08+.5*star)*point);
          if(star>.02){
            ctx.save();ctx.globalAlpha=star*.72;
            const ray=ctx.createLinearGradient(cx-u*.045,0,cx+u*.045,0);
            ray.addColorStop(0,'#fff0');ray.addColorStop(.48,'#e3f5ff44');ray.addColorStop(.5,'#fff');ray.addColorStop(.52,'#e3f5ff44');ray.addColorStop(1,'#fff0');
            ctx.fillStyle=ray;ctx.fillRect(cx-u*.045,cy-.4,u*.09,.8);ctx.restore();
          }
          ctx.globalAlpha=point;ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(cx,cy,.65+star*.85,0,TAU);ctx.fill();ctx.globalAlpha=1;
        }
        const reveal=phase(t,TIMELINE.environmentStart,TIMELINE.environmentEnd);
        if(reveal>0){ctx.globalAlpha=reveal;ctx.drawImage(t<TIMELINE.settleEnd?atmosphere:scene,0,0,width,height);ctx.globalAlpha=1;}
        if(t>=TIMELINE.burstStart && t<TIMELINE.tokenFadeEnd){
          const burst=phase(t,TIMELINE.burstStart,TIMELINE.burstEnd);
          const orbit=phase(t,TIMELINE.orbitStart,TIMELINE.orbitEnd);
          const petal=phase(t,TIMELINE.petalStart,TIMELINE.petalEnd);
          const sphere=phase(t,TIMELINE.sphereStart,TIMELINE.sphereEnd);
          const settle=phase(t,TIMELINE.settleStart,TIMELINE.settleEnd);
          const materialize=phase(t,TIMELINE.materialStart,TIMELINE.materialEnd);
          const particleFade=1-phase(t,TIMELINE.tokenFadeStart,TIMELINE.tokenFadeEnd);
          const radius=u*.32,earthX=mix(cx,layout.cx,settle),earthY=mix(cy,layout.earthY,settle),rx=mix(u*.265,layout.earthR,settle),ry=rx;
          const green=phase(t,TIMELINE.greenStart,TIMELINE.greenEnd)*(1-phase(t,TIMELINE.greenFadeStart,TIMELINE.greenFadeEnd));
          const rotation=(t-TIMELINE.petalStart)*.032*(1-sphere);
          const turn=(t-TIMELINE.orbitStart)*.42*(1-petal);
          const rotationCos=Math.cos(rotation),rotationSin=Math.sin(rotation),turnCos=Math.cos(turn),turnSin=Math.sin(turn);
          const globeReadability=sphere*(1-materialize);
          const earthTilt=mix(EARTH_TILT_START,EARTH_TILT_END,settle),tiltCos=Math.cos(earthTilt),tiltSin=Math.sin(earthTilt);
          if(sphere>0&&particleFade>0)glow(ctx,earthX,earthY,rx*1.14,'29,100,151',sphere*.045*particleFade);
          if(materialize>0)earth(ctx,earthX,earthY,rx,settle,materialize);
          // Source-over leaves dark depth between points; additive compositing
          // previously turned the center into an overexposed white disc.
          ctx.globalCompositeOperation='source-over';
          for(let i=0;i<count;i++){
            const p=particles[i],deflect=p.deflect*orbit;
            const dist=radius*(.18+.99*Math.sqrt(p.r))*burst;
            let x=cx+(p.dirX-p.dirY*deflect)*dist,y=cy+(p.dirY+p.dirX*deflect)*dist;
            // Inclined orbital bands collect the outward release. Their shared
            // rotation slows into the exact circle positions of the radial mark.
            const orbitRadius=radius*p.orbitalRadius;
            const ox=(p.orbitCos*turnCos-p.orbitSin*turnSin)*orbitRadius,oy=(p.orbitSin*turnCos+p.orbitCos*turnSin)*orbitRadius;
            const orbitalDepth=oy/radius*p.orbitDepth;
            const orbitalX=ox*p.phiCos-oy*p.inclination*p.phiSin;
            const orbitalY=ox*p.phiSin+oy*p.inclination*p.phiCos;
            x=mix(x,cx+orbitalX,orbit);y=mix(y,cy+orbitalY,orbit);
            const px=p.sx*rotationCos-p.sy*rotationSin,py=p.sx*rotationSin+p.sy*rotationCos;
            const petalDepth=px*.17+py*.12,petalPerspective=1+petalDepth*.12;
            x=mix(x,cx+px*radius*petalPerspective,petal);y=mix(y,cy+py*radius*.94*petalPerspective,petal);
            const globeY=p.my*tiltCos+p.mz*tiltSin,z=-p.my*tiltSin+p.mz*tiltCos;
            x=mix(x,earthX+p.mx*rx,sphere);y=mix(y,earthY-globeY*ry,sphere);
            const capDepth=(y-(earthY-rx))/Math.max(.3,layout.scale);
            const capFade=mix(1,1-ease((capDepth-28)/120),settle);
            const leader=p.c>.988?1.2:1,front=clamp((z+.12)/1.12);
            const orbitalLight=.35+.65*clamp(.5+orbitalDepth*.6);
            const petalLight=.85+.15*clamp(.5+petalDepth*2);
            const surfaceLight=p.land?.7+.3*front:.34+.3*front;
            const depthLight=z<0?.018:surfaceLight;
            const spatialLight=mix(mix(1,orbitalLight,orbit),petalLight,petal);
            const coreAlpha=mix(.21+p.s*.48,.48+p.s*.42,petal);
            const alpha=clamp(coreAlpha*leader*mix(spatialLight,depthLight,sphere)*mix(1,1.15,globeReadability)*particleFade*capFade);
            // White carries the form. A selected minority warms into green;
            // restrained blue on the globe anticipates its material atmosphere.
            const selected=p.c>.7?1:p.c>.58?.24:0,g=green*selected;
            const blueSphere=sphere*(1-g)*.55;
            const red=Math.round(mix(mix(245,74,g),112,blueSphere));
            const grn=Math.round(mix(mix(249,244,g),190,blueSphere));
            const blue=Math.round(mix(mix(255,145,g),236,blueSphere));
            ctx.fillStyle=`rgba(${red},${grn},${blue},${alpha})`;
            const depthSize=mix(mix(1,.9+orbitalDepth*.18,orbit*(1-petal)),.88+.22*front,sphere);
            const rawSize=(.58+p.s*.58)*(p.c>.988?1.15:1)*depthSize*Math.min(1.15,Math.max(.72,width/1400));
            // Subpixel cores lost most of their light to coverage averaging on
            // ordinary screens. A one-CSS-pixel floor keeps each point legible
            // once the geometry has organized, without bloom or connected lines.
            const size=mix(rawSize,Math.max(1.08,rawSize),petal);
            if(p.c>.988){ctx.beginPath();ctx.arc(x,y,size*.5,0,TAU);ctx.fill();}
            else ctx.fillRect(x-size*.5,y-size*.5,size,size);
          }
          ctx.globalCompositeOperation='source-over';
          const center=1-phase(t,TIMELINE.centerFadeStart,TIMELINE.centerFadeEnd);
          if(center>0){
            glow(ctx,cx,cy,u*.018,'217,239,255',center*.3);
            ctx.globalAlpha=center*.85;ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(cx,cy,.9,0,TAU);ctx.fill();ctx.globalAlpha=1;
          }
        }
        identity.style.opacity=String(phase(t,TIMELINE.identityStart,TIMELINE.identityEnd));
        if(t>=TIMELINE.finalAt){element.classList.add('is-finished');finishTimer=setTimeout(removeIntro,470);return;}
        raf=requestAnimationFrame(frame);
      } catch { removeIntro(); }
    }
    raf=requestAnimationFrame(frame);
  }catch{removeIntro();}
})();

/* Mark trace. One point of light follows threeLobeCurve for a single closed pass.
   The permanent hero above is already painted and stays after this overlay leaves. */
(() => {
  if (!GL_MARK_TRACE) return;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)');
  if (reduce.matches || document.hidden) return;
  const siteCanvas = document.getElementById('siteCanvas');
  if (!siteCanvas) return;
  let seen = false;
  try { seen = sessionStorage.getItem('gl-mark-trace') === '1'; } catch { seen = false; }
  if (seen) return;
  try { sessionStorage.setItem('gl-mark-trace', '1'); } catch { /* still play */ }

  const TAU = Math.PI * 2;
  const K = 0.999;
  const AMP = 0.46;
  const SAMPLES = 640;
  const ASIN_K = Math.asin(K);
  const ease = x => { x = Math.max(0, Math.min(1, x)); return x * x * x * (x * (x * 6 - 15) + 10); };
  const pts = Array.from({length: SAMPLES + 1}, (_, i) => {
    const t = (i / SAMPLES) * TAU;
    return {
      x: Math.asin(K * Math.cos(t)) / ASIN_K,
      y: AMP * Math.sin(3 * t),
      z: Math.sin(2 * t)
    };
  });

  let removed = false;
  let raf = 0;
  let skipAt = 0;
  const offs = [];
  const listen = (target, type, fn, options) => {
    target.addEventListener(type, fn, options);
    offs.push(() => target.removeEventListener(type, fn, options));
  };
  const element = document.createElement('div');
  element.id = 'glIntro';
  element.className = 'gl-mark';
  element.setAttribute('aria-hidden', 'true');
  element.dataset.stage = 'black';
  element.style.pointerEvents = 'auto';
  element.style.background = 'transparent';
  const canvas = document.createElement('canvas');
  canvas.className = 'intro-canvas';
  const ctx = canvas.getContext('2d', {alpha: true});
  if (!ctx) return;
  element.append(canvas);
  const remove = () => {
    if (removed) return;
    removed = true;
    clearTimeout(deadline);
    cancelAnimationFrame(raf);
    for (const off of offs) off();
    element.remove();
  };
  // Armed before the overlay is shown. 7.6s is inside the 8s limit.
  const deadline = setTimeout(remove, 7600);
  const skip = () => { if (!removed && !skipAt) skipAt = performance.now(); };
  const y0 = scrollY;
  listen(window, 'pointerdown', skip, true);
  listen(window, 'keydown', skip, true);
  listen(window, 'wheel', skip, {passive: true, capture: true});
  listen(window, 'scroll', () => { if (Math.abs(scrollY - y0) >= 12) skip(); }, {passive: true, capture: true});
  listen(reduce, 'change', () => { if (reduce.matches) remove(); });
  listen(document, 'visibilitychange', () => { if (document.hidden) remove(); });
  document.body.appendChild(element);

  let width = 0;
  let height = 0;
  let half = 1;
  const place = p => [width * 0.5 + p.x * half, height * 0.5 + p.y * half * 0.92];
  function size() {
    width = window.innerWidth;
    height = window.innerHeight;
    const dpr = Math.min(devicePixelRatio || 1, width < 800 ? 1.5 : 2);
    canvas.width = Math.max(1, Math.round(width * dpr));
    canvas.height = Math.max(1, Math.round(height * dpr));
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    half = Math.min(width, height) * 0.34;
  }
  function strand(over, widthPx, color, scale) {
    const head = Math.max(2, Math.round(scale * SAMPLES));
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.lineWidth = widthPx;
    for (let i = 1; i <= head; i++) {
      const p = pts[i];
      const under = p.z < 0;
      if (over ? under : !under) continue;
      if (!over && Math.abs(p.z) < 0.2) continue;
      const fade = Math.exp(-((head - i) / SAMPLES) * 2.4);
      if (fade < 0.035) continue;
      const [x1, y1] = place(pts[i - 1]);
      const [x2, y2] = place(p);
      ctx.strokeStyle = `rgba(${color},${fade})`;
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.stroke();
    }
  }
  function paint(t) {
    const stage = t >= 6.2 ? 'fade' : t >= 5.2 ? 'resolve' : t >= 0.4 ? 'trace' : 'black';
    element.dataset.stage = stage;
    const travel = t < 0.4 ? 0 : t >= 5.2 ? 1 : ease((t - 0.4) / 4.8);
    const headAlpha = t < 0.4 ? 0 : t < 0.9 ? (t - 0.4) / 0.5 : t < 4.8 ? 1 : t < 6.4 ? 1 - (t - 4.8) / 1.6 : 0;
    // The black field itself thins from 5.2s to 7.2s, so the Earth hero comes through.
    const veil = t < 5.2 ? 1 : Math.max(0, 1 - (t - 5.2) / 2);
    const overlay = 1;
    ctx.clearRect(0, 0, width, height);
    ctx.globalAlpha = 1;
    ctx.fillStyle = `rgba(0,0,0,${veil})`;
    ctx.fillRect(0, 0, width, height);
    if (travel > 0 && headAlpha > 0) {
      strand(false, 5.2, '17,51,87', travel);
      strand(true, 2.2, '217,238,252', travel);
      const head = Math.max(2, Math.round(travel * SAMPLES));
      const [x, y] = place(pts[head]);
      const radius = Math.min(width, height) * 0.028;
      const glow = ctx.createRadialGradient(x, y, 0, x, y, radius);
      glow.addColorStop(0, `rgba(255,255,255,${headAlpha})`);
      glow.addColorStop(0.22, `rgba(213,240,255,${headAlpha * 0.9})`);
      glow.addColorStop(0.55, `rgba(140,196,236,${headAlpha * 0.45})`);
      glow.addColorStop(1, 'rgba(140,196,236,0)');
      ctx.fillStyle = glow;
      ctx.beginPath();
      ctx.arc(x, y, radius, 0, TAU);
      ctx.fill();
    }
    element.style.opacity = String(overlay);
  }
  size();
  listen(window, 'resize', size, {passive: true});
  const start = performance.now();
  function frame(now) {
    if (removed) return;
    try {
      if (skipAt) {
        const fade = (now - skipAt) / 400;
        element.style.opacity = String(Math.max(0, 1 - fade));
        if (fade >= 1) remove();
        else raf = requestAnimationFrame(frame);
        return;
      }
      const t = (now - start) / 1000;
      if (t >= 7.2) { remove(); return; }
      paint(t);
      raf = requestAnimationFrame(frame);
    } catch { remove(); }
  }
  raf = requestAnimationFrame(frame);
})();

/* Scene depth for the homepage. The permanent hero above is unchanged. Reduced motion never starts this. */
(() => {
  const reduce = matchMedia('(prefers-reduced-motion: reduce)');
  if (reduce.matches) return;
  const cards = document.querySelectorAll('.reading-index button, .work-grid article, .text-link, .button, .concept-card, .reasoning-exhibit');
  for (const card of cards) {
    card.addEventListener('pointermove', event => {
      const rect = card.getBoundingClientRect();
      if (!rect.width || !rect.height) return;
      const x = (event.clientX - rect.left) / rect.width - 0.5;
      const y = (event.clientY - rect.top) / rect.height - 0.5;
      card.style.transform = `perspective(900px) rotateX(${(-y * 6).toFixed(2)}deg) rotateY(${(x * 8).toFixed(2)}deg)`;
    });
    card.addEventListener('pointerleave', () => { card.style.transform = ''; });
  }
  const host = document.querySelector('.front-door');
  if (!host) return;
  const canvas = document.createElement('canvas');
  canvas.className = 'hero-field';
  canvas.setAttribute('aria-hidden', 'true');
  host.prepend(canvas);
  const gl = canvas.getContext('webgl2', {alpha: true, antialias: false, powerPreference: 'low-power'});
  const flat = gl ? null : canvas.getContext('2d');
  if (!gl && !flat) return;
  let program = null, buffer = null, resolution = null, mouse = null, time = null;
  if (gl) {
    const compile = (type, source) => {
      const shader = gl.createShader(type);
      gl.shaderSource(shader, source);
      gl.compileShader(shader);
      return gl.getShaderParameter(shader, gl.COMPILE_STATUS) ? shader : null;
    };
    const vertex = compile(gl.VERTEX_SHADER, 'attribute vec2 p;void main(){gl_Position=vec4(p,0.,1.);}');
    const fragment = compile(gl.FRAGMENT_SHADER, 'precision mediump float;uniform vec2 r;uniform vec2 m;uniform float t;void main(){vec2 u=gl_FragCoord.xy/r;vec2 q=u-.5;q.x*=r.x/r.y;float d=length(q-vec2(m.x-.5,.2));float glow=exp(-d*d*7.)*(.55+.15*sin(t));vec3 base=vec3(.071,.078,.090);vec3 light=vec3(.549,.769,.925)*glow;gl_FragColor=vec4(base+light,.55);}');
    if (!vertex || !fragment) return;
    program = gl.createProgram();
    gl.attachShader(program, vertex);
    gl.attachShader(program, fragment);
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) return;
    buffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1,1,-1,-1,1,-1,1,1,-1,1,1]), gl.STATIC_DRAW);
    resolution = gl.getUniformLocation(program, 'r');
    mouse = gl.getUniformLocation(program, 'm');
    time = gl.getUniformLocation(program, 't');
  }
  const pointer = {x: 0.62, y: 0.42};
  host.addEventListener('pointermove', event => {
    const rect = host.getBoundingClientRect();
    pointer.x = (event.clientX - rect.left) / rect.width;
    pointer.y = (event.clientY - rect.top) / rect.height;
  });
  function size() {
    const rect = host.getBoundingClientRect();
    const dpr = Math.min(devicePixelRatio || 1, host.clientWidth < 800 ? 1.5 : 2);
    canvas.width = Math.max(1, Math.round(rect.width * dpr));
    canvas.height = Math.max(1, Math.round(rect.height * dpr));
  }
  let frameId = 0;
  let active = false;
  function frame(now) {
    if (!active) return;
    if (gl && program) {
      gl.viewport(0, 0, canvas.width, canvas.height);
      gl.useProgram(program);
      gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
      const location = gl.getAttribLocation(program, 'p');
      gl.enableVertexAttribArray(location);
      gl.vertexAttribPointer(location, 2, gl.FLOAT, false, 0, 0);
      gl.uniform2f(resolution, canvas.width, canvas.height);
      gl.uniform2f(mouse, pointer.x, pointer.y);
      gl.uniform1f(time, now * 0.001);
      gl.drawArrays(gl.TRIANGLES, 0, 6);
    } else if (flat) {
      flat.clearRect(0, 0, canvas.width, canvas.height);
      const glow = flat.createRadialGradient(canvas.width * pointer.x, canvas.height * 0.42, 0, canvas.width * pointer.x, canvas.height * 0.42, canvas.width * 0.45);
      glow.addColorStop(0, 'rgba(140,196,236,.35)');
      glow.addColorStop(1, 'rgba(18,20,23,0)');
      flat.fillStyle = glow;
      flat.fillRect(0, 0, canvas.width, canvas.height);
    }
    frameId = requestAnimationFrame(frame);
  }
  function setActive(next) {
    active = next && !document.hidden;
    cancelAnimationFrame(frameId);
    if (active) frameId = requestAnimationFrame(frame);
  }
  size();
  addEventListener('resize', size, {passive: true});
  document.addEventListener('visibilitychange', () => setActive(active));
  const observer = new IntersectionObserver(entries => setActive(entries.some(entry => entry.isIntersecting)));
  observer.observe(host);
})();

/* Homepage scenes arrive with a short blurred fade. Reduced motion and no-JS leave them visible. */
(() => {
  const reduce = matchMedia('(prefers-reduced-motion: reduce)');
  const sections = document.querySelectorAll('.home-content > section');
  if (!sections.length || reduce.matches || typeof IntersectionObserver !== 'function') return;
  const seen = new IntersectionObserver(entries => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      entry.target.classList.remove('scene-await');
      entry.target.classList.add('scene-arrive');
      seen.unobserve(entry.target);
    }
  }, {threshold: 0.16, rootMargin: '0px 0px -8% 0px'});
  for (const section of sections) {
    section.classList.add('scene-await');
    seen.observe(section);
  }
})();
