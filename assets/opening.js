/* Governed Logic opening. Native rendering; no bitmap identity or external dependency. */
(() => {
  'use strict';
  const TAU = Math.PI * 2;
  const clamp = x => Math.max(0, Math.min(1, x));
  const ease = x => { x = clamp(x); return x*x*x*(x*(x*6-15)+10); };
  const mix = (a,b,t) => a+(b-a)*t;
  const rand = n => { const x=Math.sin(n*127.1+311.7)*43758.5453123; return x-Math.floor(x); };
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  const siteCanvas = document.getElementById('siteCanvas');
  if (!siteCanvas) return;
  const context = siteCanvas.getContext('2d', {alpha:false});
  if (!context) return; // The semantic HTML identity is the no-canvas fallback.
  let width=0, height=0, dpr=1, intro=null, raf=0, deadline=0, finishTimer=0;
  const scene = document.createElement('canvas');
  const sceneCtx = scene.getContext('2d', {alpha:false});
  const atmosphere = document.createElement('canvas');
  const atmosphereCtx = atmosphere.getContext('2d', {alpha:false});
  if (!sceneCtx || !atmosphereCtx) return;
  let layout;
  const materialEarth=window.GLCreateEarth?.(()=>resize());
  const fallbackSurface=materialEarth?null:document.createElement('canvas');
  const fallbackContext=fallbackSurface?.getContext('2d');
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
  const count=matchMedia('(max-width:600px)').matches?3200:6000;
  const particles=Array.from({length:count},(_,i)=>{
    const lat=Math.asin(1-2*(i+.5)/count),lon=i*2.3999632297%TAU-Math.PI;
    const petal=i%24,theta=Math.floor(i/24)/Math.ceil(count/24)*TAU;
    const a=petal/24*TAU,x=.5+.5*Math.cos(theta),y=.5*Math.sin(theta);
    return {a:i*2.3999632297,r:rand(i+1),s:rand(i+999),sx:x*Math.cos(a)-y*Math.sin(a),sy:x*Math.sin(a)+y*Math.cos(a),lat,lon,land:inLand(lon*180/Math.PI,lat*180/Math.PI)};
  });
  // Procedural orthographic Earth surface, generated once from geographic silhouettes.
  const globeTexture=document.createElement('canvas');globeTexture.width=512;globeTexture.height=512;
  const textureContext=globeTexture.getContext('2d');
  if(!textureContext)return;
  const pixels=textureContext.createImageData(512,512);
  for(let y=0;y<512;y++)for(let x=0;x<512;x++){
    const nx=(x-255.5)/256,ny=(255.5-y)/256,rr=nx*nx+ny*ny;
    if(rr>1)continue;
    const z=Math.sqrt(1-rr),lat=Math.asin(ny),lon=Math.atan2(nx,z)-.38;
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
    if(materialEarth)ctx.drawImage(materialEarth.render(width,height,dpr,cx,cy,r,cap,layout.scale),0,0,width,height);
    else if(fallbackContext){
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
      ctx.drawImage(fallbackSurface,0,0,width,height);
    }
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
    const element=document.createElement('div');element.id='glIntro';element.setAttribute('aria-hidden','true');
    const canvas=document.createElement('canvas');canvas.className='intro-canvas';
    const ctx=canvas.getContext('2d',{alpha:false});if(!ctx)return;
    const identity=document.querySelector('#site .identity').cloneNode(true);
    identity.querySelectorAll('[id]').forEach(n=>n.id+='-intro');
    identity.querySelectorAll('[fill],[stroke],[filter]').forEach(n=>{for(const a of ['fill','stroke','filter']){const v=n.getAttribute(a);if(v?.startsWith('url(#'))n.setAttribute(a,v.replace(')', '-intro)'));}});
    element.append(canvas,identity);intro={element,canvas,ctx,identity};size(canvas,ctx);
    document.body.appendChild(element);
    // Independent safety deadline removes the overlay even after a rendering failure.
    deadline=setTimeout(removeIntro,11700);
    motion.addEventListener('change',motionChanged);
    document.addEventListener('visibilitychange',visibilityChanged);
    const start=performance.now();
    function frame(now) {
      if(!intro)return;
      try {
        const t=(now-start)/1000;
        ctx.fillStyle='#000';ctx.fillRect(0,0,width,height);
        const u=Math.min(width,height),cx=width*.5,cy=height*.5;
        if(t>=2 && t<2.85){
          const a=ease((t-2)/.85),r=.5+a*3;
          if(a>.05)glow(ctx,cx,cy,u*.065*a,'255,255,255',a);
          ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(cx,cy,r,0,TAU);ctx.fill();
        }
        const reveal=ease((t-8.55)/1.65);
        if(reveal>0){ctx.globalAlpha=reveal;ctx.drawImage(t<10.35?atmosphere:scene,0,0,width,height);ctx.globalAlpha=1;}
        if(t>=2.85 && t<10.35){
          const burst=ease((t-2.85)/.8),orbit=ease((t-3.45)/1.25),petal=ease((t-4.25)/1.5),sphere=ease((t-6.55)/1.3),settle=ease((t-7.95)/2.15);
          const radius=u*.31,earthX=mix(cx,layout.cx,settle),earthY=mix(cy,layout.earthY,settle),rx=mix(u*.245,layout.earthR,settle),ry=rx;
          const green=ease((t-5.05)/1.25)*(1-sphere),rotation=(t-4.2)*.08;
          if(sphere>.5)earth(ctx,earthX,earthY,rx,settle,ease((sphere-.5)*2));
          ctx.globalCompositeOperation='lighter';
          for(let i=0;i<count;i++){
            const p=particles[i],a=p.a+(t-3.3)*(.45+p.s*.6)*orbit,dist=u*(.12+p.r*.5)*burst;
            let x=cx+Math.cos(a)*dist,y=cy+Math.sin(a)*dist;
            const px=p.sx*Math.cos(rotation)-p.sy*Math.sin(rotation),py=p.sx*Math.sin(rotation)+p.sy*Math.cos(rotation);
            x=mix(x,cx+px*radius,petal);y=mix(y,cy+py*radius,petal);
            const lo=p.lon+.38,z=Math.cos(p.lat)*Math.cos(lo);
            x=mix(x,earthX+Math.cos(p.lat)*Math.sin(lo)*rx,sphere);y=mix(y,earthY-Math.sin(p.lat)*ry,sphere);
            const capDepth=(y-(earthY-rx))/Math.max(.3,layout.scale);
            const capFade=mix(1,1-ease((capDepth-28)/120),settle);
            let alpha=(.35+p.s*.65)*mix(1,z<0?.06:p.land?.95:.14,sphere)*(1-ease((t-8.2)/1.1))*capFade;
            const g=green*(p.s>.35?1:.2),red=Math.round(mix(255,10,g)),blue=Math.round(mix(255,65,g));
            ctx.fillStyle=`rgba(${red},255,${blue},${alpha})`;
            const size=(.55+p.s*.75)*Math.min(1.3,Math.max(.8,width/1400));
            ctx.fillRect(x-size/2,y-size/2,size,size);
          }
          ctx.globalCompositeOperation='source-over';
          if(t<3.5)glow(ctx,cx,cy,u*.05,'255,255,255',1-ease((t-2.85)/.65));
        }
        identity.style.opacity=String(ease((t-9.0)/1.25));
        if(t>=11){element.classList.add('is-finished');finishTimer=setTimeout(removeIntro,470);return;}
        raf=requestAnimationFrame(frame);
      } catch { removeIntro(); }
    }
    raf=requestAnimationFrame(frame);
  }catch{removeIntro();}
})();
