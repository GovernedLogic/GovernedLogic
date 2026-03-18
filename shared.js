function toggleTheme(){
  const h=document.documentElement,dark=h.getAttribute('data-theme')==='dark';
  h.setAttribute('data-theme',dark?'light':'dark');
  document.getElementById('sunIcon').style.display=dark?'none':'block';
  document.getElementById('moonIcon').style.display=dark?'block':'none';
  try{localStorage.setItem('gl-theme',dark?'light':'dark');}catch(e){}
}
(function(){
  try{
    const t=localStorage.getItem('gl-theme'),sys=window.matchMedia('(prefers-color-scheme: dark)').matches;
    const theme=t||(sys?'dark':'light');
    document.documentElement.setAttribute('data-theme',theme);
    if(theme==='dark'){document.getElementById('sunIcon').style.display='block';document.getElementById('moonIcon').style.display='none';}
  }catch(e){}
})();
window.addEventListener('scroll',function(){
  const s=document.documentElement,bar=document.getElementById('progress-bar');
  if(bar){const pct=(s.scrollTop/(s.scrollHeight-s.clientHeight))*100;bar.style.width=Math.min(pct,100)+'%';}
});
