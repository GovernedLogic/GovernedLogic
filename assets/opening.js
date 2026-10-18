/* Governed Logic opening. Native rendering; no bitmap identity or external dependency. */
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
            const petalLight=.67+.33*clamp(.5+petalDepth*2);
            const surfaceLight=p.land?.55+.45*front:.13+.2*front;
            const depthLight=z<0?.018:surfaceLight;
            const spatialLight=mix(mix(1,orbitalLight,orbit),petalLight,petal);
            const alpha=clamp((.21+p.s*.48)*leader*mix(spatialLight,depthLight,sphere)*mix(1,1.15,globeReadability)*particleFade*capFade);
            // White carries the form. A selected minority warms into green;
            // restrained blue on the globe anticipates its material atmosphere.
            const selected=p.c>.76?1:p.c>.62?.32:0,g=green*selected;
            const blueSphere=sphere*(1-g)*.55;
            const red=Math.round(mix(mix(245,105,g),112,blueSphere));
            const grn=Math.round(mix(mix(249,212,g),190,blueSphere));
            const blue=Math.round(mix(mix(255,151,g),236,blueSphere));
            ctx.fillStyle=`rgba(${red},${grn},${blue},${alpha})`;
            const depthSize=mix(mix(1,.9+orbitalDepth*.18,orbit*(1-petal)),.88+.22*front,sphere);
            const size=(.58+p.s*.58)*(p.c>.988?1.15:1)*depthSize*Math.min(1.15,Math.max(.72,width/1400));
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
