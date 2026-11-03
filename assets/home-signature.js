/* Homepage signature: truth at the top of one axis, down the chain, out to every edge. Replaces the logo fly-up.
   Decorative only. Adds one aria-hidden SVG inside .gl-hero-art, whose size CSS already fixes, and nothing else.
   Plays once per browser session and only without reduced motion. After that the still end state shows at once. */
(()=>{
const art=document.querySelector('body.gl-home-page #explore .gl-hero-art'),chain=document.querySelector('body.gl-home-page .gl-chain');
if(!art||!chain)return;
const NS='http://www.w3.org/2000/svg';
function build(){
  const old=art.querySelector('.gl-sig');if(old)old.remove();
  const a=art.getBoundingClientRect(),c=chain.getBoundingClientRect(),W=Math.round(a.width),H=Math.round(a.height);
  if(W<40||H<40)return;
  const p=Math.min(1,innerWidth/1440),inside=c.top<a.bottom-8,ax=c.left-a.left-(innerWidth>900?46*p:14);
  const src=inside?[ax,Math.min(H-8,c.bottom-a.top)]:[W/2,H-6];
  const keep=[c.left-a.left-60,c.top-a.top-30,c.right-a.left+20,c.bottom-a.top+20];
  let s=1447;const r=()=>(s=s*16807%2147483647)/2147483647;
  const n=innerWidth>900?46:30,pts=[];
  for(let t=0;pts.length<n&&t<4000;t++){
    const x=W*(.14+.86*r()),y=H*r();
    if(x>keep[0]&&x<keep[2]&&y>keep[1]&&y<keep[3])continue;
    if(pts.some(q=>Math.hypot(q[0]-x,q[1]-y)<Math.min(W,H)*.09))continue;
    pts.push([x,y]);
  }
  const dist=q=>Math.hypot(q[0]-src[0],q[1]-src[1]);
  pts.sort((u,v)=>dist(u)-dist(v));
  const far=Math.max(...pts.map(dist),1);
  const svg=document.createElementNS(NS,'svg');
  svg.setAttribute('class','gl-sig');svg.setAttribute('viewBox',`0 0 ${W} ${H}`);svg.setAttribute('aria-hidden','true');svg.setAttribute('focusable','false');
  const add=(tag,at,d)=>{const e=document.createElementNS(NS,tag);for(const k in at)e.setAttribute(k,at[k]);e.style.setProperty('--d',d+'ms');svg.appendChild(e);};
  const placed=[src],delay=q=>Math.round(2050+1500*dist(q)/far);
  for(const q of pts){
    const near=placed.map(o=>[Math.hypot(o[0]-q[0],o[1]-q[1]),o]).sort((u,v)=>u[0]-v[0]);
    const d=delay(q);
    near.slice(0,q===pts[0]?1:2).forEach(([,o],i)=>add('line',{x1:o[0],y1:o[1],x2:q[0],y2:q[1],pathLength:1,'stroke-opacity':i?.45:1},d-260));
    placed.push(q);
  }
  for(const q of pts)add('circle',{cx:q[0],cy:q[1],r:1.6+r()*1.6,'fill-opacity':.55+r()*.45},delay(q));
  add('circle',{cx:src[0],cy:src[1],r:3,class:'gl-sig-src'},1900);
  art.appendChild(svg);
}
build();
let run=matchMedia('(prefers-reduced-motion: no-preference)').matches;
if(run){try{if(sessionStorage.getItem('gl-sig'))run=false;else sessionStorage.setItem('gl-sig','1');}catch(e){}}
if(run)document.body.classList.add('gl-sig-run');
let t;addEventListener('resize',()=>{clearTimeout(t);t=setTimeout(()=>{document.body.classList.remove('gl-sig-run');build();},200);},{passive:true});
})();
