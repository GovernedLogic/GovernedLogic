/* Logo chime: replaces the old opening on the homepage (Paul, 2026-11-01; C8, WEB-215; WEB-227 FIFTH).
   A copy of the header mark glows over the hero for about 1.6s, then settles into its place in the header.
   Decorative only: aria-hidden, takes no pointer events, hides and delays nothing. Skipped under
   prefers-reduced-motion; plays once per browser session. */
(()=>{
  try{
    if(matchMedia('(prefers-reduced-motion: reduce)').matches||sessionStorage.getItem('gl-chime'))return;
    sessionStorage.setItem('gl-chime','1');
  }catch(e){return;}
  const mark=document.querySelector('#gl-home-bar .site-brand img');
  const art=document.querySelector('#explore .gl-hero-art')||document.getElementById('explore');
  if(!mark||!art||!mark.animate)return;
  const to=mark.getBoundingClientRect(),a=art.getBoundingClientRect();
  if(!to.width)return;
  const top=Math.max(a.top,to.bottom),bottom=Math.min(a.bottom,innerHeight);
  const cx=bottom>top?(Math.max(a.left,0)+Math.min(a.right,innerWidth))/2:innerWidth/2;
  const cy=bottom>top?(top+bottom)/2:(to.bottom+innerHeight)/2;
  const size=Math.max(88,Math.min(200,Math.min(innerWidth,innerHeight)*.22));
  const s=size/to.width,dx=cx-size/2-to.left,dy=cy-size/2-to.top;
  const el=new Image();
  el.src=mark.currentSrc||mark.src;el.alt='';el.className='gl-chime';el.setAttribute('aria-hidden','true');
  Object.assign(el.style,{left:to.left+'px',top:to.top+'px',width:to.width+'px',height:to.height+'px'});
  document.body.appendChild(el);
  const glow=(r,o)=>`drop-shadow(0 0 ${r}px rgba(22,140,250,${o}))`,at=`translate(${dx}px,${dy}px) scale(${s})`;
  const run=el.animate([
    {transform:at+' rotate(-60deg)',opacity:0,filter:glow(0,0)},
    {offset:.3,transform:at+' rotate(0deg)',opacity:1,filter:glow(4,.9)},
    {offset:.5,transform:at+' rotate(0deg)',opacity:1,filter:glow(1.5,.5)},
    {transform:'none',opacity:1,filter:glow(0,0)}
  ],{duration:1600,easing:'cubic-bezier(.3,0,.2,1)'});
  const hide=mark.animate([{opacity:0},{opacity:0,offset:.97},{opacity:1}],{duration:1600});
  const end=()=>{run.finish();hide.finish();};
  addEventListener('scroll',end,{once:true,passive:true});
  run.finished.catch(()=>{}).then(()=>{removeEventListener('scroll',end);el.remove();});
})();
